/* Foreign Property Screener.

   One row per market, every factor a column, filter and sort by any of them.

   The thing this page knows that the usual "best countries to buy abroad" list
   does not: what the destination charges a NON-RESIDENT, and what it charges
   after a ten-year hold rather than at the headline rate. Several markets stop
   taxing the gain entirely once a property has been held five years, which no
   headline table shows. Those rates are read off PwC and carried in
   rates_pwc.json; markets without them are marked.

   Charts derive their viewBox from the rendered container so one SVG unit is
   one CSS pixel. A fixed viewBox scaled into a phone shrinks every label with
   it, and the failure is silent: font-size still reports its declared value
   while the eye gets a third of it. */

const $ = id => document.getElementById(id);
const fmtMoney = v => v == null ? "" : "A$" + Math.round(v).toLocaleString("en-AU");
const fmtK = v => v == null ? "" : "A$" + Math.round(v / 1000) + "k";
const pc = v => v == null ? "" : (+v).toFixed(1) + "%";

let DATA = null, MAP = null, PICKED = null, SORT = { key: "ease", dir: -1 };

/* Columns. `get` pulls the value, `show` renders it, `num` marks it plottable.
   Order here is the order on screen. */
const COLS = [
  { key: "country", label: "Market", show: c => c.country, align: "left" },
  { key: "ease", label: "Ease", num: true, show: c => easeCell(c) },
  { key: "price_aud", label: "Entry", num: true, show: c => fmtK(c.price_aud), unit: "A$" },
  { key: "gross_yield", label: "Gross yield", num: true, show: c => pc(c.gross_yield), unit: "%" },
  { key: "net_yield", label: "Net yield", num: true, show: c => pc(c.net_yield), unit: "%" },
  { key: "rent_tax", label: "Tax on rent", num: true, show: c => taxCell(c, "rent"), unit: "%" },
  { key: "gain_tax", label: "Tax on gain", num: true, show: c => taxCell(c, "cgt"), unit: "%" },
  { key: "purchase_costs", label: "Buying costs", num: true, show: c => pc(c.purchase_costs), unit: "%" },
  { key: "months_to_sell", label: "Months to sell", num: true, show: c => c.months_to_sell ?? "" },
  { key: "price_to_income", label: "Price to income", num: true, show: c => c.price_to_income ?? "" },
  { key: "property_rights", label: "Property rights", num: true, show: c => c.property_rights ?? "" },
  { key: "cpi_score", label: "Corruption score", num: true, show: c => c.cpi_score ?? "" },
  { key: "pop_growth", label: "Population growth", num: true, show: c => pc(c.pop_growth), unit: "%" },
  { key: "gdp_per_capita", label: "GDP per head", num: true, show: c => c.gdp_per_capita ? "$" + Math.round(c.gdp_per_capita / 1000) + "k" : "" },
  { key: "fx_vol", label: "Currency swing", num: true, show: c => pc(c.fx_vol), unit: "%" },
  { key: "sp_rating", label: "Credit rating", show: c => c.sp_rating },
];

/* The two tax columns are the point of the page, so they are sortable numbers
   rather than the source's prose. A rate that cannot be reduced to one number
   sorts last rather than as zero, which would rank "unknown" as "tax free". */
const rate = (c, kind) => {
  const r = kind === "rent" ? c.rent_rate : c.cgt_rate;
  const basis = kind === "rent" ? c.rent_basis : c.cgt_basis;
  const usable = kind === "rent"
    ? ["gain", "gross", "net", "exempt"].includes(basis)
    : ["gain", "exempt", "none"].includes(basis);
  return usable && r != null ? r : null;
};

function val(c, key) {
  if (key === "rent_tax") return rate(c, "rent");
  if (key === "gain_tax") return rate(c, "cgt");
  return c[key];
}

function taxCell(c, kind) {
  const r = rate(c, kind);
  if (r === 0) return `<span class="tax-nil">none</span>`;
  if (r != null) return pc(r);
  return `<span class="tax-unknown" title="The source gives a schedule or a choice of regimes, not one rate">schedule</span>`;
}

function easeCell(c) {
  if (c.ease == null) return "";
  return `<span class="ease"><span class="ease-bar"><i style="width:${c.ease}%"></i></span>${c.ease}</span>`;
}

