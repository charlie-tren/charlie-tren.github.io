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
/* Nine columns on screen, not sixteen. The rest were readable individually and
   unreadable together: at sixteen every column is narrow, the eye has nothing
   to anchor on, and the ones a reader actually screens by are lost among the
   ones they look up afterwards. Those moved into the expanded row.

   `group` draws a hairline before the column, so the table reads as three
   blocks - what it costs, what it yields, what it is taxed - instead of one
   undifferentiated run of numbers. */
const COLS = [
  { key: "country", label: "Market", show: c => c.country, align: "left" },
  { key: "ease", label: "Ease", num: true, show: c => easeCell(c) },
  { key: "price_aud", label: "Entry", num: true, group: true, show: c => fmtK(c.price_aud), unit: "A$" },
  { key: "purchase_costs", label: "To buy", num: true, show: c => pc(c.purchase_costs), unit: "%" },
  { key: "gross_yield", label: "Gross yield", num: true, group: true, soft: true, show: c => pc(c.gross_yield), unit: "%" },
  { key: "net_yield", label: "Net yield", num: true, soft: true, show: c => pc(c.net_yield), unit: "%" },
  { key: "rent_tax", label: "Tax on rent", num: true, group: true, show: c => taxCell(c, "rent"), unit: "%" },
  { key: "gain_tax", label: "Tax on gain", num: true, show: c => taxCell(c, "cgt"), unit: "%" },
  { key: "months_to_sell", label: "Months to sell", num: true, group: true, show: c => c.months_text || (c.months_to_sell ?? "") },
];

/* Still plottable on the map and still shown when a row is opened, just not
   given a column of their own. */
const EXTRA = [
  { key: "price_to_income", label: "Price to income", num: true },
  { key: "property_rights", label: "Property rights", num: true },
  { key: "cpi_score", label: "Corruption score", num: true },
  { key: "pop_growth", label: "Population growth", num: true, unit: "%" },
  { key: "gdp_per_capita", label: "GDP per head", num: true, unit: "A$" },
  { key: "fx_vol", label: "Currency swing", num: true, unit: "%" },
];
const PLOTTABLE = [...COLS.filter(c => c.num), ...EXTRA];

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
  return `<span class="tax-unknown" title="The source gives a sliding scale or a choice of regimes, not one rate. Open the row for what it says.">scale</span>`;
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

   Robinson. Equirectangular came free by treating longitude and latitude as x
   and y, and it looked it: Canada and Russia smeared across the top, Alaska
   bigger than India, every parallel the same length so the world read as a
   rectangle of countries rather than as a globe. Robinson is a lookup table of
   nineteen latitudes interpolated between - about twenty lines, still no
   library - and it is the projection an atlas would use for exactly this job.

   Antarctica is cropped because it is a third of the height and none of the
   subject.

   Colour runs light to dark on one hue. A market with no figure for the chosen
   factor is left the same grey as the rest of the world and said so in the key,
   because colouring it at the bottom of the ramp would claim a value. */


/* Robinson's published table: the length of each parallel (PX) and its distance
   from the equator (PY), both relative to the equator, every five degrees. */
const PX = [1, .9986, .9954, .99, .9822, .973, .96, .9427, .9216, .8962, .8679,
            .835, .7986, .7597, .7186, .6732, .6213, .5722, .5322];
const PY = [0, .062, .124, .186, .248, .31, .372, .434, .4958, .5571, .6176,
            .6769, .7346, .7903, .8435, .8936, .9394, .9761, 1];

function robinson(lon, lat) {
  const a = Math.min(Math.abs(lat), 90) / 5;
  const i = Math.min(Math.floor(a), 17), t = a - i;
  const px = PX[i] + (PX[i + 1] - PX[i]) * t;
  const py = PY[i] + (PY[i + 1] - PY[i]) * t;
  return [0.8487 * px * (lon * Math.PI / 180), 1.3523 * py * (lat < 0 ? -1 : 1)];
}

