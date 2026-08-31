/* Absentee. What a property abroad returns after your own country taxes it.

   The arithmetic, in one place:

   A country with a lower tax rate than yours is not a cheaper country to own
   property in. Where your home country taxes worldwide income and gives a
   credit for tax already paid abroad, the credit is capped at what you actually
   paid there, so the foreign rate is a floor and your own rate is the bill. The
   destination's rate only bites when it is HIGHER than yours. That single fact
   is why a ranking built on foreign tax rates ranks the wrong thing.

   Charts derive their viewBox from the rendered container so one SVG unit is
   one CSS pixel. A fixed wide viewBox scaled into a phone shrinks every label
   with it, and the failure is silent: font-size still reports its declared
   value while the eye gets a third of it. */

const N = 10;                 // years
const MER = 0.002;            // index fund fee
const BROKERAGE = 0.001;
const DIST = 0.02;            // index fund distribution yield

const $ = id => document.getElementById(id);
const fmtPc = v => (v >= 0 ? "" : "-") + Math.abs(v).toFixed(1) + "%";
const fmtMoney = v => "A$" + Math.round(v).toLocaleString("en-AU");
const fmtK = v => "A$" + Math.round(v / 1000).toLocaleString("en-AU") + "k";

let DATA = null, PICKED = null;

/* ---------- the model ---------- */

function irr(cf) {
  const npv = r => cf.reduce((s, c, i) => s + c / Math.pow(1 + r, i), 0);
  let lo = -0.95, hi = 3;
  if (npv(lo) * npv(hi) > 0) return null;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    if (npv(lo) * npv(mid) <= 0) hi = mid; else lo = mid;
  }
  return (lo + hi) / 2;
}

/* A foreign rate is only usable where it is charged on the same base we are
   modelling. "2.5% of sale price" and "27% on net gain" are not comparable
   numbers, so the ones charged on proceeds, on a deemed return, or offered as a
   choice of regimes are set aside and the country is named in the notes rather
   than quietly given a rate the source never states. */
const rentUsable = c => ["gain", "gross", "exempt"].includes(c.foreign_rental_basis);
const cgtUsable  = c => ["gain", "exempt"].includes(c.foreign_cgt_basis);
const needsReview = c => !rentUsable(c) || !cgtUsable(c);

function model(c, s, fxFall, taxFree) {
  const g = s.growth / 100;
  const fx = Math.pow(1 - (fxFall || 0), 1 / N) - 1;   // annual currency drift
  const pc = c.purchase_costs / 100, sc = c.sale_costs / 100;

  const fRent = !taxFree && rentUsable(c) && c.foreign_rental_tax != null ? c.foreign_rental_tax / 100 : 0;
  const fCgt  = !taxFree && cgtUsable(c)  && c.foreign_cgt != null        ? c.foreign_cgt / 100        : 0;

  // Credit method: the total is whichever rate is higher, never the sum.
  const rentRate = taxFree ? 0 : s.worldwide ? Math.max(fRent, s.mtr / 100) : fRent;
  const cgtRate  = taxFree ? 0 : s.worldwide ? Math.max(fCgt,  s.cgt / 100) : fCgt;

  const P = c.price_aud;
  const cf = [-P * (1 + pc)];
  let val = P, rate = 1, grossRent = 0, taxRent = 0;

  for (let t = 0; t < N; t++) {
    rate *= 1 + fx;
    const rent = val * (c.net_yield / 100) * rate;
    grossRent += rent;
    taxRent += rent * rentRate;
    cf.push(rent * (1 - rentRate));
    val *= 1 + g;
  }

  const proceeds = val * rate * (1 - sc);
  const gain = Math.max(0, proceeds - P * (1 + pc));
  const exitTax = gain * cgtRate;
  cf[cf.length - 1] += proceeds - exitTax;

  const r = irr(cf);
  return { irr: r === null ? null : r * 100, grossRent, taxRent, exitTax, proceeds };
}

/* The benchmark holds the same money in an unleveraged global index fund and
   pays the reader's own rates on it, so the comparison is after-tax on both
   sides rather than after-tax against gross. */