/* ---------- filtering ---------- */

function filters() {
  return {
    ease: +$("f-ease").value,
    yield: +$("f-yield").value,
    price: +$("f-price").value,
    own: $("f-own").value,
    visa: $("f-visa").value,
    repat: $("f-repat").value,
  };
}

function passes(c, f) {
  if ((c.ease ?? 0) < f.ease) return false;
  if ((c.net_yield ?? 0) < f.yield) return false;
  if ((c.price_aud ?? 0) > f.price) return false;
  const part = k => c.ease_parts?.[k]?.score ?? -1;
  if (f.own && part("ownership") < +f.own) return false;
  if (f.visa && part("visa") < +f.visa) return false;
  if (f.repat && part("repatriation") < +f.repat) return false;
  return true;
}

/* ---------- chart plumbing ---------- */

function frame(svg, height) {
  const w = Math.max(240, svg.getBoundingClientRect().width || svg.parentNode.getBoundingClientRect().width);
  svg.setAttribute("viewBox", `0 0 ${w} ${height}`);
  svg.setAttribute("height", height);
  svg.textContent = "";
  return w;
}

const SVGNS = "http://www.w3.org/2000/svg";
function el(parent, name, attrs, text) {
  const n = document.createElementNS(SVGNS, name);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (text != null) n.textContent = text;
  parent.appendChild(n);
  return n;
}

function showReadout(box, fig, ev, html) {
  box.innerHTML = html;
  box.hidden = false;
  if (window.innerWidth <= 620) {
    box.style.position = "static"; box.style.left = box.style.top = "";
    return;
  }
  box.style.position = "absolute";
  const fr = fig.getBoundingClientRect(), br = box.getBoundingClientRect();
  let x = ev.clientX - fr.left + 14, y = ev.clientY - fr.top + 14;
  if (x + br.width > fr.width) x = ev.clientX - fr.left - br.width - 14;
  if (y + br.height > fr.height) y = fr.height - br.height - 2;
  box.style.left = Math.max(0, x) + "px";
  box.style.top = Math.max(0, y) + "px";
}

/* ---------- the map ----------

   Equirectangular, which is the projection you get for free by treating
   longitude and latitude as x and y. It stretches the poles badly, and for a
   map whose job is "which country is this" rather than "how big is it" that is
   the right trade: no projection maths, no library, and every market lands
   where a reader expects it. Antarctica is cropped because it is a third of the
   height and none of the subject.

   Colour runs light to dark on one hue. A market with no figure for the chosen
   factor is left the same grey as the rest of the world and said so in the key,
   because colouring it at the bottom of the ramp would claim a value. */

const RAMP = ["#dbe6f0", "#b3cbe2", "#89aed1", "#5f90bf", "#3a71a8", "#22548a"];

function colourFor(v, lo, hi, invert) {
  if (v == null || v === "" || !isFinite(v)) return null;
  let t = hi === lo ? 0.5 : (v - lo) / (hi - lo);
  if (invert) t = 1 - t;
  return RAMP[Math.max(0, Math.min(RAMP.length - 1, Math.floor(t * RAMP.length)))];
}

/* Factors where a BIG number is the worse outcome, so the ramp is flipped and
   dark always means "more of what you want". Without this the map would show
   the most expensive and most corrupt markets in the strongest colour. */
const INVERT = new Set(["price_aud", "purchase_costs", "months_to_sell", "price_to_income",
                        "rent_tax", "gain_tax", "fx_vol"]);

