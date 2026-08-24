/* Spectrum - the shared mode for the question pages.

   One room per 4-letter code, held by a Cloudflare Durable Object. The client is
   deliberately thin: it never decides the statement, the order, or who the host
   is, because two browsers would disagree. It sends "I moved" and renders
   whatever the room says is true. */
(function () {
  var API = /^(localhost|127\.0\.0\.1)$/.test(location.hostname)
    ? "http://127.0.0.1:8787"
    : "https://spectrum.charlietrenorden.com";
  var WS = API.replace(/^http/, "ws");

  /* Codes are four digits now. The pattern stays wider than that on purpose:
     rooms created when they were letters are still live and still joinable. */
  var CODE_RE = /^[A-Z0-9]{4}$/;
  var el = function (id) { return document.getElementById(id); };
  var ws = null, me = null, myX = 0.5, myY = 0.5, sendTimer = null, pending = false;
  var mode = "line";
  var room = null, myName = null, token = null;
  var beat = null, retry = null, tries = 0, paused = false;

  /* Identity that survives the socket. A phone that locks its screen, a tab left
     in the background, a train going into a tunnel - all of them kill the
     websocket, and without this you came back as a second dot in a new colour
     while your old one sat on the axis forever.

     sessionStorage, NOT localStorage: the room treats a second join on the same
     token as the same person coming back and closes the older socket, so two
     tabs of this page in one browser shared one seat - and because each of them
     reconnects when its socket closes, they took turns kicking each other off
     forever. Measured at eleven sockets in four seconds between two tabs, with
     one of them always showing whatever it had been told before it was last
     kicked. Per-tab storage still survives a reload, which is the case the token
     exists for. */
  function myToken() {
    var t = null;
    try { t = sessionStorage.getItem("spectrum-token"); } catch (x) {}
    if (!/^[A-Za-z0-9-]{8,64}$/.test(t || "")) {
      t = (crypto.randomUUID ? crypto.randomUUID()
        : "t" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10));
      try { sessionStorage.setItem("spectrum-token", t); } catch (x) {}
    }
    return t;
  }

  function show(view) {
    el("lobby").hidden = view !== "lobby";
    el("room").hidden = view !== "room";
    el("results").hidden = view !== "results";
  }

  function fail(msg) { el("err").textContent = msg; }
  function note(msg) { el("tally").textContent = msg; }

  function send(o) {
    if (!ws || ws.readyState !== 1) return false;
    try { ws.send(JSON.stringify(o)); return true; } catch (x) { return false; }
  }

  function connect(code, name) {
    room = code;
    myName = name;
    token = myToken();
    try { localStorage.setItem("spectrum-name", name); } catch (x) {}
    history.replaceState(null, "", "?room=" + code);
    el("code").textContent = code;
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
      if (pending) pushMove();
      /* The room answers "ping" from the runtime itself, so this keeps the
         socket warm without waking the Durable Object or costing anything. */
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
      /* Reconnecting is the whole point of the token, so a dropped socket is a
         pause rather than the end of the game. */
      tries += 1;
      var wait = Math.min(8000, 400 * Math.pow(2, tries - 1));
      note(tries > 2 ? "Reconnecting…" : "");
      retry = setTimeout(open, wait);
    };

    ws.onerror = function () { if (el("lobby").hidden === false) fail("Could not reach the room. Try again."); };
  }

  /* A backgrounded tab has its timers throttled, so the heartbeat stops and the
     socket usually dies while nobody is looking. Coming back to the tab, or back
     onto a network, is the moment to check rather than wait out the backoff.

     Every route back in clears `paused` itself rather than checking it. A phone
     that fires pagehide when you switch apps and then never fires pageshow used
     to be stuck: coming back to the tab called wake(), wake() saw the flag still
     set and returned, and the page sat there showing a dead socket's last state
     with everyone frozen wherever they were when it died. */
  function wake() {
    if (!room) return;
    paused = false;
    if (!ws || ws.readyState > 1) { tries = 0; open(); }
  }
  document.addEventListener("visibilitychange", function () { if (!document.hidden) wake(); });
  window.addEventListener("online", wake);
  window.addEventListener("pageshow", wake);
  /* pagehide means "closed" or "parked in the back/forward cache". Stop
     reconnecting for now; anything that brings the page back starts it again. */
  window.addEventListener("pagehide", function () {
    paused = true; clearInterval(beat); clearTimeout(retry);
  });

  function render(s) {
    me = s.you;
    mode = s.mode === "plane" ? "plane" : "line";
    document.documentElement.style.setProperty("--me", me.colour);
    el("progress").textContent = s.index + " of " + s.total;

    /* One axis or two is a room setting, so only the host sees the switch, and
       everyone's view follows whatever the room says it is. */
    el("modeSwitch").hidden = !me.admin;
    Array.prototype.forEach.call(el("modeSwitch").children, function (b) {
      b.setAttribute("aria-pressed", b.dataset.mode === mode ? "true" : "false");
    });
    el("statement").hidden = mode !== "line";
    el("track").hidden = mode !== "line";
    el("padwrap").hidden = mode !== "plane";
    el("nextBtn").textContent = mode === "plane" ? "Next pair" : "Next statement";

    /* Other players are drawn separately from you; your own position is the
       slider thumb or the pin, so it is never drawn twice. */
    var others = s.players.filter(function (p) { return p.id !== me.id; });

    if (mode === "plane") paintPlane(s, others);
    else paintLine(s, others);

    var placed = s.players.filter(function (p) { return p.placed; }).length;
    note(s.revealed
      ? "Revealed - " + s.players.length + (s.players.length === 1 ? " player" : " players")
      : placed + " of " + s.players.length + " placed");

    el("hostrow").hidden = !me.admin;
    el("revealBtn").disabled = s.revealed;
    el("revealBtn").textContent = s.revealed ? "Shown" : "Show everyone";
    /* Live as soon as two people have placed, not only once the host has
       advanced - a room that has answered one statement can compare it. */
    el("compareBtn").disabled = !(s.rounds || placed >= 2);

    if (s.results) { paintResults(s.results); show("results"); }
    else show("room");
    /* After show(), never before: a hidden section measures zero, so laying the
       names out first put every one of them in row 0 on top of each other. */
    if (mode === "plane") layoutPadLabels(); else layoutLabels();
  }

  function paintLine(s, others) {
    el("statement").textContent = s.statement;
    others.sort(function (a, b) { return a.x - b.x; });
    var marks = others.map(function (p) {
      return '<span class="dot-m' + (p.placed ? "" : " unplaced") + (s.revealed ? " revealed" : "") +
        '" data-x="' + p.x.toFixed(4) + '" style="--x:' + p.x.toFixed(4) + '">' +
        "<b>" + (s.revealed && p.name ? esc(p.name) : "&nbsp;") + "</b>" +
        '<i style="background:' + p.colour + '"></i></span>';
    });
    marks.push(meLabel(s, "dot-m"));
    el("dots").innerHTML = marks.join("");
  }

  /* Your own position is the slider thumb, or the pin on the square, so it is
     never drawn as a dot. At the reveal it still needs something over it, or
     yours is the one marker on screen that nobody can put a name to. The dot
     inside is present but invisible: it holds the same box as everybody else's,
     so the label sits on the same line and joins the same collision pass. */
  function meLabel(s, cls) {
    if (!s.revealed) return "";
    var mine = null;
    for (var i = 0; i < s.players.length; i++) {
      if (s.players[i].id === me.id) mine = s.players[i];
    }
    if (!mine) return "";
    var y = mine.y === undefined ? 0.5 : mine.y;
    var pos = cls === "pad-m"
      ? ' data-x="' + mine.x.toFixed(4) + '" data-y="' + y.toFixed(4) +
        '" style="left:' + (mine.x * 100).toFixed(2) + "%;top:" + (y * 100).toFixed(2) + '%"'
      : ' data-x="' + mine.x.toFixed(4) + '" style="--x:' + mine.x.toFixed(4) + '"';
    return '<span class="' + cls + ' me revealed"' + pos +
      '><b>You</b><i style="visibility:hidden"></i></span>';
  }

  /* y runs 0 at the top, which is why axes[1][0] labels the top edge. */
  function paintPlane(s, others) {
    var ax = s.axes || [["", ""], ["", ""]];
    el("axLeft").textContent = ax[0][0];
    el("axRight").textContent = ax[0][1];
    el("axTop").textContent = ax[1][0];
    el("axBottom").textContent = ax[1][1];
    el("pad").setAttribute("aria-label",
      ax[0][0] + " to " + ax[0][1] + " across, " + ax[1][0] + " to " + ax[1][1] + " up and down");

    el("paddots").innerHTML = others.map(function (p) {
      var y = p.y === undefined ? 0.5 : p.y;
      return '<span class="pad-m' + (p.placed ? "" : " unplaced") + (s.revealed ? " revealed" : "") +
        '" data-x="' + p.x.toFixed(4) + '" data-y="' + y.toFixed(4) + '"' +
        ' style="left:' + (p.x * 100).toFixed(2) + "%;top:" + (y * 100).toFixed(2) + '%">' +
        "<b>" + (s.revealed && p.name ? esc(p.name) : "&nbsp;") + "</b>" +
        '<i style="background:' + p.colour + '"></i></span>';
    }).concat(meLabel(s, "pad-m")).join("");
    el("mepin").style.left = (myX * 100).toFixed(2) + "%";
    el("mepin").style.top = (myY * 100).toFixed(2) + "%";
  }

  /* Names are laid out by MEASUREMENT, not by a fixed gap in track units. A name
     is many times wider than the dot under it, so "far enough apart" depends on
     how long the names are and how wide the phone is - a constant got both wrong,
     and at the ends of the axis a centred name simply ran off the screen. */
  function layoutLabels() {
    var wrap = el("dots");
    var W = wrap.clientWidth;
    if (!W) return;
    var marks = Array.prototype.slice.call(wrap.children);
    var items = [];
    marks.forEach(function (m) {
      m.style.setProperty("--nudge", "0px");
      m.style.setProperty("--row", 0);
      var b = m.querySelector("b");
      var w = b.offsetWidth;
      if (!w) return;                    /* hidden - mobile, before the reveal */
      /* The slider thumb is 18px wide, so its centre travels from 9px to W-9px,
         not from 0 to W. The markers have to use the same travel or a dot sits
         beside the thumb that put it there. */
      var c = 9 + Number(m.dataset.x) * (W - 18);
      var shift = 0;
      if (c - w / 2 < 0) shift = w / 2 - c;
      else if (c + w / 2 > W) shift = W - (c + w / 2);
      items.push({ m: m, left: c - w / 2 + shift, right: c + w / 2 + shift, shift: shift });
    });
    items.sort(function (a, b) { return a.left - b.left; });
    var lastRight = [];
    items.forEach(function (it) {
      var row = 0;
      while (lastRight[row] !== undefined && it.left < lastRight[row] + 8) row++;
      lastRight[row] = it.right;
      it.m.style.setProperty("--row", row);
      it.m.style.setProperty("--nudge", it.shift.toFixed(1) + "px");
    });
    /* The track reserves headroom for however many rows it actually took, so a
       full room of long names cannot print itself over the statement. */
    wrap.closest(".track").style.setProperty("--rows", Math.max(1, lastRight.length));
  }
  window.addEventListener("resize", function () {
    if (mode === "plane") layoutPadLabels(); else layoutLabels();
  });

  /* Same measured approach as the line, in two directions. A name sits under its
     own dot, is nudged sideways so it cannot leave the square, and is dropped
     line by line until it clears every name already placed. Sorted top-down so
     the one that moves is always the lower of an overlapping pair. */
  function layoutPadLabels() {
    var pad = el("pad");
    var W = pad.clientWidth, H = pad.clientHeight;
    if (!W || !H) return;
    var placed = [];
    Array.prototype.slice.call(el("paddots").children)
      .map(function (m) {
        m.style.setProperty("--nudge", "0px");
        m.style.setProperty("--drop", "0px");
        return { m: m, x: Number(m.dataset.x) * W, y: Number(m.dataset.y) * H };
      })
      .sort(function (a, b) { return a.y - b.y; })
      .forEach(function (it) {
        var b = it.m.querySelector("b");
        var w = b.offsetWidth, h = b.offsetHeight;
        if (!w) return;                  /* hidden - mobile, before the reveal */

        /* Sideways first, so a name near an edge cannot leave the square. */
        var shift = 0;
        if (it.x - w / 2 < 0) shift = w / 2 - it.x;
        else if (it.x + w / 2 > W) shift = W - (it.x + w / 2);
        var left = it.x - w / 2 + shift, right = left + w;

        /* Then a side, BEFORE resolving overlaps rather than after. Flipping a
           label above the dot as a last resort once it had already been placed
           dropped it straight onto a neighbour, which is exactly what the
           overlap loop was there to prevent. */
        var below = it.y + 11 + h <= H;
        var step = (h + 2) * (below ? 1 : -1);
        var top = below ? it.y + 11 : it.y - 11 - h;
        for (var guard = 0; guard < 14; guard++) {
          var clear = placed.every(function (q) {
            return left >= q.right + 4 || right <= q.left - 4 ||
                   top >= q.bottom + 2 || top + h <= q.top - 2;
          });
          if (clear) break;
          top += step;
        }

        it.m.style.setProperty("--nudge", shift.toFixed(1) + "px");
        it.m.style.setProperty("--drop", (top - (it.y + 11)).toFixed(1) + "px");
        placed.push({ left: left, right: right, top: top, bottom: top + h });
      });
  }

  function paintResults(r) {
    el("resHost").hidden = !me.admin;
    var rows = r.you || [];
    el("resCount").textContent = plural(r.rounds, "round");

    if (!rows.length) {
      el("resLede").textContent = "Nobody else has answered the same rounds as you yet.";
      el("simlist").innerHTML = "";
      el("resnote").hidden = true;
      el("roomstats").innerHTML = "";
      return;
    }
    el("resnote").hidden = false;
    var top = rows[0], bottom = rows[rows.length - 1];
    el("resLede").textContent = rows.length === 1
      ? "You and " + top.name + ", across " + plural(top.n, "round") + "."
      : "Closest to you: " + top.name + ". Furthest: " + bottom.name + ".";

    el("simlist").innerHTML = rows.map(function (p) {
      var pct = Math.round(p.agree * 100);
      return '<li class="simrow">' +
        '<i class="swatch" style="background:' + p.colour + '"></i>' +
        '<span class="simname">' + esc(p.name || "Someone") + "</span>" +
        '<span class="simbar"><span style="width:' + pct + "%;background:" + p.colour + '"></span></span>' +
        '<span class="simpct">' + pct + "%</span>" +
        (p.n < r.rounds ? '<span class="simn">' + plural(p.n, "round") + "</span>" : "") +
        "</li>";
    }).join("");

    var stats = "";
    if (r.divided) stats += statBlock("Most divided", r.divided.label);
    if (r.united && r.rounds > 1) stats += statBlock("Most agreed", r.united.label);
    el("roomstats").innerHTML = stats;
  }

  function statBlock(label, statement) {
    return '<div class="stat"><span class="statlbl">' + label + "</span>" +
      '<p class="statq">' + esc(statement) + "</p></div>";
  }

  function resetMe() {
    el("slider").value = 500;
    myX = 0.5;
    myY = 0.5;
    el("mepin").style.left = "50%";
    el("mepin").style.top = "50%";
  }

  function plural(n, word) { return n + " " + word + (n === 1 ? "" : "s"); }

  function esc(t) {
    return String(t).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* Throttled: a drag fires input events every few milliseconds and every one
     would be a round trip to the room and a broadcast to everybody in it.
     A move made before the socket opens is REMEMBERED, not dropped - dragging
     during connect used to leave you showing as unplaced for the whole round. */
  function pushMove() {
    if (!ws || ws.readyState !== 1) { pending = true; return; }
    if (sendTimer) return;
    sendTimer = setTimeout(function () {
      sendTimer = null;
      pending = false;
      send({ t: "move", x: myX, y: myY });
    }, 70);
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      var saved = localStorage.getItem("spectrum-name");
      if (saved) el("name").value = saved;
    } catch (x) {}

    /* An invite link should offer ONE action. Showing "Create a room" as the
       primary button on a page titled "Join room V8FT" is the clunky bit. */
    var joining = (new URLSearchParams(location.search).get("room") || "").toUpperCase();
    if (CODE_RE.test(joining)) {
      el("joincode").value = joining;
      el("lobbyTitle").textContent = "Join room " + joining;
      el("lobbyLede").textContent = "Put your name in and you are in the room.";
      el("createBlock").hidden = true;
      el("joinBlock").hidden = false;
    }

    function join() {
      var name = el("name").value.trim();
      var c = (el("joincode").value.trim() || joining).toUpperCase();
      if (!name) return fail("Put your name in first.");
      if (!CODE_RE.test(c)) return fail("A room code is four digits.");
      fail("");
      /* Every four-letter code addresses a valid room object, so a mistyped one
         used to drop you into a real but empty room - alone, as its host, with
         nothing to distinguish that from being the first to arrive. */
      setJoining(true);
      fetch(API + "/api/room?code=" + encodeURIComponent(c))
        .then(function (r) { return r.json(); })
        .then(function (d) {
          setJoining(false);
          if (!d.exists) return fail("No room with that code. Check it, or create your own.");
          connect(c, name);
        })
        .catch(function () {
          setJoining(false);
          fail("Could not reach the room. Try again.");
        });
    }

    function setJoining(on) {
      [el("joinBtn"), el("joinBtn2")].forEach(function (b) {
        if (b) { b.disabled = on; b.textContent = on ? "Checking…" : (b.id === "joinBtn" ? "Join" : "Join room"); }
      });
    }

    function create() {
      var name = el("name").value.trim();
      if (!name) return fail("Put your name in first.");
      fail("");
      el("startBtn").disabled = true;
      if (el("startBtn2")) el("startBtn2").disabled = true;
      fetch(API + "/api/room", { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.code) throw new Error("no code");
          /* A new room is a new game, so it must not inherit the seat and colour
             held by the token from the last one. */
          try { sessionStorage.removeItem("spectrum-token"); } catch (x) {}
          connect(d.code, name);
        })
        .catch(function () {
          fail("Could not create a room. Try again.");
          el("startBtn").disabled = false;
          if (el("startBtn2")) el("startBtn2").disabled = false;
        });
    }

    el("startBtn").addEventListener("click", create);
    el("startBtn2").addEventListener("click", create);
    el("joinBtn").addEventListener("click", join);
    el("joinBtn2").addEventListener("click", join);
    /* Enter should do the obvious thing from either field. */
    el("name").addEventListener("keydown", function (e) {
      if (e.key === "Enter") (joining ? join : create)();
    });
    el("joincode").addEventListener("keydown", function (e) { if (e.key === "Enter") join(); });

    el("slider").addEventListener("input", function (e) {
      myX = Number(e.target.value) / 1000;
      pushMove();
    });

    /* A drag anywhere in the square, not a handle to find first - the pin follows
       the finger. touch-action:none on .pad stops the page scrolling under it. */
    var pad = el("pad");
    function placeFrom(e) {
      var r = pad.getBoundingClientRect();
      myX = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
      myY = Math.min(1, Math.max(0, (e.clientY - r.top) / r.height));
      el("mepin").style.left = (myX * 100).toFixed(2) + "%";
      el("mepin").style.top = (myY * 100).toFixed(2) + "%";
      pushMove();
    }
    /* The drag is tracked with our own flag rather than by asking the element
       whether it still holds the pointer: setPointerCapture is allowed to fail,
       and when it does the finger goes down, the dot jumps once, and the rest of
       the drag is silently ignored. */
    var dragging = false;
    pad.addEventListener("pointerdown", function (e) {
      dragging = true;
      try { pad.setPointerCapture(e.pointerId); } catch (x) {}
      e.preventDefault();
      placeFrom(e);
    });
    pad.addEventListener("pointermove", function (e) { if (dragging) placeFrom(e); });
    ["pointerup", "pointercancel"].forEach(function (t) {
      pad.addEventListener(t, function () { dragging = false; });
      window.addEventListener(t, function () { dragging = false; });
    });
    /* Arrows, so the square is reachable without a pointer. The slider got this
       free by being a real range input; this has to ask. */
    pad.addEventListener("keydown", function (e) {
      var step = e.shiftKey ? 0.1 : 0.02, dx = 0, dy = 0;
      if (e.key === "ArrowLeft") dx = -step;
      else if (e.key === "ArrowRight") dx = step;
      else if (e.key === "ArrowUp") dy = -step;
      else if (e.key === "ArrowDown") dy = step;
      else return;
      e.preventDefault();
      myX = Math.min(1, Math.max(0, myX + dx));
      myY = Math.min(1, Math.max(0, myY + dy));
      el("mepin").style.left = (myX * 100).toFixed(2) + "%";
      el("mepin").style.top = (myY * 100).toFixed(2) + "%";
      pushMove();
    });

    Array.prototype.forEach.call(el("modeSwitch").children, function (b) {
      b.addEventListener("click", function () { send({ t: "mode", mode: b.dataset.mode }); });
    });

    el("revealBtn").addEventListener("click", function () { send({ t: "reveal" }); });
    el("nextBtn").addEventListener("click", function () {
      send({ t: "next" });
      resetMe();
    });
    el("compareBtn").addEventListener("click", function () { send({ t: "results" }); });
    el("resumeBtn").addEventListener("click", function () { send({ t: "resume" }); });

    el("copyBtn").addEventListener("click", function () {
      navigator.clipboard.writeText(location.href).then(function () {
        el("copyBtn").textContent = "Copied";
        setTimeout(function () { el("copyBtn").textContent = "Copy invite link"; }, 1600);
      });
    });
  });
})();
