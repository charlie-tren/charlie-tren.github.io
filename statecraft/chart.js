// Statecraft's opening chart: what a country taxes against what it spends.
//
// WHY THESE TWO AXES. Both numbers exist for the visitor and for all twenty
// coded countries on exactly the same basis, because both are read out of the
// same model: the vertical is the headline tax rate the country's coded tax
// regime runs at, the horizontal is what its own thirteen coded choices cost.
// The consequence is the property the chart is here for: on load your marker
// sits exactly on your starting country's dot, and every slider you move drags
// it off. A chart drawn against the measured tax take instead would have looked
// better spread and would have started you a couple of points away from the
// country you were told you were starting from, which is worse than banded.
//
// The curve is your own budget line: for any rate, what that rate can fund. It
// bends because realised revenue does, so the diminishing return at the top of
// the tax slider is a thing you can see rather than a claim in a paragraph.
// Everything right of it is spending you cannot pay for.
//
// DRAWN AT CONTAINER PIXEL SCALE. The viewBox is derived from the host's own
// bounding rect so one user unit is one CSS pixel and an 11px label is 11px on
// a phone. Redraw on resize.

import { TAX, realisedRevenue, spendOf, rateForOption } from './budget.js';
import { ladder } from './cascade.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

function el(name, attrs, text) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, String(v));
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Everything the chart needs that does not change while the visitor drags. */
export function chartBase(data) {
  const countries = data.countries.map((c) => ({
    code: c.code,
    name: c.name,
    spend: spendOf(data, c.choices),
    rate: rateForOption(data, c.choices.tax),
  }));

  // The reachable spend, so the horizontal axis is fixed for the whole session
  // rather than jumping about under a marker the visitor is dragging.
  let floorSpend = 0;
  for (const domain of data.domains) {
    if (domain.id === 'tax') continue;
    const rungs = ladder(data, domain.id);
    if (rungs.length) floorSpend += rungs[0].financial || 0;
  }
  return { countries, floorSpend };
}

/** A tick step that gives between four and eight labelled gridlines. */
function stepFor(span, maxTicks) {
  for (const s of [1, 2, 5, 10, 20]) {
    if (span / s <= maxTicks) return s;
  }
  return 25;
}

function ticks(lo, hi, step) {
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(v);
  return out;
}

/**
 * @param {HTMLElement} host       the element the svg is drawn into
 * @param {object} data            parsed data.json
 * @param {object} base            chartBase(data)
 * @param {object} view            {startCode, rate, spend, capacity, matched}
 *   matched: Map code -> domains matched, 0 to 13
 */