function drawMap(shown) {
  const svg = $("map"), fig = svg.parentNode, box = $("map-readout");
  if (!MAP) return;
  const key = $("map-metric").value;
  const col = COLS.find(c => c.key === key);
  const narrow = window.innerWidth <= 620;

  // 2:1 is equirectangular's natural ratio; cropping Antarctica takes the
  // bottom off, so the drawn band is 84N to 58S.
  const W = frame(svg, 0);
  const LAT0 = 84, LAT1 = -58;
  const H = Math.round(W * (LAT0 - LAT1) / 360);
  frame(svg, H);
  const X = lon => (lon + 180) / 360 * W;
  const Y = lat => (LAT0 - lat) / (LAT0 - LAT1) * H;

  const inSet = new Map(shown.map(c => [c.country, c]));
  const vals = shown.map(c => val(c, key)).filter(v => v != null && v !== "" && isFinite(v)).map(Number);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const invert = INVERT.has(key);

  const path = rings => rings.map(r =>
    "M" + r.map(pt => X(pt[0]).toFixed(1) + " " + Y(pt[1]).toFixed(1)).join("L") + "Z").join(" ");

  // Everything grey first, then the markets over it, so a market border is
  // never hidden under a neighbour drawn later.
  MAP.features.forEach(f => {
    if (f.m && inSet.has(f.m)) return;
    el(svg, "path", { d: path(f.r), class: "map-land" });
  });

  MAP.features.forEach(f => {
    const c = f.m && inSet.get(f.m);
    if (!c) return;
    const fill = colourFor(val(c, key), lo, hi, invert);
    const node = el(svg, "path", {
      d: path(f.r), class: "map-mkt" + (c.country === PICKED ? " picked" : ""),
      fill: fill || "var(--map-land)",
    });
    bindMarket(node, c, col, box, fig);
  });

  (MAP.points || []).forEach(pt => {
    const c = inSet.get(pt.m);
    if (!c) return;
    const fill = colourFor(val(c, key), lo, hi, invert);
    const node = el(svg, "circle", {
      cx: X(pt.p[0]), cy: Y(pt.p[1]), r: c.country === PICKED ? 6 : 4.5,
      class: "map-dot", fill: fill || "var(--map-land)",
    });
    bindMarket(node, c, col, box, fig);
  });

  const scale = $("map-scale");
  const fmtEnd = v => col.unit === "A$" ? fmtK(v) : (Math.abs(v) >= 100 ? Math.round(v) : (+v).toFixed(1)) + (col.unit === "%" ? "%" : "");
  const ramp = (invert ? [...RAMP].reverse() : RAMP).map(c => `<i style="background:${c}"></i>`).join("");
  const anyMissing = shown.some(c => { const v = val(c, key); return v == null || v === "" || !isFinite(v); });
  scale.innerHTML = `<span>${fmtEnd(lo)}</span><span class="ramp">${ramp}</span><span>${fmtEnd(hi)}</span>`
    + (anyMissing ? `<span class="none"><i></i>no figure</span>` : "");
}

function bindMarket(node, c, col, box, fig) {
  node.style.cursor = "pointer";
  const v = val(c, col.key);
  const shownVal = v == null || v === "" ? "no figure" :
    (col.unit === "A$" ? fmtK(v) : (Math.abs(v) >= 100 ? Math.round(v) : (+v).toFixed(1)) + (col.unit === "%" ? "%" : ""));
  node.addEventListener("mousemove", ev => showReadout(box, fig, ev,
    `<strong>${c.country}</strong><span class="num">${col.label}: ${shownVal}</span><br>
     <span class="num">Ease ${c.ease}</span>`));
  node.addEventListener("mouseleave", () => { box.hidden = true; });
  node.addEventListener("click", () => { PICKED = c.country === PICKED ? null : c.country; render(); });
}

/* ---------- the scatter ---------- */

