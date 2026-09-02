// Statecraft, the builder screen. Wiring only.
//
// Every decision worth testing lives in budget.js, cascade.js, match.js and
// state.js. This file owns the DOM and nothing else: it reads data.json, paints
// the chart, the picker, the meters and the thirteen sliders, and keeps them in
// step with one immutable state object.
//
// THE ONE RULE THIS FILE ADDS. A move is never applied by writing to `state`
// directly. It goes through applyChange or setTaxRate, which return a whole new
// state with the cascade already run, and then the page repaints from that. The
// sliders are outputs, not the record.

import {
  TAX, TAX_DOMAIN, budgets, blockers, realisedRevenue, rateForOption, startingState,
  ladder, positionsOf, valuesAt, posFromSelection, reformCost,
} from './budget.js';
import { applyChange, setTaxRate, toggleLock, isLocked } from './cascade.js';
import { rank, matchable } from './match.js';
import { renderReveal } from './reveal.js';
import { encode, decode, countryForTimezone, detectTimezone } from './state.js';
import { chartBase, drawChart } from './chart.js';

const THEME_KEY = 'sc-theme';
// 0.1, not 0.5. A 43 point range in half-point steps is 86 stops and the thumb
// visibly stairs on a slow drag. The tax figure is shown to one decimal anyway.
const RATE_STEP = 0.1;

/* Theme -------------------------------------------------------------------
 * With nothing stored the page follows the system, so an explicit choice is
 * the only thing ever written. Private windows throw on localStorage, hence
 * the try/catch on both sides. */

function readStored(key) {
  try { return localStorage.getItem(key); } catch (err) { return null; }
}

function writeStored(key, value) {
  try { localStorage.setItem(key, value); } catch (err) { /* private window */ }
}

function systemIsDark() {
  try { return window.matchMedia('(prefers-color-scheme: dark)').matches; } catch (err) { return false; }
}

function reducedMotion() {
  try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (err) { return false; }
}

function currentTheme() {
  const stamped = document.documentElement.getAttribute('data-theme');
  if (stamped === 'dark' || stamped === 'light') return stamped;
  return systemIsDark() ? 'dark' : 'light';
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const label = document.getElementById('themeLbl');
  // The label names where the button takes you, not where you are.
  if (label) label.textContent = theme === 'dark' ? 'Light' : 'Dark';
}

function setUpTheme() {
  const saved = readStored(THEME_KEY);
  if (saved === 'dark' || saved === 'light') {
    applyTheme(saved);
  } else {
    const label = document.getElementById('themeLbl');
    if (label) label.textContent = systemIsDark() ? 'Light' : 'Dark';
  }
  const btn = document.getElementById('themeBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      const next = currentTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      writeStored(THEME_KEY, next);
      paintChart();
    });
  }
}

/* Helpers ------------------------------------------------------------------ */

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const one = (n) => Number(n).toFixed(1);

/* State -------------------------------------------------------------------- */

let data = null;
let base = null;           // chartBase(data), fixed for the session
let state = null;          // {start, taxRate, selection, pos, locked}
let previewRate = null;    // the tax slider mid-drag, before the cascade runs
// The same idea for the twelve categorical sliders, which are continuous too as
// of 01/09/2026: mid-drag the position is a preview, so the budget, the meters
// and the fingerprint follow the thumb, and nothing is cut until the visitor
// lets go. Cutting on every frame would empty the country on the way past.
let previewPos = null;     // {id, value} or null
// The slider currently under a finger. render() writes every slider's value back
// from state, which on a continuous drag would yank the thumb to the nearest
// stop on every frame and undo the whole point of the fine step. The one being
// dragged is left alone until it is released.
let draggingId = null;
let touched = false;       // has the visitor actually changed anything yet
let revealed = false;      // has the visitor asked for the result at least once
let noteTimer = 0;
const tweens = new Map();

function countryName(code) {
  const hit = data.countries.find((c) => c.code === code);
  return hit ? hit.name : code;
}

function domainOf(id) {
  return data.domains.find((d) => d.id === id);
}

