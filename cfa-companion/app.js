/* CFA Companion: Level I practice questions.
   No build step. Bank in data/, progress in localStorage.
   Everything is built with DOM nodes and textContent, so question text is never
   parsed as markup. */

(function () {
  "use strict";

  var STORE = "cfa-companion.v1";
  var LETTERS = ["A", "B", "C"];
  var SR_DAYS = [1, 3, 7, 21, 60];
  var DAY = 86400000;

  var index = null;          // data/index.json
  var bank = {};             // topic key -> [question]
  var byId = {};             // question id -> question, carrying .topic
  var store = load();
  var run = null;            // the live test
  var tick = null;           // clock interval
  var shown = 0;             // when the current question appeared
  var committed = {};        // qid -> true, once recorded in a strict section

  var el = {};
  ["home", "test", "break", "report", "progress", "history", "builder", "topicpick",
   "modenote", "t-pos", "t-topic", "t-clock", "t-flag", "t-hl", "t-overview", "t-end", "t-stem",
   "t-choices", "t-feedback", "t-prev", "t-next", "t-ovpanel", "ov-grid", "ov-close",
   "b-topics", "b-count", "b-timed", "b-strict", "b-cancel", "f-topics", "f-start",
   "f-cancel", "banksize", "loaderr", "br-count", "br-go", "r-what", "r-pct", "r-count", "r-verdict", "r-topic",
   "r-pace", "r-review", "r-done", "h-topic", "h-pace", "p-answered", "p-acc",
   "p-pace", "p-weak", "wipe", "plan", "pl-days", "pl-done", "pl-donecap",
   "pl-need", "pl-today", "pl-bar", "pl-exam", "pl-target", "pl-extra",
   "pl-addbtn", "pl-resetbtn", "pl-key", "pl-keysave", "pl-keynew", "pl-sync"].forEach(function (id) { el[id] = document.getElementById(id); });

  /* ---------------------------------------------------------------- storage */

  function load() {
    try {
      var raw = localStorage.getItem(STORE);
      if (raw) {
        var s = JSON.parse(raw);
        s.attempts = s.attempts || [];
        s.sr = s.sr || {};
        s.plan = s.plan || {};
        s.time = s.time || { days: {} };
        return migrate(s);
      }
    } catch (e) { /* private mode, or corrupt: start clean */ }
    return migrate({ attempts: [], sr: {}, plan: {}, time: { days: {} } });
  }

  /* Time is kept per device per day. Summing devices is what makes a merge
     idempotent: each device only ever raises its own counter, so taking the
     larger of two copies can neither lose nor double-count. A single total
     could not be merged at all. */
  function migrate(s) {
    s.device = s.device || rand(8);
    s.time = s.time || { days: {} };
    s.time.days = s.time.days || {};
    Object.keys(s.time.days).forEach(function (d) {
      if (typeof s.time.days[d] === "number") {
        var was = s.time.days[d];
        s.time.days[d] = {};
        s.time.days[d][s.device] = was;
      }
    });
    if (typeof s.time.sec === "number") delete s.time.sec;
    return s;
  }

  function rand(n) {
    var bytes = new Uint8Array(n);
    (window.crypto || window.msCrypto).getRandomValues(bytes);
    return Array.prototype.map.call(bytes, function (b) {
      return b.toString(36).padStart(2, "0");
    }).join("").slice(0, n * 2);
  }

  function save() {
    try { localStorage.setItem(STORE, JSON.stringify(store)); } catch (e) { /* full or blocked */ }
    syncSoon();
  }

  function record(qid, topic, ok, ms, mode) {
    store.attempts.push({ q: qid, t: topic, ok: ok, ms: ms, at: Date.now(), m: mode });
    var box = ok ? Math.min(5, ((store.sr[qid] || {}).box || 0) + 1) : 1;
    store.sr[qid] = { box: box, due: Date.now() + SR_DAYS[box - 1] * DAY };
    save();
  }

  /* ------------------------------------------------------------------- data */

  /* bank.js carries the whole bank in a script tag, so the normal path makes no
     requests and cannot fail part way. The fetch path is kept as a fallback for a
     copy served without it, with one silent retry to ride out a load caught
     mid-deploy. */
  function boot() {
    if (window.BANK) {
      index = window.BANK.index;
      Object.keys(window.BANK.topics).forEach(function (k) {
        var qs = window.BANK.topics[k];
        qs.forEach(function (q) { q.topic = k; byId[q.id] = q; });
        bank[k] = qs;
      });
      ready();
      return;
    }
    load_bank().catch(function () {
      return new Promise(function (r) { setTimeout(r, 1400); }).then(load_bank);
    }).catch(failed);
  }

  function load_bank() {
    return fetch("data/index.json")
      .then(function (r) { return r.json(); })
      .then(function (ix) {
        index = ix;
        return Promise.all(ix.topics.map(function (t) {
          return fetch("data/" + t.key + ".json")
            .then(function (r) { return r.json(); })
            .then(function (qs) {
              qs.forEach(function (q) { q.topic = t.key; byId[q.id] = q; });
              bank[t.key] = qs;
            });
        }));
      })
      .then(ready);
  }

  /* Two very different failures reach the same catch, and blaming the site for
     both sent the reader to the wrong place. A page opened straight off disk cannot
     fetch at all, which is a browser rule rather than a fault. */
  function failed(err) {
    document.body.classList.add("failed");
    el.loaderr.hidden = false;
    el.loaderr.textContent = "";
    var proto = window.location.protocol;
    if (proto !== "http:" && proto !== "https:") {
      el.loaderr.appendChild(para(null,
        "This page was opened over " + proto + ", and browsers only allow it to read "
        + "its questions over http or https. Open it at "
        + "charlietrenorden.com/cfa-companion instead, or serve this folder."));
      return;
    }
    el.loaderr.appendChild(para(null, "The question bank did not load: " + String(err)));
    el.loaderr.appendChild(para("where",
      "Tried " + new URL("data/index.json", window.location.href).href
      + (navigator.onLine === false ? ". The browser reports no connection." : "")));
    var again = document.createElement("button");
    again.type = "button";
    again.className = "primary";
    again.textContent = "Try again";
    again.addEventListener("click", function () {
      document.body.classList.remove("failed");
      el.loaderr.hidden = true;
      boot();
    });
    el.loaderr.appendChild(again);
  }

  function topicMeta(key) {
    for (var i = 0; i < index.topics.length; i++) {
      if (index.topics[i].key === key) return index.topics[i];
    }
    return { key: key, short: key, name: key, target: 0 };
  }

  function allQuestions(topics) {
    var out = [];
    (topics || index.topics.map(function (t) { return t.key; })).forEach(function (k) {
      (bank[k] || []).forEach(function (q) { out.push(q); });
    });
    return out;
  }

  /* ------------------------------------------------------------------- sync */

  var SYNC = "https://cfa-sync.charlietrenorden.com/state";
  var syncTimer = null;
  var syncing = false;

  /* The merge has to be safe to run twice, because two devices can both push.
     Attempts are a union keyed by question and timestamp, time takes the larger
     of each device's own counter, and the plan is whichever was edited last.
     Spaced repetition is replayed from the merged attempts rather than merged,
     since a box depends on the order answers arrived in. */
  function mergeState(local, remote) {
    if (!remote) return local;

    var seen = {};
    var attempts = [];
    (local.attempts || []).concat(remote.attempts || []).forEach(function (a) {
      var k = a.q + "@" + a.at;
      if (!seen[k]) { seen[k] = true; attempts.push(a); }
    });
    attempts.sort(function (x, y) { return x.at - y.at; });

    var days = {};
    [(local.time || {}).days || {}, (remote.time || {}).days || {}].forEach(function (src) {
      Object.keys(src).forEach(function (d) {
        days[d] = days[d] || {};
        var per = src[d] || {};
        Object.keys(per).forEach(function (dev) {
          days[d][dev] = Math.max(days[d][dev] || 0, per[dev]);
        });
      });
    });

    var lp = local.plan || {};
    var rp = remote.plan || {};
    var plan = (rp.at || 0) > (lp.at || 0) ? rp : lp;

    return {
      attempts: attempts,
      sr: replaySR(attempts),
      plan: plan,
      time: { days: days },
      device: local.device,
      key: local.key,
      syncedAt: local.syncedAt
    };
  }

  function replaySR(attempts) {
    var sr = {};
    attempts.forEach(function (a) {
      var box = a.ok ? Math.min(5, ((sr[a.q] || {}).box || 0) + 1) : 1;
      sr[a.q] = { box: box, due: a.at + SR_DAYS[box - 1] * DAY };
    });
    return sr;
  }

  function shareable() {
    return { attempts: store.attempts, plan: store.plan, time: store.time };
  }

  function paintSync(state, detail) {
    var e = el["pl-sync"];
    e.className = "syncstate" + (state === "bad" ? " bad" : state === "busy" ? " busy" : "");
    if (!store.key) { e.textContent = "not syncing"; return; }
    if (state === "busy") { e.textContent = "syncing"; return; }
    if (state === "bad") { e.textContent = detail || "sync failed"; return; }
    var ago = store.syncedAt ? Math.round((Date.now() - store.syncedAt) / 60000) : null;
    e.textContent = ago === null ? "not synced yet"
      : ago < 1 ? "synced just now" : "synced " + ago + "m ago";
  }

  function syncNow() {
    if (!store.key || syncing) return Promise.resolve();
    syncing = true;
    lastSync = Date.now();
    paintSync("busy");
    return fetch(SYNC, { headers: { "X-Sync-Key": store.key } })
      .then(function (r) {
        if (!r.ok) throw new Error("read " + r.status);
        return r.json();
      })
      .then(function (res) {
        if (res.blob) {
          store = mergeState(store, res.blob);
          save();
        }
        return fetch(SYNC, {
          method: "PUT",
          headers: { "X-Sync-Key": store.key, "Content-Type": "application/json" },
          body: JSON.stringify({ blob: shareable() })
        });
      })
      .then(function (r) {
        if (!r.ok) throw new Error("write " + r.status);
        store.syncedAt = Date.now();
        save();
        syncing = false;
        paintSync("ok");
        if (!el.home.hidden) { refreshHome(); paintPlan(); }
      })
      .catch(function (err) {
        syncing = false;
        paintSync("bad", "sync failed, will retry");
        if (window.console) window.console.warn("sync:", err.message);
      });
  }

  /* Batched, because every answer writes to storage and none of them is urgent.
     The syncing guard matters: syncNow saves, and save schedules a sync, so
     without it the two would push each other round in a loop for ever. The floor
     keeps an hour of steady practice to about sixty requests rather than a
     thousand. */
  var lastSync = 0;
  var FLOOR = 60000;

  function syncSoon() {
    if (!store.key || syncing || syncTimer) return;
    var wait = Math.max(8000, FLOOR - (Date.now() - lastSync));
    syncTimer = setTimeout(function () {
      syncTimer = null;
      syncNow();
    }, wait);
  }

  function wireSync() {
    el["pl-key"].value = store.key || "";
    paintSync("ok");

    el["pl-keysave"].addEventListener("click", function () {
      var v = el["pl-key"].value.trim();
      if (v && (v.length < 16 || v.length > 128)) {
        paintSync("bad", "a key needs 16 characters or more");
        return;
      }
      store.key = v || null;
      save();
      paintSync("ok");
      if (store.key) syncNow();
    });

    el["pl-keynew"].addEventListener("click", function () {
      store.key = rand(12);
      el["pl-key"].value = store.key;
      save();
      paintSync("ok");
      syncNow();
    });

    window.addEventListener("pagehide", function () {
      if (!store.key) return;
      try {
        fetch(SYNC, {
          method: "PUT",
          keepalive: true,
          headers: { "X-Sync-Key": store.key, "Content-Type": "application/json" },
          body: JSON.stringify({ blob: shareable() })
        });
      } catch (e) { /* the tab is going away regardless */ }
    });
  }

  /* ------------------------------------------------------- the study plan */

  var TICK = 5;                  // seconds counted per tick
  var IDLE = 300000;             // stop counting after five minutes untouched
  var lastTouch = Date.now();
  var unsaved = 0;

  function today() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-"
      + String(d.getDate()).padStart(2, "0");
  }

  function counting() {
    return document.visibilityState === "visible" && (Date.now() - lastTouch) < IDLE;
  }

  /* Time on the site is the honest measure of hours put in, so it is counted
     rather than asked for. It pauses when the tab is hidden or untouched, or an
     evening with the page left open would log eight hours nobody studied. */
  function startTimer() {
    ["pointerdown", "keydown", "wheel", "touchstart"].forEach(function (e) {
      document.addEventListener(e, function () { lastTouch = Date.now(); }, { passive: true });
    });
    document.addEventListener("visibilitychange", function () {
      lastTouch = Date.now();
      flushTime();
    });
    window.addEventListener("pagehide", flushTime);
    setInterval(function () {
      if (!counting()) { paintToday(); return; }
      var day = store.time.days[today()] || (store.time.days[today()] = {});
      day[store.device] = (day[store.device] || 0) + TICK;
      unsaved += TICK;
      if (unsaved >= 30) flushTime();
      paintToday();
    }, TICK * 1000);
  }

  function flushTime() {
    if (unsaved > 0) { unsaved = 0; save(); }
  }

  function daySeconds(day) {
    var per = store.time.days[day] || {};
    return Object.keys(per).reduce(function (a, k) { return a + per[k]; }, 0);
  }

  function totalSeconds() {
    return Object.keys(store.time.days).reduce(function (a, d) {
      return a + daySeconds(d);
    }, 0);
  }

  function hoursDone() {
    return totalSeconds() / 3600 + (store.plan.extraMin || 0) / 60;
  }

  function daysToGo() {
    if (!store.plan.exam) return null;
    var exam = new Date(store.plan.exam + "T00:00:00");
    var now = new Date();
    now = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return Math.round((exam - now) / DAY);
  }

  function hm(hours) {
    var mins = Math.round(hours * 60);
    var h = Math.floor(mins / 60);
    return h > 0 ? h + "h " + (mins % 60) + "m" : (mins % 60) + "m";
  }

  function paintToday() {
    var secs = daySeconds(today());
    el["pl-today"].textContent = hm(secs / 3600);
    el["pl-today"].classList.toggle("paused", !counting());
  }

  function paintPlan() {
    var target = store.plan.target || 300;
    var done = hoursDone();
    var left = daysToGo();

    el["pl-done"].textContent = hm(done);
    el["pl-donecap"].textContent = "of " + target + " hours";
    el["pl-bar"].style.width = Math.min(100, 100 * done / target) + "%";

    if (left === null) {
      el["pl-days"].textContent = "set a date";
      el["pl-need"].textContent = "set a date";
    } else if (left < 0) {
      el["pl-days"].textContent = "passed";
      el["pl-need"].textContent = "done";
    } else {
      el["pl-days"].textContent = String(left);
      var remaining = Math.max(0, target - done);
      el["pl-need"].textContent = left === 0
        ? hm(remaining)
        : (remaining / left).toFixed(1);
    }
    paintToday();
  }

  function wirePlan() {
    el["pl-exam"].value = store.plan.exam || "";
    el["pl-target"].value = store.plan.target || 300;

    el["pl-exam"].addEventListener("change", function () {
      store.plan.exam = el["pl-exam"].value || null;
      store.plan.at = Date.now();
      save();
      paintPlan();
    });
    el["pl-target"].addEventListener("change", function () {
      var v = parseInt(el["pl-target"].value, 10);
      store.plan.target = v > 0 ? v : 300;
      store.plan.at = Date.now();
      el["pl-target"].value = store.plan.target;
      save();
      paintPlan();
    });
    el["pl-addbtn"].addEventListener("click", function () {
      var v = parseFloat(el["pl-extra"].value);
      if (!(v > 0)) return;
      store.plan.extraMin = (store.plan.extraMin || 0) + Math.round(v * 60);
      store.plan.at = Date.now();
      el["pl-extra"].value = "";
      save();
      paintPlan();
    });
    el["pl-resetbtn"].addEventListener("click", function () {
      if (!window.confirm("Set the hours logged back to zero? The exam date stays.")) return;
      store.time = { days: {} };
      store.plan.extraMin = 0;
      save();
      paintPlan();
    });
  }

  /* --------------------------------------------------------------- history */

  function blankTally() {
    var acc = {};
    index.topics.forEach(function (t) { acc[t.key] = { n: 0, ok: 0, times: [] }; });
    return acc;
  }

  function statsByTopic() {
    var acc = blankTally();
    store.attempts.forEach(function (a) {
      if (!acc[a.t]) return;
      acc[a.t].n += 1;
      if (a.ok) acc[a.t].ok += 1;
      if (a.ms > 0) acc[a.t].times.push(a.ms);
    });
    return acc;
  }

  function median(list) {
    if (!list.length) return null;
    var s = list.slice().sort(function (a, b) { return a - b; });
    var mid = Math.floor(s.length / 2);
    return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
  }

  function weakestTopic() {
    var acc = statsByTopic();
    var ranked = index.topics.filter(function (t) { return (bank[t.key] || []).length > 0; });
    var seasoned = ranked.filter(function (t) { return acc[t.key].n >= 5; });
    if (seasoned.length) {
      seasoned.sort(function (a, b) {
        return (acc[a.key].ok / acc[a.key].n) - (acc[b.key].ok / acc[b.key].n);
      });
      return seasoned[0].key;
    }
    ranked.sort(function (a, b) { return acc[a.key].n - acc[b.key].n; });
    return ranked.length ? ranked[0].key : null;
  }

  /* There is only a weakest topic if the topics differ. With everything at the
     same accuracy the sort still returns something, and naming it would invent a
     weakness the answers do not show. The drill still needs a topic to pick, so
     that path keeps using weakestTopic() regardless. */
  function weakestTopicForDisplay() {
    var acc = statsByTopic();
    var rates = index.topics
      .filter(function (t) { return acc[t.key].n >= 5; })
      .map(function (t) { return acc[t.key].ok / acc[t.key].n; });
    if (rates.length < 2) return null;
    if (Math.max.apply(null, rates) === Math.min.apply(null, rates)) return null;
    return weakestTopic();
  }

  function lastVerdict() {
    var last = {};
    store.attempts.forEach(function (a) { last[a.q] = a.ok; });
    return last;
  }

  function timesSeen() {
    var n = {};
    store.attempts.forEach(function (a) { n[a.q] = (n[a.q] || 0) + 1; });
    return n;
  }

  function wrongIds() {
    var last = lastVerdict();
    return Object.keys(last).filter(function (id) { return last[id] === false && byId[id]; });
  }

  function dueIds() {
    return Object.keys(store.sr).filter(function (id) {
      return byId[id] && store.sr[id].due <= Date.now();
    });
  }

  /* -------------------------------------------------------------- selection */

  function shuffle(list) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /* Least-seen first, random within a tier: a fresh question beats a repeat. */
  function preferUnseen(list) {
    var seen = timesSeen();
    return shuffle(list).sort(function (a, b) {
      return (seen[a.id] || 0) - (seen[b.id] || 0);
    });
  }

  /* Allocate n across topics in proportion to the exam's weights, then take up
     whatever a thin topic cannot supply. */
  function weightedPick(n, topics) {
    var keys = topics || index.topics.map(function (t) { return t.key; });
    var pools = {};
    var total = 0;
    keys.forEach(function (k) {
      pools[k] = preferUnseen(bank[k] || []);
      total += topicMeta(k).target;
    });
    var want = {};
    var allocated = 0;
    keys.forEach(function (k) {
      want[k] = Math.min(pools[k].length, Math.round(n * topicMeta(k).target / total));
      allocated += want[k];
    });
    var order = keys.slice().sort(function (a, b) { return topicMeta(b).target - topicMeta(a).target; });
    var guard = 0;
    while (allocated !== n && guard++ < 2000) {
      var moved = false;
      for (var i = 0; i < order.length; i++) {
        var k = order[i];
        if (allocated < n && want[k] < pools[k].length) { want[k] += 1; allocated += 1; moved = true; }
        else if (allocated > n && want[k] > 0) { want[k] -= 1; allocated -= 1; moved = true; }
        if (allocated === n) break;
      }
      if (!moved) break;
    }
    var out = [];
    keys.forEach(function (k) { out = out.concat(pools[k].slice(0, want[k])); });
    return shuffle(out);
  }

  /* ------------------------------------------------------------------- runs */

  function startRun(cfg) {
    committed = {};
    run = {
      mode: cfg.mode,
      items: cfg.items.map(function (q) { return q.id; }),
      idx: 0,
      picks: {},
      flags: {},
      struck: {},
      marks: {},          // qid -> [[start, end]] character ranges the reader highlighted
      spent: {},          // qid -> ms
      strict: !!cfg.strict,
      sessions: cfg.sessions || null,
      session: 0,
      endsAt: null,
      minutes: cfg.minutes || 0,
      done: false
    };
    if (run.sessions) beginSession(0);
    else if (cfg.minutes) run.endsAt = Date.now() + cfg.minutes * 60000;
    show("test");
    el["t-flag"].hidden = !run.strict;
    el["t-hl"].hidden = !run.strict;
    el["t-overview"].hidden = !run.strict;
    el["t-clock"].hidden = !run.endsAt;
    if (run.endsAt) startClock();
    render();
  }

  function beginSession(n) {
    run.session = n;
    run.idx = run.sessions[n][0];
    run.endsAt = Date.now() + run.minutes * 60000;
  }

  function sessionRange() {
    return run.sessions ? run.sessions[run.session] : [0, run.items.length - 1];
  }

  function startClock() {
    stopClock();
    tick = setInterval(function () {
      var left = run.endsAt - Date.now();
      if (left <= 0) { el["t-clock"].textContent = "0:00:00"; endSession(); return; }
      el["t-clock"].textContent = hms(left);
      el["t-clock"].classList.toggle("low", left < 5 * 60000);
    }, 250);
    el["t-clock"].textContent = hms(run.endsAt - Date.now());
  }

  function stopClock() { if (tick) { clearInterval(tick); tick = null; } }

  function hms(ms) {
    var s = Math.max(0, Math.floor(ms / 1000));
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
    return h + ":" + String(m).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
  }

  function current() { return byId[run.items[run.idx]]; }

  function chargeTime() {
    if (!shown) return;
    var q = current();
    if (q) run.spent[q.id] = (run.spent[q.id] || 0) + (Date.now() - shown);
    shown = 0;
  }

  function renderStem(q) {
    var host = el["t-stem"];
    host.textContent = "";
    var ranges = run.marks[q.id] || [];
    var pos = 0;
    ranges.forEach(function (r) {
      if (r[0] > pos) host.appendChild(document.createTextNode(q.stem.slice(pos, r[0])));
      var m = document.createElement("mark");
      m.textContent = q.stem.slice(r[0], r[1]);
      host.appendChild(m);
      pos = r[1];
    });
    if (pos < q.stem.length) host.appendChild(document.createTextNode(q.stem.slice(pos)));
  }

  function render() {
    var q = current();
    var r = sessionRange();
    shown = Date.now();

    el["t-pos"].textContent = run.mode === "free"
      ? "Question " + (run.idx + 1)
      : "Question " + (run.idx - r[0] + 1) + " of " + (r[1] - r[0] + 1) +
        (run.sessions ? "   session " + (run.session + 1) + " of 2" : "");

    el["t-topic"].textContent = topicMeta(q.topic).short;

    renderStem(q);

    el["t-choices"].textContent = "";
    q.choices.forEach(function (text, i) {
      var li = document.createElement("li");
      var b = document.createElement("button");
      b.type = "button";
      b.className = "choice";
      var letter = document.createElement("span");
      letter.className = "letter";
      letter.textContent = LETTERS[i];
      var body = document.createElement("span");
      body.className = "body";
      body.textContent = text;
      b.appendChild(letter);
      b.appendChild(body);
      if (run.picks[q.id] === i) b.classList.add("picked");
      if ((run.struck[q.id] || {})[i]) b.classList.add("struck");
      if (!run.strict && run.picks[q.id] !== undefined) {
        if (i === q.answer) b.classList.add("right");
        else if (run.picks[q.id] === i) b.classList.add("wrong");
        b.disabled = true;
      }
      b.addEventListener("click", function () { pick(i); });
      li.appendChild(b);
      if (run.strict) {
        var s = document.createElement("button");
        s.type = "button";
        s.className = "strike";
        s.title = "Strike out this choice";
        s.setAttribute("aria-label", "Strike out choice " + LETTERS[i]);
        s.textContent = LETTERS[i];
        s.addEventListener("click", function () {
          run.struck[q.id] = run.struck[q.id] || {};
          run.struck[q.id][i] = !run.struck[q.id][i];
          render();
        });
        li.appendChild(s);
      }
      el["t-choices"].appendChild(li);
    });

    el["t-flag"].classList.toggle("flagged", !!run.flags[q.id]);
    el["t-flag"].textContent = run.flags[q.id] ? "Flagged" : "Flag";

    if (!run.strict && run.picks[q.id] !== undefined) showFeedback(q);
    else { el["t-feedback"].hidden = true; el["t-feedback"].textContent = ""; }

    el["t-prev"].disabled = run.idx <= r[0];
    el["t-next"].textContent = run.idx >= r[1]
      ? (run.sessions && run.session === 0 ? "End session" : "Finish")
      : "Next";
    window.scrollTo(0, 0);
  }

  function para(cls, text, leadLetter) {
    var p = document.createElement("p");
    if (cls) p.className = cls;
    if (leadLetter) {
      var b = document.createElement("b");
      b.textContent = leadLetter;
      p.appendChild(b);
      p.appendChild(document.createTextNode(" " + text));
    } else {
      p.textContent = text;
    }
    return p;
  }

  function showFeedback(q) {
    var picked = run.picks[q.id];
    var ok = picked === q.answer;
    var f = el["t-feedback"];
    f.className = "feedback " + (ok ? "ok" : "no");
    f.textContent = "";
    f.appendChild(para("ref", q.ref));
    f.appendChild(para("verd", ok ? "Correct." : "Not right. The answer is " + LETTERS[q.answer] + "."));
    f.appendChild(para(null, q.solution));
    if (!ok && q.distractors[picked]) {
      f.appendChild(para("why", q.distractors[picked], LETTERS[picked]));
    }
    f.hidden = false;
  }

  function pick(i) {
    var q = current();
    if (i >= q.choices.length) return;
    if (!run.strict && run.picks[q.id] !== undefined) return;   // answered, no changing it
    run.picks[q.id] = i;
    if (!run.strict) {
      chargeTime();
      record(q.id, q.topic, i === q.answer, run.spent[q.id] || 0, run.mode);
      shown = Date.now();
    }
    render();
  }

  function next() {
    var r = sessionRange();
    chargeTime();
    if (run.idx >= r[1]) {
      if (run.sessions && run.session === 0) { pauseForBreak(); return; }
      finish();
      return;
    }
    run.idx += 1;
    render();
  }

  function prev() {
    var r = sessionRange();
    if (run.idx <= r[0]) return;
    chargeTime();
    run.idx -= 1;
    render();
  }

  function pauseForBreak() {
    stopClock();
    commitStrict(sessionRange());
    var r = sessionRange();
    var answered = 0;
    for (var i = r[0]; i <= r[1]; i++) if (run.picks[run.items[i]] !== undefined) answered += 1;
    el["br-count"].textContent = answered + " of " + (r[1] - r[0] + 1);
    show("break");
  }

  function endSession() {
    if (run.sessions && run.session === 0) { pauseForBreak(); return; }
    finish();
  }

  /* In a strict run nothing is recorded until the section closes. That delay is
     the point of it: the score arrives all at once, as it does on the day. */
  function commitStrict(range) {
    if (!run.strict) return;
    for (var i = range[0]; i <= range[1]; i++) {
      var q = byId[run.items[i]];
      var picked = run.picks[q.id];
      if (picked === undefined || committed[q.id]) continue;
      record(q.id, q.topic, picked === q.answer, run.spent[q.id] || 0, run.mode);
      committed[q.id] = true;
    }
  }

  function finish() {
    stopClock();
    chargeTime();
    commitStrict(sessionRange());
    run.done = true;
    report();
  }

  /* ----------------------------------------------------------------- report */

  /* What the report may show. A free run stops wherever the reader stops, so the
     questions it never delivered stay unseen rather than being spoiled in the
     review. Under exam conditions the whole section was available, so a blank
     there is a blank and belongs in the report. */
  function reachable() {
    if (!run.strict) {
      return run.items.filter(function (id) { return run.picks[id] !== undefined; });
    }
    var end = run.sessions ? run.sessions[run.session][1] : run.items.length - 1;
    return run.items.slice(0, end + 1);
  }

  var MODE_NAMES = {
    free: "Free run", drill: "Weak-topic drill", mistakes: "My mistakes",
    review: "Due for review", custom: "Custom set", session: "Single session",
    mock: "Full mock"
  };

  function report() {
    var pool = reachable();
    el["r-what"].textContent = (MODE_NAMES[run.mode] || run.mode) + ", " +
      pool.length + (pool.length === 1 ? " question" : " questions") +
      (run.strict ? " under exam conditions" : "");
    var seen = pool.filter(function (id) { return run.picks[id] !== undefined; });
    var right = seen.filter(function (id) { return run.picks[id] === byId[id].answer; });
    var pct = seen.length ? Math.round(100 * right.length / seen.length) : 0;

    el["r-pct"].textContent = seen.length ? pct + "%" : "no answers";
    el["r-count"].textContent = right.length + " of " + seen.length + " correct" +
      (seen.length < pool.length ? ", " + (pool.length - seen.length) + " left blank" : "");
    el["r-verdict"].textContent = seen.length
      ? "The minimum passing score is not published. The line at 70% is the reference the official score report draws, not a pass mark."
      : "Nothing was answered, so there is nothing to score.";

    var acc = blankTally();
    pool.forEach(function (id) {
      var q = byId[id];
      if (run.picks[id] === undefined) return;
      acc[q.topic].n += 1;
      if (run.picks[id] === q.answer) acc[q.topic].ok += 1;
      if (run.spent[id]) acc[q.topic].times.push(run.spent[id]);
    });

    drawTopicChart(el["r-topic"], acc);
    drawPaceChart(el["r-pace"], acc);
    drawReview();
    show("report");
  }

  function band(pct) { return pct >= 70 ? "b-good" : pct >= 50 ? "b-mid" : "b-bad"; }

  function barRow(label, fillClass, widthPct, valueText, lines, n) {
    var row = document.createElement("div");
    row.className = "bar";
    var lab = document.createElement("span");
    lab.className = "lab";
    lab.textContent = label;
    if (n) {
      var nq = document.createElement("span");
      nq.className = "nq";
      nq.textContent = String(n);
      lab.appendChild(nq);
    }
    var track = document.createElement("span");
    track.className = "track";
    var fill = document.createElement("span");
    fill.className = "fill " + fillClass;
    fill.style.width = widthPct + "%";
    track.appendChild(fill);
    lines.forEach(function (l) {
      var line = document.createElement("span");
      line.className = "refline" + (l.hard ? " hard" : "");
      line.style.left = l.at + "%";
      track.appendChild(line);
    });
    var val = document.createElement("span");
    val.className = "val";
    val.textContent = valueText;
    row.appendChild(lab);
    row.appendChild(track);
    row.appendChild(val);
    return row;
  }

  function axisRow(marks) {
    var ax = document.createElement("div");
    ax.className = "axis";
    ax.appendChild(document.createElement("span"));
    var m = document.createElement("span");
    m.className = "marks";
    marks.forEach(function (k) {
      var s = document.createElement("span");
      s.style.left = k.at + "%";
      s.textContent = k.text;
      m.appendChild(s);
    });
    ax.appendChild(m);
    ax.appendChild(document.createElement("span"));
    return ax;
  }

  function note(host, text) {
    host.textContent = "";
    host.appendChild(para("empty", text));
  }

  function drawTopicChart(host, acc) {
    var rows = index.topics.filter(function (t) { return acc[t.key].n > 0; });
    host.textContent = "";
    if (!rows.length) { note(host, "No answers yet."); return; }
    var bars = document.createElement("div");
    bars.className = "bars";
    rows.forEach(function (t) {
      var a = acc[t.key];
      var pct = Math.round(100 * a.ok / a.n);
      bars.appendChild(barRow(t.short, band(pct), pct, pct + "%",
        [{ at: 50 }, { at: 70, hard: true }], a.n));
    });
    host.appendChild(bars);
    host.appendChild(axisRow([{ at: 50, text: "50%" }, { at: 70, text: "70%" }]));
    var key = document.createElement("div");
    key.className = "key";
    [["var(--good)", "at or above 70%"], ["var(--mid)", "50% to 70%"], ["var(--bad)", "below 50%"]]
      .forEach(function (pair) {
        var s = document.createElement("span");
        var i = document.createElement("i");
        i.style.background = pair[0];
        s.appendChild(i);
        s.appendChild(document.createTextNode(pair[1]));
        key.appendChild(s);
      });
    host.appendChild(key);
  }

  function drawPaceChart(host, acc) {
    var rows = index.topics.filter(function (t) { return acc[t.key].times.length > 0; });
    host.textContent = "";
    if (!rows.length) { note(host, "No timings recorded."); return; }
    var meds = {};
    var max = 90;
    rows.forEach(function (t) {
      meds[t.key] = median(acc[t.key].times) / 1000;
      max = Math.max(max, meds[t.key]);
    });
    max = Math.ceil(max * 1.15 / 10) * 10;
    var budget = 100 * 90 / max;
    var bars = document.createElement("div");
    bars.className = "bars";
    rows.forEach(function (t) {
      var s = meds[t.key];
      var cls = s <= 90 ? "b-good" : s <= 120 ? "b-mid" : "b-bad";
      bars.appendChild(barRow(t.short, cls, Math.min(100, 100 * s / max),
        Math.round(s) + "s", [{ at: budget, hard: true }], acc[t.key].times.length));
    });
    host.appendChild(bars);
    host.appendChild(axisRow([{ at: budget, text: "90s" }]));
  }

  function drawReview() {
    var host = el["r-review"];
    host.textContent = "";
    reachable().forEach(function (id) {
      var q = byId[id];
      var picked = run.picks[id];
      var ok = picked === q.answer;
      var secs = Math.round((run.spent[id] || 0) / 1000);
      var d = document.createElement("div");
      d.className = "rq" + (ok ? "" : " no");
      d.dataset.wrong = ok ? "0" : "1";
      d.dataset.slow = secs > 90 ? "1" : "0";

      var head = document.createElement("div");
      head.className = "rhead";
      var top = document.createElement("span");
      top.className = "topic";
      top.textContent = topicMeta(q.topic).short;
      head.appendChild(top);
      var ref = document.createElement("span");
      ref.className = "ref";
      ref.textContent = q.ref;
      head.appendChild(ref);
      var tm = document.createElement("span");
      tm.className = "t";
      tm.textContent = secs + "s";
      head.appendChild(tm);
      d.appendChild(head);

      d.appendChild(para("rstem", q.stem));

      var ans = document.createElement("p");
      ans.className = "rans";
      ans.appendChild(document.createTextNode("Your answer "));
      var mine = document.createElement("b");
      mine.textContent = picked === undefined ? "left blank" : LETTERS[picked];
      ans.appendChild(mine);
      ans.appendChild(document.createTextNode(". Correct answer "));
      var corr = document.createElement("b");
      corr.textContent = LETTERS[q.answer];
      ans.appendChild(corr);
      ans.appendChild(document.createTextNode(": " + q.choices[q.answer]));
      d.appendChild(ans);

      d.appendChild(para("rsol", q.solution));

      if (q.distractors.filter(function (w) { return w; }).length) {
        var det = document.createElement("details");
        var sum = document.createElement("summary");
        sum.textContent = "Why the other two are tempting";
        det.appendChild(sum);
        q.distractors.forEach(function (why, i) {
          if (why) det.appendChild(para(null, why, LETTERS[i]));
        });
        d.appendChild(det);
      }
      host.appendChild(d);
    });
  }

  /* ------------------------------------------------------------------- home */

  function ready() {
    buildTopicPickers();
    wire();
    wirePlan();
    wireSync();
    startTimer();
    show("home");
    if (store.key) syncNow();
  }

  function refreshHome() {
    var n = store.attempts.length;
    el.progress.hidden = n === 0;
    el.history.hidden = n === 0;
    if (n) {
      var ok = store.attempts.filter(function (a) { return a.ok; }).length;
      var med = median(store.attempts.map(function (a) { return a.ms; })
        .filter(function (m) { return m > 0; }));
      el["p-answered"].textContent = String(n);
      el["p-acc"].textContent = Math.round(100 * ok / n) + "%";
      el["p-pace"].textContent = med ? Math.round(med / 1000) + "s" : "not timed";
      var w = weakestTopicForDisplay();
      el["p-weak"].textContent = w ? topicMeta(w).short : "all level";
      var acc = statsByTopic();
      drawTopicChart(el["h-topic"], acc);
      drawPaceChart(el["h-pace"], acc);
    }

    var wrong = wrongIds().length;
    var due = dueIds().length;
    var total = allQuestions().length;

    el.banksize.textContent = total + " questions in the bank, weighted to the "
      + "exam's topic split.";

    setMode("mistakes", wrong > 0,
      wrong ? wrong + " to revisit." : "Only questions you last got wrong.");
    setMode("review", due > 0,
      due ? due + " due today." : "Spaced repetition on what you have seen.");
    setMode("session", total >= index.session_size,
      total >= index.session_size
        ? "90 questions, 2h15, no feedback until the end."
        : "Needs " + index.session_size + " questions. The bank holds " + total + " so far.");
    setMode("mock", total >= index.mock_size,
      total >= index.mock_size
        ? "180 questions in two timed sessions, weighted like the exam."
        : "Needs " + index.mock_size + " questions. The bank holds " + total + " so far.");
  }

  function setMode(mode, enabled, text) {
    var b = document.querySelector("[data-mode='" + mode + "']");
    if (!b) return;
    b.disabled = !enabled;
    var span = b.querySelector("span");
    if (span && text) span.textContent = text;
  }

  function pickerLabel(type, name, value, text, count, enabled, checked) {
    var lab = document.createElement("label");
    var input = document.createElement("input");
    input.type = type;
    if (name) input.name = name;
    input.value = value;
    input.disabled = !enabled;
    input.checked = !!checked;
    var t = document.createElement("span");
    t.textContent = text;
    var n = document.createElement("span");
    n.className = "n";
    n.textContent = String(count);
    lab.appendChild(input);
    lab.appendChild(t);
    lab.appendChild(n);
    return lab;
  }

  function buildTopicPickers() {
    if (el["b-topics"].querySelector(".grid")) return;   // a retry must not double them
    var grid = document.createElement("div");
    grid.className = "grid";
    index.topics.forEach(function (t) {
      var n = (bank[t.key] || []).length;
      grid.appendChild(pickerLabel("checkbox", null, t.key, t.short, n, n > 0, false));
    });
    el["b-topics"].appendChild(grid);

    var one = document.createElement("div");
    one.className = "grid";
    one.appendChild(pickerLabel("radio", "ft", "", "All topics", allQuestions().length, true, true));
    index.topics.forEach(function (t) {
      var n = (bank[t.key] || []).length;
      one.appendChild(pickerLabel("radio", "ft", t.key, t.short, n, n > 0, false));
    });
    el["f-topics"].appendChild(one);
  }

  function show(name) {
    ["home", "test", "break", "report"].forEach(function (s) { el[s].hidden = s !== name; });
    el["t-ovpanel"].hidden = true;
    if (name === "home") { refreshHome(); paintPlan(); }
  }

  /* ------------------------------------------------------------------- wire */

  function wire() {
    document.querySelectorAll("[data-mode]").forEach(function (b) {
      b.addEventListener("click", function () { chooseMode(b.dataset.mode); });
    });

    el["b-cancel"].addEventListener("click", function () { el.builder.hidden = true; });
    el["f-cancel"].addEventListener("click", function () { el.topicpick.hidden = true; });

    el.builder.addEventListener("submit", function (e) {
      e.preventDefault();
      var keys = Array.prototype.slice
        .call(el["b-topics"].querySelectorAll("input:checked"))
        .map(function (i) { return i.value; });
      if (!keys.length) keys = index.topics.map(function (t) { return t.key; });
      var pool = allQuestions(keys);
      var n = Math.max(1, Math.min(parseInt(el["b-count"].value, 10) || 20, pool.length));
      var strict = el["b-strict"].checked;
      var timed = el["b-timed"].checked;
      el.builder.hidden = true;
      startRun({
        mode: "custom",
        items: keys.length === 1 ? preferUnseen(pool).slice(0, n) : weightedPick(n, keys),
        strict: strict,
        minutes: timed ? Math.max(1, Math.round(n * index.seconds_per_question / 60)) : 0
      });
    });

    el["f-start"].addEventListener("click", function () {
      var v = el["f-topics"].querySelector("input:checked").value;
      var pool = v ? allQuestions([v]) : allQuestions();
      el.topicpick.hidden = true;
      startRun({ mode: "free", items: preferUnseen(pool), strict: false, minutes: 0 });
    });

    el["t-next"].addEventListener("click", next);
    el["t-prev"].addEventListener("click", prev);
    el["t-end"].addEventListener("click", function () {
      if (run && !run.done && window.confirm("End here and see the report?")) finish();
    });
    el["t-flag"].addEventListener("click", function () {
      run.flags[current().id] = !run.flags[current().id];
      render();
    });
    el["t-hl"].addEventListener("click", highlight);
    el["t-overview"].addEventListener("click", function () {
      el["t-ovpanel"].hidden = false;
      drawOverview("all");
    });
    el["ov-close"].addEventListener("click", function () { el["t-ovpanel"].hidden = true; });
    el["t-ovpanel"].querySelectorAll("[data-filter]").forEach(function (b) {
      b.addEventListener("click", function () {
        el["t-ovpanel"].querySelectorAll("[data-filter]").forEach(function (o) { o.classList.remove("on"); });
        b.classList.add("on");
        drawOverview(b.dataset.filter);
      });
    });

    el["br-go"].addEventListener("click", function () {
      beginSession(1);
      show("test");
      startClock();
      render();
    });

    el["r-done"].addEventListener("click", function () { run = null; show("home"); });
    document.querySelectorAll("[data-rfilter]").forEach(function (b) {
      b.addEventListener("click", function () {
        document.querySelectorAll("[data-rfilter]").forEach(function (o) { o.classList.remove("on"); });
        b.classList.add("on");
        var f = b.dataset.rfilter;
        el["r-review"].querySelectorAll(".rq").forEach(function (rq) {
          rq.hidden = f === "wrong" ? rq.dataset.wrong !== "1"
            : f === "slow" ? rq.dataset.slow !== "1" : false;
        });
      });
    });

    el.wipe.addEventListener("click", function () {
      if (!window.confirm("Delete every answer and timing stored in this browser?")) return;
      store.attempts = [];
      store.sr = {};
      save();
      refreshHome();
    });

    document.addEventListener("keydown", function (e) {
      if (el.test.hidden || !run || run.done) return;
      if (e.target && e.target.tagName === "INPUT") return;
      var k = e.key.toLowerCase();
      if (k === "a" || k === "1") pick(0);
      else if (k === "b" || k === "2") pick(1);
      else if (k === "c" || k === "3") pick(2);
      else if (k === "arrowright") next();
      else if (k === "arrowleft") prev();
    });
  }

  function chooseMode(mode) {
    el.builder.hidden = true;
    el.topicpick.hidden = true;

    if (mode === "custom") { el.builder.hidden = false; return; }
    if (mode === "free") { el.topicpick.hidden = false; return; }

    if (mode === "mock") {
      var items = weightedPick(index.mock_size);
      startRun({
        mode: "mock",
        items: items,
        strict: true,
        minutes: index.session_minutes,
        sessions: [[0, index.session_size - 1], [index.session_size, items.length - 1]]
      });
      return;
    }
    if (mode === "session") {
      startRun({
        mode: "session",
        items: weightedPick(index.session_size),
        strict: true,
        minutes: index.session_minutes
      });
      return;
    }
    if (mode === "drill") {
      startRun({
        mode: "drill",
        items: preferUnseen(allQuestions([weakestTopic()])).slice(0, 10),
        strict: false,
        minutes: 0
      });
      return;
    }
    if (mode === "mistakes") {
      startRun({
        mode: "mistakes",
        items: shuffle(wrongIds().map(function (id) { return byId[id]; })),
        strict: false,
        minutes: 0
      });
      return;
    }
    if (mode === "review") {
      startRun({
        mode: "review",
        items: shuffle(dueIds().map(function (id) { return byId[id]; })),
        strict: false,
        minutes: 0
      });
    }
  }

  function drawOverview(filter) {
    var r = sessionRange();
    var host = el["ov-grid"];
    host.textContent = "";
    for (var i = r[0]; i <= r[1]; i++) {
      var id = run.items[i];
      var answered = run.picks[id] !== undefined;
      var flagged = !!run.flags[id];
      if (filter === "unattempted" && answered) continue;
      if (filter === "attempted" && !answered) continue;
      if (filter === "flagged" && !flagged) continue;
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = String(i - r[0] + 1);
      var cls = [];
      if (answered) cls.push("done");
      if (flagged) cls.push("flag");
      if (i === run.idx) cls.push("here");
      b.className = cls.join(" ");
      b.dataset.i = String(i);
      b.addEventListener("click", function (e) {
        chargeTime();
        run.idx = parseInt(e.currentTarget.dataset.i, 10);
        el["t-ovpanel"].hidden = true;
        render();
      });
      host.appendChild(b);
    }
    if (!host.children.length) note(host, "Nothing in that group.");
  }

  /* Highlights are stored as character offsets into the stem, so they survive a
     re-render and never need the text to be treated as markup. */
  function offsetIn(node, offset) {
    var walker = document.createTreeWalker(el["t-stem"], NodeFilter.SHOW_TEXT, null);
    var total = 0;
    var n = walker.nextNode();
    while (n) {
      if (n === node) return total + offset;
      total += n.nodeValue.length;
      n = walker.nextNode();
    }
    return null;
  }

  function highlight() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;
    var range = sel.getRangeAt(0);
    if (!el["t-stem"].contains(range.startContainer)) return;
    if (!el["t-stem"].contains(range.endContainer)) return;
    var a = offsetIn(range.startContainer, range.startOffset);
    var b = offsetIn(range.endContainer, range.endOffset);
    if (a === null || b === null || b <= a) return;
    var q = current();
    var merged = [];
    (run.marks[q.id] || []).concat([[a, b]])
      .sort(function (x, y) { return x[0] - y[0]; })
      .forEach(function (x) {
        var last = merged[merged.length - 1];
        if (last && x[0] <= last[1]) last[1] = Math.max(last[1], x[1]);
        else merged.push([x[0], x[1]]);
      });
    run.marks[q.id] = merged;
    sel.removeAllRanges();
    render();
  }

  window.CFA_COMPANION = {                     // handles for the test harness
    clock: function () {
      return { counting: counting(), sec: totalSeconds(), today: daySeconds(today()) };
    },
    goIdle: function () { lastTouch = 0; },
    sync: function () { return syncNow(); },
    setKey: function (k) { store.key = k; save(); },
    dump: function () { return shareable(); },
    merge: mergeState,
    peek: function () {
      return {
        mode: run && run.mode,
        strict: run && run.strict,
        length: run && run.items.length,
        idx: run && run.idx,
        session: run && run.session,
        done: run && run.done,
        topics: run && run.items.map(function (id) { return byId[id].topic; }),
        answered: run ? Object.keys(run.picks).length : 0,
        attempts: store.attempts.length
      };
    },
    fill: function (correctly) {
      var guard = 0;
      while (run && !run.done && guard++ < 500) {
        var q = current();
        run.picks[q.id] = correctly ? q.answer : (q.answer + 1) % q.choices.length;
        run.spent[q.id] = 60000;
        if (!run.strict) record(q.id, q.topic, correctly, 60000, run.mode);
        var r = sessionRange();
        if (run.idx >= r[1]) { endSession(); return; }
        run.idx += 1;
      }
    }
  };

  boot();
})();