function drawScatter(shown, all) {
  const svg = $("scatter"), fig = svg.parentNode, box = $("scatter-readout");
  const narrow = window.innerWidth <= 620;
  const xKey = $("x-axis").value, yKey = $("y-axis").value;
  const xCol = COLS.find(c => c.key === xKey), yCol = COLS.find(c => c.key === yKey);

  const H = narrow ? 300 : 380, W = frame(svg, H);
  const L = narrow ? 44 : 56, R = 16, T = 14, B = 52;
  const plotW = Math.max(60, W - L - R), plotH = H - T - B;

  const pts = shown.map(c => ({ c, x: val(c, xKey), y: val(c, yKey) }))
                   .filter(p => p.x != null && p.y != null && p.x !== "" && p.y !== "");
  const missing = shown.length - pts.length;

  if (!pts.length) {
    el(svg, "text", { x: W / 2, y: H / 2, "text-anchor": "middle", fill: "var(--ink-faint)", "font-size": 13 },
       "Nothing to plot with those two factors.");
    $("scatter-note").textContent = "";
    return;
  }

  const xs = pts.map(p => +p.x), ys = pts.map(p => +p.y);
  const pad = (a, b) => { const d = (b - a) || Math.abs(a) || 1; return [a - d * 0.08, b + d * 0.08]; };
  const [x0, x1] = pad(Math.min(...xs), Math.max(...xs));
  const [y0, y1] = pad(Math.min(...ys), Math.max(...ys));
  const X = v => L + ((v - x0) / (x1 - x0)) * plotW;
  const Y = v => T + plotH - ((v - y0) / (y1 - y0)) * plotH;
  const fmtAxis = (v, col) => col.unit === "A$" ? fmtK(v) : (Math.abs(v) >= 100 ? Math.round(v) : (+v).toFixed(1)) + (col.unit === "%" ? "%" : "");

  for (let i = 0; i <= 4; i++) {
    const v = y0 + (y1 - y0) * (i / 4);
    el(svg, "line", { x1: L, y1: Y(v), x2: L + plotW, y2: Y(v), stroke: "var(--rule)", "stroke-width": 1 });
    el(svg, "text", { x: L - 7, y: Y(v) + 3.6, "text-anchor": "end", fill: "var(--ink-faint)", "font-size": narrow ? 10 : 11 }, fmtAxis(v, yCol));
  }
  for (let i = 0; i <= 4; i++) {
    const v = x0 + (x1 - x0) * (i / 4);
    el(svg, "text", {
      x: X(v), y: H - B + 20, "text-anchor": i === 0 ? "start" : i === 4 ? "end" : "middle",
      fill: "var(--ink-faint)", "font-size": narrow ? 10 : 11,
    }, fmtAxis(v, xCol));
  }
  el(svg, "text", { x: L + plotW / 2, y: H - 6, "text-anchor": "middle", fill: "var(--ink-faint)", "font-size": narrow ? 11 : 12 }, xCol.label);
  el(svg, "text", {
    x: 13, y: T + plotH / 2, "text-anchor": "middle", fill: "var(--ink-faint)",
    "font-size": narrow ? 11 : 12, transform: `rotate(-90 13 ${T + plotH / 2})`,
  }, yCol.label);

  // Medians, so a point reads as "expensive for what it yields" rather than
  // just "somewhere in a cloud". Four quadrants beats thirty-four dots.
  const med = a => { const b = [...a].sort((x, y) => x - y); return b[b.length >> 1]; };
  const mx = med(xs), my = med(ys);
  el(svg, "line", { x1: X(mx), y1: T, x2: X(mx), y2: T + plotH, stroke: "var(--rule)", "stroke-width": 1, "stroke-dasharray": "4 4" });
  el(svg, "line", { x1: L, y1: Y(my), x2: L + plotW, y2: Y(my), stroke: "var(--rule)", "stroke-width": 1, "stroke-dasharray": "4 4" });

  // Labels are placed after the dots and skipped where they would collide with
  // one already placed, so a crowded corner loses its labels rather than
  // turning into a smear. The dot is still hoverable either way.
  const placed = [];
  const fits = (x, y, w, h) => !placed.some(r => x < r.x + r.w && r.x < x + w && y < r.y + r.h && r.y < y + h);

  pts.forEach(p => {
    const sel = p.c.country === PICKED;
    const g = el(svg, "g", { style: "cursor:pointer" });
    el(g, "circle", {
      cx: X(+p.x), cy: Y(+p.y), r: sel ? 7 : 5,
      fill: sel ? "var(--accent)" : "var(--dot)",
      stroke: "var(--panel)", "stroke-width": 1.5,
    });
    // A hit area bigger than the dot, so a 5px target is not a 5px target.
    const hit = el(g, "circle", { cx: X(+p.x), cy: Y(+p.y), r: 13, fill: "transparent" });
    hit.addEventListener("mousemove", ev => showReadout(box, fig, ev,
      `<strong>${p.c.country}</strong>
       <span class="num">${xCol.label}: ${fmtAxis(+p.x, xCol)}</span><br>
       <span class="num">${yCol.label}: ${fmtAxis(+p.y, yCol)}</span>`));
    hit.addEventListener("mouseleave", () => { box.hidden = true; });
    hit.addEventListener("click", () => { PICKED = p.c.country === PICKED ? null : p.c.country; render(); });

    if (!narrow) {
      const text = p.c.country;
      // Estimated, because the width is needed before the text exists. The
      // estimate is deliberately generous: a label wrongly skipped costs
      // nothing, a label wrongly kept overlaps its neighbour.
      const w = text.length * 6.4 + 12, h = 15;
      const lx = X(+p.x) + 9, ly = Y(+p.y) - 6;
      if (sel || fits(lx, ly - h, w, h)) {
        placed.push({ x: lx, y: ly - h, w, h });
        el(svg, "text", {
          x: lx, y: ly + 4, fill: sel ? "var(--ink)" : "var(--ink-soft)",
          "font-size": 10.5, "font-weight": sel ? 700 : 400,
          "paint-order": "stroke", stroke: "var(--panel)", "stroke-width": 3, "stroke-linejoin": "round",
        }, text);
      }
    }
  });

  $("scatter-note").textContent = missing
    ? `${missing} of the ${shown.length} markets shown have no figure for one of these and are not plotted.`
    : "";
}

