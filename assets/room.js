/* Shared engine for /beyond-small-talk and /split-the-room.
   Each page sets window.ROOM = { items: [...] } before loading this. */
(function () {
  var ITEMS = (window.ROOM && window.ROOM.items) || [];

  var qEl = document.getElementById("q");
  var stage = document.getElementById("stage");
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

  /* shorter lines get bigger type; the box height stays fixed either way */
  function bucket(t) {
    var n = t.length;
    return n <= 45 ? "len-s" : n <= 80 ? "len-m" : n <= 120 ? "len-l" : "len-xl";
  }

  function paint(text) {
    qEl.textContent = text;
    qEl.className = "q " + bucket(text);   /* also clears .out, fading it back in */
  }

  var busy = false;
  function next(animate) {
    if (busy) return;
    if (!animate) { paint(draw()); return; }
    busy = true;
    qEl.classList.add("out");
    setTimeout(function () {
      paint(draw());
      busy = false;
    }, 200);
  }

  if (ITEMS.length) {
    stage.addEventListener("click", function () { next(true); });
    document.addEventListener("keydown", function (e) {
      if (e.key === " " || e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        next(true);
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
