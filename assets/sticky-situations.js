/* Sticky Situations.

   One room per 4-digit code, held by a Cloudflare Durable Object. The client is
   deliberately thin: it never decides the phase, the situation, whose turn it is
   or who the host is, because two browsers would disagree. It sends "I played
   this" and renders whatever the room says is true.

   Three things this page is never sent and therefore cannot leak: anybody
   else's hand, who played which card before the round has scored, and who voted
   for what. All three are withheld in the Worker. Cards are voted on by SLOT,
   and the slot order is reshuffled every round, so this file never holds a
   mapping from card to player. */
(function () {
  var API = /^(localhost|127\.0\.0\.1)$/.test(location.hostname)
    ? "http://127.0.0.1:8787"
    : "https://sticky.charlietrenorden.com";
  var WS = API.replace(/^http/, "ws");

  var CODE_RE = /^[0-9]{4}$/;
  var el = function (id) { return document.getElementById(id); };
  var ws = null, room = null, myName = null, token = null;
  var beat = null, retry = null, tries = 0, paused = false;
  var last = null, serial = null, picked = null, swapping = false;

  /* Identity that survives the socket. A phone that locks its screen, a tab left
     in the background, a train going into a tunnel: all of them kill the
     websocket, and without this you come back as a second seat while your old
     one sits in the room holding a hand nobody can play.

     sessionStorage, NOT localStorage: the room treats a second join on the same
     token as the same person returning and closes the older socket, so two tabs
     in one browser would share a seat and take turns kicking each other off
     forever. Per-tab storage still survives a reload, which is the case the
     token exists for. */
  function myToken() {
    var t = null;
    try { t = sessionStorage.getItem("sticky-token"); } catch (x) {}
    if (!/^[A-Za-z0-9-]{8,64}$/.test(t || "")) {
      t = (crypto.randomUUID ? crypto.randomUUID()
        : "t" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10));
      try { sessionStorage.setItem("sticky-token", t); } catch (x) {}
    }
    return t;
  }

  function show(view) {
    el("lobby").hidden = view !== "lobby";
    el("room").hidden = view !== "room";
  }
  function fail(msg) { el("err").textContent = msg; }
  function note(msg) { el("tally").textContent = msg; }

  function send(o) {
    if (!ws || ws.readyState !== 1) return false;
    try { ws.send(JSON.stringify(o)); return true; } catch (x) { return false; }
  }

  function connect(codeIn, name) {
    room = codeIn;
    myName = name;
    token = myToken();
    try { localStorage.setItem("sticky-name", name); } catch (x) {}
    history.replaceState(null, "", "?room=" + codeIn);
    el("code").textContent = codeIn;
    show("room");
    open();
  }

  function open() {
    paused = false;
    clearTimeout(retry);
    if (ws) { try { ws.onclose = null; ws.close(); } catch (x) {} }
    ws = new WebSocket(WS + "/api/ws?code=" + encodeURIComponent(room));

    ws.onopen = function () {
      tries = 0;
      send({ t: "join", name: myName, token: token });
      /* The room answers "ping" from the runtime itself, so this keeps the
         socket warm without waking the Durable Object or costing anything. A
         round spends most of its life silent while people argue. */
      clearInterval(beat);
      beat = setInterval(function () {
        if (ws && ws.readyState === 1) { try { ws.send("ping"); } catch (x) {} }
      }, 25000);
    };

    ws.onmessage = function (e) {
      if (e.data === "pong") return;
      var s;
      try { s = JSON.parse(e.data); } catch (x) { return; }
      if (s.t === "state") render(s);
    };

    ws.onclose = function () {
      clearInterval(beat);
      if (paused) return;
      tries += 1;
      var wait = Math.min(8000, 400 * Math.pow(2, tries - 1));
      note(tries > 2 ? "Reconnecting…" : "");
      retry = setTimeout(open, wait);
    };

    ws.onerror = function () {
      if (el("lobby").hidden === false) fail("Could not reach the room. Try again.");
    };
  }

  /* A backgrounded tab has its timers throttled, so the heartbeat stops and the
     socket usually dies while nobody is looking. Coming back to the tab, or back
     onto a network, is the moment to check rather than wait out the backoff.
     Every route back in clears `paused` itself rather than checking it: a phone
     that fires pagehide when you switch apps and never fires pageshow would
     otherwise sit on a dead socket showing a round that had long since moved. */
  function wake() {
    if (!room) return;
    paused = false;
    if (!ws || ws.readyState === 3 || ws.readyState === 2) { tries = 0; open(); }
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") wake();
  });
  window.addEventListener("pageshow", wake);
  window.addEventListener("online", wake);

  /* ------------------------------------------------------------- rendering -- */

  function seatRow(q, phase) {
    /* "Watching" only means something once a game exists. Before it starts
       nobody is playing yet, so marking the whole lobby as watchers reads as if
       the room is broken. */
    var watching = !q.playing && phase !== "lobby";
    var li = document.createElement("li");
    li.className = "seat" + (watching ? " watching" : "");
    var nm = document.createElement("span");
    nm.className = "nm";
    nm.textContent = q.name;
    li.appendChild(nm);
    if (!watching) {
      var sc = document.createElement("span");
      sc.className = "sc";
      sc.textContent = q.score;
      /* A score of zero before anybody has played is noise, not information. */
      if (phase !== "lobby") li.appendChild(sc);
      /* A tick means "this player has done the thing the round is waiting for".
         Nothing is shown in a phase that is not waiting on anybody. */
      var done = phase === "playing" ? q.played : phase === "voting" ? q.voted : false;
      if (done) {
        var tick = document.createElement("span");
        tick.className = "tick";
        tick.textContent = "✓";
        li.appendChild(tick);
      }
    } else {
      var w = document.createElement("span");
      w.textContent = "watching";
      li.appendChild(w);
    }
    return li;
  }

  function cardBtn(text, opts) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "card" + (opts.cls ? " " + opts.cls : "");
    b.appendChild(document.createTextNode(text));
    if (opts.who) {
      var w = document.createElement("span");
      w.className = "who";
      w.textContent = opts.who;
      b.appendChild(w);
    }
    if (opts.votes !== undefined && opts.votes !== null) {
      var v = document.createElement("span");
      v.className = "votes";
      v.textContent = opts.votes === 1 ? "1 vote" : opts.votes + " votes";
      b.appendChild(v);
    }
    if (opts.onClick) b.addEventListener("click", opts.onClick);
    else b.disabled = true;
    return b;
  }

  function render(s) {
    last = s;
    /* Bumped by the room on every transition, so a client clears its own
       selection when the round turns over rather than only the host who pressed
       the button. */
    if (s.serial !== serial) { serial = s.serial; picked = null; }

    var you = s.you;
    el("progress").textContent = s.phase === "lobby" ? ""
      : s.phase === "finished" ? "Ten rounds played"
      : "Round " + s.round + " of " + s.rounds;

    /* Hidden once the game is over: the Final Scores list below is the same
       scoreboard, and printing it twice makes the reader check whether the two
       disagree. */
    var seats = el("seats");
    seats.hidden = s.phase === "finished";
    seats.textContent = "";
    if (!seats.hidden) {
      s.players.forEach(function (q) { seats.appendChild(seatRow(q, s.phase)); });
    }

    el("preGame").hidden = s.phase !== "lobby";
    el("play").hidden = s.phase === "lobby" || s.phase === "finished";
    el("over").hidden = s.phase !== "finished";

    if (s.phase === "lobby") return renderLobby(s);
    if (s.phase === "finished") return renderFinal(s);
    renderRound(s);
  }

  function renderLobby(s) {
    var enough = s.players.length >= 3;
    el("startRow").hidden = !s.you.admin;
    el("beginBtn").disabled = !enough;
    el("waiting").textContent = s.you.admin
      ? (enough ? "Everyone in? Start when you are ready."
                : "Sticky Situations needs three players. Send the code round.")
      : (enough ? "Waiting for " + hostName(s) + " to start."
                : "Sticky Situations needs three players. Send the code round.");
  }

  function hostName(s) {
    /* The host is the lowest seat still connected, and the room sends players in
       seat order, so the first playing entry is the host. */
    return s.players.length ? s.players[0].name : "the host";
  }

  function renderRound(s) {
    var you = s.you;

    el("modifier").hidden = !s.modifier;
    if (s.modifier) {
      el("modifier").textContent = s.modifier === "worst"
        ? "Worst card wins this round"
        : "Points are doubled this round";
    }
    el("situation").textContent = s.situation || "";
    el("criteria").textContent = s.criteria || "";

    /* Your hand, while there is still something to do with it. */
    var showHand = s.phase === "playing" && you.playing;
    el("handWrap").hidden = !showHand;
    if (showHand) {
      /* The swap is spent, or the round has moved on, so disarm rather than
         leave a card tap doing something the player has forgotten they armed. */
      if (you.redrawUsed || you.played) swapping = false;
      el("swapBtn").hidden = you.redrawUsed || you.played;
      el("swapBtn").textContent = swapping ? "Keep them all" : "Swap a card";

      var hand = el("hand");
      hand.textContent = "";
      you.hand.forEach(function (text, i) {
        var idx = you.handCards[i];
        hand.appendChild(cardBtn(text, {
          cls: you.played ? "spent" : (picked === idx ? "chosen" : "") + (swapping ? " swapping" : ""),
          onClick: you.played ? null : function () {
            if (swapping) { swapping = false; send({ t: "redraw", card: idx }); return; }
            picked = idx;
            send({ t: "play", card: idx });
          },
        }));
      });
      el("handNote").textContent = you.played
        ? "Played. Waiting for the rest of the room."
        : swapping ? "Pick the card to send back. You get one swap a game."
        : "";
    }

    /* The table. Anonymous until the round has scored: this page is not sent an
       owner before then, so there is nothing here to hide. */
    var table = s.table;
    el("tableWrap").hidden = !table;
    if (table) {
      el("tableHead").textContent = s.phase === "voting" ? "Pick The Winner"
        : s.phase === "scored" ? "The Result" : "On The Table";
      var wrap = el("table");
      wrap.textContent = "";
      var top = 0;
      table.forEach(function (c) { if (c.votes > top) top = c.votes; });
      table.forEach(function (c) {
        var mine = c.slot === you.mySlot;
        var canVote = s.phase === "voting" && you.playing && !mine && !you.voted;
        var cls = [];
        /* Dimmed only while it matters. The treatment exists to say "you cannot
           vote for this one", so once the round has scored it is just another
           card and dimming it would read as a result rather than a rule. */
        if (mine && s.phase !== "scored") cls.push("mine");
        if (picked === "v" + c.slot) cls.push("chosen");
        if (s.phase === "scored" && top > 0 && c.votes === top) cls.push("won");
        wrap.appendChild(cardBtn(c.text, {
          cls: cls.join(" "),
          who: s.phase === "scored" ? ownerName(s, c.owner) : (mine ? "Yours" : null),
          votes: s.phase === "scored" ? c.votes : null,
          onClick: canVote ? function () {
            picked = "v" + c.slot;
            send({ t: "vote", slot: c.slot });
          } : null,
        }));
      });
    }

    /* One host control, wearing two labels. Which transition it performs is
       decided by the room, not here. */
    var canAdvance = you.admin && (s.phase === "discussing" || s.phase === "scored");
    el("hostrow").hidden = !canAdvance;
    if (canAdvance) {
      el("advanceBtn").textContent = s.phase === "discussing" ? "Open the vote"
        : s.round >= s.rounds ? "See the final scores" : "Next round";
    }

    note(roundNote(s));
  }

  function roundNote(s) {
    var you = s.you;
    if (!you.playing) return "You joined after the deal, so you are watching this game out.";
    if (s.phase === "playing") {
      var waiting = s.players.filter(function (q) { return q.playing && !q.played; }).length;
      return waiting ? waiting + " still to play." : "";
    }
    if (s.phase === "discussing") {
      return you.admin ? "Talk it out, then open the vote."
        : "Talk it out. " + hostName(s) + " opens the vote.";
    }
    if (s.phase === "voting") {
      if (!you.voted) return "You cannot vote for your own card.";
      var left = s.players.filter(function (q) { return q.playing && !q.voted; }).length;
      return left ? left + " still to vote." : "";
    }
    if (s.phase === "scored" && s.last) {
      var gained = s.last.gained[you.id];
      var bits = [];
      if (gained !== undefined) bits.push(gained === 1 ? "You scored 1 point." : "You scored " + gained + " points.");
      if (s.last.sweep) {
        /* A sweep on a worst round is nobody voting for you, which is the
           opposite of taking the room. Saying "took the room" there printed the
           reverse of what had just happened. */
        bits.push(s.last.worst
          ? "Nobody voted for " + ownerName(s, s.last.sweep) + "."
          : ownerName(s, s.last.sweep) + " took the room.");
      }
      return bits.join(" ");
    }
    return "";
  }

  function ownerName(s, id) {
    if (!id) return null;
    if (id === s.you.id) return "You";
    for (var i = 0; i < s.players.length; i++) {
      if (s.players[i].id === id) return s.players[i].name;
    }
    return "Someone who left";
  }

  function renderFinal(s) {
    note("");
    var list = el("final");
    list.textContent = "";
    var ranked = s.players.filter(function (q) { return q.playing; })
      .slice().sort(function (a, b) { return b.score - a.score; });
    var top = ranked.length ? ranked[0].score : 0;
    ranked.forEach(function (q) {
      var li = document.createElement("li");
      li.className = "simrow";
      var nm = document.createElement("span");
      nm.className = "simname";
      nm.textContent = q.name;
      var bar = document.createElement("span");
      bar.className = "simbar";
      var fill = document.createElement("span");
      fill.style.width = (top ? Math.round((q.score / top) * 100) : 0) + "%";
      fill.style.background = "var(--accent)";
      bar.appendChild(fill);
      var pct = document.createElement("span");
      pct.className = "simpct";
      pct.textContent = q.score;
      li.appendChild(nm); li.appendChild(bar); li.appendChild(pct);
      list.appendChild(li);
    });
  }

  /* ---------------------------------------------------------------- lobby -- */

  function nameOrNag() {
    var v = el("name").value.trim().slice(0, 24);
    if (!v) { fail("Put your name in first."); el("name").focus(); return null; }
    fail("");
    return v;
  }

  el("startBtn").addEventListener("click", createRoom);
  if (el("startBtn2")) el("startBtn2").addEventListener("click", createRoom);
  function createRoom() {
    var name = nameOrNag();
    if (!name) return;
    el("startBtn").disabled = true;
    fetch(API + "/api/room", { method: "POST" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        el("startBtn").disabled = false;
        if (!j.code) return fail("Could not open a room. Try again.");
        connect(j.code, name);
      })
      .catch(function () {
        el("startBtn").disabled = false;
        fail("Could not open a room. Try again.");
      });
  }

  function joinTyped() {
    var name = nameOrNag();
    if (!name) return;
    var c = (el("joincode").value || "").trim();
    if (!CODE_RE.test(c)) return fail("A room code is four digits.");
    joinCode(c, name);
  }
  el("joinBtn").addEventListener("click", joinTyped);
  el("joincode").addEventListener("keydown", function (e) {
    if (e.key === "Enter") joinTyped();
  });
  if (el("joinBtn2")) el("joinBtn2").addEventListener("click", function () {
    var name = nameOrNag();
    if (name) joinCode(invited, name);
  });

  function joinCode(c, name) {
    /* Asked over HTTP first so a mistyped code can say something useful. Without
       it you open a socket to four digits nobody created and sit there as the
       host of a game nobody else is in, which looks exactly like arriving early. */
    fetch(API + "/api/room?code=" + encodeURIComponent(c))
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j.exists) return fail("No room with that code.");
        connect(c, name);
      })
      .catch(function () { fail("Could not reach the room. Try again."); });
  }

  el("copyBtn").addEventListener("click", function () {
    var url = location.origin + location.pathname + "?room=" + room;
    var done = function () {
      el("copyBtn").textContent = "Copied";
      setTimeout(function () { el("copyBtn").textContent = "Copy invite link"; }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done, done);
    } else { done(); }
  });

  el("swapBtn").addEventListener("click", function () {
    swapping = !swapping;
    if (last) render(last);
  });
  el("beginBtn").addEventListener("click", function () { send({ t: "start" }); });
  el("advanceBtn").addEventListener("click", function () { send({ t: "advance" }); });

  /* Arriving on an invite link. Only one of create and join makes sense then, so
     the other is hidden rather than offered and ignored. */
  var invited = (new URLSearchParams(location.search).get("room") || "").trim();
  if (CODE_RE.test(invited)) {
    el("lobbyTitle").textContent = "Join room " + invited;
    el("lobbyLede").textContent = "Everyone plays a card. Nobody knows whose is whose until the room has voted.";
    el("createBlock").hidden = true;
    el("joinBlock").hidden = false;
  }
  try {
    var saved = localStorage.getItem("sticky-name");
    if (saved) el("name").value = saved;
  } catch (x) {}

  /* theme toggle - shares localStorage with the hub */
  var root = document.documentElement;
  var btn = el("themeBtn"), lbl = el("themeLbl");
  function sync() { lbl.textContent = root.getAttribute("data-theme") === "dark" ? "Dark" : "Light"; }
  sync();
  btn.addEventListener("click", function () {
    var dark = root.getAttribute("data-theme") !== "dark";
    root.setAttribute("data-theme", dark ? "dark" : "light");
    try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch (x) {}
    sync();
  });
})();