/* ---------- the table ---------- */

function drawTable(shown) {
  const head = $("grid-head"), body = $("grid-body");
  head.innerHTML = "";
  COLS.forEach(col => {
    const th = document.createElement("th");
    th.textContent = col.label;
    th.className = (col.align === "left" ? "l " : "") + (SORT.key === col.key ? "sorted" : "");
    if (SORT.key === col.key) th.dataset.dir = SORT.dir < 0 ? "desc" : "asc";
    th.tabIndex = 0;
    const sort = () => {
      SORT = SORT.key === col.key ? { key: col.key, dir: -SORT.dir } : { key: col.key, dir: col.key === "country" ? 1 : -1 };
      render();
    };
    th.addEventListener("click", sort);
    th.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); sort(); } });
    head.appendChild(th);
  });

  body.innerHTML = "";
  shown.forEach(c => {
    const tr = document.createElement("tr");
    tr.className = c.country === PICKED ? "picked" : "";
    COLS.forEach(col => {
      const td = document.createElement("td");
      td.innerHTML = col.show(c) ?? "";
      if (col.align === "left") td.className = "l";
      tr.appendChild(td);
    });
    tr.addEventListener("click", () => { PICKED = c.country === PICKED ? null : c.country; render(); });
    body.appendChild(tr);

    if (c.country === PICKED) {
      const det = document.createElement("tr");
      det.className = "detail";
      const td = document.createElement("td");
      td.colSpan = COLS.length;
      td.appendChild(detail(c));
      det.appendChild(td);
      body.appendChild(det);
    }
  });
}

function detail(c) {
  const wrap = document.createElement("div");
  wrap.className = "detail-inner";

  const parts = document.createElement("div");
  parts.className = "ease-parts";
  const order = ["ownership", "visa", "repatriation", "liquidity", "costs", "rights"];
  const names = {
    ownership: "Who can own", visa: "Residency", repatriation: "Money out",
    liquidity: "Time to sell", costs: "Cost to buy", rights: "Property rights",
  };
  order.forEach(k => {
    const p = c.ease_parts?.[k];
    if (!p || p.score == null) return;
    const d = document.createElement("div");
    d.className = "ease-part s" + p.score;
    d.innerHTML = `<span class="ep-name"></span><span class="ep-label"></span>`;
    d.querySelector(".ep-name").textContent = names[k];
    d.querySelector(".ep-label").textContent = p.label;
    parts.appendChild(d);
  });
  wrap.appendChild(parts);

  const facts = document.createElement("dl");
  facts.className = "facts";
  const add = (dt, dd) => {
    if (!dd) return;
    const d = document.createElement("div");
    d.innerHTML = "<dt></dt><dd></dd>";
    d.querySelector("dt").textContent = dt;
    d.querySelector("dd").textContent = dd;
    facts.appendChild(d);
  };
  add("Tax on rent, as the source puts it", c.rental_tax_text);
  add("Tax on the gain", c.cgt_text);
  add("After a ten-year hold", c.verified ? c.cgt_note : "Not checked against PwC; workbook figure");
  add("Estate or inheritance tax", c.estate_text);
  add("Ownership rules", c.ownership);
  add("Residency pathway", c.visa);
  add("Getting money out", c.repatriation);
  add("Obstacles", c.obstacles);
  wrap.appendChild(facts);

  if (c.profile) {
    const p = document.createElement("p");
    p.className = "profile";
    p.textContent = c.profile;
    wrap.appendChild(p);
  }
  return wrap;
}

