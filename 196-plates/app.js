(async function () {
  const ORDER = ["Europe", "Middle East", "Africa", "South Asia", "Central Asia", "Southeast Asia", "East Asia", "Americas", "Oceania"];
  const D = await (await fetch("data.json")).json();
  document.getElementById("n").textContent = D.pins.length;

  const map = L.map("map", { zoomControl: true, attributionControl: true, zoomSnap: 0.25 });
  const BASE = window.__BASE || { url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' };
  if (window.__BASE_FILTER) document.documentElement.style.setProperty("--tile-filter", window.__BASE_FILTER);
  L.tileLayer(BASE.url, {
    maxZoom: 19, maxNativeZoom: BASE.max || 19, subdomains: BASE.sub || "abc", attribution: BASE.attribution
  }).addTo(map);

  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const c2ok = c => /^[a-z]{2}$/.test(c);
  D.pins = D.pins.filter(p => c2ok(p.c2));
  const small = window.matchMedia("(max-width: 760px)").matches;
  const size = () => (small ? 22 : 28);
  const safeUrl = u => /^https?:\/\//.test(u || "") ? u : null;
  const card = p => {
    const s0 = (p.src || []).find(s => safeUrl(s.url));
    const n = p.sources || (p.src || []).length;
    const dots = Array.from({ length: Math.min(n, 9) }, () => '<span class="dot"></span>').join("");
    return `<div class="card-flag"><img src="flags/${p.c2}-320.png" alt="Flag of ${esc(p.country)}"></div>
    <div class="card-body"><div class="card-name">${esc(p.name)}</div>
    <div class="card-meta">${esc(p.country)}${p.suburb ? " &middot; " + esc(p.suburb) : ""}</div>
    ${n ? `<div class="card-src">${dots}<span>${n} ${n === 1 ? "source" : "sources"}</span></div>` : ""}
    ${s0 ? `<a class="card-btn" href="${esc(s0.url)}" target="_blank" rel="noopener">Read ${esc(s0.name)}'s review &rarr;</a>` : ""}</div>`;
  };

  const markers = {};
  D.pins.forEach(p => {
    const w = size(p);
    const m = L.marker([p.lat, p.lon], {
      title: p.country, riseOnHover: true, zIndexOffset: p.sources * 10,
      icon: L.divIcon({ className: "", iconSize: [w, w], iconAnchor: [w / 2, w / 2],
        html: `<div class="pin" style="width:${w}px;height:${w}px;background-image:url(flags/${p.c2}-80.png)"></div>` })
    }).addTo(map);
    m.bindPopup(card(p), { className: "card", closeButton: false, offset: [0, -w / 2 + 4], autoPanPadding: [24, 24] });
    markers[p.cc] = m;
  });
  map.fitBounds(L.latLngBounds(D.pins.map(p => [p.lat, p.lon])), { padding: [30, 30] });

  const groups = document.getElementById("groups");
  ORDER.forEach(g => {
    const ps = D.pins.filter(p => p.group === g);
    if (!ps.length) return;
    const sec = document.createElement("section");
    sec.className = "group";
    sec.innerHTML = `<h2>${esc(g)}</h2><div class="flags"></div>`;
    ps.forEach(p => {
      const b = document.createElement("button");
      b.className = "flag"; b.type = "button"; b.title = p.country; b.setAttribute("aria-label", p.country + ": " + p.name);
      b.innerHTML = `<img src="flags/${p.c2}-80.png" alt="" loading="lazy">`;
      b.addEventListener("click", () => {
        const m = markers[p.cc];
        map.flyTo(m.getLatLng(), Math.max(map.getZoom(), 13), { duration: 0.8 });
        map.once("moveend", () => m.openPopup());
        if (window.matchMedia("(max-width: 760px)").matches) document.getElementById("map").scrollIntoView({ behavior: "smooth" });
      });
      sec.querySelector(".flags").appendChild(b);
    });
    groups.appendChild(sec);
  });
})();
