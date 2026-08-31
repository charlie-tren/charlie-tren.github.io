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
   numbers, so the ones charged on proceeds or on a deemed return are set aside
   and the country is named in the notes rather than quietly given a wrong rate. */
const rentUsable = c => c.foreign_rental_basis === "gain" || c.foreign_rental_basis === "gross" || c.foreign_rental_basis === "exempt";
const cgtUsable  = c => c.foreign_cgt_basis === "gain" || c.foreign_cgt_basis === "exempt";
const needsReview = c => !rentUsable(c) || !cgtUsable(c);

function model(c, s, fxFall) {
  const g = s.growth / 100;
  const fx = Math.pow(1 - (fxFall || 0), 1 / N) - 1;   // annual currency drift
  const pc = c.purchase_costs / 100, sc = c.sale_costs / 100;

  const fRent = rentUsable(c) && c.foreign_rental_tax != null ? c.foreign_rental_tax / 100 : 0;
  const fCgt  = cgtUsable(c)  && c.foreign_cgt != null        ? c.foreign_cgt / 100        : 0;

  // Credit method: the total is whichever rate is higher, never the sum.
  const rentRate = s.worldwide ? Math.max(fRent, s.mtr / 100) : fRent;
  const cgtRate  = s.worldwide ? Math.max(fCgt,  s.cgt / 100) : fCgt;

  const P = c.price_aud;
  const cf = [-P * (1 + pc)];
  let val = P, rate = 1, grossRent = 0, taxThere = 0, taxHome = 0;

  for (let t = 0; t < N; t++) {
    rate *= 1 + fx;
    const rent = val * (c.net_yield / 100) * rate;
    grossRent += rent;
    taxThere += rent * fRent;
    taxHome  += rent * (rentRate - fRent);
    cf.push(rent * (1 - rentRate));
    val *= 1 + g;
  }

  const proceeds = val * rate * (1 - sc);
  const gain = Math.max(0, proceeds - P * (1 + pc));
  const exitTax = gain * cgtRate;
  cf[cf.length - 1] += proceeds - exitTax;

  const r = irr(cf);
  return {
    irr: r === null ? null : r * 100,
    grossRent, taxThere, taxHome, kept: grossRent - taxThere - taxHome,
    proceeds, gain, exitTax, rentRate: rentRate * 100, fRent: fRent * 100,
  };
}

/* The benchmark holds the same money in an unleveraged global index fund and
   pays the reader's own rates on it, so the comparison is after-tax on both
   sides rather than after-tax against gross. */