function optionOf(domainId, optionId) {
  const domain = domainOf(domainId);
  return domain ? (domain.options || []).find((o) => o.id === optionId) : null;
}

function baseline() {
  const country = data.countries.find((c) => c.code === state.start);
  return country ? country.choices : {};
}

/** "Australia, Canada, Ireland and 3 more", or the deliberate "Nowhere yet." */
function whereLine(codes) {
  const list = (codes || []).map(countryName);
  if (!list.length) return 'Nowhere yet.';
  if (list.length <= 4) {
    const last = list.pop();
    return list.length ? `${list.join(', ')} and ${last}.` : `${last}.`;
  }
  const shown = list.slice(0, 4);
  return `${shown.join(', ')} and ${list.length - 4} more.`;
}

/** The state the meters, the chart and the reveal are drawn from. */
function liveState() {
  let live = state;
  if (previewRate !== null) live = { ...live, taxRate: previewRate };
  if (previewPos) {
    const held = valuesAt(data, previewPos.id, previewPos.value);
    if (held) {
      live = {
        ...live,
        pos: { ...positionsOf(data, live), [previewPos.id]: held.pos },
        // The identity follows the thumb too, so the label, the chip and the
        // reveal all say the same thing the meters are pricing.
        selection: { ...live.selection, [previewPos.id]: held.optionId },
      };
    }
  }
  return live;
}

/* Painting ------------------------------------------------------------------ */

// Only matchable countries can be a STARTING country. Picking a start loads
// that country's thirteen choices as the design, so a measured-only country
// would open the page on an empty selection with every meter reading nothing.
// Added 30/08/2026 with the twenty-five measured-only rows; before that every
// country in the file had a matrix and the filter was not needed.
function paintPicker() {
  const sel = document.getElementById('startSel');
  const sorted = matchable(data).slice().sort((a, b) => a.name.localeCompare(b.name, 'en'));
  sel.innerHTML = sorted
    .map((c) => `<option value="${esc(c.code)}">${esc(c.name)}</option>`)
    .join('');
  sel.value = state.start;
}

/** Names the shapes on screen, and the break where a policy has no reading.
 *
 * The starting country's entry appears only once its outline does. Until the
 * visitor moves something the two shapes are identical and the reference is
 * hidden, so naming it would point at a line nobody can see. */
function paintKey(startCode, gaps, differs) {
  const gapNote = (gaps || []).length
    ? `<span class="ck"><i class="ck-sw ck-gap" aria-hidden="true"></i>Break in the outline: ${esc((gaps || []).join(' and '))} has no reading here</span>`
    : '';
  const themEntry = differs
    ? `<span class="ck"><i class="ck-sw ck-them" aria-hidden="true"></i>${esc(countryName(startCode))}</span>`
    : '';
  document.getElementById('chartKey').innerHTML = `
    <span class="ck"><i class="ck-sw ck-you" aria-hidden="true"></i>Your country</span>
    ${themEntry}
    ${gapNote}`;
}

/** What this domain was when you arrived, and what moving it has cost.
 *
 * Unchanged it says so. Changed, it names the policy you left and the money the
 * move costs, signed, so a slider carries its own before and after rather than
 * only its current state. */
function sinceStart(id, live) {
  const from = baseline()[id];
  const to = live.selection[id];
  if (from === to) return '<span class="d-home">Where you started</span>';

  const a = optionOf(id, from);
  const b = optionOf(id, to);
  if (!a || !b) return '';

  if (id === TAX_DOMAIN) {
    const was = rateForOption(data, from);
    const now = Number(live.taxRate);
    const d = now - was;
    return `<span class="d-was">Was ${esc(one(was))}%, now ${esc(one(now))}%`
      + `<b>${d >= 0 ? '+' : ''}${esc(one(d))} points</b></span>`;
  }

  const d = (b.financial || 0) - (a.financial || 0);
  const money = Math.abs(d) < 0.05
    ? 'about the same money'
    : `${d > 0 ? '+' : ''}${one(d)}% of GDP`;
  return `<span class="d-was">Was ${esc(a.label)}<b>${esc(money)}</b></span>`;
}

