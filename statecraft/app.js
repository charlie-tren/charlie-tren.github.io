// Statecraft, the builder screen. Wiring only.
//
// Every decision worth testing lives in budget.js, match.js and state.js.
// This file owns the DOM and nothing else: it reads data.json, paints the
// picker, the meters and the thirteen domains, and keeps them in step.

import { budgets, blockers } from './budget.js';
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
  document.getElementById('blockedNote').textContent = stuck.length
    ? `You have spent more than you have of ${stuck.map((k) => names[k]).join(' and ')}. Trim something to reveal.`
    : '';

  // A fresh visit and a shared link must not look alike, so the default is
  // never written. The hash appears the moment the visitor changes something.
  if (touched) {
    history.replaceState(null, '', `#${encode(data, startCode, selection)}`);
  }
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
    // The reveal panel is a later task.
  });
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
  setUpControls();
  render();
}

boot();
