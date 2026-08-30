// Statecraft's opening image: a radial fingerprint of the thirteen policies.
//
// WHAT IS DRAWN. One spoke per domain, in data.domains order, each scaled to
// that domain's own axis using the bounds in data.axes, so a spoke's length is
// where that policy sits on the measured range rather than on a made-up scale.
// Two shapes: the visitor's design, and the country they started from.
//
// WHY THE STARTING COUNTRY AND NOT THE NEAREST MATCH. The nearest match is the
// answer the reveal button exists to give, and printing its shape at the top of
// the page would hand it over before the visitor has built anything. The
// starting country gives nothing away, and it is the better comparison anyway:
// the two shapes begin exactly superimposed and every slider the visitor moves
// pulls their outline off the one underneath. The graphic's job is distance
// travelled from where you began.
//
// WHY BOTH SHAPES COME OUT OF THE CODED MODEL. The starting country's spokes are
// read from its own thirteen coded choices through the same option axis values
// the visitor's are, not from its measured indicators. That is what makes the
// two shapes identical on load. A shape drawn from the measured indicators would
// have sat a little off the design the visitor was told they were starting from,
// which is the opposite of the property this graphic is here for. The one
// exception is tax, where the slider is continuous: both sides use the rate, the
// visitor's live and the country's the rate its own state runs at, which are the
// same number until the slider moves.
//
// DRAWN AT CONTAINER PIXEL SCALE. The viewBox comes from the host's own bounding
// rect, so one user unit is one CSS pixel and an 11.5px label renders at 11.5px
// on a phone. Redrawn on resize and on a theme change.
//
// LABELS, WHICH ARE THE HARD PART. Thirteen names round a ring do not fit on a
// phone, and shrinking one to make it fit is not allowed here. The full domain
// names were measured first and they do not fit at any width this page can
// reach either: the panel caps at 48rem, and at that width "Speech and
// Information" and "Voting and Representation" sit next to each other at the
// bottom of the ring and would need a radius of about 360px to clear. So the
// ring is labelled with each domain's first word, which is distinct across all
// thirteen, and below the width where even those fit the labels are dropped
// entirely rather than shrunk or clipped. Both tiers are built, measured with
// getBBox, and rejected if any label leaves the panel or touches its neighbour.
// A tier is taken whole or not at all, so the ring never ends up with nine names
// and four gaps.

import { TAX, startingRate } from './budget.js';
import { axisValues } from './match.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

// A spoke never starts at the hub. A reading at the bottom of its range is a
// reading, and collapsing it onto the centre point would make thirteen
// different floors look like one.
const HUB = 0.1;

function el(name, attrs, text) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, String(v));
  if (text !== undefined) node.textContent = text;
  return node;
}

function reducedMotion() {
  try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (err) { return false; }
}

/** Everything the fingerprint needs that does not change while the visitor drags. */
export function chartBase(data) {
  const axisFor = new Map();
  for (const axis of data.axes) {
    if (axis.domain) axisFor.set(axis.domain, axis);
  }
  const spokes = data.domains.map((domain) => {
    const axis = axisFor.get(domain.id) || null;
    return {
      id: domain.id,
      name: domain.name,
      short: String(domain.name).split(' ')[0],
      axisId: axis ? axis.id : null,
      lo: axis ? axis.bounds[0] : 0,
      hi: axis ? axis.bounds[1] : 1,
      unit: axis ? axis.unit : '',
      label: axis ? axis.label : domain.name,
    };
  });
  return { spokes };
}

/** A value on an axis as 0 to 1 of its own bounds, or null where it does not apply. */
function norm(spoke, value) {
  if (value === null || value === undefined || !Number.isFinite(value)) return null;
  const span = spoke.hi - spoke.lo;
  if (!span) return null;
  return Math.max(0, Math.min(1, (value - spoke.lo) / span));
}

const clampRate = (r) => Math.min(TAX.MAX, Math.max(TAX.MIN, Number(r)));

/**
 * The two shapes, as arrays of 0-to-1 positions with null for "does not apply".
 * @returns {{you: Array<number|null>, them: Array<number|null>, gaps: string[]}}
 */
