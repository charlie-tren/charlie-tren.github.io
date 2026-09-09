/* Property Atlas.

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
  { key: "ease", label: "Ease", num: true, align: "left", show: c => easeCell(c) },
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
/* The basis allowlist that used to live here threw away every rate resolve_taxes
   recovered: it accepted gain/gross/net/exempt and the recovered ones are flat,
   wht and proceeds, so Albania's 15% rendered as a word again. It is not needed
   any more - `_rate` is null exactly when no single rate was stated, decided in
   one place - and a second opinion about that here is how the two disagreed. */
/* Sorts on the one rate where there is one and on the BOTTOM of the range where
   there is not, so a cell reading 15-45% ranks with the 15s. The bottom is a
   figure the source states; a midpoint is not, and this project has already
   shipped an invented 4.5 once. */
const rate = (c, kind) => {
  const r = kind === "rent" ? c.rent_rate : c.cgt_rate;
  if (r != null) return r;
  const low = kind === "rent" ? c.rent_low : c.cgt_low;
  return low ?? null;
};

function val(c, key) {
  if (key === "rent_tax") return rate(c, "rent");
  if (key === "gain_tax") return rate(c, "cgt");
  return c[key];
}

//: Why a cell shows a range rather than one rate. There is no vocabulary to
//: learn any more: the cell shows the source's own figures, and this only says
//: what shape they are.
const RANGE_WHY = {
  progressive: "A band. Which rate applies depends on the owner's other income in that market.",
  deemed: "Charged on a deemed return rather than on the rent actually received.",
  regimes: "Two regimes, and the seller or landlord elects between them.",
  schedule: "The source gives a schedule rather than one rate.",
  unclear: "The source does not reduce to one rate."
};

//: Where the number came from, on hover, because three sources now feed this
//: column and a reader should be able to tell which one they are reading.
const RATE_WHY = {
  pwc: "PwC's country guide for this market.",
  workbook: "Read off the market's own tax note. The rate a non-resident actually pays where the guide gave a choice.",
  text: "Read off the market's own tax note."
};

//: WHAT THE RATE IS CHARGED ON. Egypt's 2.5% is 2.5% of the sale price and
//: Spain's 24% is 24% of gross rent; a column of percentages hides that, so the
//: hover says it and `.tax-basis` marks the ones that are not on the obvious base.
const BASIS_WHY = {
  gain: "of the realised gain",
  proceeds: "of the sale price, not of the gain",
  gross: "of gross rent, with no deduction",
  net: "of net rent, after deductions",
  wht: "withheld at source, on the gross amount",
  flat: "a flat rate",
  exempt: "not taxed"
};

/* ONE FORMAT FOR EVERY TAX CELL. There used to be three: bold accent for
   "none", small faint italic for the words, plain for a number - so a column of
   percentages had three typographic registers in it and, as Charlie put it, the
   formatting was different without saying why. Every cell is now a figure in the
   same face; the only mark is a dotted underline where the base is not the
   obvious one, and it promises the hover it has. */
function taxCell(c, kind) {
  const single = kind === "rent" ? c.rent_rate : c.cgt_rate;
  const basis = c[kind + "_basis"];
  const odd = basis === "proceeds" || basis === "gross" || basis === "deemed";

  if (single === 0) {
    return `<span class="tax-cell tax-nil" title="This market does not tax it.">0%</span>`;
  }
  const text = single != null ? pc(single) : (c[kind + "_range"] || "");
  if (!text) return "";
  const why = single != null
    ? [BASIS_WHY[basis], RATE_WHY[c[kind + "_src"]]].filter(Boolean).join(". ")
    : [RANGE_WHY[basis], BASIS_WHY[basis]].filter(Boolean).join(" ");
  return `<span class="tax-cell${odd ? " tax-basis" : ""}" title="${text}. ${why}">${text}</span>`;
}

function easeCell(c) {
  if (c.ease == null) return "";
  return `<span class="ease"><span class="ease-bar"><i style="width:${c.ease}%"></i></span>${c.ease}</span>`;
}

/* One slider's readout and track fill. */
function setSlider(name, text, active) {
  const input = $("f-" + name);
  const out = $("f-" + name + "-out");
  out.textContent = text;
  const box = input.closest(".control");
  box.classList.toggle("on", active);
  const min = +input.min, max = +input.max;
  const pct = max === min ? 0 : ((+input.value - min) / (max - min)) * 100;
  input.style.setProperty("--pct", pct.toFixed(2) + "%");
}

/* ---------- filtering ---------- */

