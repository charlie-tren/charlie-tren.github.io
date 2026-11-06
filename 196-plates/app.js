(async function () {
  const ORDER = ["Europe", "Middle East", "Africa", "South Asia", "Central Asia", "Southeast Asia", "East Asia", "Americas", "Oceania"];
  const D = await (await fetch("data.json")).json();

  const map = L.map("map", { zoomControl: true, attributionControl: true, zoomSnap: 0.25 });
  const BASE = window.__BASE || { url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' };
  if (window.__BASE_FILTER) document.documentElement.style.setProperty("--tile-filter", window.__BASE_FILTER);
  L.tileLayer(BASE.url, {
    maxZoom: 19, maxNativeZoom: BASE.max || 19, subdomains: BASE.sub || "abc", attribution: BASE.attribution
  }).addTo(map);

  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = u => /^https?:\/\//.test(u || "") ? u : null;
  D.pins = D.pins.filter(p => /^[a-z]{2}$/.test(p.c2));
  document.getElementById("n").textContent = D.pins.length;
  const small = window.matchMedia("(max-width: 760px)").matches;
  const W = small ? 22 : 28;

  // ---- places you have been, kept on this device ----
  const KEY = "196plates.been." + (D.city || "sydney").toLowerCase();
  let been = new Set();
  try { been = new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify([...been])); } catch (e) {} };
  const beenCount = document.getElementById("been");
  const paint = () => {
    beenCount.hidden = been.size === 0;
    beenCount.textContent = `You've been to ${been.size}`;
    document.querySelectorAll("[data-cc]").forEach(el => el.classList.toggle("is-been", been.has(el.dataset.cc)));
  };

  const dirUrl = p => "https://www.google.com/maps/dir/?api=1&destination=" +
    encodeURIComponent(p.address ? `${p.name}, ${p.address}` : `${p.name}, ${p.suburb || ""} NSW`);

  const card = p => {
    const links = (p.src || []).filter(s => safeUrl(s.url));
    const rev = p.review && safeUrl(p.review.url) ? p.review : null;
    const n = links.length;
    return `<div class="card-flag"><img src="flags/${p.c2}-320.png" alt="Flag of ${esc(p.country)}"></div>
    <div class="card-body">
      <div class="card-kicker">${esc(p.adj)}${p.suburb ? " &middot; " + esc(p.suburb) : ""}</div>
      <div class="card-name">${esc(p.name)}</div>
      ${n ? `<details class="card-src"><summary>${n} ${n === 1 ? "source" : "sources"}</summary><ul>${links.map(s =>
        `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a></li>`).join("")}</ul></details>` : ""}
      <div class="card-actions">
        ${rev ? `<a class="card-btn" href="${esc(rev.url)}" target="_blank" rel="noopener">Read ${esc(rev.name)}'s review</a>` : ""}
        <a class="card-btn alt" href="${dirUrl(p)}" target="_blank" rel="noopener">Directions</a>
        <button type="button" class="card-btn been" data-been="${esc(p.cc)}" aria-pressed="${been.has(p.cc)}">${been.has(p.cc) ? "&#10003; Been here" : "Been here?"}</button>
      </div>
    </div>`;
  };

  const markers = {};
  D.pins.forEach(p => {
    const m = L.marker([p.lat, p.lon], {
      title: `${p.adj}: ${p.name}`, riseOnHover: true,
      icon: L.divIcon({ className: "", iconSize: [W, W], iconAnchor: [W / 2, W / 2],
        html: `<div class="pin" data-cc="${esc(p.cc)}" style="width:${W}px;height:${W}px;background-image:url(flags/circle/${p.c2}.svg)"></div>` })
    }).addTo(map);
    m.bindPopup(() => card(p), { className: "card", closeButton: true, offset: [0, -W / 2 + 4], autoPanPadding: [24, 24], maxWidth: 270, minWidth: 250 });
    markers[p.cc] = m;
  });
  const cityBounds = L.latLngBounds(D.pins.map(p => [p.lat, p.lon]));
  const mapEl = document.getElementById("map");

  // ---- the search intro: pick a city, flight paths draw in, the camera flies to the city ----
  const intro = document.getElementById("intro");
  const skip = location.hash === "#" + (D.city || "sydney").toLowerCase() || !intro;
  const showPins = on => mapEl.classList.toggle("pins-hidden", !on);
  if (skip) {
    if (intro) intro.remove();
    map.fitBounds(cityBounds, { padding: [30, 30] });
  } else {
    map.setView([8, 150], small ? 1 : 2);
    showPins(false);
    const input = intro.querySelector("input"), list = intro.querySelector("ul");
    const cities = [{ name: D.city || "Sydney", country: "Australia", n: D.pins.length }];
    const render = () => {
      const q = input.value.trim().toLowerCase();
      const hits = cities.filter(c => !q || c.name.toLowerCase().startsWith(q));
      list.hidden = !q;
      list.innerHTML = hits.map(c => `<li><button type="button" data-city="${esc(c.name)}"><span><b>${esc(c.name)}</b>, ${esc(c.country)}</span><span class="n">${c.n} plates</span></button></li>`).join("")
        + `<li class="soon">More cities coming</li>`;
      list.querySelectorAll("button").forEach(b => b.addEventListener("click", go));
    };
    input.addEventListener("input", render);
    input.addEventListener("keydown", e => { if (e.key === "Enter") { const b = list.querySelector("button"); if (b) b.click(); } });
    input.focus();
    let started = false;
    async function go() {
      if (started) return; started = true;
      input.blur();
      intro.classList.add("gone");
      history.replaceState(null, "", "#" + (D.city || "sydney").toLowerCase());
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      let world = null;
      try {
        const [w, n3] = await Promise.all([fetch("world-110m.json").then(r => r.json()), fetch("ccn3.json").then(r => r.json())]);
        const have = new Set(D.pins.map(p => p.cc));
        const F = topojson.feature(w, w.objects.countries);
        const fix = r => { const xs = r.map(p => p[0]), spans = Math.max(...xs) - Math.min(...xs) > 180, mean = xs.reduce((a, b) => a + b, 0) / xs.length;
          return r.map(([x, y]) => [(spans ? x < 0 : mean < -25) ? x + 360 : x, y]); };
        F.features.forEach(d => { const g = d.geometry; if (!g) return;
          if (g.type === "Polygon") g.coordinates = g.coordinates.map(fix); else if (g.type === "MultiPolygon") g.coordinates = g.coordinates.map(pl => pl.map(fix)); });
        const canvas = L.canvas({ padding: 0.5 });
        const live = F.features.filter(f => have.has(n3[f.id]));
        world = L.featureGroup().addTo(map);
        L.geoJSON({ type: "FeatureCollection", features: live }, { renderer: canvas, interactive: false,
          style: { weight: 0, fillColor: "#2f6f4f", fillOpacity: .75 } }).addTo(world);
        const SYD = cityBounds.getCenter();
        const arcs = live.map(f => {
          const b = L.geoJSON(f).getBounds().getCenter();
          const pts = []; for (let i = 0; i <= 40; i++) { const t = i / 40; pts.push([b.lat + (SYD.lat - b.lat) * t, b.lng + (SYD.lng - b.lng) * t + Math.sin(Math.PI * t) * 0]); }
          return L.polyline(pts.slice(0, 2), { renderer: canvas, color: "#e4572e", weight: 1.1, opacity: .7, interactive: false, _all: pts }).addTo(world);
        });
        if (!reduce) await new Promise(res => { const t0 = performance.now(), T = 1600;
          const step = now => { const k = Math.min(1, (now - t0) / T);
            arcs.forEach((a, i) => { const ki = Math.max(0, Math.min(1, k * 1.6 - i / arcs.length * 0.6)); const all = a.options._all; a.setLatLngs(all.slice(0, Math.max(2, Math.round(all.length * ki)))); });
            k < 1 ? requestAnimationFrame(step) : res(); };
          requestAnimationFrame(step); });
        else arcs.forEach(a => a.setLatLngs(a.options._all));
      } catch (e) { world = null; }
      const done = () => { if (world) map.removeLayer(world); showPins(true); intro.remove(); };
      if (reduce) { map.fitBounds(cityBounds, { padding: [30, 30] }); done(); return; }
      map.once("zoomend", () => {});
      map.on("zoom", function fade() { if (map.getZoom() > 5 && world) { map.removeLayer(world); world = null; map.off("zoom", fade); } });
      map.flyToBounds(cityBounds, { padding: [30, 30], duration: 4.2, easeLinearity: 0.2 });
      map.once("moveend", done);
    }
  }

  map.on("popupopen", e => {
    const b = e.popup.getElement().querySelector("[data-been]");
    if (!b) return;
    b.addEventListener("click", () => {
      const cc = b.dataset.been;
      been.has(cc) ? been.delete(cc) : been.add(cc);
      save(); paint();
      b.setAttribute("aria-pressed", been.has(cc));
      b.innerHTML = been.has(cc) ? "&#10003; Been here" : "Been here?";
    });
  });

  const groups = document.getElementById("groups");
  ORDER.forEach(g => {
    const ps = D.pins.filter(p => p.group === g).sort((a, b) => a.country.localeCompare(b.country));
    if (!ps.length) return;
    const sec = document.createElement("section");
    sec.className = "group";
    sec.innerHTML = `<h2>${esc(g)}</h2><div class="flags"></div>`;
    ps.forEach(p => {
      const b = document.createElement("button");
      b.className = "flag"; b.type = "button"; b.title = `${p.adj}: ${p.name}`; b.dataset.cc = p.cc;
      b.setAttribute("aria-label", `${p.adj}: ${p.name}`);
      b.innerHTML = `<img class="fit-${p.fit}" src="flags/${p.c2}-80.png" alt="" loading="lazy">`;
      b.addEventListener("click", () => {
        const m = markers[p.cc];
        map.flyTo(m.getLatLng(), Math.max(map.getZoom(), 14), { duration: 0.8 });
        map.once("moveend", () => m.openPopup());
        if (small) document.getElementById("map").scrollIntoView({ behavior: "smooth" });
      });
      sec.querySelector(".flags").appendChild(b);
    });
    groups.appendChild(sec);
  });
  paint();
})();