export function fingerprint(data, base, view) {
  const mine = axisValues(data, view.selection);
  const country = data.countries.find((c) => c.code === view.startCode) || null;
  const theirs = country ? axisValues(data, country.choices) : {};
  const theirRate = country ? clampRate(startingRate(data, country)) : TAX.MIN;

  const you = [];
  const them = [];
  const gaps = [];
  for (const spoke of base.spokes) {
    const isTax = spoke.id === 'tax';
    const a = norm(spoke, isTax ? clampRate(view.rate) : mine[spoke.axisId]);
    const b = norm(spoke, isTax ? theirRate : theirs[spoke.axisId]);
    you.push(a);
    them.push(b);
    if (a === null || b === null) gaps.push(spoke.name);
  }
  // Computed ONCE, here, and used by both the drawing and the key. Worked out
  // separately in two places they could disagree, and the failure would be a
  // key naming an outline that is not on screen.
  const differs = you.some((v, i) => {
    const t = them[i];
    if (v === null || t === null) return v !== t;
    return Math.abs(v - t) > 0.002;
  });
  return { you, them, gaps, differs };
}

/** Ring geometry for thirteen spokes, twelve o'clock first and clockwise. */
function angles(n) {
  const out = [];
  for (let i = 0; i < n; i += 1) out.push(-Math.PI / 2 + (i * 2 * Math.PI) / n);
  return out;
}

function point(cx, cy, ang, r) {
  return [cx + Math.cos(ang) * r, cy + Math.sin(ang) * r];
}