function benchmark(P, s) {
  const growth = s.bench / 100 - DIST - MER;
  const cf = [-P * (1 + BROKERAGE)];
  let val = P;
  for (let t = 0; t < N; t++) {
    cf.push(val * DIST * (1 - s.mtr / 100));
    val *= 1 + growth;
  }
  const proceeds = val * (1 - BROKERAGE);
  const gain = Math.max(0, proceeds - P * (1 + BROKERAGE));
  cf[cf.length - 1] += proceeds - gain * (s.cgt / 100);
  const r = irr(cf);
  return r === null ? null : r * 100;
}

/* The currency fall that drags a country down to the benchmark. Monotonic in
   fxFall, so a bisection is exact enough and cannot get stuck. */
function fxBreakeven(c, s, bench) {
  if (model(c, s, 0).irr <= bench) return 0;
  if (model(c, s, 0.95).irr > bench) return null;      // survives anything
  let lo = 0, hi = 0.95;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (model(c, s, mid).irr > bench) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

/* A rate is hard to hold in the head; the money it turns into is not. This is
   the same number as the IRR, restated, so the two charts cannot disagree. */
const grown = (P, ratePc) => P * Math.pow(1 + ratePc / 100, N);

function settings() {
  return {
    mtr: +$("mtr").value,
    cgt: +$("cgt").value,
    growth: +$("growth").value,
    bench: +$("bench").value,
    worldwide: $("scope").value === "worldwide",
  };
}

/* ---------- chart plumbing ---------- */

/* One SVG unit is one CSS pixel, read off the rendered container. */
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

/* The readout follows the pointer and flips near an edge so it never sits over
   the marks it describes. Below 620px it goes static under the chart, where a
   finger is not already covering it. */
function showReadout(box, fig, ev, html) {
  box.innerHTML = html;
  box.hidden = false;
  if (window.innerWidth <= 620) {
    box.style.position = "static";
    box.style.left = box.style.top = "";
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

/* ---------- chart 1: the ranking ---------- */

function drawRank(rows, bench) {
  const svg = $("rank"), fig = svg.parentNode, box = $("rank-readout");
  const narrow = window.innerWidth <= 620;
  const rowH = narrow ? 15 : 17;
  const L = narrow ? 108 : 142, R = narrow ? 40 : 52, T = 26, B = 8;
  const H = T + rows.length * rowH + B;
  const W = frame(svg, H);
  const plotW = Math.max(60, W - L - R);

  const vals = rows.map(r => r.irr).concat([bench, 0]);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.08 || 1;
  lo = Math.min(0, lo - pad); hi = hi + pad;
  const x = v => L + ((v - lo) / (hi - lo)) * plotW;

  // Five ticks across 390px put "-0.4%" and "1.2%" edge to edge with no gap
  // between them. Three is what the width holds.
  const ticks = narrow ? 3 : 4;
  for (let i = 0; i <= ticks; i++) {
    const v = lo + (hi - lo) * (i / ticks);
    el(svg, "line", { x1: x(v), y1: T - 6, x2: x(v), y2: H - B, stroke: "var(--rule)", "stroke-width": 1 });
    el(svg, "text", {
      x: x(v), y: T - 11,
      "text-anchor": i === 0 ? "start" : i === ticks ? "end" : "middle",
      fill: "var(--ink-faint)", "font-size": narrow ? 10 : 11,
    }, fmtPc(v));
  }

  rows.forEach((r, i) => {
    const y = T + i * rowH, mid = y + rowH / 2;
    const x0 = x(0), x1 = x(r.irr);
    el(svg, "rect", {
      x: Math.min(x0, x1), y: y + 2, width: Math.max(1.5, Math.abs(x1 - x0)),
      height: rowH - 4, rx: 1.5, fill: r.irr > bench ? "var(--over)" : "var(--under)",
      opacity: r.country === PICKED ? 1 : 0.82,
    });
    el(svg, "text", {
      x: L - 8, y: mid + 3.6, "text-anchor": "end",
      fill: r.country === PICKED ? "var(--ink)" : "var(--ink-soft)",
      "font-size": narrow ? 10.5 : 12, "font-weight": r.country === PICKED ? 700 : 400,
    }, r.country);
  });

  // Under the value labels: drawn last it struck through half of them, because
  // a bar ending near the benchmark puts its own number on the line.
  el(svg, "line", {
    x1: x(bench), y1: T - 6, x2: x(bench), y2: H - B,
    stroke: "var(--bench)", "stroke-width": 2, "stroke-dasharray": "5 4",
  });

  rows.forEach((r, i) => {
    // Drawing the label over the benchmark rule is not enough: the dashes show
    // through the gaps between the glyphs and the number reads as struck
    // through. paint-order puts a panel-coloured stroke behind the fill, which
    // knocks a hole in the rule the exact shape of the text.
    el(svg, "text", {
      x: Math.max(x(0), x(r.irr)) + 6, y: T + i * rowH + rowH / 2 + 3.6,
      fill: "var(--ink-faint)", "font-size": narrow ? 10 : 11,
      "paint-order": "stroke", stroke: "var(--panel)", "stroke-width": 3.5,
      "stroke-linejoin": "round",
    }, fmtPc(r.irr));
  });

  rows.forEach((r, i) => {
    const band = el(svg, "rect", { x: 0, y: T + i * rowH, width: W, height: rowH, fill: "transparent", style: "cursor:pointer" });
    const gap = r.irr - bench;
    band.addEventListener("mousemove", ev => showReadout(box, fig, ev,
      `<strong>${r.country}</strong><span class="num">${fmtPc(r.irr)} a year after tax</span><br>
       <span class="num">${gap >= 0 ? "+" : ""}${gap.toFixed(1)} points ${gap >= 0 ? "above" : "below"} the index fund</span><br>
       <span class="num">${fmtMoney(r.price_aud)} to buy</span>`));
    band.addEventListener("mouseleave", () => { box.hidden = true; });
    band.addEventListener("click", () => select(r.country));
  });
}

/* ---------- chart 2: the same money, ten years on ----------

   Was a stacked bar splitting ten years of rent between the two governments.
   It carried the tax finding but nobody could read it: "ten years of rent" is
   an odd unit, and a three-way split needs a legend decoded before it says
   anything. Three bars of money answer the reader's actual question - what do
   I end up with - and the tax still shows, as the gap between the first two. */

function drawCompare(c, s, m, gross, bench) {
  const svg = $("compare"), fig = svg.parentNode, box = $("compare-readout");
  const narrow = window.innerWidth <= 620;
  const P = c.price_aud;
  const bars = [
    { label: "If nobody taxed it", v: grown(P, gross.irr), fill: "var(--ghost)" },
    { label: "The property, after tax", v: grown(P, m.irr), fill: m.irr > bench ? "var(--over)" : "var(--under)" },
    { label: "An index fund, after tax", v: grown(P, bench), fill: "var(--bench-bar)" },
  ];

  const rowH = narrow ? 46 : 52, T = 22, B = 26;
  const H = T + bars.length * rowH + B;
  const W = frame(svg, H);
  const L = 0, R = narrow ? 0 : 0;
  const plotW = Math.max(60, W - L - R);
  const hi = Math.max(...bars.map(b => b.v)) * 1.02;

  el(svg, "text", { x: 0, y: 13, fill: "var(--ink-faint)", "font-size": narrow ? 11 : 11.5 },
     `${fmtMoney(P)} put in, ten years on`);

  bars.forEach((b, i) => {
    const y = T + i * rowH, w = (b.v / hi) * plotW, barH = narrow ? 22 : 25;
    el(svg, "text", { x: 0, y: y + 11, fill: "var(--ink-soft)", "font-size": narrow ? 11.5 : 12.5 }, b.label);
    el(svg, "rect", { x: 0, y: y + 17, width: Math.max(2, w), height: barH, rx: 2, fill: b.fill });
    // The amount sits inside a bar wide enough to hold it, outside otherwise,
    // so a short bar never pushes its own number off the panel.
    const inside = w > (narrow ? 96 : 108);
    el(svg, "text", {
      x: inside ? w - 9 : w + 9, y: y + 17 + barH / 2 + 4.5,
      "text-anchor": inside ? "end" : "start",
      fill: inside ? "#fff" : "var(--ink)",
      "font-size": narrow ? 12.5 : 14, "font-weight": 650,
    }, fmtMoney(b.v));

    const hit = el(svg, "rect", { x: 0, y, width: W, height: rowH, fill: "transparent" });
    hit.addEventListener("mousemove", ev => showReadout(box, fig, ev,
      `<strong>${b.label}</strong><span class="num">${fmtMoney(b.v)} after ten years</span>`));
    hit.addEventListener("mouseleave", () => { box.hidden = true; });
  });

  const taxCost = grown(P, gross.irr) - grown(P, m.irr);
  el(svg, "text", { x: 0, y: H - 8, fill: "var(--ink-faint)", "font-size": narrow ? 11 : 11.5 },
     `Tax takes ${fmtMoney(taxCost)} of it.`);
}

/* ---------- chart 3: how far the currency can fall ----------

   Was net return plotted against the size of the currency move. A curve of one
   abstract quantity against another, and the answer the reader wants is a
   single threshold. So: one track, the safe part and the losing part, marked. */

function drawFx(c, s, be) {
  const svg = $("fx"), fig = svg.parentNode, box = $("fx-readout");
  const narrow = window.innerWidth <= 620;
  const MAX = 0.8;
  // barY leaves a row for the marker's own label between the caption and the
  // bar. At barY=24 the label sat on the caption's baseline and the two
  // collided whenever the threshold landed near the left edge.
  const H = 94, W = frame(svg, H);
  const L = 0, R = 0, barY = 42, barH = 26;
  const plotW = Math.max(60, W - L - R);
  const X = f => (Math.min(f, MAX) / MAX) * plotW;

  const cut = be == null ? MAX : Math.min(be, MAX);

  el(svg, "rect", { x: 0, y: barY, width: plotW, height: barH, rx: 3, fill: "var(--under)" });
  if (cut > 0) el(svg, "rect", { x: 0, y: barY, width: X(cut), height: barH, rx: 3, fill: "var(--over)" });

  for (let i = 0; i <= 4; i++) {
    const f = (i / 4) * MAX;
    el(svg, "text", {
      x: X(f), y: barY + barH + 17, "text-anchor": i === 0 ? "start" : i === 4 ? "end" : "middle",
      fill: "var(--ink-faint)", "font-size": narrow ? 10 : 11,
    }, Math.round(f * 100) + "%");
    if (i > 0 && i < 4) el(svg, "line", { x1: X(f), y1: barY, x2: X(f), y2: barY + barH, stroke: "var(--bg)", "stroke-width": 1, opacity: .5 });
  }

  if (be != null && be > 0 && be < MAX) {
    el(svg, "line", { x1: X(be), y1: barY - 7, x2: X(be), y2: barY + barH + 3, stroke: "var(--ink)", "stroke-width": 2 });
    const anchor = be / MAX > 0.75 ? "end" : "start";
    el(svg, "text", {
      x: X(be) + (anchor === "end" ? -5 : 5), y: barY - 8, "text-anchor": anchor,
      fill: "var(--ink)", "font-size": narrow ? 11.5 : 12.5, "font-weight": 650,
    }, `${(be * 100).toFixed(0)}%`);
  }

  el(svg, "text", { x: 0, y: 12, fill: "var(--ink-faint)", "font-size": narrow ? 11 : 11.5 },
     `How far ${c.currency || "the currency"} falls against the Australian dollar`);

  const hit = el(svg, "rect", { x: 0, y: barY, width: plotW, height: barH, fill: "transparent" });
  hit.addEventListener("mousemove", ev => {
    const rect = svg.getBoundingClientRect();
    const f = Math.max(0, Math.min(MAX, ((ev.clientX - rect.left) * (W / rect.width) / plotW) * MAX));
    showReadout(box, fig, ev,
      `<strong>${(f * 100).toFixed(0)}% fall</strong><span class="num">${fmtPc(model(c, s, f).irr)} a year after tax</span><br>
       <span class="num">${f < cut ? "still ahead of the fund" : "behind the fund"}</span>`);
  });
  hit.addEventListener("mouseleave", () => { box.hidden = true; });
}

/* ---------- render ---------- */

function select(name) {
  PICKED = name;
  render();
  const url = new URL(location);
  url.searchParams.set("c", name);
  history.replaceState(null, "", url);
}

function render() {
  const s = settings();
  const cs = DATA.countries;

  $("mtr-out").textContent = s.mtr.toFixed(1) + "%";
  $("cgt-out").textContent = s.cgt.toFixed(1) + "%";
  $("growth-out").textContent = s.growth.toFixed(2) + "%";
  $("bench-out").textContent = s.bench.toFixed(2) + "%";
  $("controls").classList.toggle("locked", $("residence").value === "au");
  $("residence-hint").textContent = $("residence").value === "au"
    ? "Top bracket plus Medicare plus HELP." : "Enter your own rates.";

  const rows = cs.map(c => Object.assign({}, c, model(c, s, 0)))
                 .filter(r => r.irr !== null)
                 .sort((a, b) => b.irr - a.irr);

  // Every country is bought at its own price, so the benchmark is computed on
  // the median of them rather than on any one country's outlay. It is a rate,
  // so the level barely moves; taking one country's price would still be wrong.
  const prices = cs.map(c => c.price_aud).sort((a, b) => a - b);
  const bench = benchmark(prices[Math.floor(prices.length / 2)], s);

  const beat = rows.filter(r => r.irr > bench).length;
  $("rank-blurb").textContent =
    `${beat} of ${rows.length} beat an index fund holding the same money, which returns ${fmtPc(bench)} a year after the same taxes.`;

  drawRank(rows, bench);

  if (!PICKED || !cs.some(c => c.country === PICKED)) PICKED = rows[0].country;
  const c = cs.find(x => x.country === PICKED);
  const m = model(c, s, 0);
  const gross = model(c, s, 0, true);
  const be = fxBreakeven(c, s, bench);
  const over = m.irr > bench;

  $("picked-name").textContent = c.country;
  const v = $("picked-verdict");
  v.textContent = over ? `${(m.irr - bench).toFixed(1)} points ahead` : `${(bench - m.irr).toFixed(1)} points behind`;
  v.className = "verdict " + (over ? "over" : "under");

  $("fx-blurb").textContent = be == null
    ? "No currency move inside ten years drags this below the fund."
    : be === 0
      ? "Already behind the fund before the currency moves."
      : `Past a ${(be * 100).toFixed(0)}% fall, the fund wins.`;

  drawCompare(c, s, m, gross, bench);
  drawFx(c, s, be);

  const facts = $("facts");
  facts.innerHTML = "";
  const add = (dt, dd) => {
    if (!dd) return;
    const d = document.createElement("div");
    d.innerHTML = "<dt></dt><dd></dd>";
    d.querySelector("dt").textContent = dt;
    d.querySelector("dd").textContent = dd;
    facts.appendChild(d);
  };
  add("Median home", fmtMoney(c.price_aud));
  add("Net rent", c.net_yield + "%");
  add("Buying costs", c.purchase_costs + "%");
  add("Tax on rent there", c.rental_tax_text);
  add("Tax on the gain there", c.cgt_text);
  add("Treaty with Australia", c.au_dta ? "Yes" : "No");

  $("note-tax").textContent = s.worldwide
    ? "Australia taxes what you earn abroad and credits the tax you paid there, capped at that amount. The foreign rate is a floor; yours is the bill."
    : "Foreign income is not taxed at home, so only the destination's rates apply.";

  const review = cs.filter(needsReview).length;
  $("note-review").textContent =
    `In ${review} of ${cs.length} countries the local rate is a schedule, not one number, so it is shown as text and left out. `
    + `That does not move the return: the total is whichever rate is higher, and none of the readable rates is above yours.`;
}

/* ---------- boot ---------- */

fetch("data.json")
  .then(r => r.json())
  .then(d => {
    DATA = d;
    const want = new URL(location).searchParams.get("c");
    if (want && d.countries.some(c => c.country === want)) PICKED = want;

    const tb = $("sources");
    (d.sources || []).forEach(s => {
      const tr = document.createElement("tr");
      const a = s.url ? `<a href="${s.url.startsWith("http") ? s.url : "https://" + s.url}" rel="noopener">${s.name}</a>` : s.name;
      // The caveat column is the point of this table, not decoration: the yield
      // and price rows are user-contributed data, and a reader deciding whether
      // to trust a number needs that next to the number's source.
      tr.innerHTML = `<td>${s.measure}</td><td>${a}</td><td></td>`;
      tr.lastElementChild.textContent = s.caveat || "";
      tb.appendChild(tr);
    });

    ["mtr", "cgt", "growth", "bench", "scope", "residence"].forEach(id =>
      $(id).addEventListener("input", () => {
        if (id === "residence" && $("residence").value === "au") {
          $("mtr").value = 47; $("cgt").value = 23.5; $("scope").value = "worldwide";
        }
        render();
      }));

    render();
    let t;
    addEventListener("resize", () => { clearTimeout(t); t = setTimeout(render, 120); });
  })
  .catch(() => {
    document.querySelector("main").insertAdjacentHTML("afterbegin",
      '<p class="sub">The country data did not load. Try a refresh.</p>');
  });
