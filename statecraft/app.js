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
} from './budget.js';
import { applyChange, setTaxRate, toggleLock, isLocked, ladder } from './cascade.js';
import { rank } from './match.js';
import { renderReveal } from './reveal.js';
import { encode, decode, countryForTimezone, detectTimezone } from './state.js';
import { chartBase, drawChart } from './chart.js';

const THEME_KEY = 'sc-theme';
const RATE_STEP = 0.5;

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
let state = null;          // {start, taxRate, selection, locked}
let previewRate = null;    // the tax slider mid-drag, before the cascade runs
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
  return previewRate === null ? state : { ...state, taxRate: previewRate };
}

/* Painting ------------------------------------------------------------------ */

function paintPicker() {
  const sel = document.getElementById('startSel');
  const sorted = data.countries.slice().sort((a, b) => a.name.localeCompare(b.name, 'en'));
  sel.innerHTML = sorted
    .map((c) => `<option value="${esc(c.code)}">${esc(c.name)}</option>`)
    .join('');
  sel.value = state.start;
}

function paintKey() {
  document.getElementById('chartKey').innerHTML = `
    <span class="ck"><i class="ck-sw ck-you" aria-hidden="true"></i>Your design</span>
    <span class="ck"><i class="ck-sw ck-curve" aria-hidden="true"></i>What your tax funds</span>
    <span class="ck"><i class="ck-sw ck-band" aria-hidden="true"></i>More than it funds</span>
    <span class="ck ck-ramp"><span class="ck-n">Policies you share:</span>
      <i class="ck-sw ch-s0" aria-hidden="true"></i><span class="ck-n">0 to 4</span>
      <i class="ck-sw ch-s1" aria-hidden="true"></i><span class="ck-n">5 to 7</span>
      <i class="ck-sw ch-s2" aria-hidden="true"></i><span class="ck-n">8 to 11</span>
      <i class="ck-sw ch-s3" aria-hidden="true"></i><span class="ck-n">12 or 13</span>
    </span>`;
}

