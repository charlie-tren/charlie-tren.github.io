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
  var last = null, serial = null, picked = null, swapping = false, pokeSeen = null;

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
    /* Tapping somebody the round is stuck on pokes them. A whole chip is a big
       target, which is what you want on a phone when you are trying to hurry a
       friend along. */
    var li = document.createElement(q.waiting ? "button" : "li");
    if (q.waiting) {
      li.type = "button";
      li.title = "Poke " + q.name;
      li.addEventListener("click", function () { send({ t: "poke", id: q.id }); });
    }
    li.className = "seat" + (watching ? " watching" : "") +
      (q.waiting ? " stalling" : "") + (q.here === false ? " away" : "");
    var nm = document.createElement("span");
    nm.className = "nm";
    nm.textContent = q.name;
    li.appendChild(nm);
    if (q.bot) {
      var tag = document.createElement("span");
      tag.className = "bottag";
      tag.textContent = "bot";
      li.appendChild(tag);
    }
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
      s.players.forEach(function (q) {
        var row = seatRow(q, s.phase);
        if (row.tagName === "BUTTON") {
          var li = document.createElement("li");
          li.appendChild(row);
          seats.appendChild(li);
        } else {
          seats.appendChild(row);
        }
      });
    }

    /* Somebody poked you. Animate on the counter changing rather than on a
       message, so a poke sent while this tab was asleep still lands when it
       wakes rather than being lost. */
    if (pokeSeen === null) pokeSeen = s.poked || 0;
    else if ((s.poked || 0) > pokeSeen) {
      pokeSeen = s.poked;
      nudge();
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

    /* The theme picker. Shown to everybody so the room can see the choice being
       made, but only the host's taps do anything - a control that silently
       ignores you is worse than one that is plainly not yours. */
    var box = el("themes");
    box.textContent = "";
    (s.menu || []).forEach(function (m) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "theme" + (m.slug === s.deck ? " on" : "");
      b.disabled = !s.you.admin;
      var t = document.createElement("span");
      t.className = "tname";
      t.textContent = m.theme;
      var d = document.createElement("span");
      d.className = "tdesc";
      d.textContent = m.premise;
      var n = document.createElement("span");
      n.className = "trounds";
      /* Said up front, because a 30-card deck gives a much shorter game than
         Plus One and finding that out afterwards would be a nasty surprise. */
      n.textContent = m.rounds + " rounds";
      b.appendChild(t); b.appendChild(d); b.appendChild(n);
      b.addEventListener("click", function () { send({ t: "deck", deck: m.slug }); });
      box.appendChild(b);
    });
    el("botRow").hidden = !s.you.admin;
    el("botN").textContent = s.bots || 0;
    el("botLess").disabled = (s.bots || 0) <= 0;
    el("botMore").disabled = (s.bots || 0) >= (s.maxBots || 5);
    el("botLbl").textContent = (s.bots || 0) === 1 ? "Bot" : "Bots";

    el("startRow").hidden = !s.you.admin;
    el("beginBtn").disabled = !enough;
    /* Bots count towards the three, which is what makes a solo game possible,
       so the line says so rather than sending you off to find two friends. */
    var short = 3 - s.players.length;
    var need = s.you.admin
      ? "Three players needed. Add " + short + (short === 1 ? " bot" : " bots") +
        ", or send the code round."
      : "Three players needed. Send the code round.";
    el("waiting").textContent = s.you.admin
      ? (enough ? "Everyone in? Start when you are ready." : need)
      : (enough ? "Waiting for " + hostName(s) + " to start." : need);
  }

  function hostName(s) {
    /* The host is the lowest seat still connected, and the room sends players in
       seat order, so the first playing entry is the host. */
    return s.players.length ? s.players[0].name : "the host";
  }

  function renderRound(s) {
    var you = s.you;

    /* The instruction, in the words a player needs: what to hunt for in the
       hand, and what the room will be asked at the vote. A reverse round says
       the opposite of every other round, so it is the loud one. */
    var reverse = s.ask === "worst";
    el("ask").textContent = reverse
      ? "REVERSE ROUND: play your BEST card. The room votes for the WORST."
      : "Play your WORST card. The room votes for the best of a bad lot.";
    el("ask").className = "ask" + (reverse ? " reverse" : "");

    el("modifier").hidden = !s.modifier || s.modifier === "reverse";
    if (s.modifier === "double") {
      el("modifier").textContent = "Double blame this round";
    }
    /* The premise sits above the prompt so a player knows what game they are
       in before they read what varies this round. */
    el("premise").textContent = s.premise || "";
    el("sitlabel").textContent = s.situationLabel || "";
    el("situation").textContent = s.situation || "";

    /* What you played. Shown from the moment you play until the round scores,
       after which the table names it as yours anyway. */
    var mine = you.playedText && s.phase !== "scored";
    el("yours").hidden = !mine;
    if (mine) el("yours").textContent = "You played: " + you.playedText;

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
      el("tableHead").textContent = s.phase === "voting"
          ? (reverse ? "Pick The Worst" : "Pick The Best")
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

    /* The room never decides on its own that an absent player has gone: a locked
       phone closes the socket, and guessing there once scored a round without
       somebody's vote. The host decides, and only once there is somebody to
       decide about. */
    /* Only once the round is genuinely half-done. Offered the moment a round
       opened, "Carry on without 3 players" invited the host to skip everybody
       before anybody had a chance to play, which is not waiting, it is just the
       start of a round. */
    var acted = s.players.filter(function (q) {
      return q.playing && (s.phase === "voting" ? q.voted : q.played);
    }).length;
    var stuck = acted > 0 && (s.waiting || []).length > 0;
    el("carryrow").hidden = !(you.admin && stuck);
    if (you.admin && stuck) {
      el("carryBtn").textContent = s.waiting.length === 1
        ? "Carry on without " + s.waiting[0]
        : "Carry on without " + s.waiting.length + " players";
    }

    /* Offered only when the room can actually do it: there has to be a seat
       free and enough undealt cards for the rounds that are left. */
    el("joinRow").hidden = !(you.playing === false && s.canJoin);

    note(roundNote(s));
  }

  function roundNote(s) {
    var you = s.you;
    if (!you.playing) return "You joined after the deal, so you are watching this game out.";
    if (s.phase === "playing") {
      return anyoneActed(s) && s.waiting && s.waiting.length
        ? waitLine(s, "to play") : "";
    }
    if (s.phase === "discussing") {
      return you.admin ? "Talk it out, then open the vote."
        : "Talk it out. " + hostName(s) + " opens the vote.";
    }
    if (s.phase === "voting") {
      if (!you.voted) return "You cannot vote for your own card.";
      return anyoneActed(s) && s.waiting && s.waiting.length
        ? waitLine(s, "to vote") : "";
    }
    if (s.phase === "scored" && s.last) {
      var gained = s.last.gained[you.id];
      var bits = [];
      /* Blame is bad, so taking none is the good outcome and says so. */
      if (gained === 0) bits.push("No blame. Nobody picked yours.");
      else if (gained !== undefined) bits.push("You take " + gained + " blame.");
      if (s.last.sweep) {
        bits.push(ownerName(s, s.last.sweep) + " was picked by the whole room.");
      }
      return bits.join(" ");
    }
    return "";
  }

  /* Nobody has done anything yet is not the same as waiting on somebody. At the
     top of a round everybody is outstanding, and saying so is noise. */
  function anyoneActed(s) {
    return s.players.some(function (q) {
      return q.playing && (s.phase === "voting" ? q.voted : q.played);
    });
  }

  /* Names them, rather than counting them. "Waiting on Bo" tells you who to
     chase; "1 still to vote" tells you nothing you can act on. */
  function waitLine(s, what) {
    var w = s.waiting;
    var who = w.length === 1 ? w[0]
      : w.length === 2 ? w[0] + " and " + w[1]
      : w.slice(0, -1).join(", ") + " and " + w[w.length - 1];
    return "Waiting on " + who + " " + what + ". Tap a name to poke them.";
  }

  /* Being poked. Deliberately physical: a shake, and a buzz on a phone, because
     the whole point is that you are not looking at the screen. */
  function nudge() {
    var page = document.querySelector(".page");
    if (!page) return;
    page.classList.remove("poked");
    void page.offsetWidth;                    /* restart the animation */
    page.classList.add("poked");
    setTimeout(function () { page.classList.remove("poked"); }, 900);
    try { if (navigator.vibrate) navigator.vibrate([90, 60, 90]); } catch (x) {}
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
    el("againRow").hidden = !s.you.admin;
    var list = el("final");
    list.textContent = "";
    /* Ascending: this is golf, and the fewest blame wins. */
    var ranked = s.players.filter(function (q) { return q.playing; })
      .slice().sort(function (a, b) { return a.score - b.score; });
    var top = ranked.reduce(function (m, q) { return Math.max(m, q.score); }, 0);
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
      /* The bar is how much blame you carry, so a long bar is a bad thing and
         the accent would read as a prize. */
      fill.style.background = "var(--soft)";
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
  el("carryBtn").addEventListener("click", function () { send({ t: "carryon" }); });
  el("botMore").addEventListener("click", function () {
    send({ t: "bots", count: ((last && last.bots) || 0) + 1 });
  });
  el("botLess").addEventListener("click", function () {
    send({ t: "bots", count: ((last && last.bots) || 0) - 1 });
  });
  el("joinInBtn").addEventListener("click", function () { send({ t: "joinin" }); });
  el("againBtn").addEventListener("click", function () { send({ t: "restart" }); });
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

  /* A worked round, for the homepage card. The lobby is a name field and a
     button, which tells a viewer nothing about the game, and the shooter cannot
     stand up a four-player room to photograph a real one.

     This goes through the SAME render() as a live game rather than injecting
     markup, so the card cannot drift into showing something the game does not
     do. Every card and the situation are real entries from the Plus One deck.
     No socket is opened and no room is created. */
  if (new URLSearchParams(location.search).get("demo") === "1") {
    var them = [
      { id: "p1", name: "Charlie", score: 7, playing: true, played: true, voted: true },
      { id: "p2", name: "Bo", score: 9, playing: true, played: true, voted: true },
      { id: "p3", name: "Cal", score: 6, playing: true, played: true, voted: true },
      { id: "p4", name: "Di", score: 8, playing: true, played: true, voted: true },
    ];
    show("room");
    el("code").textContent = "1478";
    render({
      t: "state", serial: 1, phase: "scored", round: 4, rounds: 10,
      theme: "Plus One",
      premise: "You have been invited somewhere and you are allowed to bring one person.",
      situationLabel: "Event",
      deck: "plus-one", menu: null, bots: 0, maxBots: 5, canJoin: false,
      situation: "You are at the opening night of your friend's one-man show. It runs two hours and there are eleven seats.",
      modifier: null,
      players: them,
      you: {
        id: "p1", name: "Charlie", admin: true, playing: true,
        hand: [], handCards: [], played: true, voted: true, playedText: null,
        redrawUsed: false, mySlot: 1,
      },
      table: [
        { slot: 0, text: "a bloke in a full morph suit", owner: "p2", votes: 1 },
        { slot: 1, text: "a life-size cardboard cutout of yourself", owner: "p1", votes: 2 },
        { slot: 2, text: "a nan who is 94 and deaf", owner: "p4", votes: 0 },
        { slot: 3, text: "a friend who has just got back from Bali", owner: "p3", votes: 0 },
      ],
      ask: "best",
      last: { round: 4, reverse: false, ask: "best", double: false, sweep: null,
              gained: { p1: 2, p2: 1, p3: 0, p4: 0 } },
    });
  }
})();
