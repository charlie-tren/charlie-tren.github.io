/* 196 Plates world map ("Your map" and the city's world view). No dependencies: TopoJSON decoding and the Mercator
   maths are inline. WorldMap.render(el, { mode, eaten, pins, city, onPick }) -> { destroy() }. */
(function () {
  const RAD = Math.PI / 180, C = 150, CUT = C - 180, TOP = 75, BOT = -70.5, TOTAL = 196;
  const COL = { eaten: "#17283a", city: "#b3c3d2", none: "#f7f6f2", sea: "#e4ebef", coast: "#4f6478", coastW: .8, border: "#6d8296", borderW: .6 };
  // UN members (plus the site's three) with no outline at 110m: a point to hover or tap
  const SMALL = { AND: [1.5, 42.5, "Andorra"], ATG: [-61.8, 17.1, "Antigua and Barbuda"], BHR: [50.5, 26, "Bahrain"], BRB: [-59.5, 13.2, "Barbados"],
    COM: [44.2, -12.2, "Comoros"], CPV: [-24, 16, "Cape Verde"], DMA: [-61.3, 15.4, "Dominica"], FSM: [158.2, 6.9, "Micronesia"], GRD: [-61.7, 12.1, "Grenada"],
    KIR: [173, 1.4, "Kiribati"], KNA: [-62.8, 17.3, "Saint Kitts and Nevis"], LCA: [-61, 13.9, "Saint Lucia"], LIE: [9.5, 47.3, "Liechtenstein"],
    MCO: [7.4, 43.7, "Monaco"], MDV: [73, 3.2, "Maldives"], MHL: [168, 9, "Marshall Islands"], MLT: [14.6, 35.8, "Malta"], MUS: [57.5, -20.3, "Mauritius"],
    NRU: [166.9, -0.5, "Nauru"], PLW: [134.5, 7.5, "Palau"], SGP: [103.8, 1.4, "Singapore"], SMR: [12.4, 43.8, "San Marino"],
    STP: [7, 1, "São Tomé and Príncipe"], SYC: [55.7, -4.6, "Seychelles"], TON: [-175, -20, "Tonga"], TUV: [178, -8, "Tuvalu"],
    VAT: [12.4, 41.9, "Vatican City"], VCT: [-61.2, 13.2, "Saint Vincent and the Grenadines"], WSM: [-172.3, -13.6, "Samoa"] };
  const NAME = { "W. Sahara": "Western Sahara", "Dem. Rep. Congo": "DR Congo", "Dominican Rep.": "Dominican Republic", "Falkland Is.": "Falkland Islands",
    "Fr. S. Antarctic Lands": "French Southern Lands", "Central African Rep.": "Central African Republic", "Eq. Guinea": "Equatorial Guinea",
    "Solomon Is.": "Solomon Islands", "Bosnia and Herz.": "Bosnia and Herzegovina", "S. Sudan": "South Sudan" };
  const NS = "http://www.w3.org/2000/svg";
  let worldP = null;

  const load = o => o.world ? Promise.resolve(o.world) : (worldP = worldP || Promise.all([
    fetch((o.base || "") + "world-110m.json").then(r => r.json()), fetch((o.base || "") + "ccn3.json").then(r => r.json())])
    .then(([topo, n3]) => ({ topo, n3 })));

  function decode(topo) {
    const t = topo.transform;
    const arcs = topo.arcs.map(a => { let x = 0, y = 0;
      return a.map(p => t ? [(x += p[0]) * t.scale[0] + t.translate[0], (y += p[1]) * t.scale[1] + t.translate[1]] : p); });
    const ring = ids => { const out = []; ids.forEach((i, k) => { let a = i < 0 ? arcs[~i].slice().reverse() : arcs[i]; out.push(...(k ? a.slice(1) : a)); }); return out; };
    const geoms = topo.objects.countries.geometries.filter(g => g.arcs);
    const owners = new Map();
    const feats = geoms.map((g, gi) => {
      const polys = g.type === "Polygon" ? [g.arcs] : g.arcs;
      polys.forEach(p => p.forEach(r => r.forEach(i => { const a = i < 0 ? ~i : i; owners.set(a, (owners.get(a) || new Set()).add(gi)); })));
      return { id: g.id, name: g.properties && g.properties.name, polys: polys.map(p => p.map(ring)) };
    });
    const borders = [...owners].filter(([, s]) => s.size > 1).map(([a]) => arcs[a]);
    return { feats, borders };
  }

  // whole rings move east of the cut (never sliced); Antarctica, which rings the pole, is opened at the cut
  const shiftRing = r => { const xs = r.map(p => p[0]), spans = Math.max(...xs) - Math.min(...xs) > 180, mean = xs.reduce((a, b) => a + b, 0) / xs.length;
    return r.map(([x, y]) => [(spans ? x < 0 : mean < CUT) ? x + 360 : x, y]); };
  const poleRing = r => { let p = r.filter(q => q[1] > -85).map(([x, y]) => [x < CUT ? x + 360 : x, y]);
    const i = p.findIndex((q, k) => k && Math.abs(q[0] - p[k - 1][0]) > 180); if (i > 0) p = p.slice(i).concat(p.slice(0, i));
    return p.concat([[p[p.length - 1][0], -85], [p[0][0], -85]]); };
  const shiftLine = l => { const xs = l.map(p => p[0]), m = xs.reduce((a, b) => a + b, 0) / xs.length; return l.map(([x, y]) => [m < CUT ? x + 360 : x, y]); };
  const my = la => Math.log(Math.tan(Math.PI / 4 + Math.max(-85, Math.min(85, la)) * RAD / 2));

  function prepare(world) {
    const { feats, borders } = decode(world.topo);
    feats.forEach(f => { f.a3 = world.n3[f.id];
      f.polys = f.polys.map(p => p.map(r => f.id === "010" && Math.max(...r.map(q => q[0])) - Math.min(...r.map(q => q[0])) > 300 ? poleRing(r) : shiftRing(r))); });
    let l0 = Infinity, l1 = -Infinity;
    // the frame is the land's extent: Antarctica's strip runs off both edges and does not set it
    feats.filter(f => f.id !== "010").forEach(f => f.polys.forEach(p => p.forEach(r => r.forEach(([x, y]) => { if (y <= TOP && y >= BOT) { if (x < l0) l0 = x; if (x > l1) l1 = x; } }))));
    Object.values(SMALL).forEach(([x]) => { x = x < CUT ? x + 360 : x; if (x < l0) l0 = x; if (x > l1) l1 = x; });
    return { feats, borders: borders.map(shiftLine), l0: l0 - 1.5, l1: l1 + 1.5 };
  }

  function render(el, o) {
    o = { eaten: {}, pins: [], city: "Sydney", onPick: () => {}, ...o };
    const PAL = { ...COL, ...(o.palette || {}) }, flagBase = o.flagBase || (o.base || "") + "flags/";
    let dead = false, W = 0, H = 0, raf = 0, P = null;
    const root = document.createElement("div"); root.className = "wm"; el.appendChild(root);
    const byCC = Object.fromEntries(o.pins.map(p => [p.cc, p]));
    const eaten = new Set(Object.keys(o.eaten || {}));
    // one view: eaten, then in the city, then the rest; with nothing eaten yet it is the city's two states
    const three = o.mode === "mine" || (o.mode !== "city" && eaten.size > 0);
    const state = a3 => three ? (eaten.has(a3) ? "eaten" : byCC[a3] ? "city" : "none") : (byCC[a3] ? "eaten" : "none");
    const pickable = a3 => !!byCC[a3] || eaten.has(a3);
    const nameOf = (a3, fallback) => (byCC[a3] && byCC[a3].country) || (SMALL[a3] && SMALL[a3][2]) || NAME[fallback] || fallback || a3;

    const draw = () => {
      if (dead || !P) return;
      W = el.clientWidth; H = el.clientHeight; if (!W || !H) return;
      const span = (P.l1 - P.l0) * RAD, yT = my(TOP), yB = my(BOT);
      let k = W / span, mh = k * (yT - yB);
      // fill the width unless that leaves the band too little room; then fit the height and centre
      const minBand = Math.max(150, Math.min(240, H * .2));
      if (mh > H - minBand) { k = (H - minBand) / (yT - yB); mh = H - minBand; }
      const mw = k * span, x0 = (W - mw) / 2;
      const pj = (x, y) => [x0 + k * (x - P.l0) * RAD, k * (yT - my(y))];
      const s = Math.max(.42, Math.min(1, (H - mh) / 309, W / 700));
      // a tall container (a phone held upright) gets the band it needs, and band plus map sit centred
      const band = Math.min(H - mh, Math.round(309 * s + 24)), top0 = Math.round((H - mh - band) / 2);
      root.style.setProperty("--wm-s", s.toFixed(3)); root.classList.toggle("wm-narrow", W < 360);

      // the band: count and the three-state bar
      // every figure is out of 196 and says what it counts
      const esc = t => String(t).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
      const nC = o.pins.length, nNone = Math.max(0, TOTAL - nC - [...eaten].filter(a => !byCC[a]).length);
      const nE = three ? eaten.size : nC, inC = "In " + esc(o.city), notC = "Not in " + esc(o.city);
      const parts = three
        ? [[eaten.size, PAL.eaten, `Eaten <b>${eaten.size}</b>`], [nC - [...eaten].filter(a => byCC[a]).length, PAL.city, `${inC} <b>${nC}</b>`], [nNone, PAL.none, `${notC} <b>${nNone}</b>`]]
        : [[nC, PAL.eaten, `${inC} <b>${nC}</b>`], [nNone, PAL.none, `${notC} <b>${nNone}</b>`]];
      root.innerHTML = `<div class="wm-band" style="top:${top0}px;height:${band}px"><div class="wm-count"><b>${nE}</b><span>of ${TOTAL} ${three ? "eaten" : "in " + esc(o.city)}</span></div>
        <div class="wm-bar"><div class="wm-track">${parts.map(([n, c], i) => `<i style="flex:${n};background:${c}"${i === parts.length - 1 ? ' class="gap"' : ""}></i>`).join("")}</div>
        <div class="wm-names">${parts.map(([n, , t]) => `<span style="flex:${n} 1 0">${t}</span>`).join("")}</div></div></div>
        <div class="wm-card" hidden></div><div class="wm-keys"></div>`;
      const svg = document.createElementNS(NS, "svg");
      svg.setAttribute("class", "wm-map"); svg.setAttribute("viewBox", `0 0 ${W} ${mh}`); svg.setAttribute("width", W); svg.setAttribute("height", mh);
      svg.setAttribute("role", "img"); svg.setAttribute("aria-label", `World map: ${nE} of ${TOTAL}`);
      svg.style.top = (top0 + band) + "px"; root.appendChild(svg);

      const items = [], out = [];
      const ringD = r => "M" + r.map(([x, y]) => pj(x, y).map(v => v.toFixed(1)).join(",")).join("L") + "Z";
      out.push(`<rect width="${W}" height="${mh}" fill="${PAL.sea}"/>`);
      P.feats.forEach(f => {
        let best = null, area = 0;
        const d = f.polys.map(p => p.map((r, ri) => { const pts = r.map(([x, y]) => pj(x, y));
          if (!ri) { let a = 0, cx = 0, cy = 0; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) { const c = pts[j][0] * pts[i][1] - pts[i][0] * pts[j][1]; a += c; cx += (pts[j][0] + pts[i][0]) * c; cy += (pts[j][1] + pts[i][1]) * c; }
            area += Math.abs(a / 2); if (a && (!best || Math.abs(a) > best.a)) best = { a: Math.abs(a), xy: [cx / (3 * a), cy / (3 * a)] }; }
          return ringD(r); }).join("")).join("");
        const st = f.id === "010" ? "none" : state(f.a3), ix = items.length;
        items.push({ a3: f.a3, name: nameOf(f.a3, f.name), xy: best ? best.xy : [0, 0], d, st, ant: f.id === "010" });
        out.push(`<path d="${d}" fill="${PAL[st]}" stroke="${PAL.coast}" stroke-width="${PAL.coastW}" stroke-linejoin="round"${f.id === "010" ? "" : ` data-k="${ix}" data-cc="${f.a3}"${pickable(f.a3) ? " data-pick" : ""}`}/>`);
        f.area = area;
      });
      out.push(`<path d="${P.borders.map(l => "M" + l.map(([x, y]) => pj(x, y).map(v => v.toFixed(1)).join(",")).join("L")).join("")}" fill="none" stroke="${PAL.border}" stroke-width="${PAL.borderW}" stroke-linejoin="round"/>`);
      // points for the countries too small to see: drawn when they are eaten or in the city, a hit area either way
      const dots = Object.entries(SMALL).map(([a3, [x, y]]) => ({ a3, xy: pj(x < CUT ? x + 360 : x, y), name: nameOf(a3) }))
        .concat(P.feats.filter(f => f.area < 30 && f.id !== "010").map(f => ({ a3: f.a3, xy: items.find(i => i.a3 === f.a3).xy, name: nameOf(f.a3, f.name), tiny: true })));
      dots.forEach(dt => { const st = state(dt.a3), ix = items.length;
        items.push({ ...dt, st, dot: true });
        const vis = st !== "none" && (!dt.tiny || st === "eaten") ? `<circle cx="${dt.xy[0].toFixed(1)}" cy="${dt.xy[1].toFixed(1)}" r="3.6" fill="${PAL[st]}" stroke="#fff" stroke-width="1.2"/>` : "";
        out.push(`${vis}<circle cx="${dt.xy[0].toFixed(1)}" cy="${dt.xy[1].toFixed(1)}" r="8" fill="transparent" data-k="${ix}"${pickable(dt.a3) ? " data-pick" : ""}/>`); });
      out.push(`<g class="wm-hl" pointer-events="none"></g>`);
      svg.innerHTML = out.join("");

      // hover (mouse) or first tap (touch) shows the name; click, or a second tap, opens the pin
      const tab = root.querySelector(".wm-card"), hl = svg.querySelector(".wm-hl");
      let cur = -1;
      const show = (ix, key) => {
        if (ix === cur && !key) return; cur = ix;
        if (ix < 0) { tab.hidden = true; hl.innerHTML = ""; return; }
        const it = items[ix], dark = it.st === "eaten";
        // a keyboard focus gets a ring that reads on any fill: white under, ink over
        const ring = key ? (it.dot ? `<circle cx="${it.xy[0]}" cy="${it.xy[1]}" r="7" fill="none" stroke="#fff" stroke-width="4"/>`
          : `<path d="${it.d}" fill="none" stroke="#fff" stroke-width="4.5" stroke-linejoin="round"/>`) : "";
        hl.innerHTML = ring + (it.dot ? `<circle cx="${it.xy[0]}" cy="${it.xy[1]}" r="7" fill="none" stroke="#0b1622" stroke-width="${key ? 2 : 1.4}"/>`
          : `<path d="${it.d}" fill="${dark ? "rgba(255,255,255,.16)" : "rgba(23,40,58,.10)"}" stroke="#0b1622" stroke-width="${key ? 2 : 1.2}" stroke-linejoin="round"/>`);
        const p = byCC[it.a3], day = o.eaten && o.eaten[it.a3], fmt = d => d.split("-").reverse().join("/");
        tab.innerHTML = p ? `<img src="${flagBase}${p.c2}-80.png" width="33" height="22" alt=""${p.fit === "contain" ? ' class="c"' : ""}><div><b>${esc(p.country)}</b><span>${esc(p.name)}</span>`
            + `<small>${esc([p.suburb, day && "Eaten " + fmt(day)].filter(Boolean).join(" \u00b7 "))}</small></div>`
          : `<div><b>${esc(it.name)}</b><small>Not in ${esc(o.city)} yet</small></div>`;
        tab.hidden = false;
        const tw = tab.offsetWidth, th = tab.offsetHeight, ax = it.xy[0], ay = top0 + band + it.xy[1];
        tab.style.left = Math.max(4, Math.min(W - tw - 4, ax - tw / 2)) + "px";
        tab.style.top = (ay - th - 9 < top0 + band + 4 ? ay + 10 : ay - th - 9) + "px";
      };
      const kOf = e => { const t = e.target.closest && e.target.closest("[data-k]"); return t ? +t.dataset.k : -1; };
      svg.addEventListener("pointermove", e => { if (e.pointerType !== "touch") show(kOf(e)); });
      svg.addEventListener("pointerleave", e => { if (e.pointerType !== "touch") show(-1); });
      svg.addEventListener("click", e => {
        const ix = kOf(e), touch = e.pointerType === "touch" || (e.sourceCapabilities && e.sourceCapabilities.firesTouchEvents);
        if (ix < 0) { show(-1); return; }
        if (touch && ix !== cur) { show(ix); return; }
        if (pickable(items[ix].a3)) o.onPick(items[ix].a3);
      });
      // keyboard: one button per country with a pick, in left-to-right order; focus shows the card, Enter opens the pin
      const keys = root.querySelector(".wm-keys"), seen = new Set();
      keys.style.top = (top0 + band) + "px";
      items.map((it, ix) => ({ it, ix })).filter(({ it }) => !it.ant && pickable(it.a3) && !seen.has(it.a3) && seen.add(it.a3))
        .sort((a, b) => a.it.xy[0] - b.it.xy[0]).forEach(({ it, ix }) => {
          const p = byCC[it.a3], b = document.createElement("button");
          b.type = "button"; b.className = "wm-key"; b.style.left = it.xy[0] + "px"; b.style.top = it.xy[1] + "px";
          b.setAttribute("aria-label", p ? `${p.country}: ${p.name}` : it.name);
          b.addEventListener("focus", () => show(ix, true)); b.addEventListener("blur", () => show(-1));
          b.addEventListener("click", () => o.onPick(it.a3));
          keys.appendChild(b);
        });
      if (o.onReady) o.onReady();
    };

    const ro = new ResizeObserver(() => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { if (el.clientWidth !== W || el.clientHeight !== H) draw(); }); });
    load(o).then(world => { if (dead) return; P = world.__wm || (world.__wm = prepare(world)); draw(); ro.observe(el); })
      .catch(err => { if (!dead) root.textContent = "The map could not load."; console.error(err); });
    return { destroy() { dead = true; ro.disconnect(); cancelAnimationFrame(raf); root.remove(); } };
  }

  window.WorldMap = { render };
})();