/** One slider per domain, painted once. Values are written by render(). */
function paintDomains() {
  const host = document.getElementById('domains');

  host.innerHTML = data.domains.map((domain, i) => {
    const isTax = domain.id === TAX_DOMAIN;
    // Only the first section spells the padlock out. Thirteen copies of the
    // word would be noise; none at all and nobody finds the feature.
    const first = i === 0;
    const rungs = isTax ? [] : ladder(data, domain.id);
    const rangeAttrs = isTax
      ? `min="${TAX.MIN}" max="${TAX.MAX}" step="${RATE_STEP}"`
      // A fine step, not one per option. With step="1" a five-option slider has
      // five thumb positions and the drag is a stair; the policy still snaps to
      // the nearest stop, but the thumb follows the finger and lands on release.
      : `min="0" max="${Math.max(0, rungs.length - 1)}" step="0.01"`;
    const ends = isTax
      ? [`Taxes least, ${TAX.MIN}%`, `Taxes most, ${TAX.MAX}%`]
      : ['Spends least', 'Spends most'];

    // A tick per stop, so a slider with five settings looks like a slider with
    // five settings. On tax the ticks are the six coded regimes, which is the
    // only thing about a continuous rate that is not continuous.
    const stops = isTax
      ? (domain.options || []).slice().sort((a, b) => a.rate - b.rate)
        .map((o) => ({ id: o.id, at: (o.rate - TAX.MIN) / (TAX.MAX - TAX.MIN) }))
      : rungs.map((o, i) => ({ id: o.id, at: rungs.length > 1 ? i / (rungs.length - 1) : 0 }));
    const ticks = stops
      .map((s) => `<i data-stop="${esc(s.id)}" style="left:${(s.at * 100).toFixed(3)}%"></i>`)
      .join('');

    return `
    <section class="domain${isTax ? ' tax' : ''}" id="dom_${esc(domain.id)}" data-domain="${esc(domain.id)}">
      <div class="d-head">
        <h2 id="h_${esc(domain.id)}">${esc(domain.name)}</h2>
        <span class="chip" id="chip_${esc(domain.id)}" hidden>Changed</span>
        ${`<button class="lock" type="button" id="lock_${esc(domain.id)}"
                data-lock="${esc(domain.id)}" aria-pressed="false">
          <svg class="lk" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
            <rect class="lk-body" x="3" y="7" width="10" height="7" rx="1.6"/>
            <path class="lk-shackle" fill="none" stroke-width="1.7" stroke-linecap="round"/>
          </svg><span class="lk-hint">Lock</span>
        </button>`}
      </div>
      <div class="d-slide">
        <span class="d-rail" aria-hidden="true"></span>
        <span class="d-ticks" id="tk_${esc(domain.id)}" aria-hidden="true">${ticks}</span>
        <input class="rng" type="range" id="rng_${esc(domain.id)}" data-range="${esc(domain.id)}"
               ${rangeAttrs} aria-labelledby="h_${esc(domain.id)}" aria-describedby="val_${esc(domain.id)}">
        <p class="d-ends"><span>${esc(ends[0])}</span><span>${esc(ends[1])}</span></p>
      </div>
      <p class="d-val" id="val_${esc(domain.id)}"></p>
      <p class="d-detail" id="det_${esc(domain.id)}"></p>
      <p class="d-where" id="who_${esc(domain.id)}"></p>
      <p class="d-cut" id="cut_${esc(domain.id)}" hidden></p>
    </section>`;
  }).join('');

  host.addEventListener('input', (ev) => {
    const input = ev.target;
    if (!input || !input.dataset || !input.dataset.range) return;
    const id = input.dataset.range;
    if (id === TAX_DOMAIN) {
      // Mid-drag the rate is a preview: the budget moves with the thumb, but
      // nothing is cut until the visitor lets go. Cutting on every pixel of a
      // drag would empty the country on the way past.
      previewRate = Number(input.value);
      touched = true;
      render();
      return;
    }
    // The thumb is continuous and so is what it costs. Mid-drag the position is
    // a preview: the money and the shape move with the finger, and the cascade
    // waits for the release. The label still snaps, because there is no such
    // country as two thirds of a health system.
    draggingId = id;
    previewPos = { id, value: Number(input.value) };
    touched = true;
    render();
  });

  host.addEventListener('change', (ev) => {
    const input = ev.target;
    if (!input || !input.dataset || !input.dataset.range) return;
    const id = input.dataset.range;
    if (id === TAX_DOMAIN) {
      previewRate = null;
      commit(setTaxRate(data, state, Number(input.value)));
      return;
    }
    // The thumb rests where it was left. It is not snapped back to a rung any
    // more: the position between two options is a real setting with a real
    // price, and pulling the thumb off it on release would take that back.
    draggingId = null;
    previewPos = null;
    commit(applyChange(data, state, id, Number(input.value)));
  });

  host.addEventListener('click', (ev) => {
    const btn = ev.target.closest ? ev.target.closest('[data-lock]') : null;
    if (!btn) return;
    state = toggleLock(state, btn.dataset.lock);
    touched = true;
    render();
  });
}

