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
  const D = await (await fetch("data.json")).json();
  const CITY = (D.city || "Sydney").toLowerCase();
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = u => /^https?:\/\//.test(u || "") ? u : null;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
                  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  D.pins = D.pins.filter(p => /^[a-z]{2}$/.test(p.c2));
  const byCC = Object.fromEntries(D.pins.map(p => [p.cc, p]));
  document.getElementById("n").textContent = D.pins.length;
  const small = window.matchMedia("(max-width: 760px)").matches;
  const W = small ? 22 : 32;

  // ---- theme ----
  const themeBtn = document.getElementById("theme");
  const setTheme = t => { document.documentElement.dataset.theme = t; themeBtn.setAttribute("aria-pressed", t === "dark");
    themeBtn.querySelector(".lbl").textContent = t === "dark" ? "Light" : "Dark"; store.set("196plates.theme", t); };
  setTheme(document.documentElement.dataset.theme || "dark");
  themeBtn.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));

  // ---- map ----
  const map = L.map("map", { zoomControl: true, attributionControl: true, zoomSnap: 1, worldCopyJump: false });
  map.attributionControl.setPrefix(false);
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
  if (saved && !small) setPanel(saved);
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
  let eaten = store.get(KEY, {});
  const isEaten = cc => !!eaten[cc];
  const eatenCount = document.getElementById("been");
  const paint = () => {
    const n = Object.keys(eaten).length;
    eatenCount.hidden = n === 0;
    if (n === 0 && filterMode !== "all") { filterMode = "all"; }  // the filter hides at zero, so it must not leave the list filtered
    eatenCount.innerHTML = `${n} of ${D.pins.length} eaten &middot; <button type="button" class="linkish" id="mine">Your map</button>`;
    document.getElementById("filter").hidden = n === 0;
    applyFilter();
    const mine = document.getElementById("mine"); if (mine) mine.onclick = () => showWorld("mine");
    document.querySelectorAll("[data-cc]").forEach(el => el.classList.toggle("is-been", isEaten(el.dataset.cc)));
  };
  const toggleEaten = cc => { if (eaten[cc]) delete eaten[cc]; else eaten[cc] = new Date().toISOString().slice(0, 10); store.set(KEY, eaten); paint(); };
  const fmtDate = iso => iso ? iso.split("-").reverse().join("/") : "";

  const dirUrl = p => "https://www.google.com/maps/dir/?api=1&destination=" +
    encodeURIComponent(p.address ? `${p.name}, ${p.address}` : `${p.name}, ${p.suburb || ""} NSW`);
  const card = p => {
    const links = (p.src || []).filter(s => safeUrl(s.url));
    const rev = p.review && safeUrl(p.review.url) ? p.review : null;
    const web = safeUrl(p.web);
    const n = links.length;
    return `<div class="card-flag"><img src="flags/${p.c2}-320.png" alt="Flag of ${esc(p.country)}"></div>
    <div class="card-body">
      <div class="card-kicker">${esc(p.adj)}${p.suburb ? " &middot; " + esc(p.suburb) : ""}</div>
      <div class="card-name">${esc(p.name)}</div>
      ${n ? `<details class="card-src"><summary>${n} ${n === 1 ? "source" : "sources"}</summary><ul>${links.map(s =>
        `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a></li>`).join("")}</ul></details>` : ""}
      <div class="card-actions">
        ${rev ? `<a class="card-btn wide" href="${esc(rev.url)}" target="_blank" rel="noopener">Read the review <span class="via">&middot; ${esc(rev.name)}</span></a>` : ""}
        ${web ? `<a class="card-btn alt" href="${esc(web)}" target="_blank" rel="noopener">Website</a>` : ""}
        <a class="card-btn alt" href="${dirUrl(p)}" target="_blank" rel="noopener">Directions</a>
        <label class="card-check"><input type="checkbox" data-eat="${esc(p.cc)}" ${isEaten(p.cc) ? "checked" : ""}> Eaten here</label>
      </div>
    </div>`;
  };

  const pinLayer = L.featureGroup();
  const markers = {};
  D.pins.forEach(p => {
    const m = L.marker([p.lat, p.lon], {
      title: `${p.adj}: ${p.name}`, riseOnHover: true,
      icon: L.divIcon({ className: "", iconSize: [W, W], iconAnchor: [W / 2, W / 2],
        html: `<div class="pin" data-cc="${esc(p.cc)}" style="width:${W}px;height:${W}px;background-image:url(flags/circle/${p.c2}.svg)"></div>` })
    });
    m.bindPopup(() => card(p), { className: "card", closeButton: true, offset: [0, -W / 2 + 4], autoPanPadding: [24, 24], maxWidth: 270, minWidth: 250 });
    pinLayer.addLayer(m);
    markers[p.cc] = m;
  });
  map.addLayer(pinLayer);
  map.on("popupopen", e => {
    const b = e.popup.getElement().querySelector("[data-eat]");
    if (b) b.addEventListener("change", () => toggleEaten(b.dataset.eat));
  });
  const cityBounds = L.latLngBounds(D.pins.map(p => [p.lat, p.lon]));
  const openPin = cc => { map.once("moveend", () => markers[cc].openPopup()); map.flyTo(markers[cc].getLatLng(), Math.max(map.getZoom(), 15), { duration: .8 }); };

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
      li.innerHTML = `<button type="button" class="row" data-cc="${esc(p.cc)}"><img class="fit-${p.fit}" src="flags/${p.c2}-80.png" alt="" loading="lazy"><span class="rc">${esc(p.country)}</span><span class="rn">${esc(p.name)}</span></button>`;
      li.querySelector("button").addEventListener("click", () => { hideWorld(); openPin(p.cc); if (small) document.getElementById("map").scrollIntoView({ behavior: "smooth" }); });
      sec.querySelector(".rows").appendChild(li);
    });
    groups.appendChild(sec);
  });

  // ---- filter the list: all / eaten / to try, and a search on country, cuisine or restaurant ----
  let filterMode = "all";
  const fold = s => String(s || "").normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  function applyFilter() {
    const q = fold(document.getElementById("find").value.trim());
    document.querySelectorAll("#groups .rows li").forEach(li => {
      const cc = li.firstElementChild.dataset.cc, p = byCC[cc];
      const hit = !q || [p.country, p.adj, p.name].some(s => fold(s).includes(q));
      li.hidden = !hit || (filterMode === "eaten" ? !isEaten(cc) : filterMode === "not" ? isEaten(cc) : false);
    });
    document.querySelectorAll("#groups .group").forEach(sec => { sec.hidden = ![...sec.querySelectorAll("li")].some(li => !li.hidden); });
    document.querySelectorAll("#filter button").forEach(b => b.setAttribute("aria-pressed", b.dataset.f === filterMode));
  }
  document.querySelectorAll("#filter button").forEach(b => b.addEventListener("click", () => { filterMode = b.dataset.f; applyFilter(); }));
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
  let wm = null;
  function showWorld(mode) {
    hideWorld();
    const box = document.createElement("div"); box.id = "worldmap"; box.style.cssText = "position:absolute;inset:0;z-index:800";
    document.querySelector(".mapwrap").appendChild(box);
    map.closePopup(); lock(true);
    wm = WorldMap.render(box, { mode, eaten, pins: D.pins, city: D.city, onPick: cc => { hideWorld(); openPin(cc); } });
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

  // ---- the search intro: a plain page; pick a city, great-circle arcs draw in, the camera flies to it ----
  const intro = document.getElementById("intro");
  const skip = location.hash === "#" + CITY || !intro;
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
    // the world view and every pin's flag load behind the search, so the intro starts on a finished map
    map.setView([10, 150], worldZoom(), { animate: false });
    map.removeLayer(pinLayer);
    // the orange fills use 50m outlines, close enough to the tile coastlines at the zooms they are seen at
    let introGeo = null;
    const loadIntro = () => introGeo || (introGeo = fetch("intro-50m.json").then(r => r.json()).then(G => {
      G.features.forEach(f => { f.cc = f.properties.cc; f.geometry.coordinates = f.geometry.coordinates.map(pl => pl.map(fix)); }); return G; }));
    let globe = null, started = false;
    startGlobe().then(g => {
      // what only the flight needs waits until the globe is up, so it does not queue behind the globe's textures
      loadIntro(); D.pins.forEach(p => { new Image().src = `flags/circle/${p.c2}.svg`; });
      if (!g) { document.body.classList.add("flat"); map.invalidateSize(); map.setView([10, 150], worldZoom(), { animate: false }); lock(true); return; }
      if (started) g.destroy(); else globe = g;
    });
    const input = intro.querySelector("input"), list = intro.querySelector("ul");
    const cities = [{ name: D.city, country: "Australia", n: D.pins.length }];
    const render = () => {
      const q = input.value.trim().toLowerCase();
      const hits = cities.filter(c => !q || c.name.toLowerCase().startsWith(q));
      list.hidden = !q;
      list.innerHTML = hits.map(c => `<li><button type="button"><span><b>${esc(c.name)}</b>, ${esc(c.country)}</span><span class="n">${c.n} cuisines</span></button></li>`).join("")
        + `<li class="soon">More cities coming</li>`;
      list.querySelectorAll("button").forEach(b => b.addEventListener("click", go));
    };
    input.addEventListener("input", render);
    input.addEventListener("keydown", e => { if (e.key === "Enter") { const b = list.querySelector("button"); if (b) b.click(); } });
    input.focus();
    async function go() {
      if (started) return; started = true;
      history.replaceState(null, "", "#" + CITY);
      document.body.classList.remove("searching", "flat");
      map.invalidateSize();
      map.setView([10, 150], worldZoom(), { animate: false });
      document.getElementById("map").classList.add("pins-hidden");
      lock(true);
      intro.classList.add("gone");
      // the globe turns to the city as it fades, then the map's own intro runs from the world view beneath it
      if (globe) { const g = globe, c = cityBounds.getCenter(); globe = null; await g.turnTo(c.lng, c.lat, 1000); setTimeout(() => g.destroy(), reduce ? 1000 : 0); }
      // the flight is Leaflet's own van Wijk path, eased in and out; every tile it will pass over is fetched while the
      // arcs draw, and tiles are refreshed every frame, so no zoom level arrives blank
      const size = map.getSize(), z0 = map.getZoom(), from = map.project(map.getCenter(), z0);
      const tgt = map._getBoundsCenterZoom(cityBounds, { padding: [30, 30] });
      const toPx = map.project(tgt.center, z0), w0 = Math.max(size.x, size.y), w1 = w0 * map.getZoomScale(z0, tgt.zoom);
      const u1 = toPx.distanceTo(from) || 1, rho = 1.42, rho2 = rho * rho;
      const rr = i => { const b = (w1 * w1 - w0 * w0 + (i ? -1 : 1) * rho2 * rho2 * u1 * u1) / (2 * (i ? w1 : w0) * rho2 * u1), sq = Math.sqrt(b * b + 1) - b; return sq < 1e-9 ? -18 : Math.log(sq); };
      const r0 = rr(0), S = (rr(1) - r0) / rho;
      const at = t => { if (t >= 1) return tgt; const s = t * S, w = w0 * Math.cosh(r0) / Math.cosh(r0 + rho * s), u = w0 * (Math.cosh(r0) * Math.tanh(r0 + rho * s) - Math.sinh(r0)) / rho2;
        return { center: map.unproject(from.add(toPx.subtract(from).multiplyBy(u / u1)), z0), zoom: map.getScaleZoom(w0 / w, z0) }; };
      if (!reduce) {
        const subs = tiles.options.subdomains, seen = new Set(), maxZ = tiles.options.maxNativeZoom;
        for (let i = 0; i <= 120; i++) {
          const v = at(i / 120), tz = Math.min(maxZ, Math.round(v.zoom)), n = 2 ** tz, c = map.project(v.center, tz), h = size.divideBy(2 * 2 ** (v.zoom - tz));
          for (let x = Math.floor((c.x - h.x) / 256); x <= Math.floor((c.x + h.x) / 256); x++)
            for (let y = Math.max(0, Math.floor((c.y - h.y) / 256)); y <= Math.min(n - 1, Math.floor((c.y + h.y) / 256)); y++) {
              const xx = ((x % n) + n) % n, url = L.Util.template(tiles._url, { s: subs[Math.abs(xx + y) % subs.length], x: xx, y, z: tz, r: "" });
              if (!seen.has(url)) { seen.add(url); new Image().src = url; }
            }
        }
      }
      const fly = T => new Promise(res => {
        map._stop(); map._moveStart(true, false);
        const t0 = performance.now();
        let last = null;
        const frame = now => { const t = Math.min(1, (now - t0) / T), e = t < .5 ? 4 * t * t * t : 1 - (2 - 2 * t) ** 3 / 2, v = at(e);
          map._move(v.center, v.zoom, { flyTo: true });
          // new tiles only when the view has moved a quarter tile at the current tile zoom
          const c = map.project(v.center, Math.round(v.zoom));
          if (!last || last.z !== Math.round(v.zoom) || c.distanceTo(last.c) > 64) { tiles._update(); tiles._pruneTiles(); last = { z: Math.round(v.zoom), c }; }
          if (t < 1) requestAnimationFrame(frame); else { map._moveEnd(true); res(); } };
        requestAnimationFrame(frame);
      });
      let fx = null;
      try {
        const F = await loadIntro();
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
          const step = now => { const k = Math.min(1, (now - t0) / T);
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
      } catch (e) { fx = null; }
      const done = () => { if (fx) { map.removeLayer(fx); fx = null; } map.addLayer(pinLayer); intro.remove(); paint(); lock(false); limitWorld();
        requestAnimationFrame(() => document.getElementById("map").classList.remove("pins-hidden")); };
      if (reduce) { map.fitBounds(cityBounds, { padding: [30, 30] }); done(); return; }
      // the arcs and fills fade out as the camera passes the continent, before they can pile into a fan
      const fxPane = map.getPanes().overlayPane;
      map.on("zoom", function fade() {
        const k = Math.max(0, 1 - (map.getZoom() - z0 - .6) / 1.2);
        fxPane.style.opacity = k;
        if (k === 0 && fx) { map.removeLayer(fx); fx = null; fxPane.style.opacity = ""; map.off("zoom", fade); }
      });
      await fly(3800);
      done();
    }
  }
  paint();
})();