const PMIN = 75000, PMAX = 650000;

function filters() {
  return {
    ease: +$("f-ease").value,
    yield: +$("f-yield").value,
    // The slider runs left-to-right like the other two, so its raw value is a
    // POSITION and the cap is its mirror: hard left is the top of the range (no
    // filter), hard right is the cheapest. PMIN + PMAX is the axis it reflects in.
    price: PMIN + PMAX - +$("f-price").value,
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

  /* NAME EVERY MARKET THAT HAS ROOM FOR ITS NAME.
     There used to be a cutoff here: at more than twelve shown, nothing was
     labelled at all, on the reasoning that the labels collide into a smear.
     Charlie: "why do country names disappear when there's too many". Because of
     that line - and it was belt-and-braces over a collision test thirty lines
     below that already skips any label overlapping one already placed. So the
     smear could not happen anyway, and the cutoff was throwing away the United
     States, Brazil, Turkey and every other market with space around it in order
     to prevent something the placement loop prevents.
     Drawn PICKED first and then alphabetically, so which names win is fixed
     rather than following whatever the table happens to be sorted by. */
  const named = [...shown].sort((a, b) =>
    (b.country === PICKED) - (a.country === PICKED) || a.country.localeCompare(b.country));
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
  // Never the same figure twice. The second line is a fixed companion - ease, unless
  // ease is already what the map is shaded by, in which case net yield, because a
  // readout that repeats itself is worse than a readout with one line.
  const second = col.key === "ease"
    ? { label: "Net yield", text: c.net_yield == null ? "no figure" : (+c.net_yield).toFixed(1) + "%" }
    : { label: "Ease", text: c.ease == null ? "no figure" : c.ease + "/100" };
  node.addEventListener("mousemove", ev => showReadout(box, fig, ev,
    `<strong>${c.country}</strong><span class="num">${col.label}: ${shownVal}</span><br>
     <span class="num">${second.label}: ${second.text}</span>`));
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
    if (SORT.key === col.key) {
      th.dataset.dir = SORT.dir < 0 ? "desc" : "asc";
      th.setAttribute("aria-sort", SORT.dir < 0 ? "descending" : "ascending");
    } else {
      th.setAttribute("aria-sort", "none");
    }
    th.setAttribute("role", "columnheader");
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
  add("Where these rates come from",
      [["Rent", c.rent_src, c.rent_rate], ["Gain", c.cgt_src, c.cgt_rate]]
        .map(([what, src, r]) => `${what}: ` + (
          r == null ? "no single rate stated"
          : src === "pwc" ? "PwC's country guide"
          : src === "workbook" ? "the market's own tax note, where PwC gave a choice"
          : "the market's own tax note"))
        .join(". ") + ".");
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
  // THE FILL IS THE PART YOU HAVE EXCLUDED, measured from the end that means
  // "no filter". Two of these sliders are minimums and one is a maximum, so with
  // a plain accent-color the price slider sat FULL while the other two sat empty
  // and all three meant the same thing: any. Painting the excluded region
  // instead makes an untouched bar an empty bar, whichever way it runs.
  // `.on` marks a filter that is actually doing something - the readout is quiet
  // until then, because three bold "any"s were the loudest thing in the bar.
  setSlider("ease",  f.ease  ? f.ease + "/100" : "any", !!f.ease);
  setSlider("yield", f.yield ? f.yield.toFixed(1) + "%" : "any", !!f.yield);
  setSlider("price", f.price >= PMAX ? "any" : fmtK(f.price), f.price < PMAX);

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

  drawTable(shown);
  drawMap(shown);
  fadeHint();

  // THE CALC, not a list of its inputs. Charlie: "break down this calc more".
  // Derived from the data rather than typed, so the divisor cannot drift from the
  // number of parts, and test_data.py asserts the formula still reproduces every
  // published score.
  const parts = Object.keys(DATA.countries[0].ease_parts);
  const cap = Math.max(...DATA.countries.flatMap(
    c => Object.values(c.ease_parts).map(p => p.score)));
  const names = { ownership: "who may own", visa: "residency from buying",
    repatriation: "getting money out", liquidity: "time to sell",
    costs: "cost to buy", rights: "property rights" };
  EASE_HELP = `Six things a foreign buyer runs into, scored out of 100: `
    + parts.map(k => names[k] || k).join(", ") + `. Open a row for its own six.`;
  const help = $("ease-help");
  if (help.textContent !== EASE_HELP) help.textContent = EASE_HELP;
  $("ease-info").title = EASE_HELP;

  // No Notes entry for this. The i beside the filter carries the same sentence,
  // at the control it describes, and two homes for one formula is the thing the
  // house rule is about.

  $("note-tax").innerHTML =
    `<strong>Tax</strong> is what a non-resident pays on a ten-year hold, from PwC. `
    + `Ranges are theirs.`;
}

/* ---------- boot ---------- */

// The links for the four source rows whose url is the word "Various". A separate
// file because data.json is rebuilt from the workbook and would drop them, and a
// .catch so a missing file costs those four rows their links and nothing else.
let SOURCE_LINKS = {};
//: How old each figure is, keyed by the source row's measure. Every date here is
//: either the edition the source itself names or a bound from the repo's own
//: history - never a restamp, because restamping is how a page claims to be
//: fresher than its data.
let SOURCE_DATES = {};
//: The ease breakdown, derived once in render() and reused by the note, the
//: little i beside the filter, and the line that i opens. Three copies of a
//: formula is three chances for one of them to be the old formula.
let EASE_HELP = "";

Promise.all([
  fetch("data.json").then(r => r.json()),
  fetch("world.json").then(r => r.json()).catch(() => null),
  fetch("sources_links.json").then(r => r.json()).catch(() => ({})),
  fetch("source_dates.json").then(r => r.json()).catch(() => ({})),
])
  .then(([d, m, links, dates]) => {
    DATA = d;
    MAP = m;
    SOURCE_LINKS = links || {};
    SOURCE_DATES = dates || {};

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
      // Four rows carried the word "Various" in their url, because the column
      // really was assembled from several sources - and linkifying that produced
      // href="https://Various", citations that went nowhere on a page whose whole
      // claim is that the numbers were checked. So those four now name each source
      // separately in sources_links.json, every one of them followable, rather
      // than one link standing for three.
      const many = SOURCE_LINKS[s.measure];
      const linkable = /^(https?:\/\/)?[a-z0-9-]+(\.[a-z0-9-]+)+([\/?#]|$)/i.test(s.url || "");
      const href = s.url && s.url.startsWith("http") ? s.url : "https://" + s.url;
      const a = many
        ? many.map(l => `<a href="${l.url}" rel="noopener">${l.name}</a>`).join(", ")
        : linkable ? `<a href="${href}" rel="noopener">${s.name}</a>` : s.name;
      // AS AT. A source that dates itself shows its edition; one that does not
      // shows a dash rather than borrowing its neighbour's date, with the reason
      // on hover. One caveat on this page read "spot rates as at research date"
      // and the research date appeared nowhere at all.
      const dt = SOURCE_DATES[s.measure] || {};
      const when = dt.as_at
        ? `<span title="${dt.how || ""}">${dt.as_at}</span>`
        : `<span class="undated" title="${dt.how || "Not dated by its source."}">not dated</span>`;
      tr.innerHTML = `<td>${s.measure}</td><td>${a}</td><td class="asat">${when}</td><td></td>`;
      // A caveat that only repeats the As at column is the same clutter as a
      // chart caption, so two rows override theirs from source_dates.json.
      tr.lastElementChild.textContent = dt.caveat || s.caveat || "";
      tb.appendChild(tr);
    });


    ["f-ease", "f-yield", "f-price", "f-own", "f-visa", "f-repat"]
      .forEach(id => $(id).addEventListener("input", render));

    /* The i opens the line rather than only carrying a title, because a
       hover-only tooltip is nothing at all on a phone - and this page is checked
       at 390px. The title stays for the pointer, the click is for everyone else. */
    const info = $("ease-info"), help = $("ease-help");
    info.addEventListener("click", () => {
      const open = info.getAttribute("aria-expanded") === "true";
      info.setAttribute("aria-expanded", open ? "false" : "true");
      help.hidden = open;
    });

    const root = document.documentElement, btn = $("theme");
    const paint = () => {
      const dark = root.getAttribute("data-theme") === "dark";
      $("theme-label").textContent = dark ? "Light" : "Dark";
      btn.setAttribute("aria-pressed", dark ? "true" : "false");
      btn.setAttribute("aria-label", dark ? "Switch to the light theme" : "Switch to the dark theme");
    };
    btn.addEventListener("click", () => {
      const dark = root.getAttribute("data-theme") === "dark";
      root.setAttribute("data-theme", dark ? "light" : "dark");
      try { localStorage.setItem("pa-theme", dark ? "light" : "dark"); } catch (e) {}
      paint();
      render();
    });
    paint();

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
