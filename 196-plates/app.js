(async function () {
  // 196 Plates on MapLibre GL. The search page's globe and the dive are intro.js (a hook: runIntro); everything after
  // landing is here. Without WebGL the page runs app-leaflet.js instead (the loader in the template decides).
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ORDER = ["Europe", "Africa", "Middle East", "Central Asia", "South Asia", "Southeast Asia", "East Asia", "Oceania", "Americas"]; // left to right across the world view
  // cities.json lists every city; each keeps its data and dive imagery under its own folder (the first city's at the root)
  const [cl, d0] = await Promise.all([fetch("cities.json").then(r => r.json()).catch(() => null), fetch("data.json").then(r => r.json())]);
  const CITIES = cl && cl.length ? cl : [{ id: (d0.city || "Sydney").toLowerCase(), name: d0.city, country: "Australia", n: 0, base: "" }];
  const loadCity = async c => { if (!c.base) return d0; const r = await fetch(c.base + "data.json"); if (!r.ok) throw new Error(r.status); return r.json(); };
  const hashCity = CITIES.find(c => "#" + c.id === location.hash.toLowerCase());
  let C = hashCity || CITIES[0], D, CITY, byCC, BOUNDS, KEY, eaten = {};
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = u => /^https?:\/\//.test(u || "") ? u : null;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
                  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  // places you have eaten at are kept on this device per city (cc -> date); a tick on a country the city no longer lists
  // is set aside: opening it from the world map crashed
  const useData = d => {
    d.pins = d.pins.filter(p => /^[a-z]{2}$/.test(p.c2)); D = d; CITY = C.id;
    byCC = Object.fromEntries(D.pins.map(p => [p.cc, p]));
    document.getElementById("n").textContent = D.pins.length;
    const lons = D.pins.map(p => p.lon), lats = D.pins.map(p => p.lat);
    BOUNDS = [[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]];
    KEY = "196plates.eaten." + CITY;
    eaten = Object.fromEntries(Object.entries(store.get(KEY, {}) || {}).filter(([cc]) => byCC[cc]));
  };
  try { useData(await loadCity(C)); } catch (e) { C = CITIES.find(c => !c.base) || CITIES[0]; useData(await loadCity(C)); }
  // every circle flag is one image (flags-atlas.webp, built by build_atlas.py): one request, started before anything else
  const atlas = Promise.all([fetch("flags-atlas.json").then(r => r.json()), new Promise(res => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = "flags-atlas.webp"; })]);
  const mq = window.matchMedia("(max-width: 760px)"), phone = () => mq.matches, coarse = window.matchMedia("(pointer: coarse)");
  let W = mq.matches ? 22 : 32;
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

  // ---- the city's frame: fitted at a whole zoom so the raster tiles stay sharp ----
  const MC = maplibregl.MercatorCoordinate;
  // the zoom buttons cover the right edge: the pins fit in the width left of them (Yemen sat under them on a phone)
  const ctrlW = () => { const e = mapEl.querySelector(".maplibregl-ctrl-bottom-right .maplibregl-ctrl-group"); return e ? e.offsetWidth + 10 : 52; };
  const fitCamera = (w, h, pad = { top: 0, bottom: 0, left: 0, right: 0 }) => {
    const a = MC.fromLngLat(BOUNDS[0]), b = MC.fromLngLat(BOUNDS[1]), R = ctrlW();
    const z = Math.min(Math.log2((w - pad.left - pad.right - R - 64) / (512 * Math.abs(b.x - a.x))), Math.log2((h - pad.top - pad.bottom - 64) / (512 * Math.abs(b.y - a.y))));
    const c = new MC((a.x + b.x) / 2 + R / 2 / (512 * 2 ** z), (a.y + b.y) / 2).toLngLat();
    return { center: [c.lng, c.lat], zoom: z, padding: pad };
  };

  // ---- the intro decides how the map starts ----
  const intro = document.getElementById("intro");
  const deep = !intro || !!hashCity;
  if (intro) { const cr = intro.querySelector(".credit"); if (cr) cr.remove(); } // the map's own credit replaces the page's
  if (deep) { if (intro) intro.remove(); document.body.classList.remove("searching"); }
  else document.body.classList.add("searching");

  // ---- map ----
  const OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  let map = null;
  // v: { center, zoom, padding?, landed }. Landed is the city (OSM on, flat); otherwise the globe's start, which the intro takes over.
  const createMap = v => {
    map = new maplibregl.Map({ container: mapEl, center: v.center, zoom: v.zoom, minZoom: -2, maxZoom: 18, maxPitch: 0,
      dragRotate: false, pitchWithRotate: false, touchPitch: false, attributionControl: false, renderWorldCopies: !v.landed, antialias: !v.landed, fadeDuration: 300,
      style: { version: 8, sources: { osm: { type: "raster", tiles: [OSM], tileSize: 256, maxzoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>' } },
        layers: [{ id: "osm", type: "raster", source: "osm", layout: { visibility: v.landed ? "visible" : "none" }, paint: { "raster-fade-duration": 100 } }] } });
    map.touchZoomRotate.disableRotation(); map.keyboard.disableRotation();
    if (v.padding) map.setPadding(v.padding);
    if (/[?&]debug\b/.test(location.search)) window.__map = map;
  };
  createMap(deep ? { ...fitCamera(mapEl.clientWidth, mapEl.clientHeight), landed: true } : { center: [150, 8], zoom: 1, landed: false });
  // a lost WebGL context drops the map's style until it is restored: anything that touches the style asks first
  const ok = () => !!(map && map.style);
  const gs = k => ["global-state", k];

  // the map cannot be dragged or zoomed while the intro plays or the world view is up, and its controls hide
  const HANDLERS = ["scrollZoom", "boxZoom", "dragPan", "keyboard", "doubleClickZoom", "touchZoomRotate"];
  let locked = false;
  const lock = on => { locked = on; HANDLERS.forEach(h => on ? map[h].disable() : map[h].enable()); mapEl.classList.toggle("locked", on); };

  // the world never shows twice: at the widest it fills the map's width once, and the city map cannot pan past the edges
  let limited = false;
  const limitWorld = () => { limited = true; map.setRenderWorldCopies(false); map.setMinZoom(Math.log2(mapEl.clientWidth / 512)); map.setMaxBounds([[-179.99, -85.05], [179.99, 85.05]]); }; // a full 360 degrees throws in MapLibre 5.24

  // ---- controls: World top right; zoom in, out and fit stacked bottom right above a compact (i) credit (added to the map in wireMap) ----
  const ctl = el => ({ onAdd: () => el, onRemove: () => el.remove() });
  // MapLibre reopens a compact credit whenever a source adds an attribution; it stays shut unless the reader opens it
  let creditOpen = false, credit = null;
  const closeCredit = () => { if (creditOpen || !credit) return; credit.removeAttribute("open"); credit.classList.remove("maplibregl-compact-show"); };
  const zs = document.createElement("div"); zs.className = "maplibregl-ctrl zoomstack";
  zs.innerHTML = `<button type="button" aria-label="Zoom in">+</button><button type="button" aria-label="Zoom out">&minus;</button>`
    + `<button type="button" class="fit"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/><circle cx="12" cy="12" r="2.2"/></svg></button>`;
  const [zin, zout, zfit] = zs.querySelectorAll("button");
  const dur = ms => reduce ? 0 : ms;
  zin.onclick = () => map.zoomIn({ duration: dur(250) }); zout.onclick = () => map.zoomOut({ duration: dur(250) });
  const fitCity = () => { const c = fitCamera(mapEl.clientWidth, mapEl.clientHeight); map.easeTo({ center: c.center, zoom: c.zoom, duration: dur(500) }); };
  zfit.onclick = fitCity;
  const zoomState = () => { const z = map.getZoom(); zin.disabled = z >= map.getMaxZoom() - .01; zout.disabled = z <= map.getMinZoom() + .01; };
  const wb = document.createElement("div"); wb.className = "maplibregl-ctrl map-toggle"; wb.innerHTML = `<button type="button" id="worldbtn">World</button>`;
  const worldBtn = wb.firstElementChild;

  // ---- the list is resizable: drag or arrow keys on the edge, width kept on this device ----
  const grip = document.getElementById("grip");
  const setPanel = w => { w = Math.round(Math.min(Math.max(w, 240), Math.min(760, innerWidth - 320)));
    document.documentElement.style.setProperty("--panel", w + "px"); map.resize(); return w; };
  const saved = store.get("196plates.panel", null);
  if (saved) document.documentElement.style.setProperty("--panel", saved + "px"); // the CSS fits it to the window, then and on resize
  grip.addEventListener("pointerdown", e => {
    e.preventDefault(); grip.setPointerCapture(e.pointerId); grip.classList.add("drag");
    const move = ev => setPanel(ev.clientX);
    const up = ev => { grip.classList.remove("drag"); store.set("196plates.panel", setPanel(ev.clientX));
      grip.removeEventListener("pointermove", move); grip.removeEventListener("pointerup", up); grip.removeEventListener("pointercancel", up); };
    grip.addEventListener("pointermove", move); grip.addEventListener("pointerup", up); grip.addEventListener("pointercancel", up);
  });
  grip.addEventListener("keydown", e => {
    const d = e.key === "ArrowLeft" ? -24 : e.key === "ArrowRight" ? 24 : 0;
    if (d) { e.preventDefault(); store.set("196plates.panel", setPanel(document.querySelector(".panel").offsetWidth + d)); }
  });

  // ---- places you have eaten at ----
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
    if (pinsIn && ok()) D.pins.forEach(p => map.setFeatureState({ source: "pins", id: p.cc }, { eaten: isEaten(p.cc) }));
  };
  const toggleEaten = cc => { if (eaten[cc]) delete eaten[cc]; else eaten[cc] = new Date().toISOString().slice(0, 10); store.set(KEY, eaten); paint(); };

  // a row shows the name without its trailing bracket ("Restoran Dukat (Bonnyrigg Sports Club)"); the card keeps it whole
  const SHORT = { "Mother Chu's Taiwanese Gourmet": "Mother Chu's", "Mama Lor Restaurant & Bakery": "Mama Lor",
    "K&K Austrian Cafe & Coffee House": "K&K Austrian Cafe", "Botellon Spanish Tapas & Wine Bar": "Botellon" };
  const rowName = p => `<span class="rn"><span class="nm">${esc(SHORT[p.name] || p.name.replace(/\s*\([^)]*\)$/, ""))}</span>${p.price
    ? `<span class="rp" aria-label="${["", "Cheap", "Mid-range", "Expensive"][p.price]}">${"$".repeat(p.price)}</span>` : ""}</span>`;
  const dirUrl = p => "https://www.google.com/maps/dir/?api=1&destination=" +
    encodeURIComponent(p.address ? `${p.name}, ${p.address}` : `${p.name}, ${p.suburb || ""}, ${D.city}`);
  const cardParts = p => {
    const links = (p.src || []).filter(s => safeUrl(s.url));
    const rev = p.review && safeUrl(p.review.url) ? p.review : null;
    const web = safeUrl(p.web);
    const n = links.length;
    return {
      head: `<div class="card-kicker">${esc(p.adj)}${p.suburb ? " &middot; " + esc(p.suburb) : ""}${p.price ? " &middot; " + "$".repeat(p.price) : ""}</div>
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

  // ---- the pins: each flag drawn once into the map as a round icon with the dark rim, at the screen's pixel ratio ----
  let pinsIn = false, pinT = deep ? 9 : -1; // seconds since the camera landed: each flag pops in on its own beat
  // the pop-in: each flag's own beat k (0..1) comes from the shared clock pinT and the flag's fixed offset r
  const popK = ["max", 0, ["min", 1, ["/", ["-", gs("pinT"), ["*", ["get", "r"], .5]], .42]]];
  const popSize = ["let", "k", popK, ["+", 1, ["*", 2.9, ["^", ["-", ["var", "k"], 1], 3]], ["*", 1.9, ["^", ["-", ["var", "k"], 1], 2]]]];
  const popOp = ["min", 1, ["/", popK, .3]];
  const pinData = () => ({ type: "FeatureCollection", features: D.pins.map(p =>
    ({ type: "Feature", properties: { cc: p.cc, c2: p.c2, k: -p.lat, r: (p.lat * 977 % 1 + 1) % 1 }, geometry: { type: "Point", coordinates: [p.lon, p.lat] } })) });
  const drawFlags = (AT, sheet) => {
    const dpr = Math.min(devicePixelRatio || 1, 3), n = Math.round(W * dpr);
    if (sheet) D.pins.forEach(p => {
      const xy = AT.at[p.c2]; if (!xy) return;
      const c = document.createElement("canvas"); c.width = c.height = n;
      const x = c.getContext("2d", { willReadFrequently: true }), r = n / 2, rim = 2.5 * dpr;
      x.save(); x.beginPath(); x.arc(r, r, r - rim / 2, 0, Math.PI * 2); x.clip(); x.drawImage(sheet, xy[0], xy[1], AT.cell, AT.cell, 0, 0, n, n); x.restore();
      x.beginPath(); x.arc(r, r, r - rim / 2, 0, Math.PI * 2); x.lineWidth = rim; x.strokeStyle = "#16191d"; x.stroke();
      if (map.hasImage("f-" + p.c2)) map.removeImage("f-" + p.c2);
      map.addImage("f-" + p.c2, x.getImageData(0, 0, n, n), { pixelRatio: dpr });
    });
  };
  // crossing the phone breakpoint (a rotation, a resized window) redraws the flags at the new size
  mq.addEventListener("change", async () => {
    W = phone() ? 22 : 32;
    keyBox.querySelectorAll(".pin-key").forEach(b => { b.style.width = b.style.height = W + "px"; });
    if (!pinsIn || !ok()) return;
    const [AT, sheet] = await atlas; if (!pinsIn || !ok()) return;
    drawFlags(AT, sheet);
    map.setLayoutProperty("ticks", "icon-offset", [W / 2 - 1.5, 0.5 - W / 2]);
    map.triggerRepaint(); placeKey();
  });
  const addPins = async () => {
    const dpr = Math.min(devicePixelRatio || 1, 3);
    const m = map, [AT, sheet] = await atlas;
    if (m !== map || !ok()) return; // the map was rebuilt, or lost its context, while the flags loaded
    drawFlags(AT, sheet);
    // the eaten tick: a green disc with a white ring, top right of the flag
    const t = Math.round(18 * dpr), tc = document.createElement("canvas"); tc.width = tc.height = t;
    const x = tc.getContext("2d", { willReadFrequently: true }), tr = t / 2;
    x.beginPath(); x.arc(tr, tr, tr - .75 * dpr, 0, Math.PI * 2); x.fillStyle = "#2f6f4f"; x.fill(); x.lineWidth = 1.5 * dpr; x.strokeStyle = "#fff"; x.stroke();
    x.fillStyle = "#fff"; x.font = `700 ${9 * dpr}px -apple-system, "Segoe UI", Roboto, Arial, sans-serif`; x.textAlign = "center"; x.textBaseline = "middle"; x.fillText("✓", tr, tr + .5 * dpr);
    map.addImage("tick", x.getImageData(0, 0, t, t), { pixelRatio: dpr });
    map.setGlobalStateProperty("pinT", pinT);
    map.addSource("pins", { type: "geojson", data: pinData(), promoteId: "cc" });
    const dim = ["case", ["boolean", ["feature-state", "dim"], false], .25, 1];
    map.addLayer({ id: "pins", type: "symbol", source: "pins", layout: { "icon-image": ["concat", "f-", ["get", "c2"]], "icon-allow-overlap": true, "icon-ignore-placement": true,
      "icon-size": popSize, "symbol-sort-key": ["get", "k"] }, paint: { "icon-opacity": ["*", popOp, dim] } });
    map.addLayer({ id: "ticks", type: "symbol", source: "pins", layout: { "icon-image": "tick", "icon-allow-overlap": true, "icon-ignore-placement": true,
      "symbol-sort-key": ["get", "k"], "icon-offset": [W / 2 - 1.5, 0.5 - W / 2] },
      paint: { "icon-opacity": ["*", popOp, ["case", ["boolean", ["feature-state", "eaten"], false], dim, 0]] } });
    // the pin under the pointer grows 1.15x: the same flag drawn larger on a layer above, filtered to that one
    map.addLayer({ id: "pin-hover", type: "symbol", source: "pins", filter: ["==", ["get", "cc"], ""], layout: { "icon-image": ["concat", "f-", ["get", "c2"]],
      "icon-allow-overlap": true, "icon-ignore-placement": true, "icon-size": 1.15 }, paint: { "icon-opacity": 1 } }, "ticks");
    pinsIn = true; paint();
  };
  // the intro moves the pins out from the CBD and fades them in
  const pinsAt = t => { if (t === pinT) return; pinT = t; if (pinsIn && ok()) { map.setGlobalStateProperty("pinT", t); map.triggerRepaint(); } };

  // which pins sit under a point, topmost (southernmost) first; dimmed ones are not there
  const dimmed = cc => !inFilter(cc);
  const pinsNear = (pt, r) => D.pins.filter(q => !dimmed(q.cc)).map(q => ({ q, d: map.project([q.lon, q.lat]).dist(pt) })).filter(x => x.d <= r);
  const onMouseMove = e => {
    const h = !locked && !introBusy && pinsNear(e.point, W / 2).sort((a, b) => a.q.lat - b.q.lat)[0];
    map.getCanvas().style.cursor = h ? "pointer" : ""; map.getCanvas().title = h ? `${h.q.adj}: ${h.q.name}` : "";
    hover(h ? h.q.cc : "");
  };
  let hovered = "";
  const hover = cc => { if (cc === hovered || !pinsIn || !ok()) return; hovered = cc; map.setFilter("pin-hover", ["==", ["get", "cc"], cc]); };
  const onMapClick = e => {
    if (locked || introBusy) return;
    const hits = pinsNear(e.point, W / 2 + (coarse.matches ? 9 : 0));
    if (!hits.length) { closeSheet(); return; }
    const p = hits.sort((a, b) => a.q.lat - b.q.lat)[0].q;
    if (phone()) tapPin(p, e.point); else openCard(p, keys[p.cc]);
  };

  // ---- keyboard: one hidden button per pin, in the map; focus shows a ring on the pin, Enter opens its card ----
  const keyBox = document.createElement("div"); keyBox.className = "pin-keys";
  mapEl.appendChild(keyBox);
  const keys = {};
  let keyOn = null;
  const placeKey = () => { if (!keyOn) return; const p = byCC[keyOn.dataset.cc], pt = map.project([p.lon, p.lat]); keyOn.style.left = pt.x + "px"; keyOn.style.top = pt.y + "px"; };
  const buildKeys = () => { keyBox.querySelectorAll(".pin-key").forEach(b => b.remove()); for (const k in keys) delete keys[k]; keyOn = null;
  D.pins.forEach(p => {
    const b = document.createElement("button"); b.type = "button"; b.className = "pin-key"; b.dataset.cc = p.cc;
    b.setAttribute("aria-label", `${p.adj}: ${p.name}`); b.style.width = b.style.height = W + "px";
    b.addEventListener("focus", () => { keyOn = b; const m = mapEl.getBoundingClientRect(), pt = map.project([p.lon, p.lat]);
      if (pt.x < W || pt.y < W || pt.x > m.width - W || pt.y > m.height - W) map.panTo([p.lon, p.lat], { duration: dur(300) }); placeKey(); });
    b.addEventListener("blur", () => { if (keyOn === b) keyOn = null; });
    b.addEventListener("click", () => { if (phone()) openSheet([p], { opener: b, at: [p.lon, p.lat], zoom: map.getZoom() }); else openCard(p, b); });
    keyBox.appendChild(b); keys[p.cc] = b;
  }); };
  buildKeys();

  // ---- the desktop card: a popup above the pin that pans itself clear of the map's controls and holds focus ----
  let cardPopup = null, cardPin = null, opener = null, nextOpener = null;
  const panIntoView = pp => {
    const el = pp.getElement(); if (!el || cardPopup !== pp) return;
    const r = el.getBoundingClientRect(), m = mapEl.getBoundingClientRect(), w = wb.getBoundingClientRect(), z = zs.getBoundingClientRect();
    const T = m.top + (w.height ? w.bottom - m.top + 8 : 24), Lf = m.left + 24, B = m.bottom - 24;
    const Rt = m.right - (z.width && r.width + (m.right - z.left) + 32 <= m.width ? m.right - z.left + 8 : 24);
    let dx = 0, dy = 0;
    if (r.right > Rt) dx = r.right - Rt; if (r.left - dx < Lf) dx = r.left - Lf;
    if (r.bottom > B) dy = r.bottom - B; if (r.top - dy < T) dy = r.top - T;
    if (dx || dy) map.panBy([dx, dy], { duration: dur(250) });
  };
  function openCard(p, from) {
    if (cardPopup) { const old = cardPopup; cardPopup = null; old.remove(); }
    const pp = new maplibregl.Popup({ className: "card", closeButton: true, closeOnClick: true, closeOnMove: false, anchor: "bottom",
      offset: [0, -(W / 2 - 4)], maxWidth: "270px", focusAfterOpen: false }).setLngLat([p.lon, p.lat]).setHTML(card(p));
    cardPopup = pp; cardPin = p; opener = from || nextOpener || keys[p.cc]; nextOpener = null; let el = null;
    pp.on("close", () => {
      if (cardPopup !== pp) return;
      const a = document.activeElement, o = opener; cardPopup = null; cardPin = null; opener = null;
      if (o && document.contains(o) && (!a || a === document.body || !document.contains(a) || (el && el.contains(a)))) o.focus({ preventScroll: true });
    });
    pp.addTo(map);
    el = pp.getElement(); const c = el.querySelector(".maplibregl-popup-content");
    c.tabIndex = -1; c.setAttribute("role", "dialog"); c.setAttribute("aria-label", p.name);
    const b = el.querySelector("[data-eat]"); if (b) b.addEventListener("change", () => toggleEaten(b.dataset.eat));
    const img = el.querySelector(".card-flag img"); if (img && !img.complete) img.addEventListener("load", () => panIntoView(pp), { once: true });
    const src = el.querySelector(".card-src"); if (src) src.addEventListener("toggle", () => panIntoView(pp));
    c.focus({ preventScroll: true });
    panIntoView(pp);
  }
  const closeCard = () => { if (cardPopup) cardPopup.remove(); };
  const preloadFlags = () => D.pins.forEach(p => { const im = new Image(); im.src = `flags/${p.c2}-320.png`; });
  const openPin = (cc, mapTop) => {
    const p = byCC[cc], z = Math.max(map.getZoom(), 14);
    if (phone()) { openSheet([p], { opener: nextOpener || keys[cc], at: [p.lon, p.lat], zoom: z, mapTop }); nextOpener = null; return; }
    closeCard();
    map.once("moveend", () => openCard(p)); map.flyTo({ center: [p.lon, p.lat], zoom: z, duration: dur(800) });
  };
  const openRow = (cc, b) => { nextOpener = b; hideWorld(); openPin(cc, toMap()); };

  // ---- the phone card: a bottom sheet; a tap where several pins overlap lists them first, a big pile zooms in ----
  const sheet = document.getElementById("sheet");
  let sheetOn = false, sheetOpener = null, sheetAt = null;
  const tapPin = (p, pt) => {
    let near = [p];
    if (pt) near = pinsNear(pt, 21).sort((a, b) => a.d - b.d).map(x => x.q);
    if (!near.includes(p)) near.unshift(p);
    const lo = [Math.min(...near.map(q => q.lon)), Math.min(...near.map(q => q.lat))], hi = [Math.max(...near.map(q => q.lon)), Math.max(...near.map(q => q.lat))];
    const at = near.length > 1 ? [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2] : [p.lon, p.lat];
    // more than 6 under the finger: zoom into the pile, leaving room at the bottom for the card that comes next
    if (near.length > 6) {
      const r = mapEl.getBoundingClientRect(), under = Math.min(r.height / 2, Math.max(0, r.bottom - innerHeight * .55));
      const padding = { top: 40, left: 40, right: 40, bottom: 40 + under }, cam = map.cameraForBounds([lo, hi], { padding });
      if (cam && cam.zoom > map.getZoom() + .01) { closeSheet(); map.fitBounds([lo, hi], { padding, duration: dur(800), maxZoom: map.getMaxZoom() }); return; }
    }
    openSheet(near, { opener: keys[p.cc], at, zoom: map.getZoom() });
  };
  // centre the map so a point sits midway between the top of the visible map and the top of the sheet
  const placeAbove = (at, z, mapTop) => {
    const H = mapEl.clientHeight, t = mapTop == null ? mapEl.getBoundingClientRect().top : mapTop;
    const visTop = Math.max(0, t), visBot = Math.max(visTop + 80, Math.min(t + H, innerHeight - (sheetOn ? sheet.offsetHeight : 0)));
    const o = { center: at, zoom: z, offset: [0, (visTop + visBot) / 2 - t - H / 2] };
    if (reduce) map.easeTo({ ...o, duration: 0 });
    else if (Math.abs(z - map.getZoom()) > .01) map.flyTo({ ...o, duration: 800 });
    else map.easeTo({ ...o, duration: 300 });
  };
  function openSheet(list, o) {
    closeCard();
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
      const q = byCC[r.dataset.cc]; openSheet([q], { at: [q.lon, q.lat], zoom: map.getZoom() }); }));
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
  mq.addEventListener("change", () => { closeSheet(); closeCard(); });

  // ---- side panel: rows, alphabetical within each region ----
  const groups = document.getElementById("groups");
  const buildGroups = () => { groups.innerHTML = ""; ORDER.forEach(g => {
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
  }); };
  buildGroups();

  // ---- filter the list: all / eaten / to try, and a search on country, cuisine or restaurant ----
  let filterMode = "all";
  const fold = s => String(s || "").normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  const prices = new Set();  // empty = any price
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
    D.pins.forEach(p => { const off = !inFilter(p.cc);
      if (pinsIn && ok()) map.setFeatureState({ source: "pins", id: p.cc }, { dim: off });
      if (keys[p.cc]) keys[p.cc].tabIndex = off ? -1 : 0; });
  }
  document.querySelectorAll("#filter button").forEach(b => b.addEventListener("click", () => { filterMode = b.dataset.f; applyFilter(); }));
  document.querySelectorAll("#price button").forEach(b => b.addEventListener("click", () => {
    const v = +b.dataset.p; if (!prices.delete(v)) prices.add(v); applyFilter(); }));
  const find = document.getElementById("find");
  find.addEventListener("input", applyFilter);
  find.addEventListener("keydown", e => { if (e.key !== "Enter") return;
    const li = [...document.querySelectorAll("#groups .rows li")].find(l => !l.hidden); if (li) li.firstElementChild.click(); });
  const cityText = () => {
    document.querySelector(".lede").textContent = `How many of the ${D.pins.length} cuisines in ${D.city} can you eat?`;
    document.querySelectorAll(".how .city").forEach(s => { s.textContent = D.city; });
    // a city's venue count: the template carries the first city's; null means none is stated
    if (D.venues) document.querySelectorAll(".how .nv").forEach(s => { s.textContent = (Math.round(D.venues / 100) * 100).toLocaleString("en-AU"); });
    document.querySelectorAll(".how .nvw").forEach(s => { s.hidden = D.venues === null; });
    zfit.setAttribute("aria-label", `Fit ${D.city}`); zfit.title = `Fit ${D.city}`; mapEl.setAttribute("aria-label", `Map of ${D.city}`);
  };
  cityText();
  // another city picked on the search page: the list, keys and pins are rebuilt for it under the spinning globe
  const setCity = async c => {
    const d = await loadCity(c); C = c; useData(d); buildKeys(); buildGroups(); cityText(); if (landed) preloadFlags();
    if (pinsIn && ok()) { const m = map, [AT, sheet] = await atlas; if (m === map && ok()) { drawFlags(AT, sheet); map.getSource("pins").setData(pinData()); } }
    paint();
  };
  addEventListener("hashchange", () => { const c = CITIES.find(x => "#" + x.id === location.hash.toLowerCase()); if (c && c !== C) location.reload(); });
  // panned or zoomed into another city: the page follows it (cities.json "b" is each city's pin bounds)
  let following = false;
  function followCity() {
    if (!landed || introBusy || wm || following || map.getZoom() < 7) return;
    const { lng, lat } = map.getCenter(), P = 0.3;
    const c = CITIES.find(x => x.b && lng > x.b[0] - P && lat > x.b[1] - P && lng < x.b[2] + P && lat < x.b[3] + P);
    if (!c || c === C) return;
    following = true; closeCard(); closeSheet();
    setCity(c).then(() => { history.replaceState(null, "", "#" + CITY); following = false; }, () => { following = false; });
  }

  // ---- world views: which of 196 the city has, and your own map (worldmap.js, design 348/352) ----
  let wm = null, worldOpener = null;
  function showWorld(mode) {
    hideWorld(); worldOpener = document.activeElement;
    // inside the map's controls, after World and before the credit, so that is the tab order
    const box = document.createElement("div"); box.id = "worldmap"; box.style.cssText = "position:absolute;inset:0;z-index:1";
    mapEl.querySelector(".maplibregl-control-container").insertBefore(box, mapEl.querySelector(".maplibregl-ctrl-bottom-left"));
    closeCard(); closeSheet(); lock(true);
    wm = WorldMap.render(box, { eaten, pins: D.pins, city: D.city, onPick: cc => { hideWorld(); openPin(cc); } });
    worldBtn.textContent = `Back to ${D.city}`;
    worldBtn.onclick = hideWorld;
  }
  function hideWorld() {
    if (!wm) return;
    wm.destroy(); wm = null; document.getElementById("worldmap").remove(); lock(false);
    worldBtn.textContent = "World";
    worldBtn.onclick = () => showWorld("city");
  }
  worldBtn.onclick = () => showWorld("city");
  addEventListener("keydown", e => {
    if (e.key !== "Escape" || introBusy) return;
    if (sheetOn) { closeSheet(); return; }
    if (cardPopup) { closeCard(); return; }
    if (wm) { const o = worldOpener && document.contains(worldOpener) && worldOpener !== document.body ? worldOpener : worldBtn;
      hideWorld(); o.focus({ preventScroll: true }); }
  });

  // where the map will sit once the list is back: the intro lands the city in that part of the full-bleed map
  const landCam = () => {
    const w = mapEl.clientWidth, h = mapEl.clientHeight;
    // the landed map is 62vh tall; on a phone vh is the viewport without the address bar, not innerHeight, and the
    // difference showed as a jump at the hand-off
    const vh62 = (() => { const d = document.createElement("div"); d.style.cssText = "position:absolute;visibility:hidden;height:62vh";
      document.body.appendChild(d); const v = d.getBoundingClientRect().height; d.remove(); return v; })();
    const pad = phone() ? { top: 0, left: 0, right: 0, bottom: Math.max(0, h - Math.round(vh62)) }
      : { top: 0, bottom: 0, right: 0, left: Math.round(document.querySelector(".panel").getBoundingClientRect().right) };
    return fitCamera(w, h, pad);
  };
  const startIntro = () => { const m0 = map; return typeof window.runIntro !== "function" ? null : window.runIntro(map, { base: C.base, bounds: BOUNDS,
    land: landCam, reduce, osm: "osm", pinsAt: t => { if (m0 === map) pinsAt(t); }, pinsReady: () => pinsIn,
    layoutAt: k => { if (m0 !== map) return; document.body.classList.add("diving"); document.documentElement.style.setProperty("--k", k); } }); };
  let landed = deep, started = false, I = null, skipOff = null;
  // the camera is down: the list comes back beside (or under) the map, which keeps exactly what it shows
  const landTail = fresh => {
    if (skipOff) { skipOff(); skipOff = null; }
    const a = document.activeElement, lost = !a || a === document.body || intro.contains(a) || mapEl.contains(a);
    document.body.classList.remove("searching", "diving"); document.documentElement.style.removeProperty("--k");
    map.resize(); map.setPadding({ top: 0, bottom: 0, left: 0, right: 0 }); map.redraw();
    intro.remove(); introBusy = false; lock(false); landed = true; I = null;
    if (fresh) map.once("load", () => { limitWorld(); zoomState(); }); else { limitWorld(); zoomState(); }
    paint(); preloadFlags();
    if (pendingRow) { const [cc, b] = pendingRow; pendingRow = null; openRow(cc, b); }
    else if (lost && !phone()) find.focus({ preventScroll: true }); // a phone would raise its keyboard
  };

  // ---- a map's wiring: controls, pointer, pins and a watch on its WebGL context. It runs again on every rebuilt map. ----
  // Chrome ends the oldest WebGL context when too many are live (many tabs, GPU memory pressure). MapLibre recovers a restored
  // one itself; if none comes back the map is rebuilt from the state kept here; a second loss within a minute drops to Leaflet.
  const lastView = { center: null, zoom: null };
  let lossTimer = 0, losses = [];
  const retired = new WeakSet();
  const toLeaflet = () => { try { sessionStorage.setItem("196plates.nogl", "1"); } catch (e) {} location.reload(); };
  const wireMap = () => {
    const m = map;
    m.on("resize", () => { if (limited) m.setMinZoom(Math.log2(mapEl.clientWidth / 512)); });
    const ac = new maplibregl.AttributionControl({ compact: true });
    m.addControl(ac, "bottom-right");
    credit = ac._container; creditOpen = false; const cr = credit;
    cr.addEventListener("click", () => { creditOpen = !cr.classList.contains("maplibregl-compact-show"); }, true);
    ["styledata", "sourcedata", "resize", "idle"].forEach(t => m.on(t, closeCredit)); closeCredit(); // MapLibre reopens it as sources change
    m.on("zoom", zoomState); m.on("moveend", followCity);
    m.addControl(ctl(zs), "bottom-right"); m.addControl(ctl(wb), "top-right");
    lastView.center = m.getCenter().toArray(); lastView.zoom = m.getZoom();
    m.on("move", () => { placeKey(); lastView.center = m.getCenter().toArray(); lastView.zoom = m.getZoom(); });
    m.on("mousemove", onMouseMove); m.on("click", onMapClick);
    m.getCanvas().addEventListener("mouseleave", () => hover(""));
    hovered = ""; pinsIn = false;
    if (m.style && m.getStyle()) addPins(); else m.once("style.load", addPins);
    const cv = m.getCanvas();
    cv.addEventListener("webglcontextlost", e => {
      e.preventDefault(); // allows a restore
      if (retired.has(cv)) return; // a map this page took down itself
      const now = performance.now(); losses = losses.filter(t => now - t < 60000); losses.push(now);
      clearTimeout(lossTimer);
      if (losses.length > 1) { toLeaflet(); return; }
      lossTimer = setTimeout(() => { if (m === map) recover(); }, 1500);
    });
    // MapLibre's own restore brings the style back without its global state, so a restored map is rebuilt as well
    cv.addEventListener("webglcontextrestored", () => { clearTimeout(lossTimer); setTimeout(() => { if (m === map) recover(); }, 0); });
  };
  const recover = () => {
    clearTimeout(lossTimer);
    const phase = landed ? "landed" : started ? "dive" : "search", pin = cardPin, hadWorld = !!wm, view = { center: lastView.center, zoom: lastView.zoom };
    if (hadWorld) hideWorld();
    try { closeCard(); } catch (e) {}
    if (I) I.abort();
    try { retired.add(map.getCanvas()); map.remove(); } catch (e) {}
    keyOn = null;
    if (phase === "dive") pinT = 9; // the flags land where they belong
    try {
      if (phase === "landed") createMap({ center: view.center, zoom: view.zoom, landed: true });
      else if (phase === "dive") { const c = landCam(); createMap({ center: c.center, zoom: c.zoom, padding: c.padding, landed: true }); }
      else createMap({ center: [150, 8], zoom: 1, landed: false });
      wireMap();
    } catch (e) { toLeaflet(); return; }
    mapEl.appendChild(keyBox);
    lock(locked);
    if (phase === "search") I = startIntro();
    else if (phase === "dive") { I = null; landTail(true); }
    else { if (limited) map.once("load", () => { limitWorld(); zoomState(); }); if (pin) openCard(pin); }
    if (hadWorld) showWorld("city");
  };

  // ---- straight to the city, or the search page and the intro ----
  wireMap();
  if (deep) { map.once("load", () => { limitWorld(); zoomState(); preloadFlags(); }); paint(); return; }
  lock(true);
  let tries = 0;
  while (typeof window.runIntro !== "function" && tries++ < 100) {
    if (tries === 1 && !document.querySelector('script[src="intro.js"]')) { const s = document.createElement("script"); s.src = "intro.js"; document.head.appendChild(s); }
    await new Promise(r => setTimeout(r, 30));
  }
  if (!I) I = startIntro();
  const input = intro.querySelector("input"), list = intro.querySelector("ul");
  const cities = CITIES;
  const box = intro.querySelector(".search");
  let open = false;
  let waiting = false;
  const render = () => {
    if (waiting) return;
    const q = input.value.trim().toLowerCase();
    const hits = cities.filter(c => c.name.toLowerCase().startsWith(q));
    list.hidden = !open;
    list.innerHTML = hits.map(c => `<li><button type="button" data-id="${esc(c.id)}"><span><b>${esc(c.name)}</b>, ${esc(c.country)}</span><span class="n">${c.n} cuisines</span></button></li>`).join("")
      + (hits.length ? "" : `<li class="soon">No city matches</li>`) + `<li class="soon">More cities coming</li>`;
    list.querySelectorAll("button").forEach(b => b.addEventListener("click", go));
  };
  const show = on => { open = on; render(); };
  ["focus", "input", "click"].forEach(t => input.addEventListener(t, () => show(true)));
  box.addEventListener("focusout", e => { if (e.relatedTarget && !box.contains(e.relatedTarget)) show(false); });
  document.addEventListener("pointerdown", e => { if (open && !box.contains(e.target)) show(false); });
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") { const b = list.querySelector("button"); if (b) b.click(); }
    else if (e.key === "Escape") { e.preventDefault(); show(false); } });
  if (phone()) show(true); // the list without the keyboard
  else if (document.activeElement === document.body || !document.activeElement) input.focus(); else show(document.activeElement === input);
  async function go(e) {
    if (started) return; started = true; introBusy = true;
    const btn = e && e.currentTarget, pick = CITIES.find(c => btn && c.id === btn.dataset.id) || C;
    if (pick !== C) {
      try { await setCity(pick); } catch (err) {
        started = false; introBusy = false; const n = btn && btn.querySelector(".n"); if (n) n.textContent = "Couldn't load, try again"; return; }
      if (I && I.retarget) I.retarget({ base: C.base, bounds: BOUNDS }); }
    // the dive plays straight through, so it waits here until the rest of its imagery will arrive in time (12 s at most)
    const goNow = () => !I || (I.safe ? I.safe() : !I.progress || I.progress() >= 1);
    if (!goNow()) {
      waiting = true; input.disabled = true;
      const b = btn, n = b && b.querySelector(".n");
      let arc = null;
      if (n) { n.insertAdjacentHTML("beforeend", `<svg class="ring" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8"/><circle class="arc" cx="10" cy="10" r="8" pathLength="1"/></svg>`);
        arc = n.querySelector(".arc"); b.setAttribute("aria-busy", "true"); }
      const t1 = performance.now() + 12000;
      await new Promise(res => { const tick = () => { const p = I && I.progress ? I.progress() : 1;
        if (arc) arc.style.strokeDashoffset = 1 - p;
        if (p >= 1 || goNow() || performance.now() > t1) res(); else requestAnimationFrame(tick); }; tick(); });
      if (arc) { arc.style.strokeDashoffset = 0; await new Promise(r => setTimeout(r, 150)); }
    }
    history.replaceState(null, "", "#" + CITY);
    intro.classList.add("gone");
    // a click, tap or key from here on jumps to the end (not a wheel or pinch); armed after the event that started it
    const SKIP = ["click", "keydown"], onSkip = e => {
      if (e.type === "keydown" && ["Shift", "Control", "Alt", "Meta", "Tab"].includes(e.key)) return;
      if (I) I.skip(); if (e.type === "click" && mapEl.contains(e.target)) { e.stopPropagation(); e.preventDefault(); } };
    setTimeout(() => { if (introBusy) SKIP.forEach(t => addEventListener(t, onSkip, { capture: true })); }, 0);
    skipOff = () => SKIP.forEach(t => removeEventListener(t, onSkip, { capture: true }));
    const cur = I; await cur.go();
    if (I !== cur) return; // the map was rebuilt mid-dive and landed from there
    landTail(false);
  }
  paint();
})();
