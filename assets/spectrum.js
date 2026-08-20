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

  function show(view) {
    el("lobby").hidden = view !== "lobby";
    el("room").hidden = view !== "room";
  }

  function fail(msg) { el("err").textContent = msg; }

  function connect(code, name) {
    ws = new WebSocket(WS + "/api/ws?code=" + encodeURIComponent(code));
    ws.onopen = function () {
      ws.send(JSON.stringify({ t: "join", name: name }));
      if (pending) pushMove();
    };
    ws.onmessage = function (e) { render(JSON.parse(e.data)); };
    ws.onclose = function () {
      if (!el("room").hidden) el("tally").textContent = "Disconnected - reload to rejoin.";
    };
    ws.onerror = function () { fail("Could not reach the room. Try again."); };
    try { localStorage.setItem("spectrum-name", name); } catch (x) {}
    history.replaceState(null, "", "?room=" + code);
    el("code").textContent = code;
    show("room");
  }

  function render(s) {
    if (s.t !== "state") return;
    me = s.you;
    document.documentElement.style.setProperty("--me", me.colour);
    el("statement").textContent = s.statement;
    el("progress").textContent = s.index + " of " + s.total;

    /* Other players sit above the track; your own position is the slider itself,
       so it is never drawn twice. */
    /* Everyone agreeing is the interesting case, and it is also the one that
       draws four dots and four names on top of each other. Anything within
       CLUSTER of the dot to its left goes up a row instead. */
    var CLUSTER = 0.075;
    var others = s.players
      .filter(function (p) { return p.id !== me.id; })
      .sort(function (a, b) { return a.x - b.x; });
    var rows = [], lastInRow = [];
    others.forEach(function (p, i) {
      var row = 0;
      while (lastInRow[row] !== undefined && p.x - lastInRow[row] < CLUSTER) row++;
      lastInRow[row] = p.x;
      rows[i] = row;
    });
    el("dots").innerHTML = others.map(function (p, i) {
      return '<span class="dot-m' + (p.placed ? "" : " unplaced") + (s.revealed ? " revealed" : "") +
        '" style="left:' + (p.x * 100).toFixed(2) + '%;--row:' + rows[i] + '">' +
        '<b>' + (s.revealed && p.name ? esc(p.name) : "&nbsp;") + "</b>" +
        '<i style="background:' + p.colour + '"></i></span>';
    }).join("");

    var placed = s.players.filter(function (p) { return p.placed; }).length;
    el("tally").textContent = s.revealed
      ? "Revealed - " + s.players.length + (s.players.length === 1 ? " player" : " players")
      : placed + " of " + s.players.length + " placed";

    el("hostrow").hidden = !me.admin;
    el("revealBtn").disabled = s.revealed;
    el("revealBtn").textContent = s.revealed ? "Shown" : "Show everyone";
  }

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
      ws.send(JSON.stringify({ t: "move", x: myX }));
    }, 70);
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      var saved = localStorage.getItem("spectrum-name");
      if (saved) el("name").value = saved;
    } catch (x) {}

    var joining = new URLSearchParams(location.search).get("room");
    if (joining) {
      el("joincode").value = joining.toUpperCase();
      el("lobbyTitle").textContent = "Join room " + joining.toUpperCase();
    }

    el("startBtn").addEventListener("click", function () {
      var name = el("name").value.trim();
      if (!name) return fail("Put your name in first.");
      fail("");
      el("startBtn").disabled = true;
      fetch(API + "/api/room", { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.code) throw new Error("no code");
          connect(d.code, name);
        })
        .catch(function () { fail("Could not start a room. Try again."); el("startBtn").disabled = false; });
    });

    el("joinBtn").addEventListener("click", function () {
      var name = el("name").value.trim();
      var code = el("joincode").value.trim().toUpperCase();
      if (!name) return fail("Put your name in first.");
      if (!/^[A-Z2-9]{4}$/.test(code)) return fail("A room code is four letters or digits.");
      fail("");
      connect(code, name);
    });

    el("slider").addEventListener("input", function (e) {
      myX = Number(e.target.value) / 1000;
      pushMove();
    });

    el("revealBtn").addEventListener("click", function () { ws.send(JSON.stringify({ t: "reveal" })); });
    el("nextBtn").addEventListener("click", function () {
      ws.send(JSON.stringify({ t: "next" }));
      el("slider").value = 500;
      myX = 0.5;
    });

    el("copyBtn").addEventListener("click", function () {
      navigator.clipboard.writeText(location.href).then(function () {
        el("copyBtn").textContent = "Copied";
        setTimeout(function () { el("copyBtn").textContent = "Copy invite link"; }, 1600);
      });
    });
  });
})();