/* The table hides its scrollbar, so something else has to say there is more to
   the right. The fade appears only while there is somewhere to scroll to and
   goes when you reach the end, which a permanent gradient would not. */
function fadeHint() {
  const sc = $("table-scroll"), wrap = $("table-wrap");
  if (!sc || !wrap) return;
  const more = sc.scrollWidth - sc.clientWidth - sc.scrollLeft > 2;
  wrap.classList.toggle("more", more);
}

/* ---------- render ---------- */

function render() {
  const f = filters();
  $("f-ease-out").textContent = f.ease ? f.ease : "any";
  $("f-yield-out").textContent = f.yield ? f.yield.toFixed(1) + "%" : "any";
  $("f-price-out").textContent = f.price >= 650000 ? "any" : fmtK(f.price);

  const shown = DATA.countries.filter(c => passes(c, f));
  const col = COLS.find(c => c.key === SORT.key) || COLS[1];
  shown.sort((a, b) => {
    const av = val(a, SORT.key), bv = val(b, SORT.key);
    // Missing values sort last whichever way the column is pointing, so an
    // unknown rate never reads as the best rate.
    if (av == null || av === "") return 1;
    if (bv == null || bv === "") return -1;
    if (typeof av === "string" || typeof bv === "string") return String(av).localeCompare(String(bv)) * SORT.dir;
    return (av - bv) * SORT.dir;
  });

  $("count").textContent = shown.length === DATA.countries.length
    ? `All ${shown.length} markets.`
    : `${shown.length} of ${DATA.countries.length} markets match.`;

  drawTable(shown);
  drawMap(shown);
  drawScatter(shown, DATA.countries);
  fadeHint();

  const verified = DATA.countries.filter(c => c.verified).length;
  $("note-tax").textContent =
    `Tax on rent and on the gain is what the destination charges a non-resident, read off PwC's country guides for `
    + `${verified} of the ${DATA.countries.length} markets and taken for a ten-year hold. That is not the headline rate: `
    + `Belgium, Italy and Poland stop taxing the gain once a property has been held five years, and the Netherlands `
    + `does not tax it at all. Where the source gives a schedule or a choice of regimes rather than one number, the `
    + `column says so instead of picking one.`;
}

/* ---------- boot ---------- */

Promise.all([
  fetch("data.json").then(r => r.json()),
  fetch("world.json").then(r => r.json()).catch(() => null),
])
  .then(([d, m]) => {
    DATA = d;
    MAP = m;

    const numeric = COLS.filter(c => c.num);
    const mm = $("map-metric");
    numeric.forEach(c => {
      const o = document.createElement("option");
      o.value = c.key; o.textContent = c.label;
      if (c.key === "ease") o.selected = true;
      mm.appendChild(o);
    });
    mm.addEventListener("change", render);

    [["x-axis", "net_yield"], ["y-axis", "ease"]].forEach(([id, dflt]) => {
      const sel = $(id);
      numeric.forEach(c => {
        const o = document.createElement("option");
        o.value = c.key; o.textContent = c.label;
        if (c.key === dflt) o.selected = true;
        sel.appendChild(o);
      });
      sel.addEventListener("change", render);
    });

    const tb = $("sources");
    (d.sources || []).forEach(s => {
      const tr = document.createElement("tr");
      const a = s.url ? `<a href="${s.url.startsWith("http") ? s.url : "https://" + s.url}" rel="noopener">${s.name}</a>` : s.name;
      tr.innerHTML = `<td>${s.measure}</td><td>${a}</td><td></td>`;
      tr.lastElementChild.textContent = s.caveat || "";
      tb.appendChild(tr);
    });

    ["f-ease", "f-yield", "f-price", "f-own", "f-visa", "f-repat"]
      .forEach(id => $(id).addEventListener("input", render));

    const want = new URL(location).searchParams.get("c");
    if (want && d.countries.some(c => c.country === want)) PICKED = want;

    render();
    $("table-scroll").addEventListener("scroll", fadeHint, { passive: true });
    let t;
    addEventListener("resize", () => { clearTimeout(t); t = setTimeout(render, 120); });
  })
  .catch(() => {
    document.querySelector("main").insertAdjacentHTML("afterbegin",
      '<p class="sub">The market data did not load. Try a refresh.</p>');
  });
