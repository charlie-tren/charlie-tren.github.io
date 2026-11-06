(async function () {
  const ORDER = ["Europe", "Middle East", "Africa", "South Asia", "Central Asia", "Southeast Asia", "East Asia", "Americas", "Oceania"];
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
  const W = small ? 22 : 28;

  // ---- theme ----
  const themeBtn = document.getElementById("theme");
  const setTheme = t => { document.documentElement.dataset.theme = t; themeBtn.setAttribute("aria-pressed", t === "dark");
    themeBtn.querySelector(".lbl").textContent = t === "dark" ? "Light" : "Dark"; store.set("196plates.theme", t); };
  setTheme(document.documentElement.dataset.theme || "dark");
  themeBtn.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));

  // ---- map ----
  const map = L.map("map", { zoomControl: true, attributionControl: true, zoomSnap: 0.25, worldCopyJump: false });
  map.attributionControl.setPrefix(false);
  const BASE = window.__BASE || { url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>' };
  const tiles = L.tileLayer(BASE.url, { maxZoom: 19, maxNativeZoom: BASE.max || 19, subdomains: BASE.sub || "abc", attribution: BASE.attribution }).addTo(map);

  // ---- places you have eaten at, kept on this device (cc -> date) ----
  const KEY = "196plates.eaten." + CITY;
  let eaten = store.get(KEY, {});
  const isEaten = cc => !!eaten[cc];
  const eatenCount = document.getElementById("been");
  const paint = () => {
    const n = Object.keys(eaten).length;
    eatenCount.hidden = n === 0;
    eatenCount.innerHTML = `${n} of ${D.pins.length} tasted &middot; <button type="button" class="linkish" id="mine">Your map</button>`;
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
        <label class="card-check"><input type="checkbox" data-eat="${esc(p.cc)}" ${isEaten(p.cc) ? "checked" : ""}> Tasted</label>
      </div>
    </div>`;
  };

  const cluster = L.markerClusterGroup({ maxClusterRadius: 34, showCoverageOnHover: false, spiderfyDistanceMultiplier: 1.4,
    disableClusteringAtZoom: 15,
    iconCreateFunction: c => L.divIcon({ className: "", iconSize: [W + 6, W + 6],
      html: `<div class="cluster" style="width:${W + 6}px;height:${W + 6}px">${c.getChildCount()}</div>` }) });
  const markers = {};
  D.pins.forEach(p => {
    const m = L.marker([p.lat, p.lon], {
      title: `${p.adj}: ${p.name}`, riseOnHover: true,
      icon: L.divIcon({ className: "", iconSize: [W, W], iconAnchor: [W / 2, W / 2],
        html: `<div class="pin" data-cc="${esc(p.cc)}" style="width:${W}px;height:${W}px;background-image:url(flags/circle/${p.c2}.svg)"></div>` })
    });
    m.bindPopup(() => card(p), { className: "card", closeButton: true, offset: [0, -W / 2 + 4], autoPanPadding: [24, 24], maxWidth: 270, minWidth: 250 });
    cluster.addLayer(m);
    markers[p.cc] = m;
  });
  map.addLayer(cluster);
  cluster.on("animationend", paint);
  map.on("zoomend moveend", () => setTimeout(paint, 50));
  map.on("popupopen", e => {
    const b = e.popup.getElement().querySelector("[data-eat]");
    if (b) b.addEventListener("change", () => toggleEaten(b.dataset.eat));
  });
  const cityBounds = L.latLngBounds(D.pins.map(p => [p.lat, p.lon]));
  const openPin = cc => cluster.zoomToShowLayer(markers[cc], () => markers[cc].openPopup());

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

  // ---- filter the list: all / eaten / not yet ----
  let filterMode = "all";
  function applyFilter() {
    document.querySelectorAll("#groups .rows li").forEach(li => {
      const cc = li.firstElementChild.dataset.cc;
      li.hidden = filterMode === "eaten" ? !isEaten(cc) : filterMode === "not" ? isEaten(cc) : false;
    });
    document.querySelectorAll("#groups .group").forEach(sec => { sec.hidden = ![...sec.querySelectorAll("li")].some(li => !li.hidden); });
    document.querySelectorAll("#filter button").forEach(b => b.setAttribute("aria-pressed", b.dataset.f === filterMode));
  }
  document.querySelectorAll("#filter button").forEach(b => b.addEventListener("click", () => { filterMode = b.dataset.f; applyFilter(); }));

  // ---- world views: which of 196 the city has, and your own map ----
  let worldData = null, worldLayer = null;
  const loadWorld = async () => {
    if (worldData) return worldData;
    const [w, n3] = await Promise.all([fetch("world-110m.json").then(r => r.json()), fetch("ccn3.json").then(r => r.json())]);
    const F = topojson.feature(w, w.objects.countries);
    const fix = r => { const xs = r.map(p => p[0]), spans = Math.max(...xs) - Math.min(...xs) > 180, mean = xs.reduce((a, b) => a + b, 0) / xs.length;
      return r.map(([x, y]) => [(spans ? x < 0 : mean < -25) ? x + 360 : x, y]); };
    F.features.forEach(d => { const g = d.geometry; if (!g) return; d.cc = n3[d.id];
      if (g.type === "Polygon") g.coordinates = g.coordinates.map(fix); else if (g.type === "MultiPolygon") g.coordinates = g.coordinates.map(pl => pl.map(fix)); });
    return (worldData = F);
  };
  const worldBtn = L.control({ position: "topright" });
  worldBtn.onAdd = () => { const d = L.DomUtil.create("div", "map-toggle");
    d.innerHTML = `<button type="button" id="worldbtn">World</button>`; L.DomEvent.disableClickPropagation(d); return d; };
  worldBtn.addTo(map);
  const legend = document.getElementById("legend");
  async function showWorld(mode) {
    const F = await loadWorld();
    if (worldLayer) map.removeLayer(worldLayer);
    const on = mode === "mine" ? (cc => isEaten(cc)) : (cc => !!byCC[cc]);
    // the world view is drawn, not tiled: no street tiles (they invert badly in dark), no Antarctica
    const dark = document.documentElement.dataset.theme === "dark";
    map.removeLayer(tiles);
    document.getElementById("map").classList.add("world");
    worldLayer = L.geoJSON({ type: "FeatureCollection", features: F.features.filter(f => f.id !== "010") }, {
      style: f => ({ weight: .6, color: dark ? "#121417" : "#ffffff", fillOpacity: 1,
        fillColor: on(f.cc) ? (dark ? "#3f9a6c" : "#2f6f4f") : (dark ? "#2a2e33" : "#e9e4d8") }),
      onEachFeature: (f, l) => { const p = byCC[f.cc]; if (!p || !on(f.cc)) return;
        l.bindPopup(`<div class="card-body"><div class="card-kicker">${esc(p.adj)}${mode === "mine" ? " &middot; eaten " + fmtDate(eaten[p.cc]) : ""}</div><div class="card-name">${esc(p.name)}</div><div class="card-meta">${esc(p.suburb || "")}</div><button type="button" class="card-btn wide" data-go="${esc(p.cc)}">Show in ${esc(D.city)}</button></div>`, { className: "card" }); } }).addTo(map);
    map.removeLayer(cluster);
    // one world exactly: zoom so 360 degrees of longitude fill the map width once, no copies either side
    const mw = document.getElementById("map").clientWidth;
    map.setView([20, 150], Math.max(0, Math.log2(mw / 256)), { animate: false });
    document.getElementById("worldbtn").textContent = `Back to ${D.city}`;
    document.getElementById("worldbtn").onclick = hideWorld;
    const n = mode === "mine" ? Object.keys(eaten).length : D.pins.length;
    legend.hidden = false;
    legend.innerHTML = `<i></i>${mode === "mine" ? `You've eaten ${n} of 196` : `In ${esc(D.city)}: ${n} of 196`}`;
  }
  function hideWorld() {
    if (!worldLayer) return;
    map.removeLayer(worldLayer); worldLayer = null; legend.hidden = true; tiles.addTo(map); document.getElementById("map").classList.remove("world");
    map.addLayer(cluster); map.fitBounds(cityBounds, { padding: [30, 30] });
    document.getElementById("worldbtn").textContent = "World";
    document.getElementById("worldbtn").onclick = () => showWorld("city");
  }
  document.getElementById("worldbtn").onclick = () => showWorld("city");
  map.on("popupopen", e => { const g = e.popup.getElement().querySelector("[data-go]"); if (g) g.onclick = () => { hideWorld(); setTimeout(() => openPin(g.dataset.go), 300); }; });

  // ---- the search intro: a plain page; pick a city, great-circle arcs draw in, the camera flies to it ----
  const intro = document.getElementById("intro");
  const skip = location.hash === "#" + CITY || !intro;
  if (skip) {
    if (intro) intro.remove();
    document.body.classList.remove("searching");
    map.fitBounds(cityBounds, { padding: [30, 30] });
  } else {
    document.body.classList.add("searching");
    const input = intro.querySelector("input"), list = intro.querySelector("ul");
    const cities = [{ name: D.city, country: "Australia", n: D.pins.length }];
    const render = () => {
      const q = input.value.trim().toLowerCase();
      const hits = cities.filter(c => !q || c.name.toLowerCase().startsWith(q));
      list.hidden = !q;
      list.innerHTML = hits.map(c => `<li><button type="button"><span><b>${esc(c.name)}</b>, ${esc(c.country)}</span><span class="n">${c.n} plates</span></button></li>`).join("")
        + `<li class="soon">More cities coming</li>`;
      list.querySelectorAll("button").forEach(b => b.addEventListener("click", go));
    };
    input.addEventListener("input", render);
    input.addEventListener("keydown", e => { if (e.key === "Enter") { const b = list.querySelector("button"); if (b) b.click(); } });
    input.focus();
    let started = false;
    async function go() {
      if (started) return; started = true;
      history.replaceState(null, "", "#" + CITY);
      document.body.classList.remove("searching");
      map.invalidateSize();
      map.setView([10, 150], small ? 1 : 2, { animate: false });
      map.removeLayer(cluster);
      intro.classList.add("gone");
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      let fx = null;
      try {
        const F = await loadWorld();
        fx = L.featureGroup().addTo(map);
        const canvas = L.canvas({ padding: .5 });
        const to = cityBounds.getCenter(), rad = Math.PI / 180;
        // farthest first, so the world lights up from the edges in towards the city
        const dist = f => { const c = L.geoJSON(f).getBounds().getCenter(); return map.distance(c, to); };
        const live = F.features.filter(f => byCC[f.cc]).sort((a, b) => dist(b) - dist(a));
        const fills = live.map(f => L.geoJSON(f, { renderer: canvas, interactive: false, style: { weight: 0, fillColor: "#e4572e", fillOpacity: 0 } }).addTo(fx));
        const counter = document.getElementById("tally");
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
        counter.hidden = false;
        if (!reduce) await new Promise(res => { const t0 = performance.now(), T = 3200, N = arcs.length;
          let lit = 0;
          const step = now => { const k = Math.min(1, (now - t0) / T);
            arcs.forEach((a, i) => {
              // one country at a time: each arc starts as the previous is half drawn, its country lights when it lands
              const ki = Math.max(0, Math.min(1, (k * (N * .35 + 1) - i * .35)));
              const all = a.options.all; a.setLatLngs(all.slice(0, Math.max(2, Math.round(all.length * ki))));
              if (ki >= 1 && !fills[i]._lit) { fills[i]._lit = true; fills[i].setStyle({ fillOpacity: .85 }); lit++; }
            });
            counter.textContent = `${Math.round(lit / N * D.pins.length)} of 196`;
            k < 1 ? requestAnimationFrame(step) : res(); };
          requestAnimationFrame(step); });
        else { fills.forEach(f => f.setStyle({ fillOpacity: .85 })); counter.textContent = `${D.pins.length} of 196`; }
      } catch (e) { fx = null; }
      const done = () => { if (fx) { map.removeLayer(fx); fx = null; } map.addLayer(cluster); intro.remove(); document.getElementById("tally").hidden = true; paint(); };
      if (reduce) { map.fitBounds(cityBounds, { padding: [30, 30] }); done(); return; }
      // the arcs and fills fade out as the camera passes the continent, before they can pile into a fan
      const z0 = map.getZoom(), fxPane = map.getPanes().overlayPane;
      map.on("zoom", function fade() {
        const k = Math.max(0, 1 - (map.getZoom() - z0 - .6) / 1.2);
        fxPane.style.opacity = k;
        if (k === 0 && fx) { map.removeLayer(fx); fx = null; fxPane.style.opacity = ""; map.off("zoom", fade); }
      });
      map.flyToBounds(cityBounds, { padding: [30, 30], duration: 4, easeLinearity: .2 });
      map.once("moveend", done);
    }
  }
  paint();
})();