export function drawChart(host, data, base, view) {
  const box = host.getBoundingClientRect();
  const w = Math.max(240, Math.round(box.width));
  const h = Math.max(200, Math.round(box.height));
  if (!w) return;

  const narrow = w < 420;
  const pad = {
    left: narrow ? 30 : 36,
    right: narrow ? 22 : 30,
    top: narrow ? 26 : 28,
    bottom: narrow ? 34 : 36,
  };
  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;
  if (plotW < 60 || plotH < 60) return;

  // Bounds derived from the marks, not rounded to a nice number. The vertical
  // is the slider's own span because the visitor's marker can reach either end
  // of it; the horizontal covers the cheapest possible design, every country,
  // and whatever the current design costs.
  const capMax = realisedRevenue(TAX.MAX) + (view.capacity - realisedRevenue(view.rate));
  const spends = base.countries.map((c) => c.spend).concat([base.floorSpend, capMax, view.spend]);
  const xLo = Math.min(...spends);
  const xHi = Math.max(...spends);
  const xPad = (xHi - xLo) * 0.04;
  const x0 = xLo - xPad;
  const x1 = xHi + xPad;
  const yPad = (TAX.MAX - TAX.MIN) * 0.04;
  const y0 = TAX.MIN - yPad;
  const y1 = TAX.MAX + yPad;

  const px = (v) => pad.left + ((v - x0) / (x1 - x0)) * plotW;
  const py = (v) => pad.top + plotH - ((v - y0) / (y1 - y0)) * plotH;

  const svg = el('svg', {
    viewBox: `0 0 ${w} ${h}`,
    width: w,
    height: h,
    role: 'img',
    'aria-label': `Twenty countries plotted by what they tax and what they spend. Your design taxes ${view.rate.toFixed(1)} and spends ${view.spend.toFixed(1)} per cent of GDP.`,
  });

  // Plot ground.
  svg.appendChild(el('rect', {
    class: 'ch-plot', x: pad.left, y: pad.top, width: plotW, height: plotH, rx: 4,
  }));

  // The part of the plot the current tax rate cannot fund.
  const cap = (r) => realisedRevenue(r) + (view.capacity - realisedRevenue(view.rate));
  const curve = [];
  for (let i = 0; i <= 60; i += 1) {
    const r = y0 + ((y1 - y0) * i) / 60;
    curve.push([px(Math.min(x1, Math.max(x0, cap(r)))), py(r)]);
  }
  // The curve runs bottom to top, so the region closes up the right-hand edge
  // and back down. Closing the other way round folds the shape over itself and
  // shades a sliver instead of the whole unaffordable half.
  const band = curve.map(([cx, cy], i) => `${i ? 'L' : 'M'}${cx.toFixed(1)},${cy.toFixed(1)}`).join('')
    + `L${(pad.left + plotW).toFixed(1)},${py(y1).toFixed(1)}L${(pad.left + plotW).toFixed(1)},${py(y0).toFixed(1)}Z`;
  svg.appendChild(el('path', { class: 'ch-band', d: band }));

  // Gridlines and ticks.
  const xStep = stepFor(x1 - x0, narrow ? 4 : 7);
  const yStep = stepFor(y1 - y0, narrow ? 4 : 7);
  for (const v of ticks(x0, x1, xStep)) {
    svg.appendChild(el('line', {
      class: 'ch-grid', x1: px(v), x2: px(v), y1: pad.top, y2: pad.top + plotH,
    }));
    svg.appendChild(el('text', {
      class: 'ch-tick', x: px(v), y: pad.top + plotH + 15, 'text-anchor': 'middle',
    }, String(v)));
  }
  for (const v of ticks(y0, y1, yStep)) {
    svg.appendChild(el('line', {
      class: 'ch-grid', x1: pad.left, x2: pad.left + plotW, y1: py(v), y2: py(v),
    }));
    svg.appendChild(el('text', {
      class: 'ch-tick', x: pad.left - 6, y: py(v) + 4, 'text-anchor': 'end',
    }, String(v)));
  }

  svg.appendChild(el('path', {
    class: 'ch-curve',
    d: curve.map(([cx, cy], i) => `${i ? 'L' : 'M'}${cx.toFixed(1)},${cy.toFixed(1)}`).join(''),
  }));

  // Axis titles. Direction is spelled out, because a share of GDP does not tell
  // a reader which way is more state.
  svg.appendChild(el('text', {
    class: 'ch-axis', x: pad.left + plotW, y: h - 5, 'text-anchor': 'end',
  }, 'Spends more, % of GDP →'));
  svg.appendChild(el('text', {
    class: 'ch-axis', x: pad.left - (narrow ? 24 : 30), y: pad.top - 10, 'text-anchor': 'start',
  }, 'Taxes more, % of GDP ↑'));

  // Boxes already claimed on the plot: every dot first, then each label as it
  // is placed. A code printed over a dot that belongs to another country is
  // worse than no code at all, so a label that cannot find clear air is
  // dropped and the dot keeps its hover title.
  const placed = [];
  const clear = (bx, by, bw, bh) => !placed.some((b) => (
    Math.abs(bx - b.x) < (bw + b.w) / 2 + 2 && Math.abs(by - b.y) < (bh + b.h) / 2 + 1
  ));
  const claim = (bx, by, bw, bh) => { placed.push({ x: bx, y: by, w: bw, h: bh }); };

  const total = data.domains.length;
  const ranked = base.countries
    .map((c) => ({ ...c, matched: view.matched.get(c.code) || 0 }))
    .sort((a, b) => a.matched - b.matched);

  const r = narrow ? 4.5 : 5;
  for (const c of ranked) {
    const share = c.matched / total;
    const band4 = share >= 0.85 ? 3 : share >= 0.6 ? 2 : share >= 0.35 ? 1 : 0;
    const cx = px(c.spend);
    const cy = py(c.rate);
    const dot = el('circle', { class: `ch-dot ch-s${band4}`, cx, cy, r });
    dot.appendChild(el('title', {}, `${c.name}: taxes ${c.rate}, spends ${c.spend.toFixed(1)}% of GDP, and already runs ${c.matched} of your ${total}`));
    svg.appendChild(dot);
    claim(cx, cy, r * 2 + 2, r * 2 + 2);
  }
  // The visitor's own marker claims its space before any label, so no country
  // code is printed under the thing the page is about.
  const mx = px(Math.min(x1, Math.max(x0, view.spend)));
  const my = py(view.rate);
  claim(mx, my, 22, 22);

  // Best match first, so where the plot is crowded the country closest to the
  // visitor's design is the one that keeps its name.
  const lw = 15;
  const lh = 12;
  for (const c of ranked.slice().reverse()) {
    const cx = px(c.spend);
    const cy = py(c.rate);
    const spots = [
      { x: cx + r + 3 + lw / 2, y: cy, anchor: 'start', tx: cx + r + 3, ty: cy + 4 },
      { x: cx - r - 3 - lw / 2, y: cy, anchor: 'end', tx: cx - r - 3, ty: cy + 4 },
      { x: cx, y: cy - r - 8, anchor: 'middle', tx: cx, ty: cy - r - 4 },
      { x: cx, y: cy + r + 8, anchor: 'middle', tx: cx, ty: cy + r + 12 },
    ];
    const spot = spots.find((s) => (
      s.x - lw / 2 > pad.left && s.x + lw / 2 < pad.left + plotW
      && s.y - lh / 2 > pad.top && s.y + lh / 2 < pad.top + plotH
      && clear(s.x, s.y, lw, lh)
    ));
    if (!spot) continue;
    claim(spot.x, spot.y, lw, lh);
    svg.appendChild(el('text', { class: 'ch-code', x: spot.tx, y: spot.ty, 'text-anchor': spot.anchor }, c.code));
  }

  // The visitor. A ring rather than a fourth shade: this is not one of the
  // twenty, it is the thing being built.
  svg.appendChild(el('circle', { class: 'ch-you-halo', cx: mx, cy: my, r: narrow ? 9 : 10 }));
  svg.appendChild(el('circle', { class: 'ch-you', cx: mx, cy: my, r: narrow ? 6 : 6.5 }));
  svg.appendChild(el('circle', { class: 'ch-you-core', cx: mx, cy: my, r: 2.2 }));

  host.replaceChildren(svg);
  return svg;
}
