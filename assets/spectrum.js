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

  var el = function (id) { return document.getElementById(id); };
  var ws = null, me = null, myX = 0.5, sendTimer = null, pending = false;
  var room = null, myName = null, token = null;
  var beat = null, retry = null, tries = 0, quit = false;

  /* Identity that survives the socket. A phone that locks its screen, a tab left
     in the background, a train going into a tunnel - all of them kill the
     websocket, and without this you came back as a second dot in a new colour
     while your old one sat on the axis forever. */
  function myToken() {
    var t = null;
    try { t = localStorage.getItem("spectrum-token"); } catch (x) {}
    if (!/^[A-Za-z0-9-]{8,64}$/.test(t || "")) {
      t = (crypto.randomUUID ? crypto.randomUUID()
        : "t" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10));
      try { localStorage.setItem("spectrum-token", t); } catch (x) {}
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
    if (quit) return;
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
      if (quit) return;
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
     onto a network, is the moment to check rather than wait out the backoff. */
  function wake() {
    if (quit || !room) return;
    if (!ws || ws.readyState > 1) { tries = 0; open(); }
  }
  document.addEventListener("visibilitychange", function () { if (!document.hidden) wake(); });
  window.addEventListener("online", wake);
  /* pagehide can mean "closed" or "parked in the back/forward cache". Stop
     reconnecting either way, and start again if the page comes back - leaving
     `quit` set through a bfcache restore would silently end the game. */
  window.addEventListener("pagehide", function () {
    quit = true; clearInterval(beat); clearTimeout(retry);
  });
  window.addEventListener("pageshow", function () { quit = false; wake(); });

  function render(s) {
    me = s.you;
    document.documentElement.style.setProperty("--me", me.colour);
    el("statement").textContent = s.statement;
    el("progress").textContent = s.index + " of " + s.total;

    /* Other players sit above the track; your own position is the slider itself,
       so it is never drawn twice. */
    var others = s.players
      .filter(function (p) { return p.id !== me.id; })
      .sort(function (a, b) { return a.x - b.x; });

    el("dots").innerHTML = others.map(function (p) {
      return '<span class="dot-m' + (p.placed ? "" : " unplaced") + (s.revealed ? " revealed" : "") +
        '" data-x="' + p.x.toFixed(4) + '" style="--x:' + p.x.toFixed(4) + '">' +
        "<b>" + (s.revealed && p.name ? esc(p.name) : "&nbsp;") + "</b>" +
        '<i style="background:' + p.colour + '"></i></span>';
    }).join("");

    var placed = s.players.filter(function (p) { return p.placed; }).length;
    note(s.revealed
      ? "Revealed - " + s.players.length + (s.players.length === 1 ? " player" : " players")
      : placed + " of " + s.players.length + " placed");

    el("hostrow").hidden = !me.admin;
    el("revealBtn").disabled = s.revealed;
    el("revealBtn").textContent = s.revealed ? "Shown" : "Show everyone";
    el("compareBtn").disabled = !s.rounds;

    if (s.results) { paintResults(s.results); show("results"); }
    else show("room");
    /* After show(), never before: a hidden section measures zero, so laying the
       names out first put every one of them in row 0 on top of each other. */
    layoutLabels();
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
  window.addEventListener("resize", layoutLabels);

  function paintResults(r) {
    el("resHost").hidden = !me.admin;
    var rows = r.you || [];
    el("resCount").textContent = r.rounds === 1 ? "1 statement" : r.rounds + " statements";

    if (!rows.length) {
      el("resLede").textContent = "Nobody else answered the same statements as you yet.";
      el("simlist").innerHTML = "";
      el("resnote").hidden = true;
      el("roomstats").innerHTML = "";
      return;
    }
    el("resnote").hidden = false;
    var top = rows[0], bottom = rows[rows.length - 1];
    el("resLede").textContent = rows.length === 1
      ? "You and " + top.name + ", across " + plural(top.n, "statement") + "."
      : "Closest to you: " + top.name + ". Furthest: " + bottom.name + ".";

    el("simlist").innerHTML = rows.map(function (p) {
      var pct = Math.round(p.agree * 100);
      return '<li class="simrow">' +
        '<i class="swatch" style="background:' + p.colour + '"></i>' +
        '<span class="simname">' + esc(p.name || "Someone") + "</span>" +
        '<span class="simbar"><span style="width:' + pct + "%;background:" + p.colour + '"></span></span>' +
        '<span class="simpct">' + pct + "%</span>" +
        (p.n < r.rounds ? '<span class="simn">' + plural(p.n, "statement") + "</span>" : "") +
        "</li>";
    }).join("");

    var stats = "";
    if (r.divided) stats += statBlock("Split the room", r.divided.statement);
    if (r.united && r.rounds > 1) stats += statBlock("Nobody argued", r.united.statement);
    el("roomstats").innerHTML = stats;
  }

  function statBlock(label, statement) {
    return '<div class="stat"><span class="statlbl">' + label + "</span>" +
      '<p class="statq">' + esc(statement) + "</p></div>";
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
      send({ t: "move", x: myX });
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
    if (/^[A-Z2-9]{4}$/.test(joining)) {
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
      if (!/^[A-Z2-9]{4}$/.test(c)) return fail("A room code is four letters or digits.");
      fail("");
      connect(c, name);
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
          try { localStorage.removeItem("spectrum-token"); } catch (x) {}
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

    el("revealBtn").addEventListener("click", function () { send({ t: "reveal" }); });
    el("nextBtn").addEventListener("click", function () {
      send({ t: "next" });
      el("slider").value = 500;
      myX = 0.5;
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
