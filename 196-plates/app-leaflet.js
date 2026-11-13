(async function () {
  // ---- the search page's globe, loaded only with no city in the address; without WebGL the flat world shows instead ----
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const THREE_JS = ["https://cdnjs.cloudflare.com/ajax/libs/three.js/0.149.0/three.min.js",
    "sha512-6p9lGA4Cm89KiwN1CixiOVQU2H9e13LeYoN6/Hj/qoUhtrMW5vNiqQz9Z96Z7/I8u89ghL6SPBz9na5HFVzF3g=="];
  const script = (src, sri) => new Promise((res, rej) => { const s = document.createElement("script"); s.src = src;
    if (sri) { s.integrity = sri; s.crossOrigin = "anonymous"; s.referrerPolicy = "no-referrer"; }
    s.onload = res; s.onerror = rej; document.head.appendChild(s); });
  const hasGL = () => { if (typeof window.__gl === "boolean") return window.__gl; try { const c = document.createElement("canvas"), g = c.getContext("webgl2") || c.getContext("webgl");
    if (g) { const x = g.getExtension("WEBGL_lose_context"); if (x) x.loseContext(); } return !!g; } catch (e) { return false; } };
  let globeReady = null;
  const startGlobe = () => {
    if (globeReady) return globeReady;
    if (!hasGL()) return (globeReady = Promise.resolve(null));
    return (globeReady = script(...THREE_JS).then(() => script("globe.js")).then(() => Globe.start(document.getElementById("intro"), { reduce })).catch(() => null));
  };
  if (!location.hash && document.getElementById("intro")) startGlobe();

  const ORDER = ["Europe", "Africa", "Middle East", "Central Asia", "South Asia", "Southeast Asia", "East Asia", "Oceania", "Americas"]; // left to right across the world view
  // the fallback plays the intro for the first city only; another city opens straight on its map (#id)
  const CITIES = await fetch("cities.json").then(r => r.json()).catch(() => null) || [{ id: "sydney", name: "Sydney", country: "Australia", base: "" }];
  const C = CITIES.find(c => "#" + c.id === location.hash.toLowerCase()) || CITIES[0];
  const D = await (await fetch(C.base + "data.json")).json();
  const CITY = C.id;
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = u => /^https?:\/\//.test(u || "") ? u : null;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
                  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  D.pins = D.pins.filter(p => /^[a-z]{2}$/.test(p.c2));
  const byCC = Object.fromEntries(D.pins.map(p => [p.cc, p]));
  document.getElementById("n").textContent = D.pins.length;
  const mq = window.matchMedia("(max-width: 760px)"), phone = () => mq.matches;
  const small = mq.matches;
  const W = small ? 22 : 32;
  const mapEl = document.getElementById("map");
  // returns where the map's top will be once the scroll lands
  const toMap = () => { if (!phone()) return null; mapEl.scrollIntoView({ behavior: reduce ? "auto" : "smooth" }); return 0; };
  let introBusy = false, pendingRow = null;

  // ---- theme ----
  const themeBtn = document.getElementById("theme");
  const setTheme = t => { document.documentElement.dataset.theme = t; themeBtn.setAttribute("aria-pressed", t === "dark");
    themeBtn.querySelector(".lbl").dataset.t = t === "dark" ? "Light" : "Dark"; store.set("196plates.theme", t); };
  setTheme(document.documentElement.dataset.theme || "dark");
  themeBtn.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));

  // ---- map ----
  const map = L.map("map", { zoomControl: false, attributionControl: true, zoomSnap: 1, worldCopyJump: false });
  map.attributionControl.setPrefix(false);
  // zoom sits bottom right above the credit; the third button fits the city again
  const zoomCtl = L.control.zoom({ position: "bottomright" }).addTo(map);
  const fitBtn = L.DomUtil.create("a", "leaflet-control-zoom-fit", zoomCtl.getContainer());
  fitBtn.href = "#"; fitBtn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/><circle cx="12" cy="12" r="2.2"/></svg>';
  fitBtn.setAttribute("role", "button"); fitBtn.title = `Fit ${D.city}`; fitBtn.setAttribute("aria-label", `Fit ${D.city}`);
  L.DomEvent.on(fitBtn, "click", e => { L.DomEvent.preventDefault(e); map.fitBounds(cityBounds, { padding: [30, 30] }); });
  const BASE = window.__BASE || { url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>' };
  const tiles = L.tileLayer(BASE.url, { maxZoom: 19, maxNativeZoom: BASE.max || 19, subdomains: BASE.sub || "abc", attribution: BASE.attribution, keepBuffer: 6, updateWhenIdle: false, updateWhenZooming: true }).addTo(map);

  // the map cannot be dragged or zoomed while the intro plays or the world view is up, and its controls hide
  const HANDLERS = ["dragging", "touchZoom", "doubleClickZoom", "scrollWheelZoom", "boxZoom", "keyboard"];
  const lock = on => { HANDLERS.forEach(h => map[h] && (on ? map[h].disable() : map[h].enable()));
    document.getElementById("map").classList.toggle("locked", on); };

  // ---- the list is resizable: drag or arrow keys on the edge, width kept on this device ----
  const grip = document.getElementById("grip");
  const setPanel = w => { w = Math.round(Math.min(Math.max(w, 240), Math.min(760, innerWidth - 320)));
    document.documentElement.style.setProperty("--panel", w + "px"); map.invalidateSize(); return w; };
  const saved = store.get("196plates.panel", null);
  if (saved) document.documentElement.style.setProperty("--panel", saved + "px"); // the CSS fits it to the window, then and on resize
  grip.addEventListener("pointerdown", e => {
    e.preventDefault(); grip.setPointerCapture(e.pointerId); grip.classList.add("drag");
    const move = ev => setPanel(ev.clientX);
    const up = ev => { grip.classList.remove("drag"); store.set("196plates.panel", setPanel(ev.clientX));
      grip.removeEventListener("pointermove", move); grip.removeEventListener("pointerup", up); };
    grip.addEventListener("pointermove", move); grip.addEventListener("pointerup", up);
  });
  grip.addEventListener("keydown", e => {
    const d = e.key === "ArrowLeft" ? -24 : e.key === "ArrowRight" ? 24 : 0;
    if (d) { e.preventDefault(); store.set("196plates.panel", setPanel(document.querySelector(".panel").offsetWidth + d)); }
  });

  // ---- places you have eaten at, kept on this device (cc -> date) ----
  const KEY = "196plates.eaten." + CITY;
  // a tick on a country this city no longer lists is set aside: opening it from the world map crashed
  let eaten = Object.fromEntries(Object.entries(store.get(KEY, {}) || {}).filter(([cc]) => D.pins.some(p => p.cc === cc)));
  const isEaten = cc => !!eaten[cc];
  const eatenCount = document.getElementById("been");
  const paint = () => {
    const n = Object.keys(eaten).length;
    eatenCount.hidden = n === 0;
    if (n === 0 && filterMode !== "all") { filterMode = "all"; }  // the filter hides at zero, so it must not leave the list filtered
    eatenCount.innerHTML = `${n} eaten &middot; <button type="button" class="linkish" id="mine">Your map</button>`;
    document.getElementById("filter").hidden = n === 0;
    applyFilter();
    const mine = document.getElementById("mine"); if (mine) mine.onclick = () => { toMap(); showWorld("mine"); };
    document.querySelectorAll("[data-cc]").forEach(el => el.classList.toggle("is-been", isEaten(el.dataset.cc)));
  };
  const toggleEaten = cc => { if (eaten[cc]) delete eaten[cc]; else eaten[cc] = new Date().toISOString().slice(0, 10); store.set(KEY, eaten); paint(); };
  const fmtDate = iso => iso ? iso.split("-").reverse().join("/") : "";

  const dirUrl = p => "https://www.google.com/maps/dir/?api=1&destination=" +
    encodeURIComponent(p.address ? `${p.name}, ${p.address}` : `${p.name}, ${p.suburb || ""}, ${D.city}`);
  const cardParts = p => {
    const links = (p.src || []).filter(s => safeUrl(s.url));
    const rev = p.review && safeUrl(p.review.url) ? p.review : null;
    const web = safeUrl(p.web);
    const n = links.length;
    return {
      head: `<div class="card-kicker">${esc(p.adj)}${p.suburb ? " &middot; " + esc(p.suburb) : ""}</div>
      <div class="card-name">${esc(p.name)}</div>`,
      src: n ? `<details class="card-src"><summary>${n} ${n === 1 ? "source" : "sources"}</summary><ul>${links.map(s =>
        `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a></li>`).join("")}</ul></details>` : "",
      actions: `<div class="card-actions">
        ${rev ? `<a class="card-btn wide" href="${esc(rev.url)}" target="_blank" rel="noopener">Read the review <span class="via">&middot; ${esc(rev.name)}</span></a>` : ""}
        ${web ? `<a class="card-btn alt" href="${esc(web)}" target="_blank" rel="noopener">Website</a>` : ""}
        <a class="card-btn alt" href="${dirUrl(p)}" target="_blank" rel="noopener">Directions</a>
        <label class="card-check"><input type="checkbox" data-eat="${esc(p.cc)}" ${isEaten(p.cc) ? "checked" : ""}> Eaten here</label>
      </div>`
    };
  };
  const card = p => { const c = cardParts(p);
    return `<div class="card-flag"><img src="flags/${p.c2}-320.png" alt="Flag of ${esc(p.country)}"></div><div class="card-body">${c.head}${c.src}${c.actions}</div>`; };

  const pinLayer = L.featureGroup();
  const markers = {};
  D.pins.forEach(p => {
    const m = L.marker([p.lat, p.lon], {
      title: `${p.adj}: ${p.name}`, riseOnHover: true,
      icon: L.divIcon({ className: "", iconSize: [W, W], iconAnchor: [W / 2, W / 2],
        html: `<div class="pin" data-cc="${esc(p.cc)}" style="width:${W}px;height:${W}px;background-image:url(flags/circle/${p.c2}.svg)"></div>` })
    });
    // phones get the bottom sheet instead of the popup
    m._openPopup = function (e) { if (!phone()) return L.Layer.prototype._openPopup.call(this, e); L.DomEvent.stop(e); tapPin(p, e); };
    m.bindPopup(() => card(p), { className: "card", closeButton: true, offset: [0, -W / 2 + 4], autoPanPadding: [24, 24], maxWidth: 270, minWidth: 250 });
    pinLayer.addLayer(m);
    markers[p.cc] = m;
  });
  map.addLayer(pinLayer);
  // the card clears the map controls, refits as it grows, and holds focus until it closes
  let cardPopup = null, opener = null, nextOpener = null;
  const refit = pp => { if (!pp._map) return; pp._updateLayout(); pp._updatePosition(); pp._adjustPan(); };
  map.on("popupopen", e => {
    const pp = e.popup, el = pp.getElement(), m = mapEl.getBoundingClientRect();
    const z = document.querySelector(".leaflet-control-zoom"), w = document.querySelector(".map-toggle");
    pp.options.autoPanPaddingTopLeft = [24, w && w.offsetWidth ? w.getBoundingClientRect().bottom - m.top + 8 : 24];
    pp.options.autoPanPaddingBottomRight = [z && z.offsetWidth && el.offsetWidth + (m.right - z.getBoundingClientRect().left) + 32 <= m.width ? m.right - z.getBoundingClientRect().left + 8 : 24, 24];
    refit(pp);
    const img = el.querySelector(".card-flag img"); if (img && !img.complete) img.addEventListener("load", () => refit(pp), { once: true });
    const src = el.querySelector(".card-src"); if (src) src.addEventListener("toggle", () => refit(pp));
    const b = el.querySelector("[data-eat]"); if (b) b.addEventListener("change", () => toggleEaten(b.dataset.eat));
    cardPopup = pp; opener = nextOpener || (pp._source && pp._source.getElement && pp._source.getElement()) || null; nextOpener = null;
    const c = el.querySelector(".leaflet-popup-content"), nm = el.querySelector(".card-name");
    c.tabIndex = -1; c.setAttribute("role", "dialog"); if (nm) c.setAttribute("aria-label", nm.textContent);
    c.focus({ preventScroll: true });
  });
  map.on("popupclose", e => {
    if (e.popup !== cardPopup) return;
    const a = document.activeElement, o = opener; cardPopup = null; opener = null;
    if (o && document.contains(o) && (!a || a === document.body || e.popup.getElement().contains(a))) o.focus({ preventScroll: true });
  });
  const cityBounds = L.latLngBounds(D.pins.map(p => [p.lat, p.lon]));
  const openPin = (cc, mapTop) => {
    const m = markers[cc], z = Math.max(map.getZoom(), 15);
    if (phone()) { openSheet([byCC[cc]], { opener: nextOpener || m.getElement(), at: m.getLatLng(), zoom: z, mapTop }); nextOpener = null; return; }
    map.once("moveend", () => m.openPopup()); map.flyTo(m.getLatLng(), z, { duration: .8 });
  };
  const openRow = (cc, b) => { nextOpener = b; hideWorld(); openPin(cc, toMap()); };

  // ---- the phone card: a bottom sheet; a tap where several pins overlap lists them first ----
  const sheet = document.getElementById("sheet");
  let sheetOn = false, sheetOpener = null, sheetAt = null;
  const tapPin = (p, e) => {
    const oe = e && e.originalEvent; let near = [p];
    if (oe && oe.type === "click" && typeof oe.clientX === "number") {
      const pt = map.mouseEventToContainerPoint(oe), d = q => map.latLngToContainerPoint([q.lat, q.lon]).distanceTo(pt);
      near = D.pins.filter(q => { const el = markers[q.cc].getElement(); return q === p || (el && !el.classList.contains("dim") && d(q) <= 21); }).sort((a, b) => d(a) - d(b));
    }
    const b = L.latLngBounds(near.map(q => [q.lat, q.lon])), at = near.length > 1 ? b.getCenter() : L.latLng(p.lat, p.lon);
    // more than 6 under the finger: zoom into the pile, leaving room at the bottom for the card that comes next
    if (near.length > 6) {
      const r = mapEl.getBoundingClientRect(), under = Math.min(r.height / 2, Math.max(0, r.bottom - innerHeight * .55));
      const tl = [40, 40], br = [40, 40 + under];
      if (map.getBoundsZoom(b, false, L.point(tl).add(br)) > map.getZoom()) {
        closeSheet(); map.flyToBounds(b, { paddingTopLeft: tl, paddingBottomRight: br, duration: reduce ? 0 : .8, animate: !reduce }); return; }
    }
    openSheet(near, { opener: markers[p.cc].getElement(), at, zoom: map.getZoom() });
  };
  // centre the map so a point sits midway between the top of the visible map and the top of the sheet
  const placeAbove = (at, z, mapTop) => {
    const H = mapEl.clientHeight, t = mapTop == null ? mapEl.getBoundingClientRect().top : mapTop;
    const visTop = Math.max(0, t), visBot = Math.max(visTop + 80, Math.min(t + H, innerHeight - (sheetOn ? sheet.offsetHeight : 0)));
    const c = map.unproject(map.project(at, z).add([0, H / 2 - ((visTop + visBot) / 2 - t)]), z);
    if (reduce) map.setView(c, z, { animate: false });
    else if (z !== map.getZoom()) map.flyTo(c, z, { duration: .8 });
    else map.panTo(c);
  };
  function openSheet(list, o) {
    const one = list.length === 1, p = list[0];
    let body, foot = "";
    if (one) { const c = cardParts(p);
      body = `<div class="sheet-head"><img class="sheet-flag fit-${p.fit}" src="flags/${p.c2}-320.png" alt="Flag of ${esc(p.country)}"><div>${c.head}</div></div>${c.src}`;
      foot = `<div class="sheet-foot">${c.actions}</div>`;
    } else body = `<ul class="sheet-list">${list.map(q => `<li><button type="button" class="row${isEaten(q.cc) ? " is-been" : ""}" data-cc="${esc(q.cc)}"><img class="fit-${q.fit}" src="flags/${q.c2}-80.png" alt=""><span class="rc">${esc(q.country)}</span>${rowName(q)}</button></li>`).join("")}</ul>`;
    sheet.innerHTML = `<div class="sheet-grab" aria-hidden="true"><span></span></div><button type="button" class="sheet-x" aria-label="Close">&times;</button><div class="sheet-body">${body}</div>${foot}`;
    sheet.setAttribute("aria-label", one ? p.name : `${list.length} restaurants`);
    sheet.style.transform = ""; sheet.hidden = false; sheetOn = true; document.body.classList.add("sheet-open");
    requestAnimationFrame(() => { if (sheetOn) sheet.classList.add("open"); });
    if (o.opener !== undefined) sheetOpener = o.opener;
    sheetAt = o.at;
    sheet.querySelector(".sheet-x").onclick = closeSheet;
    const b = sheet.querySelector("[data-eat]"); if (b) b.addEventListener("change", () => toggleEaten(b.dataset.eat));
    const src = sheet.querySelector(".card-src"); if (src) src.addEventListener("toggle", () => placeAbove(sheetAt, map.getZoom()));
    sheet.querySelectorAll(".sheet-list .row").forEach(r => r.addEventListener("click", () => {
      const q = byCC[r.dataset.cc]; openSheet([q], { at: L.latLng(q.lat, q.lon), zoom: map.getZoom() }); }));
    sheet.focus({ preventScroll: true });
    placeAbove(o.at, o.zoom, o.mapTop);
  }
  function closeSheet() {
    if (!sheetOn) return;
    const a = document.activeElement, o = sheetOpener; sheetOn = false; sheetOpener = null;
    sheet.classList.remove("open"); sheet.style.transform = ""; document.body.classList.remove("sheet-open");
    setTimeout(() => { if (!sheetOn) { sheet.hidden = true; sheet.innerHTML = ""; sheet.style.transform = ""; } }, reduce ? 0 : 260);
    if (o && document.contains(o) && (!a || a === document.body || sheet.contains(a))) o.focus({ preventScroll: true });
  }
  // the handle drags the sheet down; past 70px it closes
  sheet.addEventListener("pointerdown", e => {
    const g = e.target.closest(".sheet-grab"); if (!g) return;
    const y0 = e.clientY; let dy = 0; g.setPointerCapture(e.pointerId); sheet.style.transition = "none";
    const move = ev => { dy = Math.max(0, ev.clientY - y0); sheet.style.transform = `translateY(${dy}px)`; };
    const up = () => { g.removeEventListener("pointermove", move); g.removeEventListener("pointerup", up); g.removeEventListener("pointercancel", up);
      sheet.style.transition = ""; if (dy > 70) closeSheet(); else sheet.style.transform = ""; };
    g.addEventListener("pointermove", move); g.addEventListener("pointerup", up); g.addEventListener("pointercancel", up);
  });
  map.on("click", closeSheet);
  mq.addEventListener("change", () => { closeSheet(); map.closePopup(); });

  // ---- side panel: rows, alphabetical within each region ----
  const groups = document.getElementById("groups");
  ORDER.forEach(g => {
    const ps = D.pins.filter(p => p.group === g).sort((a, b) => a.country.localeCompare(b.country));
    if (!ps.length) return;
    const sec = document.createElement("section");
    sec.className = "group";
    sec.innerHTML = `<h2>${esc(g)}</h2><ul class="rows"></ul>`;
    ps.forEach(p => {
      const li = document.createElement("li");
      li.innerHTML = `<button type="button" class="row" data-cc="${esc(p.cc)}"><img class="fit-${p.fit}" src="flags/${p.c2}-80.png" alt="" loading="lazy"><span class="rc">${esc(p.country)}</span>${rowName(p)}</button>`;
      li.querySelector("button").addEventListener("click", e => { const b = e.currentTarget;
        if (introBusy) { pendingRow = [p.cc, b]; toMap(); } else openRow(p.cc, b); });
      sec.querySelector(".rows").appendChild(li);
    });
    groups.appendChild(sec);
  });

  // ---- filter the list: all / eaten / to try, and a search on country, cuisine or restaurant ----
  const SHORT = { "Mother Chu's Taiwanese Gourmet": "Mother Chu's", "Mama Lor Restaurant & Bakery": "Mama Lor",
    "K&K Austrian Cafe & Coffee House": "K&K Austrian Cafe", "Botellon Spanish Tapas & Wine Bar": "Botellon" };
  const rowName = p => `<span class="rn"><span class="nm">${esc(SHORT[p.name] || p.name.replace(/\s*\([^)]*\)$/, ""))}</span>${p.price
    ? `<span class="rp" aria-label="${["", "Cheap", "Mid-range", "Expensive"][p.price]}">${"$".repeat(p.price)}</span>` : ""}</span>`;
  let filterMode = "all";
  const prices = new Set();  // empty = any price
  const fold = s => String(s || "").normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  const inFilter = cc => (filterMode === "eaten" ? isEaten(cc) : filterMode === "not" ? !isEaten(cc) : true) &&
    (!prices.size || prices.has(byCC[cc].price));
  const empty = document.getElementById("empty");
  function applyFilter() {
    const q = fold(document.getElementById("find").value.trim());
    let shown = 0, hits = 0;
    document.querySelectorAll("#groups .rows li").forEach(li => {
      const cc = li.firstElementChild.dataset.cc, p = byCC[cc];
      const hit = !q || [p.country, p.adj, p.name].some(s => fold(s).includes(q));
      li.hidden = !hit || !inFilter(cc); hits += hit; shown += !li.hidden;
    });
    document.querySelectorAll("#groups .group").forEach(sec => { sec.hidden = ![...sec.querySelectorAll("li")].some(li => !li.hidden); });
    document.querySelectorAll("#filter button").forEach(b => b.setAttribute("aria-pressed", b.dataset.f === filterMode));
    document.querySelectorAll("#price button").forEach(b => b.setAttribute("aria-pressed", prices.has(+b.dataset.p)));
    empty.hidden = shown > 0;
    empty.innerHTML = shown ? "" : (filterMode !== "all" || prices.size) && hits
      ? `No match. <button type="button" class="linkish" id="showall">Show all</button>` : "No countries match.";
    const all = document.getElementById("showall");
    if (all) all.onclick = () => { filterMode = "all"; prices.clear(); applyFilter(); document.getElementById("find").focus({ preventScroll: true }); };
    D.pins.forEach(p => { const el = markers[p.cc].getElement(); if (!el) return;
      const off = !inFilter(p.cc); el.classList.toggle("dim", off); el.tabIndex = off ? -1 : 0; });
  }
  document.querySelectorAll("#filter button").forEach(b => b.addEventListener("click", () => { filterMode = b.dataset.f; applyFilter(); }));
  document.querySelectorAll("#price button").forEach(b => b.addEventListener("click", () => {
    const v = +b.dataset.p; if (!prices.delete(v)) prices.add(v); applyFilter(); }));
  const find = document.getElementById("find");
  find.addEventListener("input", applyFilter);
  find.addEventListener("keydown", e => { if (e.key !== "Enter") return;
    const li = [...document.querySelectorAll("#groups .rows li")].find(l => !l.hidden); if (li) li.firstElementChild.click(); });
  document.querySelector(".lede").textContent = `How many of the ${D.pins.length} cuisines in ${D.city} can you eat?`;
  document.querySelectorAll(".how .city").forEach(s => { s.textContent = D.city; });

  // ---- world views: which of 196 the city has, and your own map ----
  // rings west of -25 move east by 360 and date-line rings are unwrapped, so the world reads once from -25 to 335
  const fix = r => { const xs = r.map(p => p[0]), spans = Math.max(...xs) - Math.min(...xs) > 180, mean = xs.reduce((a, b) => a + b, 0) / xs.length;
    return r.map(([x, y]) => [(spans ? x < 0 : mean < -25) ? x + 360 : x, y]); };
  const worldBtn = L.control({ position: "topright" });
  worldBtn.onAdd = () => { const d = L.DomUtil.create("div", "map-toggle");
    d.innerHTML = `<button type="button" id="worldbtn">World</button>`; L.DomEvent.disableClickPropagation(d); return d; };
  worldBtn.addTo(map);
  // the world views (city and your own) are one drawn map over the tiles (worldmap.js, design 348/352)
  let wm = null, worldOpener = null;
  function showWorld(mode) {
    hideWorld(); worldOpener = document.activeElement;
    // inside the map's controls, after World and before the credit, so that is the tab order
    const box = document.createElement("div"); box.id = "worldmap"; box.style.cssText = "position:absolute;inset:0;z-index:800";
    L.DomEvent.disableClickPropagation(box); L.DomEvent.disableScrollPropagation(box); box.addEventListener("click", e => e.stopPropagation());
    map._controlContainer.insertBefore(box, map._controlCorners.bottomleft);
    map.closePopup(); closeSheet(); lock(true);
    wm = WorldMap.render(box, { eaten, pins: D.pins, city: D.city, onPick: cc => { hideWorld(); openPin(cc); } });
    document.getElementById("worldbtn").textContent = `Back to ${D.city}`;
    document.getElementById("worldbtn").onclick = hideWorld;
  }
  function hideWorld() {
    if (!wm) return;
    wm.destroy(); wm = null; document.getElementById("worldmap").remove(); lock(false);
    document.getElementById("worldbtn").textContent = "World";
    document.getElementById("worldbtn").onclick = () => showWorld("city");
  }
  document.getElementById("worldbtn").onclick = () => showWorld("city");
  addEventListener("keydown", e => {
    if (e.key !== "Escape" || introBusy) return;
    if (sheetOn) { closeSheet(); return; }
    if (cardPopup) { map.closePopup(); return; }
    if (wm) { const o = worldOpener && document.contains(worldOpener) && worldOpener !== document.body ? worldOpener : document.getElementById("worldbtn");
      hideWorld(); o.focus({ preventScroll: true }); }
  });

  // ---- the search intro: a plain page; pick a city, great-circle arcs draw in, the camera flies to it ----
  const intro = document.getElementById("intro");
  const skip = location.hash.toLowerCase() === "#" + CITY || !intro;
  // the world never shows twice: at the widest the map shows it once, and the city map cannot pan past the edges
  const worldZoom = () => Math.max(1, Math.ceil(Math.log2(map.getSize().x / 256)));
  const limitWorld = () => { map.setMinZoom(worldZoom()); map.setMaxBounds([[-85, -180], [85, 180]]); map.options.maxBoundsViscosity = 1; };
  map.on("resize", () => { if (!intro || !document.body.contains(intro)) limitWorld(); });
  if (skip) {
    if (intro) intro.remove();
    document.body.classList.remove("searching");
    map.fitBounds(cityBounds, { padding: [30, 30] }); limitWorld();
  } else {
    document.body.classList.add("searching");
    // the intro's world: the exact zoom that shows it once, unsnapped, centred on the lit countries' span (-25 to 335); zoomSnap returns on landing
    const introView = () => { map.options.zoomSnap = 0; const sz = map.getSize(), z = Math.log2(sz.x / 256), a = map.project([72, 155], z), b = map.project([-56, 155], z);
      const y = sz.x >= sz.y ? Math.min(Math.max((a.y + b.y) / 2, sz.y / 2), sz.x - sz.y / 2) : sz.x / 2;
      map.setView(map.unproject(L.point(a.x, y), z), z, { animate: false }); };
    const fitCity = () => { const s = map.options.zoomSnap; map.options.zoomSnap = 1; const r = map._getBoundsCenterZoom(cityBounds, { padding: [30, 30] }); map.options.zoomSnap = s; return r; };
    // the world view and every pin's flag load behind the search, so the intro starts on a finished map
    introView();
    map.removeLayer(pinLayer);
    // the orange fills use 50m outlines, close enough to the tile coastlines at the zooms they are seen at
    let introGeo = null;
    const loadIntro = () => introGeo || (introGeo = fetch("intro-50m.json").then(r => r.json()).then(G => {
      G.features.forEach(f => { f.cc = f.properties.cc; f.geometry.coordinates = f.geometry.coordinates.map(pl => pl.map(fix)); }); return G; }));
    const fetchTiles = (center, zoom, size, seen = new Set()) => {
      const subs = tiles.options.subdomains, tz = Math.min(tiles.options.maxNativeZoom, Math.round(zoom)), n = 2 ** tz, c = map.project(center, tz), h = size.divideBy(2 * 2 ** (zoom - tz));
      for (let x = Math.floor((c.x - h.x) / 256); x <= Math.floor((c.x + h.x) / 256); x++)
        for (let y = Math.max(0, Math.floor((c.y - h.y) / 256)); y <= Math.min(n - 1, Math.floor((c.y + h.y) / 256)); y++) {
          const xx = ((x % n) + n) % n, url = L.Util.template(tiles._url, { s: subs[Math.abs(xx + y) % subs.length], x: xx, y, z: tz, r: "" });
          if (!seen.has(url)) { seen.add(url); new Image().src = url; }
        }
      return seen;
    };
    let globe = null, started = false;
    startGlobe().then(g => {
      // what only the flight needs waits until the globe is up, so it does not queue behind the globe's textures
      loadIntro(); D.pins.forEach(p => { new Image().src = `flags/circle/${p.c2}.svg`; });
      if (!g) { document.body.classList.add("flat"); map.invalidateSize(); introView(); lock(true); return; }
      if (started) g.destroy(); else globe = g;
    });
    const input = intro.querySelector("input"), list = intro.querySelector("ul");
    const cities = CITIES;
    const box = intro.querySelector(".search");
    let open = false;
    const render = () => {
      const q = input.value.trim().toLowerCase();
      const m = cities.filter(c => c.name.toLowerCase().startsWith(q)), hits = m.length ? m : cities;
      list.hidden = !open;
      list.innerHTML = hits.map(c => `<li><button type="button" data-id="${esc(c.id)}"><span><b>${esc(c.name)}</b>, ${esc(c.country)}</span><span class="n">${c.n} cuisines</span></button></li>`).join("")
        + `<li class="soon">More cities coming</li>`;
      list.querySelectorAll("button").forEach(b => b.addEventListener("click", go));
    };
    const show = on => { open = on; render(); };
    ["focus", "input", "click"].forEach(t => input.addEventListener(t, () => show(true)));
    box.addEventListener("focusout", e => { if (e.relatedTarget && !box.contains(e.relatedTarget)) show(false); });
    document.addEventListener("pointerdown", e => { if (open && !box.contains(e.target)) show(false); });
    input.addEventListener("keydown", e => {
      if (e.key === "Enter") { const b = list.querySelector("button"); if (b) b.click(); }
      else if (e.key === "Escape") { e.preventDefault(); show(false); } });
    input.focus();
    async function go(e) {
      const id = e && e.currentTarget && e.currentTarget.dataset.id;
      if (id && id !== C.id) { location.hash = id; location.reload(); return; }
      if (started) return; started = true; introBusy = true;
      history.replaceState(null, "", "#" + CITY);
      document.body.classList.remove("searching", "flat");
      map.invalidateSize();
      introView();
      mapEl.classList.add("pins-hidden");
      lock(true);
      intro.classList.add("gone");
      // the landing view's tiles and every pin's flag start loading now, whether the intro plays out or is skipped
      const land = fitCity(), seen = fetchTiles(land.center, land.zoom, map.getSize());
      D.pins.forEach(p => { new Image().src = `flags/circle/${p.c2}.svg`; });
      // a click, tap or key from here on jumps to the end (not a wheel or pinch); armed after the event that started it
      let skipped = false, skipNow, fx = null;
      const skipP = new Promise(r => { skipNow = r; }), race = p => Promise.race([p, skipP]);
      const SKIP = ["click", "keydown"], onSkip = e => {
        if (skipped || (e.type === "keydown" && ["Shift", "Control", "Alt", "Meta"].includes(e.key))) return;
        skipped = true; skipNow();
        if (e.type === "click" && mapEl.contains(e.target)) { e.stopPropagation(); e.preventDefault(); } };
      setTimeout(() => { if (introBusy) SKIP.forEach(t => addEventListener(t, onSkip, { capture: true })); }, 0);
      const fxPane = map.getPanes().overlayPane;
      // the arcs and fills fade out as the camera passes the continent, before they can pile into a fan
      const fade = () => {
        const k = Math.max(0, 1 - (map.getZoom() - z0 - .6) / 1.2);
        fxPane.style.opacity = k;
        if (k === 0 && fx) { map.removeLayer(fx); fx = null; fxPane.style.opacity = ""; map.off("zoom", fade); }
      };
      const done = () => {
        SKIP.forEach(t => removeEventListener(t, onSkip, { capture: true }));
        map.off("zoom", fade); fxPane.style.opacity = "";
        if (fx) { map.removeLayer(fx); fx = null; }
        map.options.zoomSnap = 1;
        if (skipped) map.fitBounds(cityBounds, { padding: [30, 30], animate: false });
        const a = document.activeElement, lost = !a || a === document.body || intro.contains(a);
        map.addLayer(pinLayer); intro.remove(); introBusy = false; paint(); lock(false); limitWorld();
        // pins wait for the tiles on screen (not the buffer the flight left), up to 1.5s
        const mp = map.getPanes().markerPane, t1 = performance.now();
        const onScreen = () => { const M = mapEl.getBoundingClientRect(), lv = tiles._level; return !lv || [...lv.el.querySelectorAll("img")].every(i => {
          const r = i.getBoundingClientRect(); return i.classList.contains("leaflet-tile-loaded") || r.right <= M.left || r.left >= M.right || r.bottom <= M.top || r.top >= M.bottom; }); };
        new Promise(r => { const tick = () => onScreen() || performance.now() - t1 > 1500 ? r() : setTimeout(tick, 50); tick(); }).then(() => {
          if (skipped) { mp.style.transition = "none"; mapEl.classList.remove("pins-hidden"); void mp.offsetWidth; mp.style.transition = ""; }
          else requestAnimationFrame(() => mapEl.classList.remove("pins-hidden")); });
        if (pendingRow) { const [cc, b] = pendingRow; pendingRow = null; openRow(cc, b); }
        else if (lost) find.focus({ preventScroll: true });
      };
      // the globe turns to the city as it fades, then the map's own intro runs from the world view beneath it
      if (globe) { const g = globe, c = cityBounds.getCenter(); globe = null; await race(g.turnTo(c.lng, c.lat, 1000)); if (skipped) g.destroy(); else setTimeout(() => g.destroy(), reduce ? 1000 : 0); }
      if (skipped) return done();
      // the flight is Leaflet's own van Wijk path, eased in and out; every tile it will pass over is fetched while the
      // arcs draw, and tiles are refreshed every frame, so no zoom level arrives blank
      const size = map.getSize(), z0 = map.getZoom(), from = map.project(map.getCenter(), z0);
      const tgt = fitCity();
      const toPx = map.project(tgt.center, z0), w0 = Math.max(size.x, size.y), w1 = w0 * map.getZoomScale(z0, tgt.zoom);
      const u1 = toPx.distanceTo(from) || 1, rho = 1.42, rho2 = rho * rho;
      const rr = i => { const b = (w1 * w1 - w0 * w0 + (i ? -1 : 1) * rho2 * rho2 * u1 * u1) / (2 * (i ? w1 : w0) * rho2 * u1), sq = Math.sqrt(b * b + 1) - b; return sq < 1e-9 ? -18 : Math.log(sq); };
      const r0 = rr(0), S = (rr(1) - r0) / rho;
      const at = t => { if (t >= 1) return tgt; const s = t * S, w = w0 * Math.cosh(r0) / Math.cosh(r0 + rho * s), u = w0 * (Math.cosh(r0) * Math.tanh(r0 + rho * s) - Math.sinh(r0)) / rho2;
        return { center: map.unproject(from.add(toPx.subtract(from).multiplyBy(u / u1)), z0), zoom: map.getScaleZoom(w0 / w, z0) }; };
      if (!reduce) for (let i = 0; i <= 120; i++) { const v = at(i / 120); fetchTiles(v.center, v.zoom, size, seen); }
      const fly = T => new Promise(res => {
        map._stop(); map._moveStart(true, false);
        const t0 = performance.now();
        let last = null;
        const frame = now => { if (skipped) { map._moveEnd(true); return res(); }
          const t = Math.min(1, (now - t0) / T), e = t < .5 ? 4 * t * t * t : 1 - (2 - 2 * t) ** 3 / 2, v = at(e);
          map._move(v.center, v.zoom, { flyTo: true });
          // new tiles only when the view has moved a quarter tile at the current tile zoom
          const c = map.project(v.center, Math.round(v.zoom));
          if (!last || last.z !== Math.round(v.zoom) || c.distanceTo(last.c) > 64) { tiles._update(); tiles._pruneTiles(); last = { z: Math.round(v.zoom), c }; }
          if (t < 1) requestAnimationFrame(frame); else { map._moveEnd(true); res(); } };
        requestAnimationFrame(frame);
      });
      try {
        const F = await race(loadIntro());
        if (skipped) return done();
        fx = L.featureGroup().addTo(map);
        const canvas = L.canvas({ padding: .5 });
        const to = cityBounds.getCenter(), rad = Math.PI / 180;
        // farthest first, so the world lights up from the edges in towards the city
        const dist = f => { const c = L.geoJSON(f).getBounds().getCenter(); return map.distance(c, to); };
        const live = F.features.filter(f => byCC[f.cc]).sort((a, b) => dist(b) - dist(a));
        const fills = live.map(f => L.geoJSON(f, { renderer: canvas, interactive: false, style: { weight: 1, color: "#e4572e", opacity: 0, fillColor: "#e4572e", fillOpacity: 0 } }).addTo(fx));
        const gc = (a, b, n) => { // great-circle points between two lat/lngs, longitudes unwrapped
          const [f1, l1, f2, l2] = [a.lat * rad, a.lng * rad, b.lat * rad, b.lng * rad];
          const d = 2 * Math.asin(Math.sqrt(Math.sin((f2 - f1) / 2) ** 2 + Math.cos(f1) * Math.cos(f2) * Math.sin((l2 - l1) / 2) ** 2));
          const pts = [];
          for (let i = 0; i <= n; i++) { const t = i / n, A = Math.sin((1 - t) * d) / Math.sin(d), B = Math.sin(t * d) / Math.sin(d);
            const x = A * Math.cos(f1) * Math.cos(l1) + B * Math.cos(f2) * Math.cos(l2), y = A * Math.cos(f1) * Math.sin(l1) + B * Math.cos(f2) * Math.sin(l2), z = A * Math.sin(f1) + B * Math.sin(f2);
            pts.push([Math.atan2(z, Math.hypot(x, y)) / rad, Math.atan2(y, x) / rad]); }
          for (let i = 1; i < pts.length; i++) { while (pts[i][1] - pts[i - 1][1] > 180) pts[i][1] -= 360; while (pts[i][1] - pts[i - 1][1] < -180) pts[i][1] += 360; }
          const off = pts[pts.length - 1][1] - to.lng; pts.forEach(p => p[1] -= off);
          return pts; };
        const arcs = live.map(f => { const c = L.geoJSON(f).getBounds().getCenter(); const all = gc(c, to, 48);
          return L.polyline(all.slice(0, 2), { renderer: canvas, color: "#e4572e", weight: .9, opacity: .55, interactive: false, all }).addTo(fx); });
        if (!reduce) await new Promise(res => { const t0 = performance.now(), T = 3200, N = arcs.length, FADE = 320;
          const step = now => { if (skipped) return res();
            const k = Math.min(1, (now - t0) / T);
            let busy = k < 1;
            arcs.forEach((a, i) => {
              // one country at a time: each arc starts as the previous is half drawn, its country fades in as it lands
              const ki = Math.max(0, Math.min(1, (k * (N * .35 + 1) - i * .35)));
              const all = a.options.all, n = Math.max(2, Math.round(all.length * ki));
              if (n !== a._n) { a._n = n; a.setLatLngs(all.slice(0, n)); }
              if (ki >= 1) {
                fills[i]._t0 = fills[i]._t0 || now;
                const o = Math.min(1, (now - fills[i]._t0) / FADE) * .85;
                if (o !== fills[i]._o) { fills[i]._o = o; fills[i].setStyle({ fillOpacity: o, opacity: o }); }
                if (o < .85) busy = true;
              }
            });
            busy ? requestAnimationFrame(step) : res(); };
          requestAnimationFrame(step); });
        else fills.forEach(f => f.setStyle({ fillOpacity: .85, opacity: .85 }));
      } catch (e) { if (fx) map.removeLayer(fx); fx = null; }
      if (skipped) return done();
      if (reduce) { map.options.zoomSnap = 1; map.fitBounds(cityBounds, { padding: [30, 30] }); return done(); }
      map.on("zoom", fade);
      await fly(3800);
      done();
    }
  }
  paint();
})();
