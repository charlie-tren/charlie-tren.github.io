/* Shared engine for /beyond-small-talk and /split-the-room.
   Each page sets window.ROOM = { items: [...] } before loading this. */
(function () {
  var ITEMS = (window.ROOM && window.ROOM.items) || [];

  var qEl = document.getElementById("q");
  var stage = document.getElementById("stage");
  var prevBtn = document.getElementById("prevBtn");
  var nextBtn = document.getElementById("nextBtn");
  var bag = [], last = null;

  /* shuffle bag: every item shows once before any repeats */
  function refill() {
    bag = ITEMS.slice();
    for (var i = bag.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = bag[i]; bag[i] = bag[j]; bag[j] = t;
    }
    /* don't let a new bag open on the item just shown */
    if (bag.length > 1 && bag[bag.length - 1] === last) {
      var swap = bag.pop(); bag.unshift(swap);
    }
  }

  function draw() {
    if (!bag.length) refill();
    last = bag.pop();
    return last;
  }

  /* What has been shown, oldest first, so the arrows can walk back through it.
     Going back does NOT re-draw - it replays this list, so the sequence you saw is
     the sequence you get returning. Capped because it is a session trail, not a log;
     when it trims from the front, pos moves with it. */
  var seen = [], pos = -1, CAP = 200;

  /* shorter lines get bigger type; the box height stays fixed either way */
  function bucket(t) {
    var n = t.length;
    return n <= 45 ? "len-s" : n <= 80 ? "len-m" : n <= 120 ? "len-l" : "len-xl";
  }

  function paint(text) {
    qEl.textContent = text;
    qEl.className = "q " + bucket(text);   /* also clears .out, fading it back in */
    prevBtn.disabled = pos <= 0;
  }

  var busy = false;
  function show(animate) {
    if (!animate) { paint(seen[pos]); return; }
    busy = true;
    qEl.classList.add("out");
    setTimeout(function () {
      paint(seen[pos]);
      busy = false;
    }, 200);
  }

  function next(animate) {
    if (busy) return;
    if (pos < seen.length - 1) {
      pos++;                               /* replaying forward through history */
    } else {
      seen.push(draw());
      if (seen.length > CAP) seen.shift();
      pos = seen.length - 1;
    }
    show(animate);
  }

  function prev() {
    if (busy || pos <= 0) return;
    pos--;
    show(true);
  }

  if (ITEMS.length) {
    /* A swipe on a <button> also fires a click on touch devices, so a swipe sets a
       flag that the click handler consumes - otherwise every swipe advances twice. */
    var swiped = false, tx = 0, ty = 0;

    stage.addEventListener("touchstart", function (e) {
      var t = e.changedTouches[0];
      tx = t.clientX; ty = t.clientY; swiped = false;
    }, { passive: true });

    stage.addEventListener("touchend", function (e) {
      var t = e.changedTouches[0];
      var dx = t.clientX - tx, dy = t.clientY - ty;
      /* must be horizontal AND decisive, or it was a tap or a scroll */
      if (Math.abs(dx) < 45 || Math.abs(dx) <= Math.abs(dy)) return;
      swiped = true;
      if (dx < 0) next(true); else prev();
    }, { passive: true });

    stage.addEventListener("click", function () {
      if (swiped) { swiped = false; return; }
      next(true);
    });

    nextBtn.addEventListener("click", function () { next(true); });
    prevBtn.addEventListener("click", prev);

    document.addEventListener("keydown", function (e) {
      if (e.key === " " || e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault(); next(true);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault(); prev();
      }
    });

    next(false);
  }

  /* theme toggle - shares localStorage with the hub */
  var root = document.documentElement;
  var btn = document.getElementById("themeBtn"), lbl = document.getElementById("themeLbl");
  function sync() { lbl.textContent = root.getAttribute("data-theme") === "dark" ? "Dark" : "Light"; }
  sync();
  btn.addEventListener("click", function () {
    var dark = root.getAttribute("data-theme") !== "dark";
    root.setAttribute("data-theme", dark ? "dark" : "light");
    try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch (e) {}
    sync();
  });
})();