/* Method -------------------------------------------------------------------
 * Painted once at boot. It depends on data.json and nothing else, so nothing
 * here re-renders when a choice changes. */

/** Signed, so one column can hold both what an option raises and what it spends. */
function budgetEffect(o) {
  if (typeof o.rate === 'number') return `${o.rate}% take`;
  const v = -(o.financial || 0);
  return `${one(v)}`;
}

function costTable() {
  // Colour-coded by domain, matching the sliders above. The swatch and the
  // domain name carry the section's own hue so a reader scanning the table can
  // find the block they were just looking at.
  const rows = data.domains.map((d) => (d.options || []).map((o, i) => `
      <tr style="--dom: var(--dom-${esc(d.id)})">
        <td class="mt-dom">${i === 0
          ? `<i class="mt-sw" aria-hidden="true"></i>${esc(d.name)}`
          : ''}</td>
        <td>${esc(o.label)}</td>
        <td class="num">${esc(budgetEffect(o))}</td>
        <td class="num">${esc(Math.round(reformCost(o.political)))}</td>
        <td class="num">${esc(Math.round(reformCost(o.social)))}</td>
      </tr>`).join('')).join('');

  return `
    <table class="mt">
      <thead>
        <tr>
          <th scope="col">Domain</th>
          <th scope="col">Option</th>
          <th scope="col" class="num">Budget, % of GDP</th>
          <th scope="col" class="num">Political capital</th>
          <th scope="col" class="num">Public patience</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function axisTable() {
  const rows = data.axes.map((a) => `
      <tr>
        <td>${esc(a.label)}</td>
        <td>${esc(a.unit)}</td>
        <td>${esc(a.bounds[0])} to ${esc(a.bounds[1])}</td>
        <td>${a.url
          ? `<a href="${esc(a.url)}" rel="noopener">${esc(a.source)}</a>`
          : esc(a.source)}</td>
      </tr>`).join('');

  return `
    <table class="mt">
      <thead>
        <tr>
          <th scope="col">Axis</th>
          <th scope="col">Unit</th>
          <th scope="col">Track runs</th>
          <th scope="col">Source</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function paintMethod() {
  // THREE BASES, NOT TWO. A tax option's figure is the rate on its stop, which
  // is neither a median of countries nor a judgement, so counting it as either
  // would put a wrong number in the sentence below.
  const options = data.domains.reduce((n, d) => n + (d.options || []).length, 0);
  const hand = [];
  let slider = 0;
  for (const d of data.domains) {
    for (const o of (d.options || [])) {
      if (o.axis_basis === 'hand') hand.push(`${d.name}, ${o.label}`);
      else if (o.axis_basis === 'the rate on the slider') slider += 1;
    }
  }
  const derived = options - hand.length - slider;

  document.getElementById('method').innerHTML = `
  <h2>Method</h2>

  <p>Your match is a count. One point for every domain where you picked the policy that country actually runs. Countries level on that count are separated by how far your settings sit from theirs on the measured axes.</p>

  <p>Budget is in per cent of GDP and the tax rate sets how much of it you have. Political capital and public patience are pools of 100 points, and both are charged only on the domains you move away from where you started.</p>

  <p>${derived} of the ${options} option figures are the median of the countries running that policy. The ${slider} tax figures are just the rate you set. I set the last ${hand.length} by hand, along with every cost in the table below.</p>

  <details class="mdet">
    <summary>Every option and what it costs</summary>
    <div class="scroller">${costTable()}</div>
  </details>

  <details class="mdet">
    <summary>The ${data.axes.length} axes and their sources</summary>
    <div class="scroller">${axisTable()}</div>
  </details>

`;
}

function paintMeter(key, b, text) {
  const box = document.getElementById(`m-${key}`);
  document.getElementById(`f-${key}`).textContent = text;
  const pct = b.capacity > 0 ? Math.max(0, Math.min(100, (b.used / b.capacity) * 100)) : 0;
  document.getElementById(`b-${key}`).style.width = `${pct}%`;
  box.classList.toggle('over', !!b.over);
}

/* The chart ---------------------------------------------------------------- */

function paintChart() {
  const host = document.getElementById('chartHost');
  if (!host || !data) return;
  const live = liveState();
  const b = budgets(data, live);
  const info = drawChart(host, data, base, {
    startCode: live.start,
    selection: live.selection,
    pos: positionsOf(data, live),
    // True while a thumb is under a finger, so the fingerprint follows it 1:1
    // instead of easing toward a target that moves again next frame.
    live: previewPos !== null || previewRate !== null,
    rate: b.financial.taxRate,
  });
  // The key names the starting country, so it is rewritten whenever the chart
  // is: the picker can change which country the second shape belongs to.
  const differs = info ? info.differs : false;
  paintKey(live.start, info ? info.gaps : [], differs);
  // States what is on screen. Until something moves that is simply the starting
  // country, and saying so is more use than describing the chart.
  document.getElementById('chartCap').textContent = differs
    ? ''
    : `This is ${countryName(live.start)}, until you change something.`;
}

/* Moving a slider ----------------------------------------------------------- */

/** Slide a range input to a value it did not get to by hand. */
function tweenRange(input, to) {
  const from = Number(input.value);
  if (from === to) return;
  const old = tweens.get(input.id);
  if (old) cancelAnimationFrame(old);
  if (reducedMotion()) {
    input.value = String(to);
    return;
  }
  const started = performance.now();
  const ms = 420;
  const step = (now) => {
    const t = Math.min(1, (now - started) / ms);
    const eased = 1 - Math.pow(1 - t, 3);
    input.value = String(from + (to - from) * eased);
    if (t < 1) {
      tweens.set(input.id, requestAnimationFrame(step));
    } else {
      input.value = String(to);
      tweens.delete(input.id);
    }
  };
  tweens.set(input.id, requestAnimationFrame(step));
}

/** Take the result of applyChange or setTaxRate and repaint from it. */
function commit(res) {
  if (!res) return;
  // Defensive: a protected slider is disabled, so this should be unreachable.
  if (!res.ok && res.reason === 'locked') {
    showNote('<p class="cs-lead">That policy is protected, so it did not move. Release it first.</p>');
    render();
    return;
  }
  state = res.state;
  touched = true;
  render({ cuts: res.cuts, moved: res.moved, shortfall: res.shortfall });
  announce(res);
}

/* What paid for the move ---------------------------------------------------- */

function showNote(html) {
  const box = document.getElementById('cascade');
  box.innerHTML = `${html}<button class="cs-x" type="button" id="csX" aria-label="Dismiss">Dismiss</button>`;
  box.hidden = false;
  document.getElementById('csX').addEventListener('click', () => { box.hidden = true; });
  if (noteTimer) clearTimeout(noteTimer);
  noteTimer = setTimeout(() => { box.hidden = true; }, 12000);
  syncFinishSpace();
}

function announce(res) {
  const box = document.getElementById('cascade');
  if (!res.cuts.length && !res.shortfall) {
    box.hidden = true;
    return;
  }

  const movedName = res.moved ? res.moved.domainName : 'that change';
  const items = res.cuts.map((c) => {
    const now = optionOf(c.domain, c.to);
    return `<li><button type="button" data-goto="${esc(c.domain)}" title="Now ${esc(now ? now.label : c.to)}">
      <span class="cs-dom">${esc(c.domainName)}</span>
      <span class="cs-now">saves ${esc(one(c.saved))}%</span>
    </button></li>`;
  }).join('');

  const lead = res.cuts.length
    ? `<p class="cs-lead">${esc(movedName)} was paid for by cutting ${res.cuts.length === 1 ? 'one policy' : `${res.cuts.length} policies`}. Go to what changed:</p>`
    : `<p class="cs-lead">${esc(movedName)} could not be paid for.</p>`;

  const short = res.shortfall
    ? `<p class="cs-short">There is nothing left to cut and you are still ${esc(one(res.shortfall))}% of GDP over. Lower the spending yourself or raise the tax rate.</p>`
    : '';

  showNote(`${lead}${items ? `<ul class="cs-list">${items}</ul>` : ''}${short}`);

  const box2 = document.getElementById('cascade');
  box2.querySelectorAll('[data-goto]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const section = document.getElementById(`dom_${btn.dataset.goto}`);
      if (!section) return;
      section.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'center' });
      flash(section);
    });
  });
}