/** One slider per domain, painted once. Values are written by render(). */
function paintDomains() {
  const host = document.getElementById('domains');

  host.innerHTML = data.domains.map((domain) => {
    const isTax = domain.id === TAX_DOMAIN;
    const rungs = isTax ? [] : ladder(data, domain.id);
    const rangeAttrs = isTax
      ? `min="${TAX.MIN}" max="${TAX.MAX}" step="${RATE_STEP}"`
      : `min="0" max="${Math.max(0, rungs.length - 1)}" step="1"`;
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
        <button class="lock" type="button" id="lock_${esc(domain.id)}"
                data-lock="${esc(domain.id)}" aria-pressed="false"></button>
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
    const rungs = ladder(data, id);
    const option = rungs[Number(input.value)];
    if (option) commit(applyChange(data, state, id, option.id));
  });

  host.addEventListener('change', (ev) => {
    const input = ev.target;
    if (!input || !input.dataset || input.dataset.range !== TAX_DOMAIN) return;
    const rate = Number(input.value);
    previewRate = null;
    commit(setTaxRate(data, state, rate));
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
  const rows = data.domains.map((d) => (d.options || []).map((o) => `
      <tr>
        <td>${esc(d.name)}</td>
        <td>${esc(o.label)}</td>
        <td class="num">${esc(budgetEffect(o))}</td>
        <td class="num">${esc(o.political)}</td>
        <td class="num">${esc(o.social)}</td>
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
        <td>${esc(a.source)}</td>
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
  const options = data.domains.reduce((n, d) => n + (d.options || []).length, 0);
  const hand = [];
  for (const d of data.domains) {
    for (const o of (d.options || [])) {
      if (o.axis_basis === 'hand') hand.push(`${d.name}, ${o.label}`);
    }
  }
  const derived = options - hand.length;

  document.getElementById('method').innerHTML = `
  <h2>How Statecraft Works</h2>

  <h3>What the Match Counts</h3>
  <p>The match is a count. One point for each of the ${data.domains.length} domains where your choice is the policy that country actually has, and no point otherwise. Nothing is weighted, nothing is normalised, and a domain you might think matters more than another does not score more than another. Where two countries tie on the count, the one closer to your design on the measured axes is listed first.</p>

  <h3>What the Three Budgets Are</h3>
  <p>The Budget is real. Tax raises a share of GDP and every other policy spends one, and both figures are in the same unit an economist would use. Political capital and public patience are points, because there is no honest unit for institutional capital or for social friction, and inventing one would dress a judgement up as a measurement. Both are charged only on the domains you change from your starting country: no country spends political capital to keep the policy it already has, and a cut the budget forced on you is still a reform somebody has to pass.</p>
  <p>The costs below are judgements. Publishing them is the point, because a reader who thinks mandatory military service should cost more political capital than the 12 points charged here can see the exact number to argue with.</p>

  <h3>What a Point of Tax Actually Raises</h3>
  <p>The tax slider is a headline take: total tax revenue as a share of GDP. What the state collects is less than that, and increasingly less, because people work less, avoid more and move money. Below ${TAX.KINK} the two are the same. Above it, each point of headline take gives up ${TAX.LEAK} of a point for every point it is above ${TAX.KINK}, squared, so ${TAX.MAX} raises ${one(realisedRevenue(TAX.MAX))} rather than ${TAX.MAX}. The curve never turns over inside the slider, so pushing the rate up never lowers the budget.</p>
  <p>Your capacity is what that rate realises, plus any non-tax revenue your starting country has, plus a fixed top-up if that country already spends more than it raises. The top-up is measured once, at the country you started from, and does not move when you drag the rate.</p>

  <details class="mdet">
    <summary>Every option and what it costs</summary>
    <p class="mnote">The Budget column is what an option spends, in % of GDP. The six tax regimes carry a headline rate instead, and the slider runs between them. All ${options} options.</p>
    <div class="scroller">${costTable()}</div>
  </details>

  <details class="mdet">
    <summary>The ${data.axes.length} axes, their units and their sources</summary>
    <p class="mnote">Track runs is the span the reveal plots between, set wide enough to hold every coded country.</p>
    <div class="scroller">${axisTable()}</div>
  </details>

  <h3>The Source of Your Own Figures</h3>
  <p>Every option carries a figure on its domain's axis, and that figure is what the reveal plots as your design. Where countries in this set run the policy, the figure is the median of their measured values. Median rather than mean, so a single classification artefact cannot drag the marker: the WHO counts compulsory Swiss health cover as private insurance, which puts Switzerland at 33 per cent public where the rest of its option sits between 48 and 85.</p>
  <p>${derived} of the ${options} options are derived that way. The remaining ${hand.length} are set by hand, either because no coded country runs them or because the countries that do have no measurement on that axis. They are: ${esc(hand.join('; '))}. Redistribution is summed from your tax, work and family choices rather than owned by one domain, so it stays hand-set throughout. Where an option is the policy of a single country, its figure is that one country's cell, and the reveal says so on the track.</p>

  <h3>What Is Not Here Yet</h3>
  <p>${data.countries.length} countries are coded so far and that number will grow. A country's own indicators are read as three separate claims and never merged: a figure with a year and a source, a blank with a reason it does not apply, and an axis the country has no reading on at all.</p>
  <p>The page opens on a guess made from your browser's timezone, so the first thing you see is a country rather than an empty form. The starting country picker changes it.</p>`;
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
  const matched = new Map(rank(data, live.selection).map((r) => [r.code, r.matched]));
  drawChart(host, data, base, {
    startCode: live.start,
    rate: b.financial.taxRate,
    spend: b.financial.exact.used,
    capacity: b.financial.exact.capacity,
    matched,
  });
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

    const lock = document.getElementById(`lock_${id}`);
    lock.textContent = locked ? 'Protected' : 'Protect';
    lock.setAttribute('aria-pressed', locked ? 'true' : 'false');
    lock.title = locked
      ? 'This policy is held where it is and the budget will cut something else'
      : 'Hold this policy where it is when the budget has to find money';
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
        <span class="d-cost">political capital ${esc(stop ? stop.political : 0)}, public patience ${esc(stop ? stop.social : 0)}</span>
        ${startChoices[id] === live.selection[id] ? '<span class="d-home">Where you started</span>' : ''}`;
      document.getElementById(`det_${id}`).textContent =
        `Raises ${one(b.financial.realisedTax)}% of GDP. The next point of tax adds ${one(nextPoint)}, and at ${TAX.MAX} a point would add only ${one(realisedRevenue(TAX.MAX) - realisedRevenue(TAX.MAX - 1))}.`;
      document.getElementById(`who_${id}`).textContent = stop
        ? `${stop.detail} ${whereLine(stop.countries)}`
        : '';
      continue;
    }

    const rungs = ladder(data, id);
    const index = Math.max(0, rungs.findIndex((o) => o.id === live.selection[id]));
    const option = rungs[index];
    if (Number(input.value) !== index) {
      if (cutIds.has(id)) tweenRange(input, index); else input.value = String(index);
    }
    input.setAttribute('aria-valuetext', `${option ? option.label : ''}, ${one(option ? option.financial : 0)} per cent of GDP, step ${index + 1} of ${rungs.length}`);

    document.getElementById(`val_${id}`).innerHTML = `
      <span class="d-opt">${esc(option ? option.label : '')}</span>
      <span class="d-cost">${esc(one(option ? option.financial : 0))}% of GDP, political capital ${esc(option ? option.political : 0)}, public patience ${esc(option ? option.social : 0)}</span>
      ${startChoices[id] === live.selection[id] ? '<span class="d-home">Where you started</span>' : ''}`;
    document.getElementById(`det_${id}`).textContent = option ? option.detail : '';
    document.getElementById(`who_${id}`).textContent = option ? whereLine(option.countries) : '';

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
    result.innerHTML = renderReveal(data, rank(data, live.selection), live.selection);
    result.hidden = false;
  } else {
    result.hidden = true;
  }

  syncFinishSpace();

  // A fresh visit and a shared link must not look alike, so the default is
  // never written. The hash appears the moment the visitor changes something,
  // and it carries the rate, which the option index no longer implies.
  if (touched) {
    history.replaceState(null, '', `#${encode(data, state.start, state.selection, state.taxRate)}`);
  }
}

/* The pinned action --------------------------------------------------------
 * The reveal button is pinned to the bottom of the viewport, so the primary
 * action is on the first screen at every width. The bar is out of flow, so the
 * page reserves exactly its measured height at the bottom: the blocked note
 * wraps to two lines on a phone and a hard-coded padding would let the bar sit
 * over the last paragraph of the method section. */

function syncFinishSpace() {
  const bar = document.querySelector('.finish');
  if (!bar) return;
  const h = bar.offsetHeight;
  document.body.style.paddingBottom = h ? `${h + 16}px` : '';
  const note = document.getElementById('cascade');
  if (note) note.style.bottom = `${h + 8}px`;
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
    state = { ...state, selection: { ...shared.selection } };
    state.taxRate = shared.taxRate === null
      ? rateForOption(data, shared.selection[TAX_DOMAIN])
      : shared.taxRate;
  } else {
    state = startingState(data, countryForTimezone(data, detectTimezone()));
  }

  paintPicker();
  paintKey();
  paintDomains();
  paintMethod();
  setUpControls();
  render();
  // The chart is drawn from a measured rect, and at first paint the fonts may
  // still be swapping. One more pass once layout has settled.
  requestAnimationFrame(paintChart);
}

boot();
