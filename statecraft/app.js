// Statecraft, the builder screen. Wiring only.
//
// Every decision worth testing lives in budget.js, match.js and state.js.
// This file owns the DOM and nothing else: it reads data.json, paints the
// picker, the meters and the thirteen domains, and keeps them in step.

import { budgets, blockers } from './budget.js';
import { rank } from './match.js';
import { renderReveal } from './reveal.js';
import { encode, decode, countryForTimezone, detectTimezone } from './state.js';

const THEME_KEY = 'sc-theme';

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
let startCode = null;      // the country the design departs from
let baseline = {};         // that country's own choices, what reform is priced against
let selection = {};        // the live design
let touched = false;       // has the visitor actually changed anything yet
let revealed = false;      // has the visitor asked for the result at least once

function countryName(code) {
  const hit = data.countries.find((c) => c.code === code);
  return hit ? hit.name : code;
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

function loadCountry(code) {
  const country = data.countries.find((c) => c.code === code);
  if (!country) return;
  startCode = country.code;
  baseline = Object.assign({}, country.choices);
  selection = Object.assign({}, country.choices);
}

/* Painting ------------------------------------------------------------------ */

function paintPicker() {
  const sel = document.getElementById('startSel');
  const sorted = data.countries.slice().sort((a, b) => a.name.localeCompare(b.name, 'en'));
  sel.innerHTML = sorted
    .map((c) => `<option value="${esc(c.code)}">${esc(c.name)}</option>`)
    .join('');
  sel.value = startCode;
}

function paintDomains() {
  const host = document.getElementById('domains');
  host.innerHTML = data.domains.map((domain) => {
    const opts = (domain.options || []).map((o) => {
      // Tax raises the money. Everything else spends it.
      const money = typeof o.revenue === 'number'
        ? `Raises ${one(o.revenue)}% of GDP`
        : `Costs ${one(o.financial || 0)}% of GDP`;
      return `
      <label class="opt" data-domain="${esc(domain.id)}" data-option="${esc(o.id)}">
        <input type="radio" name="d_${esc(domain.id)}" value="${esc(o.id)}">
        <span class="o-body">
          <span class="o-top">
            <span class="o-label">${esc(o.label)}</span>
            <span class="o-start" hidden>Where you started</span>
          </span>
          <span class="o-detail">${esc(o.detail)}</span>
          <span class="o-where">${esc(whereLine(o.countries))}</span>
          <span class="o-cost">
            <span>${esc(money)}</span>
            <span>Political capital ${esc(o.political)}</span>
            <span>Public patience ${esc(o.social)}</span>
          </span>
        </span>
      </label>`;
    }).join('');

    return `
    <section class="domain" id="dom_${esc(domain.id)}" data-domain="${esc(domain.id)}">
      <div class="d-head">
        <h2 id="h_${esc(domain.id)}">${esc(domain.name)}</h2>
        <span class="chip" hidden>Changed</span>
      </div>
      <div class="opts" role="radiogroup" aria-labelledby="h_${esc(domain.id)}">${opts}</div>
    </section>`;
  }).join('');

  host.addEventListener('change', (ev) => {
    const input = ev.target;
    if (!input || input.type !== 'radio') return;
    const label = input.closest('.opt');
    if (!label) return;
    selection[label.dataset.domain] = label.dataset.option;
    touched = true;
    render();
  });
}

/* Method -------------------------------------------------------------------
 * Painted once at boot. It depends on data.json and nothing else, so nothing
 * here re-renders when a choice changes.
 *
 * Alignment is set on the column, header cell included. A right-aligned figure
 * under a left-aligned header is the failure this guards against, and it only
 * shows up once a placeholder string lands in a numeric column. */

/** Signed, so one column can hold both what an option raises and what it spends. */
function budgetEffect(o) {
  const v = typeof o.revenue === 'number' ? o.revenue : -(o.financial || 0);
  return `${v > 0 ? '+' : ''}${one(v)}`;
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
  <p>The Budget is real. Tax raises a share of GDP and every other policy spends one, and both figures are in the same unit an economist would use. Political capital and public patience are points, because there is no honest unit for institutional capital or for social friction, and inventing one would dress a judgement up as a measurement. Both are charged only on the domains you change from your starting country: no country spends political capital to keep the policy it already has.</p>
  <p>The costs below are judgements. Publishing them is the point, because a reader who thinks mandatory military service should cost more political capital than the 12 points charged here can see the exact number to argue with.</p>

  <details class="mdet">
    <summary>Every option and what it costs</summary>
    <p class="mnote">A plus in the Budget column raises revenue, a minus spends it. All ${options} options.</p>
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

function render() {
  const b = budgets(data, selection, baseline);

  paintMeter('financial', b.financial, `${one(b.financial.used)} of ${one(b.financial.capacity)}% of GDP`);
  paintMeter('political', b.political, `${b.political.used} of ${b.political.capacity}`);
  paintMeter('social', b.social, `${b.social.used} of ${b.social.capacity}`);

  const changed = new Set(b.changed.map((c) => c.domain));

  document.querySelectorAll('#domains .domain').forEach((section) => {
    const id = section.dataset.domain;
    const isChanged = changed.has(id);
    section.classList.toggle('changed', isChanged);
    section.querySelector('.chip').hidden = !isChanged;
  });

  document.querySelectorAll('#domains .opt').forEach((label) => {
    const chosen = selection[label.dataset.domain] === label.dataset.option;
    const input = label.querySelector('input');
    input.checked = chosen;
    label.classList.toggle('on', chosen);
    label.querySelector('.o-start').hidden = baseline[label.dataset.domain] !== label.dataset.option;
  });

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
    result.innerHTML = renderReveal(data, rank(data, selection), selection);
    result.hidden = false;
  } else {
    result.hidden = true;
  }

  syncFinishSpace();

  // A fresh visit and a shared link must not look alike, so the default is
  // never written. The hash appears the moment the visitor changes something.
  if (touched) {
    history.replaceState(null, '', `#${encode(data, startCode, selection)}`);
  }
}

/* The pinned action --------------------------------------------------------
 * The reveal button is pinned to the bottom of the viewport, because the page
 * it belongs to is thirteen domains of five or six cards and the button used
 * to sit under all of them. Measured at 390px that was a fourteen thousand
 * pixel scroll to reach the only thing the page exists to do.
 *
 * The bar is out of flow, so the page reserves exactly its height at the
 * bottom. Measured rather than guessed: the blocked note wraps to two lines on
 * a phone and a hard-coded padding would let the bar sit over the last
 * paragraph of the method section. */

function syncFinishSpace() {
  const bar = document.querySelector('.finish');
  if (!bar) return;
  const h = bar.offsetHeight;
  document.body.style.paddingBottom = h ? `${h + 16}px` : '';
}

/* Boot ---------------------------------------------------------------------- */

function setUpControls() {
  const sel = document.getElementById('startSel');
  sel.addEventListener('change', () => {
    // A new starting country resets the baseline too, so political capital
    // and public patience go back to nothing spent.
    loadCountry(sel.value);
    touched = true;
    render();
  });

  document.getElementById('resetBtn').addEventListener('click', () => {
    selection = Object.assign({}, baseline);
    touched = true;
    render();
  });

  document.getElementById('revealBtn').addEventListener('click', () => {
    const first = !revealed;
    revealed = true;
    if (first) render();
    const result = document.getElementById('result');
    if (result.hidden) return;
    // Instant, not smoothed. The page is sixteen thousand pixels tall and a
    // smooth scroll over that distance measured at roughly three seconds of
    // animation before the visitor sees the thing they asked for. Nothing else
    // on the page moves, so there is nothing for prefers-reduced-motion to do.
    result.scrollIntoView({ behavior: 'auto', block: 'start' });
    // Sending focus with the viewport, so a keyboard or screen-reader visitor
    // lands in the panel rather than back at the top of thirteen domains.
    result.focus({ preventScroll: true });
  });

  window.addEventListener('resize', syncFinishSpace);
}

async function boot() {
  setUpTheme();

  const res = await fetch('data.json');
  data = await res.json();

  const shared = decode(data, location.hash);
  if (shared) {
    loadCountry(shared.start);
    selection = Object.assign({}, shared.selection);
  } else {
    loadCountry(countryForTimezone(data, detectTimezone()));
  }

  paintPicker();
  paintDomains();
  paintMethod();
  setUpControls();
  render();
}

boot();