function flash(section) {
  section.classList.remove('cut');
  // Reflow, so the class comes back and the animation runs a second time.
  void section.offsetWidth;
  section.classList.add('cut');
}

/* Render -------------------------------------------------------------------- */

function render(change) {
  const live = liveState();
  const livePos = positionsOf(data, live);
  const b = budgets(data, live);
  const startChoices = baseline();
  const cutIds = new Set((change && change.cuts ? change.cuts : []).map((c) => c.domain));

  paintMeter('financial', b.financial, `${one(b.financial.used)} of ${one(b.financial.capacity)}`);
  paintMeter('political', b.political, `${b.political.used} of ${b.political.capacity}`);
  paintMeter('social', b.social, `${b.social.used} of ${b.social.capacity}`);

  const changed = new Set(b.changed.map((c) => c.domain));

  for (const domain of data.domains) {
    const id = domain.id;
    const section = document.getElementById(`dom_${id}`);
    const input = document.getElementById(`rng_${id}`);
    const locked = isLocked(live, id);

    section.classList.toggle('changed', changed.has(id));
    section.classList.toggle('locked', locked);
    document.getElementById(`chip_${id}`).hidden = !changed.has(id);

    // The tax domain has no lock: the cascade never cuts tax, so locking it would
    // only stop the visitor dragging their own control.
    const lock = document.getElementById(`lock_${id}`);
    if (lock) {
    // Shut: the shackle sits on the body. Open: it lifts and hinges right.
    lock.querySelector('.lk-shackle').setAttribute('d', locked
      ? 'M5.4 7V5.1a2.6 2.6 0 0 1 5.2 0V7'
      : 'M5.4 7V5.1a2.6 2.6 0 0 1 5.2 0');
    // The button has no text, so it needs a name of its own. It says what the
    // control is FOR, not what the click does.
    lock.setAttribute('aria-label', locked
      ? `${domain.name} is locked and cannot be cut to pay for another policy`
      : `Lock ${domain.name} so it cannot be cut to pay for another policy`);
      lock.setAttribute('aria-pressed', locked ? 'true' : 'false');
      lock.title = locked
        ? 'This policy is held where it is and the budget will cut something else'
        : 'Hold this policy where it is when the budget has to find money';
    }
    input.disabled = locked;

    // The tick the starting country sits on, so the slider says where you began.
    const ticks = document.getElementById(`tk_${id}`);
    if (ticks) {
      ticks.querySelectorAll('i').forEach((tick) => {
        tick.classList.toggle('home', tick.dataset.stop === startChoices[id]);
      });
    }

    if (id === TAX_DOMAIN) {
      const rate = b.financial.taxRate;
      const target = String(rate);
      if (input.value !== target) {
        if (cutIds.has(id)) tweenRange(input, rate); else input.value = target;
      }
      const stop = optionOf(id, live.selection[id]);
      const nextPoint = rate >= TAX.MAX
        ? realisedRevenue(TAX.MAX) - realisedRevenue(TAX.MAX - 1)
        : realisedRevenue(Math.min(TAX.MAX, rate + 1)) - realisedRevenue(rate);
      input.setAttribute('aria-valuetext', `${one(rate)} per cent of GDP, ${stop ? stop.label : ''}`);

      document.getElementById(`val_${id}`).innerHTML = `
        <span class="d-big">${esc(one(rate))}%</span>
        <span class="d-opt">${esc(stop ? stop.label : '')}</span>
        <span class="d-cost">political capital ${esc(Math.round(reformCost(stop ? stop.political : 0)))}, public patience ${esc(Math.round(reformCost(stop ? stop.social : 0)))}</span>
        ${sinceStart(id, live)}`;
      document.getElementById(`det_${id}`).textContent =
        `Raises ${one(b.financial.realisedTax)}% of GDP. The next point of tax adds ${one(nextPoint)}, and at ${TAX.MAX} a point would add only ${one(realisedRevenue(TAX.MAX) - realisedRevenue(TAX.MAX - 1))}.`;
      document.getElementById(`who_${id}`).textContent = stop
        ? `${stop.detail} ${whereLine(stop.holders)}`
        : '';
      continue;
    }

    const rungs = ladder(data, id);
    const here = valuesAt(data, id, livePos[id]);
    const option = here ? here.option : rungs[0];
    const index = here ? here.pos : 0;
    if (id !== draggingId && Number(input.value) !== index) {
      if (cutIds.has(id)) tweenRange(input, index); else input.value = String(index);
    }
    // WHAT THE SLIDER SAYS AT A POSITION BETWEEN TWO OPTIONS. The label is the
    // nearer of the two, because that is the policy and the thing the reveal
    // will match on. The costs are the interpolated ones, because that is what
    // the meters have just charged, and a line saying 7.5 above a budget that
    // moved by 8.2 would be the page lying about its own arithmetic.
    const between = here && here.lo.id !== here.hi.id
      ? ` Part way to ${here.option.id === here.lo.id ? here.hi.label : here.lo.label}.`
      : '';
    const rung = Math.round(index);
    input.setAttribute('aria-valuetext', `${option ? option.label : ''}, ${one(here ? here.financial : 0)} per cent of GDP, step ${rung + 1} of ${rungs.length}`);

    document.getElementById(`val_${id}`).innerHTML = `
      <span class="d-opt">${esc(option ? option.label : '')}</span>
      <span class="d-cost">${esc(one(here ? here.financial : 0))}% of GDP, political capital ${esc(Math.round(reformCost(here ? here.political : 0)))}, public patience ${esc(Math.round(reformCost(here ? here.social : 0)))}</span>
      ${sinceStart(id, live)}`;
    document.getElementById(`det_${id}`).textContent = option ? `${option.detail}${between}` : '';
    document.getElementById(`who_${id}`).textContent = option ? whereLine(option.holders) : '';

    const cutLine = document.getElementById(`cut_${id}`);
    if (cutIds.has(id) && change.moved) {
      cutLine.textContent = `Cut to pay for ${change.moved.domainName}.`;
      cutLine.hidden = false;
      flash(section);
    } else if (!cutIds.has(id)) {
      cutLine.hidden = true;
    }
  }

  paintChart();

  const stuck = blockers(b);
  const names = { financial: 'the budget', political: 'political capital', social: 'public patience' };
  const btn = document.getElementById('revealBtn');
  btn.disabled = stuck.length > 0;
  btn.textContent = revealed ? 'Back to the result' : 'Show me which country this is';
  document.getElementById('blockedNote').textContent = stuck.length
    ? `You have spent more than you have of ${stuck.map((k) => names[k]).join(' and ')}. Trim something to reveal.`
    : '';

  // Once asked for, the result follows the design. A visitor who changes a
  // domain after revealing should not have to press the button a second time
  // to stop the panel telling them something that is no longer true.
  const result = document.getElementById('result');
  if (revealed && !stuck.length) {
    // ONE RATE, READ OFF THE BUDGET, for both the tiebreak and the axis row.
    // It is the same expression paintChart hands the fingerprint, so the tax
    // spoke and the tax axis row are drawn from a single number rather than two
    // that agree until somebody rounds one of them.
    const rate = b.financial.taxRate;
    result.innerHTML = renderReveal(data, rank(data, live.selection, rate), live.selection, livePos, rate);
    result.hidden = false;
  } else {
    result.hidden = true;
  }

  syncFinishSpace();

  // A fresh visit and a shared link must not look alike, so the default is
  // never written. The hash appears the moment the visitor changes something,
  // and it carries the rate, which the option index no longer implies.
  if (touched) {
    history.replaceState(null, '', `#${encode(data, state.start, state.selection, state.taxRate, state.pos)}`);
  }
}