function benchmark(P, s) {
  const total = s.bench / 100;
  const growth = total - DIST - MER;
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
  let lo = 0, hi = 0.95;
  if (model(c, s, hi).irr > bench) return null;   // survives anything
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (model(c, s, mid).irr > bench) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

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

/* The readout follows the pointer and flips to the other side near an edge, so
   it never sits over the marks it is describing. Below 620px it goes static
   under the chart, where a finger is not already covering it. */
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
  let x = ev.clientX - fr.left + 14;
  let y = ev.clientY - fr.top + 14;
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

  // Axis: even spacing across the panel rather than round numbers, which leave
  // a ragged remainder short of the panel's own edge.
  const ticks = 4;
  for (let i = 0; i <= ticks; i++) {
    const v = lo + (hi - lo) * (i / ticks);
    el(svg, "line", { x1: x(v), y1: T - 6, x2: x(v), y2: H - B, stroke: "var(--rule)", "stroke-width": 1 });
    el(svg, "text", {
      x: x(v), y: T - 11, "text-anchor": "middle", fill: "var(--ink-faint)",
      "font-size": narrow ? 10 : 11,
    }, fmtPc(v));
  }

  rows.forEach((r, i) => {
    const y = T + i * rowH, mid = y + rowH / 2;
    const over = r.irr > bench;
    const x0 = x(0), x1 = x(r.irr);
    el(svg, "rect", {
      x: Math.min(x0, x1), y: y + 2, width: Math.max(1.5, Math.abs(x1 - x0)),
      height: rowH - 4, rx: 1.5, fill: over ? "var(--over)" : "var(--under)",
      opacity: r.country === PICKED ? 1 : 0.82,
    });
    el(svg, "text", {
      x: L - 8, y: mid + 3.6, "text-anchor": "end",
      fill: r.country === PICKED ? "var(--ink)" : "var(--ink-soft)",
      "font-size": narrow ? 10.5 : 12,
      "font-weight": r.country === PICKED ? 700 : 400,
    }, r.country);
  });

  // The benchmark rule sits over the bars so it reads as the line they are
  // being judged against rather than as another series. It goes under the value
  // labels, though: drawn last it struck through half of them, because a bar
  // ending near the benchmark puts its own number right on the line.
  el(svg, "line", {
    x1: x(bench), y1: T - 6, x2: x(bench), y2: H - B,
    stroke: "var(--bench)", "stroke-width": 2, "stroke-dasharray": "5 4",
  });

  rows.forEach((r, i) => {
    const mid = T + i * rowH + rowH / 2;
    el(svg, "text", {
      x: Math.max(x(0), x(r.irr)) + 6, y: mid + 3.6, fill: "var(--ink-faint)",
      "font-size": narrow ? 10 : 11,
    }, fmtPc(r.irr));
  });

  // One transparent band per row carries the hover, so the whole row is a
  // target rather than only the drawn bar.
  rows.forEach((r, i) => {
    const band = el(svg, "rect", {
      x: 0, y: T + i * rowH, width: W, height: rowH,
      fill: "transparent", style: "cursor:pointer",
    });
    const gap = r.irr - bench;
    band.addEventListener("mousemove", ev => showReadout(box, fig, ev,
      `<strong>${r.country}</strong>
       <span class="num">${fmtPc(r.irr)} a year after tax</span><br>
       <span class="num">${gap >= 0 ? "+" : ""}${gap.toFixed(1)} points ${gap >= 0 ? "above" : "below"} the index fund</span><br>
       <span class="num">${fmtMoney(r.price_aud)} to buy</span>`));
    band.addEventListener("mouseleave", () => { box.hidden = true; });
    band.addEventListener("click", () => select(r.country));
  });
}

/* ---------- chart 2: where the rent goes ---------- */

function drawSplit(c, m) {
  const svg = $("split"), fig = svg.parentNode, box = $("split-readout");
  const H = 96, W = frame(svg, H);
  const L = 0, R = 0, barY = 30, barH = 34;
  const plotW = Math.max(60, W - L - R);
  const total = m.grossRent || 1;

  /* Where the destination's own rate cannot be read as a single number, the
     total is still right, because it is whichever rate is higher and the
     reader's is the higher one. What cannot be drawn is which government took
     which half, so the bar shows one tax segment rather than inventing a split.
     Splitting it anyway would put the destination's share at zero and label
     the whole of it as topped up at home, which is a claim, not a gap. */
  const split = rentUsable(c);
  const parts = (split
    ? [
        { label: "You keep", v: m.kept, fill: "var(--kept)" },
        { label: "Taken where the property is", v: m.taxThere, fill: "var(--tax-there)" },
        { label: "Topped up at home", v: m.taxHome, fill: "var(--tax-home)" },
      ]
    : [
        { label: "You keep", v: m.kept, fill: "var(--kept)" },
        { label: "Tax, on both sides together", v: m.taxThere + m.taxHome, fill: "var(--tax-home)" },
      ]
  ).filter(p => p.v > total * 0.0005);

  $("split-legend").innerHTML = parts.map(p =>
    `<span><i style="background:${p.fill}"></i>${p.label}</span>`).join("");

  el(svg, "text", { x: 0, y: 16, fill: "var(--ink-faint)", "font-size": 11.5 },
     `${fmtMoney(total)} of rent over ten years`);

  let x = L;
  parts.forEach(p => {
    const w = (p.v / total) * plotW;
    el(svg, "rect", { x, y: barY, width: Math.max(1, w), height: barH, fill: p.fill });
    const share = (p.v / total) * 100;
    // A label only goes inside a segment wide enough to hold it; the rest are
    // carried by the key above and the hover.
    if (w > 46) {
      el(svg, "text", {
        x: x + w / 2, y: barY + barH / 2 + 4, "text-anchor": "middle",
        fill: "#fff", "font-size": 12, "font-weight": 650,
      }, share.toFixed(0) + "%");
    }
    const hit = el(svg, "rect", { x, y: barY, width: Math.max(1, w), height: barH, fill: "transparent" });
    hit.addEventListener("mousemove", ev => showReadout(box, fig, ev,
      `<strong>${p.label}</strong><span class="num">${fmtMoney(p.v)} over ten years</span><br>
       <span class="num">${share.toFixed(1)}% of the rent</span>`));
    hit.addEventListener("mouseleave", () => { box.hidden = true; });
    x += w;
  });

  el(svg, "text", { x: 0, y: barY + barH + 20, fill: "var(--ink-soft)", "font-size": 12 },
     `Sale after ten years: ${fmtMoney(m.proceeds)}, less ${fmtMoney(m.exitTax)} of tax on the gain.`);
}