/** The n-gon at a given fraction of the outer radius, used for the guide rings. */
function ringPath(cx, cy, angs, r) {
  return angs
    .map((a, i) => {
      const [x, y] = point(cx, cy, a, r);
      return `${i ? 'L' : 'M'}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join('') + 'Z';
}

/**
 * Fill and stroke for one shape.
 *
 * A null spoke is not plotted. Zero would read as a real measurement of nothing,
 * and a straight chord across the gap would read as an interpolation nobody
 * made. Instead the outline breaks: the stroke stops at the last spoke with a
 * reading and picks up at the next one, and the fill closes through the hub, so
 * the missing policy shows as a wedge cut out of the shape.
 */
function shapePath(cx, cy, angs, radii, outer) {
  const n = radii.length;
  const present = radii.map((v) => v !== null);
  const count = present.filter(Boolean).length;
  if (count === 0) return { fill: '', stroke: '' };

  const at = (i) => {
    const r = outer * (HUB + (1 - HUB) * radii[i]);
    const [x, y] = point(cx, cy, angs[i], r);
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  };

  if (count === n) {
    const d = radii.map((_, i) => `${i ? 'L' : 'M'}${at(i)}`).join('') + 'Z';
    return { fill: d, stroke: d };
  }

  // Walk the ring from the first spoke that follows a gap, so each run of
  // readings is contiguous rather than wrapping round the twelve o'clock seam.
  let start = 0;
  for (let i = 0; i < n; i += 1) {
    if (!present[(i + n - 1) % n] && present[i]) { start = i; break; }
  }
  const runs = [];
  let run = [];
  for (let k = 0; k < n; k += 1) {
    const i = (start + k) % n;
    if (present[i]) {
      run.push(i);
    } else if (run.length) {
      runs.push(run);
      run = [];
    }
  }
  if (run.length) runs.push(run);

  const fill = runs
    .map((r) => `M${cx.toFixed(2)},${cy.toFixed(2)}` + r.map((i) => `L${at(i)}`).join('') + 'Z')
    .join('');
  const stroke = runs
    .map((r) => r.map((i, j) => `${j ? 'L' : 'M'}${at(i)}`).join(''))
    .join('');
  return { fill, stroke };
}

/* Fitting the labels -------------------------------------------------------
 * Measured once per size, not once per slider move. */

const fits = new WeakMap();   // host -> {w, h, mode}
const shapes = new WeakMap(); // host -> {you: number[], them: number[], raf: number}

// The margins a tier needs are measured, not guessed. Sideways it is the width
// of that tier's own longest label, because "Immigration and Citizenship" and
// "Immigration" want very different amounts of room and one fixed number would
// be wrong for one of them. Vertically it is the rendered height of a label
// plus the offset the twelve and six o'clock labels are pushed out by, which is
// what a guessed number got wrong first time round: the ring filled the panel
// and the bottom label fell off it, so every tier failed and the desktop ring
// came out with no names at all.
const TIERS = [
  { mode: 'short', min: 56 },
  { mode: 'none', mx: 12, my: 12, min: 40 },
];

function geometryFor(tier, w, h) {
  const mx = tier.mx === undefined ? 12 : tier.mx;
  const my = tier.my === undefined ? 12 : tier.my;
  const outer = Math.min(w / 2 - mx, h / 2 - my);
  return { cx: w / 2, cy: h / 2, outer };
}

function labelNodes(base, tier, w, h) {
  if (tier.mode === 'none') return [];
  const { cx, cy, outer } = geometryFor(tier, w, h);
  const angs = angles(base.spokes.length);
  return base.spokes.map((spoke, i) => {
    const a = angs[i];
    const [x, y] = point(cx, cy, a, outer + 11);
    const cos = Math.cos(a);
    const sin = Math.sin(a);
    const anchor = Math.abs(cos) < 0.3 ? 'middle' : (cos > 0 ? 'start' : 'end');
    const dy = sin < -0.85 ? -1 : (sin > 0.85 ? 10 : 4);
    return el('text', {
      class: 'fp-lab',
      x: x.toFixed(1),
      y: (y + dy).toFixed(1),
      'text-anchor': anchor,
    }, spoke.short);
  });
}

/** True when every label sits inside the panel and clear of its neighbours. */
function labelsFit(nodes, w, h) {
  const boxes = nodes.map((node) => node.getBBox());
  for (const b of boxes) {
    if (b.x < 1 || b.y < 1 || b.x + b.width > w - 1 || b.y + b.height > h - 1) return false;
  }
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      const a = boxes[i];
      const b = boxes[j];
      if (a.x < b.x + b.width + 3 && b.x < a.x + a.width + 3
        && a.y < b.y + b.height + 2 && b.y < a.y + a.height + 2) return false;
    }
  }
  return true;
}

/** The best tier that measures clean at this size. Cached per host and size. */
function chooseTier(host, base, w, h) {
  const cached = fits.get(host);
  if (cached && cached.w === w && cached.h === h) {
    const tier = TIERS.find((t) => t.mode === cached.mode) || TIERS[1];
    tier.mx = cached.mx;
    tier.my = cached.my;
    return tier;
  }

  const probe = el('svg', { viewBox: `0 0 ${w} ${h}`, width: w, height: h, 'aria-hidden': 'true' });
  probe.style.position = 'absolute';
  probe.style.visibility = 'hidden';
  host.appendChild(probe);

  // The widest and tallest label this tier would draw, in rendered pixels.
  const measure = () => {
    const nodes = base.spokes.map((s2) => el('text', { class: 'fp-lab', x: 0, y: 40 }, s2.short));
    probe.replaceChildren(...nodes);
    const boxes = nodes.map((n) => n.getBBox());
    return {
      w: Math.max(...boxes.map((b) => b.width)),
      h: Math.max(...boxes.map((b) => b.height)),
    };
  };

  let chosen = TIERS[1];
  for (const tier of TIERS) {
    if (tier.mode !== 'none') {
      const m = measure();
      tier.mx = Math.ceil(m.w) + 14;
      tier.my = Math.ceil(m.h) + 13;
    }
    const { outer } = geometryFor(tier, w, h);
    if (outer < tier.min) continue;
    if (tier.mode === 'none') { chosen = tier; break; }
    const nodes = labelNodes(base, tier, w, h);
    probe.replaceChildren(...nodes);
    if (labelsFit(nodes, w, h)) { chosen = tier; break; }
  }
  probe.remove();

  fits.set(host, { w, h, mode: chosen.mode, mx: chosen.mx, my: chosen.my });
  return chosen;
}

/* Drawing ------------------------------------------------------------------ */

/**
 * @param {HTMLElement} host  the element the svg is drawn into
 * @param {object} data       parsed data.json
 * @param {object} base       chartBase(data)
 * @param {object} view       {startCode, selection, rate}
 * @returns {{gaps: string[]}} the domains with no reading on one side or both
 */
export function drawChart(host, data, base, view) {
  const box = host.getBoundingClientRect();
  const w = Math.max(240, Math.round(box.width));
  const h = Math.max(200, Math.round(box.height));
  if (w < 240 || h < 160) return { gaps: [], differs: false };

  const { you, them, gaps, differs } = fingerprint(data, base, view);
  const tier = chooseTier(host, base, w, h);
  const { cx, cy, outer } = geometryFor(tier, w, h);
  const angs = angles(base.spokes.length);

  const country = data.countries.find((c) => c.code === view.startCode);
  const startName = country ? country.name : view.startCode;

  const svg = el('svg', {
    viewBox: `0 0 ${w} ${h}`,
    width: w,
    height: h,
    role: 'img',
    'aria-label': `Thirteen policies drawn as spokes. Your design, and ${startName}, the country you started from. On load the two outlines are the same shape and every slider you move pulls yours off it.`,
  });

  // Guide rings, quarter by quarter of each policy's own range.
  for (const f of [0.25, 0.5, 0.75, 1]) {
    svg.appendChild(el('path', {
      class: f === 1 ? 'fp-ring fp-ring-out' : 'fp-ring',
      d: ringPath(cx, cy, angs, outer * (HUB + (1 - HUB) * f)),
    }));
  }

  // Spokes. One is dashed where that policy has no reading on either shape.
  base.spokes.forEach((spoke, i) => {
    const [x, y] = point(cx, cy, angs[i], outer);
    const [hx, hy] = point(cx, cy, angs[i], outer * HUB);
    const missing = you[i] === null || them[i] === null;
    svg.appendChild(el('line', {
      class: missing ? 'fp-spoke fp-spoke-na' : 'fp-spoke',
      x1: hx.toFixed(2), y1: hy.toFixed(2), x2: x.toFixed(2), y2: y.toFixed(2),
    }));
  });

  if (tier.mode !== 'none') {
    for (const node of labelNodes(base, tier, w, h)) svg.appendChild(node);
  }

  const themFill = el('path', { class: 'fp-them-fill' });
  const youFill = el('path', { class: 'fp-you-fill' });
  const youLine = el('path', { class: 'fp-you-line' });
  const themLine = el('path', { class: 'fp-them-line' });
  // THE STARTING COUNTRY'S OUTLINE GOES LAST, over your fill.
  //
  // Drawn underneath it disappeared: your shape carries a fill, so once three
  // sliders had moved, the country you started from was a sliver visible in one
  // corner. The point of this graphic is the GAP between the two outlines, and
  // an outline you cannot see has no gap. It is unfilled and dashed so it reads
  // as a reference line rather than as a second country competing for attention.
  svg.append(themFill, youFill, youLine, themLine);

  // A readable value per spoke, on hover and for a screen reader.
  base.spokes.forEach((spoke, i) => {
    const [x, y] = point(cx, cy, angs[i], outer * (HUB + (1 - HUB) * (you[i] === null ? 0.5 : you[i])));
    const hit = el('circle', { class: 'fp-hit', cx: x.toFixed(2), cy: y.toFixed(2), r: 9 });
    const mine = you[i] === null ? 'does not apply' : `${Math.round(you[i] * 100)} of the way up the ${spoke.label.toLowerCase()} range`;
    hit.appendChild(el('title', {}, `${spoke.name}: ${mine}`));
    svg.appendChild(hit);
  });

  // THE REFERENCE OUTLINE IS HIDDEN WHILE IT HAS NOTHING TO SAY.
  //
  // On load the two shapes are identical by construction, and the reference is
  // painted last so it sits over your fill. The result was that the page opened
  // showing nothing but a dashed grey outline: your design's own colour was
  // underneath it and never appeared, and the card shot from the live page came
  // back with no accent in it at all. A dashed line lying exactly on a solid one
  // is also just noise, since there is no gap yet to read.
  //
  // So it appears the moment the two differ, which is also when it starts
  // meaning something. `moved` is passed by the caller.
  const paint = (a, b, differs) => {
    const t = shapePath(cx, cy, angs, b, outer);
    const y = shapePath(cx, cy, angs, a, outer);
    themFill.setAttribute('d', t.fill);
    themLine.setAttribute('d', t.stroke);
    youFill.setAttribute('d', y.fill);
    youLine.setAttribute('d', y.stroke);
    const show = differs ? 'inline' : 'none';
    themFill.style.display = show;
    themLine.style.display = show;
  };

  // Animation. The outline eases toward its new shape so a slider move is
  // visibly a deformation rather than a jump cut, and rapid drags simply move
  // the target under a loop that is already running.
  const prev = shapes.get(host);
  if (prev && prev.raf) cancelAnimationFrame(prev.raf);

  const canAnimate = prev && !reducedMotion()
    && prev.you.length === you.length
    && prev.you.every((v, i) => (v === null) === (you[i] === null))
    && prev.them.every((v, i) => (v === null) === (them[i] === null));

  if (!canAnimate) {
    paint(you, them, differs);
    shapes.set(host, { you: you.slice(), them: them.slice(), raf: 0 });
  } else {
    const cur = { you: prev.you.slice(), them: prev.them.slice(), raf: 0 };
    shapes.set(host, cur);
    paint(cur.you, cur.them, differs);
    let last = performance.now();
    const step = (now) => {
      const k = 1 - Math.exp(-(now - last) / 70);
      last = now;
      let moving = false;
      for (const key of ['you', 'them']) {
        const target = key === 'you' ? you : them;
        for (let i = 0; i < target.length; i += 1) {
          if (target[i] === null || cur[key][i] === null) { cur[key][i] = target[i]; continue; }
          const d = target[i] - cur[key][i];
          if (Math.abs(d) < 0.0015) { cur[key][i] = target[i]; continue; }
          cur[key][i] += d * k;
          moving = true;
        }
      }
      paint(cur.you, cur.them, differs);
      cur.raf = moving ? requestAnimationFrame(step) : 0;
    };
    cur.raf = requestAnimationFrame(step);
  }

  host.replaceChildren(svg);
  return { gaps, differs };
}