/* The pinned action --------------------------------------------------------
 * The reveal button is pinned to the bottom of the viewport, so the primary
 * action is on the first screen at every width. The bar is out of flow, so the
 * page reserves exactly its measured height at the bottom: the blocked note
 * wraps to two lines on a phone and a hard-coded padding would let the bar sit
 * over the last paragraph of the method section. */

// The reveal is in the flow now rather than pinned to the window, so the body
// no longer reserves room for it and the cascade note has nothing to clear.
// Kept as a no-op call site would be worse than deleting it: the call is gone
// from boot() too.
function syncFinishSpace() {
  document.body.style.paddingBottom = '';
  const note = document.getElementById('cascade');
  if (note) note.style.bottom = '';
}

/* Boot ---------------------------------------------------------------------- */

function setUpControls() {
  const sel = document.getElementById('startSel');
  sel.addEventListener('change', () => {
    // A new starting country resets the baseline too, so political capital
    // and public patience go back to nothing spent, and nothing stays held
    // over from a design that no longer exists.
    state = startingState(data, sel.value);
    previewRate = null;
    touched = true;
    document.getElementById('cascade').hidden = true;
    render();
  });

  document.getElementById('resetBtn').addEventListener('click', () => {
    state = startingState(data, state.start);
    previewRate = null;
    touched = true;
    document.getElementById('cascade').hidden = true;
    render();
  });

  document.getElementById('revealBtn').addEventListener('click', () => {
    const first = !revealed;
    revealed = true;
    if (first) render();
    const result = document.getElementById('result');
    if (result.hidden) return;
    result.scrollIntoView({ behavior: 'auto', block: 'start' });
    result.focus({ preventScroll: true });
  });

  let resizeTimer = 0;
  window.addEventListener('resize', () => {
    syncFinishSpace();
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(paintChart, 90);
  });
}

async function boot() {
  setUpTheme();

  const res = await fetch('data.json');
  data = await res.json();
  base = chartBase(data);

  const shared = decode(data, location.hash);
  if (shared) {
    state = startingState(data, shared.start);
    state = {
      ...state,
      selection: { ...shared.selection },
      pos: { ...posFromSelection(data, shared.selection), ...shared.pos },
    };
    state.taxRate = shared.taxRate === null
      ? rateForOption(data, shared.selection[TAX_DOMAIN])
      : shared.taxRate;
  } else {
    state = startingState(data, countryForTimezone(data, detectTimezone()));
  }

  paintPicker();
  paintDomains();
  paintMethod();
  setUpControls();
  render();
  // The chart is drawn from a measured rect, and at first paint the fonts may
  // still be swapping. One more pass once layout has settled.
  requestAnimationFrame(paintChart);
}

boot();