/* ---------- chart 3: the currency ---------- */

function drawFx(c, s, bench, be) {
  const svg = $("fx"), fig = svg.parentNode, box = $("fx-readout");
  const narrow = window.innerWidth <= 620;
  /* B has to clear three stacked things below the plot, not one: the bottom y
     tick sits on the plot's own baseline, the x tick row goes under it, and the
     axis title under that. At B=46 the bottom y label and the first x label
     overlapped, measured, because 14px of gap does not hold a 15px line. */
  const H = narrow ? 218 : 248, W = frame(svg, H);
  const L = narrow ? 44 : 52, R = 14, T = 14, B = 54;
  const plotW = Math.max(60, W - L - R), plotH = H - T - B;

  const maxFall = 0.8;
  const pts = [];
  for (let i = 0; i <= 40; i++) {
    const f = (i / 40) * maxFall;
    pts.push([f, model(c, s, f).irr]);
  }
  const ys = pts.map(p => p[1]).concat([bench]);
  let lo = Math.min(...ys), hi = Math.max(...ys);
  const pad = (hi - lo) * 0.12 || 1;
  lo -= pad; hi += pad;

  const X = f => L + (f / maxFall) * plotW;
  const Y = v => T + plotH - ((v - lo) / (hi - lo)) * plotH;

  // Gridlines and the y axis fitted to the data, keeping zero visible when the
  // line crosses it.
  for (let i = 0; i <= 4; i++) {
    const v = lo + (hi - lo) * (i / 4);
    el(svg, "line", { x1: L, y1: Y(v), x2: L + plotW, y2: Y(v), stroke: "var(--rule)", "stroke-width": 1 });
    el(svg, "text", { x: L - 7, y: Y(v) + 3.6, "text-anchor": "end", fill: "var(--ink-faint)", "font-size": narrow ? 10 : 11 }, fmtPc(v));
  }
  for (let i = 0; i <= 4; i++) {
    const f = (i / 4) * maxFall;
    // The end labels anchor inward so they cannot reach back under the y-axis
    // column or past the right edge of the plot.
    el(svg, "text", {
      x: X(f), y: H - B + 24, "text-anchor": i === 0 ? "start" : i === 4 ? "end" : "middle",
      fill: "var(--ink-faint)", "font-size": narrow ? 10 : 11,
    }, Math.round(f * 100) + "%");
  }
  el(svg, "text", {
    x: L + plotW / 2, y: H - 6, "text-anchor": "middle",
    fill: "var(--ink-faint)", "font-size": narrow ? 10.5 : 11.5,
  }, `How far ${c.currency || "the local currency"} falls over ten years`);

  el(svg, "line", {
    x1: L, y1: Y(bench), x2: L + plotW, y2: Y(bench),
    stroke: "var(--bench)", "stroke-width": 2, "stroke-dasharray": "5 4",
  });
  el(svg, "text", { x: L + 5, y: Y(bench) - 6, fill: "var(--bench)", "font-size": narrow ? 10 : 11 }, "Index fund");

  el(svg, "path", {
    d: pts.map((p, i) => (i ? "L" : "M") + X(p[0]) + " " + Y(p[1])).join(" "),
    fill: "none", stroke: "var(--accent)", "stroke-width": 2.4, "stroke-linejoin": "round",
  });

  if (be != null && be > 0 && be < maxFall) {
    el(svg, "line", { x1: X(be), y1: T, x2: X(be), y2: T + plotH, stroke: "var(--under)", "stroke-width": 1.5, "stroke-dasharray": "3 3" });
    el(svg, "circle", { cx: X(be), cy: Y(bench), r: 4, fill: "var(--under)" });
  }

  const hit = el(svg, "rect", { x: L, y: T, width: plotW, height: plotH, fill: "transparent" });
  hit.addEventListener("mousemove", ev => {
    const rect = svg.getBoundingClientRect();
    const px = (ev.clientX - rect.left) * (W / rect.width);
    const f = Math.max(0, Math.min(maxFall, ((px - L) / plotW) * maxFall));
    const v = model(c, s, f).irr;
    showReadout(box, fig, ev,
      `<strong>${(f * 100).toFixed(0)}% fall in ${c.currency || "the currency"}</strong>
       <span class="num">${fmtPc(v)} a year after tax</span><br>
       <span class="num">${v > bench ? "still beats" : "loses to"} the index fund</span>`);
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
    ? "Top bracket plus Medicare plus HELP."
    : "Enter your own rates.";

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
    `${beat} of ${rows.length} beat an index fund holding the same money. `
    + `The fund returns ${fmtPc(bench)} a year after the same taxes.`;

  drawRank(rows, bench);

  if (!PICKED || !cs.some(c => c.country === PICKED)) PICKED = rows[0].country;
  const c = cs.find(x => x.country === PICKED);
  const m = model(c, s, 0);
  const be = fxBreakeven(c, s, bench);
  const over = m.irr > bench;

  $("picked-name").textContent = c.country;
  const v = $("picked-verdict");
  v.textContent = over ? `Beats the fund by ${(m.irr - bench).toFixed(1)} points` : `Loses by ${(bench - m.irr).toFixed(1)} points`;
  v.className = "verdict " + (over ? "over" : "under");
  $("picked-blurb").textContent =
    `${fmtMoney(c.price_aud)} buys a median home. At ${c.net_yield}% net rent and `
    + `${s.growth}% growth a year it returns ${fmtPc(m.irr)} a year after tax.`;

  $("fx-blurb").textContent = be == null
    ? `Nothing the currency does inside ten years drags this below the index fund.`
    : be === 0
      ? `It is already below the index fund before the currency moves at all.`
      : `${c.currency || "The currency"} has to hold within ${(be * 100).toFixed(0)}% of where it is now, or this drops below the index fund.`;

  drawSplit(c, m);
  drawFx(c, s, bench, be);

  const facts = $("facts");
  facts.innerHTML = "";
  const add = (dt, dd, narrow) => {
    if (!dd) return;
    const d = document.createElement("div");
    d.innerHTML = `<dt>${dt}</dt><dd class="${narrow ? "narrow" : ""}"></dd>`;
    d.querySelector("dd").textContent = dd;
    facts.appendChild(d);
  };
  add("Tax on rent where it sits", c.rental_tax_text);
  add("Tax on the gain there", c.cgt_text);
  add("Tax treaty with Australia", c.au_dta ? "Yes" : "No");
  add("Buying costs", c.purchase_costs + "%");
  add("Months to sell", c.liquidity);
  add("Estate or inheritance tax", c.estate_text, true);
  add("Can a foreigner buy", c.ownership, true);
  add("Residency for buying", c.visa, true);
  add("Getting the money out", c.repatriation, true);
  add("Obstacles", c.obstacles, true);
  $("profile").textContent = c.profile || "";

  $("note-tax").textContent = s.worldwide
    ? "Your country taxes what you earn abroad and credits the tax you already paid there, capped at that amount. So the destination's rate is a floor and yours is the bill, and a country with no tax of its own saves you nothing."
    : "Your country does not tax foreign income, so only the destination's own rates apply.";

  const review = cs.filter(needsReview).map(x => x.country);
  const readable = cs.filter(c => !needsReview(c));
  const binds = readable.filter(c => (c.foreign_rental_tax || 0) > s.mtr).map(c => c.country);
  $("note-review").textContent =
    `In ${review.length} of the ${cs.length} countries the destination's own rate is a schedule or a choice of `
    + `regimes rather than one number, so it is shown as text and left out of the arithmetic: ${review.join(", ")}. `
    + `That does not move the return. The total is whichever rate is higher, and of the ${readable.length} rates that `
    + `can be read, ${binds.length === 0 ? "none is above yours" : binds.join(" and ") + " sit above yours"}. `
    + `What it does affect is the split between the two governments, which is why those countries show one tax bar `
    + `rather than two.`;
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