/* Read from the stylesheet rather than hardcoded, so the theme owns its own
   colours and dark mode is not a second copy of the ramp living in a script. */
function ramp() {
  const cs = getComputedStyle(document.documentElement);
  const out = [];
  for (let i = 1; i <= 6; i++) {
    const v = cs.getPropertyValue("--ramp" + i).trim();
    if (v) out.push(v);
  }
  return out.length ? out : ["#d5e6e5", "#a8cfd2", "#74b3b8", "#3f9aa2", "#17808a", "#0a5b66"];
}

function colourFor(v, lo, hi, invert, R) {
  if (v == null || v === "" || !isFinite(v)) return null;
  let t = hi === lo ? 0.5 : (v - lo) / (hi - lo);
  if (invert) t = 1 - t;
  return R[Math.max(0, Math.min(R.length - 1, Math.floor(t * R.length)))];
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
  const col = PLOTTABLE.find(c => c.key === key);
  const narrow = window.innerWidth <= 620;

  // The drawn band is 78N to 56S. The projected extent is measured from the
  // projection itself rather than assumed, so changing the crop cannot silently
  // squash the map.
  const W = frame(svg, 0);
  const LAT0 = 78, LAT1 = -56;
  const top = robinson(0, LAT0)[1], bot = robinson(0, LAT1)[1];
  const halfW = robinson(180, 0)[0];
  const H = Math.round(W * (top - bot) / (2 * halfW));
  frame(svg, H);
  const k = W / (2 * halfW);
  const X = (lon, lat) => (robinson(lon, lat)[0] + halfW) * k;
  const Y = (lon, lat) => (top - robinson(lon, lat)[1]) * k;

  const inSet = new Map(shown.map(c => [c.country, c]));
  const vals = shown.map(c => val(c, key)).filter(v => v != null && v !== "" && isFinite(v)).map(Number);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const invert = INVERT.has(key);
  const R = ramp();

  const path = rings => rings.map(r =>
    "M" + r.map(pt => X(pt[0], pt[1]).toFixed(1) + " " + Y(pt[0], pt[1]).toFixed(1)).join("L") + "Z").join(" ");

  // Everything grey first, then the markets over it, so a market border is
  // never hidden under a neighbour drawn later.
  MAP.features.forEach(f => {
    if (f.m && inSet.has(f.m)) return;
    el(svg, "path", { d: path(f.r), class: "map-land" });
  });

  MAP.features.forEach(f => {
    const c = f.m && inSet.get(f.m);
    if (!c) return;
    const fill = colourFor(val(c, key), lo, hi, invert, R);
    const node = el(svg, "path", {
      d: path(f.r), class: "map-mkt" + (c.country === PICKED ? " picked" : ""),
      fill: fill || "var(--map-land)",
    });
    bindMarket(node, c, col, box, fig);
  });

  (MAP.points || []).forEach(pt => {
    const c = inSet.get(pt.m);
    if (!c) return;
    const fill = colourFor(val(c, key), lo, hi, invert, R);
    const node = el(svg, "circle", {
      cx: X(pt.p[0], pt.p[1]), cy: Y(pt.p[0], pt.p[1]), r: c.country === PICKED ? 6 : 4.5,
      class: "map-dot", fill: fill || "var(--map-land)",
    });
    bindMarket(node, c, col, box, fig);
  });

  /* Name the markets when the filter has cut the set down far enough to read.
     Above about a dozen the labels collide into a smear and the map is better
     off silent, so the threshold is the point where naming still helps. */
  const named = shown.length <= 12 ? shown : (PICKED ? shown.filter(c => c.country === PICKED) : []);
  if (named.length) {
    const placed = [];
    const centroid = f => {
      const r = f.r.reduce((a, b) => (a.length > b.length ? a : b));
      const xs = r.map(pt => pt[0]), ys = r.map(pt => pt[1]);
      const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
      const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
      return [X(cx, cy), Y(cx, cy)];
    };
    const spot = new Map();
    MAP.features.forEach(f => { if (f.m) spot.set(f.m, centroid(f)); });
    (MAP.points || []).forEach(pt => spot.set(pt.m, [X(pt.p[0], pt.p[1]), Y(pt.p[0], pt.p[1])]));

    named.forEach(c => {
      const at = spot.get(c.country);
      if (!at) return;
      const w = c.country.length * 5.4 + 8, h = 13;
      const bx = at[0] - w / 2, by = at[1] - 15;
      const clash = placed.some(r => bx < r.x + r.w && r.x < bx + w && by < r.y + r.h && r.y < by + h);
      if (clash && c.country !== PICKED) return;
      placed.push({ x: bx, y: by, w, h });
      el(svg, "text", {
        x: at[0], y: at[1] - 6, "text-anchor": "middle",
        fill: "var(--ink)", "font-size": narrow ? 9.5 : 10.5,
        "font-weight": c.country === PICKED ? 700 : 500,
        "paint-order": "stroke", stroke: "var(--panel)", "stroke-width": 3.2, "stroke-linejoin": "round",
      }, c.country);
    });
  }

  const scale = $("map-scale");
  const fmtEnd = v => col.unit === "A$" ? fmtK(v) : (Math.abs(v) >= 100 ? Math.round(v) : (+v).toFixed(1)) + (col.unit === "%" ? "%" : "");
  const swatches = (invert ? [...R].reverse() : R).map(c => `<i style="background:${c}"></i>`).join("");
  const anyMissing = shown.some(c => { const v = val(c, key); return v == null || v === "" || !isFinite(v); });
  scale.innerHTML = `<span>${fmtEnd(lo)}</span><span class="ramp">${swatches}</span><span>${fmtEnd(hi)}</span>`
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

/* ---------- the table ---------- */

function drawTable(shown) {
  const head = $("grid-head"), body = $("grid-body");
  head.innerHTML = "";
  COLS.forEach(col => {
    const th = document.createElement("th");
    th.textContent = col.label;
    th.className = [col.align === "left" ? "l" : "", col.group ? "grp" : "",
                    col.soft ? "soft" : "", SORT.key === col.key ? "sorted" : ""].filter(Boolean).join(" ");
    // Say which columns are the weak ones IN the header, where a reader deciding
    // whether to trust a number is already looking. The note at the bottom is
    // read by nobody who is mid-comparison.
    if (col.soft) th.title = "Numbeo, user-contributed. The weakest figures here: no agency publishes rental yields across countries, so there is nothing official to check them against.";
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
      td.className = [col.align === "left" ? "l" : "", col.group ? "grp" : ""].filter(Boolean).join(" ");
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
  EXTRA.forEach(x => {
    const v = c[x.key];
    if (v == null || v === "") return;
    add(x.label, x.unit === "%" ? pc(v) : x.key === "gdp_per_capita" ? "$" + Math.round(v / 1000) + "k" : String(v));
  });
  add("Credit rating", c.sp_rating);
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

  const mCol = PLOTTABLE.find(x => x.key === $("map-metric").value);
  $("map-sub").textContent = shown.length <= 12
    ? `${shown.length} markets, shaded by ${mCol.label.toLowerCase()}.`
    : `All ${shown.length} shaded by ${mCol.label.toLowerCase()}. Filter down to a dozen to see them named.`;

  drawTable(shown);
  drawMap(shown);
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

    const numeric = PLOTTABLE;
    const mm = $("map-metric");
    numeric.forEach(c => {
      const o = document.createElement("option");
      o.value = c.key; o.textContent = c.label;
      if (c.key === "ease") o.selected = true;
      mm.appendChild(o);
    });
    mm.addEventListener("change", render);

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
