// Statecraft, the reveal panel.
//
// One export, renderReveal, returning a string. No DOM reads and no fetches, so
// the panel can be rendered and diffed without a browser.
//
// The order is deliberate and was settled from a rendered comparison sheet:
// the divergences sit ABOVE the axis tracks. What a visitor wants to tell
// someone else is the two or three places they departed from a real country,
// not their position on fourteen measures.

import { axisValues } from './match.js';

/* Helpers ------------------------------------------------------------------ */

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function countryName(data, code) {
  const hit = data.countries.find((c) => c.code === code);
  return hit ? hit.name : String(code);
}

/** "Denmark, Sweden, Norway and Finland", or "Germany, France and 3 more". */
function nameList(data, codes) {
  const list = (codes || []).map((c) => countryName(data, c));
  if (!list.length) return '';
  if (list.length === 1) return list[0];
  if (list.length <= 4) {
    const last = list.pop();
    return `${list.join(', ')} and ${last}`;
  }
  return `${list.slice(0, 4).join(', ')} and ${list.length - 4} more`;
}

/**
 * Decimals follow the axis, not the number. An index bounded at 1 needs two,
 * a rate per 100,000 needs none, and a share of GDP reads badly with three.
 */
function decimals(axis) {
  const hi = axis.bounds[1];
  if (hi <= 1) return 2;
  if (hi >= 100) return 0;
  return 1;
}

function fmt(axis, value) {
  return Number(value).toFixed(decimals(axis));
}

/**
 * Marker position as a percentage of the track.
 * Every value in data.json sits inside its axis bounds and a test holds that
 * true, so a clamp firing here means the data changed underneath the page.
 * Say so rather than quietly drawing the marker at the end of the track.
 */
function markerPct(axis, value) {
  const lo = axis.bounds[0];
  const hi = axis.bounds[1];
  const span = hi - lo;
  if (!span) return 0;
  const raw = (value - lo) / span;
  if (raw < 0 || raw > 1) {
    try {
      // eslint-disable-next-line no-console
      console.warn(`Statecraft: ${axis.id} value ${value} falls outside its bounds ${lo} to ${hi}. This is a data fault, not a rendering one.`);
    } catch (err) { /* no console */ }
  }
  return Math.max(0, Math.min(1, raw)) * 100;
}

function sentence(s) {
  const t = String(s || '').trim();
  if (!t) return '';
  return /[.!?]$/.test(t) ? t : `${t}.`;
}

/* Divergences --------------------------------------------------------------- */

/** Who else runs the option the visitor picked. Five options are run by nobody. */
function whoElse(data, option) {
  const codes = (option && option.countries) || [];
  if (!codes.length) {
    return `Not the policy of any of the ${data.countries.length} countries coded.`;
  }
  return `Also the policy in ${nameList(data, codes)}.`;
}

function divergenceRow(data, row, theirName) {
  const yours = row.yours;
  const theirs = row.theirs;
  return `
  <div class="dv">
    <p class="dv-dom">${esc(row.domainName)}</p>
    <div class="dv-pair">
      <div class="dv-side">
        <p class="dv-who">Your choice</p>
        <p class="dv-opt">${esc(yours ? yours.label : 'Nothing chosen')}</p>
        <p class="dv-where">${esc(whoElse(data, yours))}</p>
      </div>
      <div class="dv-side">
        <p class="dv-who">${esc(theirName)}</p>
        <p class="dv-opt">${esc(theirs ? theirs.label : 'Not coded')}</p>
        <p class="dv-where">${esc(theirs ? theirs.detail : 'This country has no coded policy in this domain.')}</p>
      </div>
    </div>
  </div>`;
}

/* Axes ---------------------------------------------------------------------- */

/**
 * Where the visitor's own number on this axis came from, but only when that is
 * worth saying. Most options carry the median of several countries and need no
 * note. An option standing on one country's cell, or on no measurement at all,
 * does.
 */
function provenance(data, selection, axis) {
  if (axis.id === 'redistribution') {
    return 'Your figure is the sum of your tax, work and family choices, each of them set by hand.';
  }
  const domain = data.domains.find((d) => d.axis === axis.id);
  if (!domain) return '';
  const chosen = (domain.options || []).find((o) => o.id === selection[domain.id]);
  if (!chosen) return '';
  if (chosen.axis_basis === 'hand') {
    return `Your figure for "${chosen.label}" is set by hand. No measured country stands behind it.`;
  }
  if (chosen.axis_basis === 'derived from 1 country') {
    return `Your figure for "${chosen.label}" rests on a single country's measurement.`;
  }
  return '';
}

/**
 * One track per axis.
 *
 * Four cases, and they are not the same claim:
 *   - the country has a figure: marker drawn, year and source available.
 *   - the country has null with an na_reason: the reason is printed and NO
 *     marker is drawn. Plotting "does not apply" at the bottom of the track
 *     would read as a measured zero.
 *   - the axis is absent from the country entirely: no data, said in those
 *     words. The row is KEPT and the visitor's own marker is drawn alone,
 *     because this section is the visitor's profile first and dropping the row
 *     would silently shorten their own country.
 *   - the visitor has no value: their marker is not drawn and the row says
 *     which side is missing. The country's marker still is.
 * A row with nothing on either side is dropped: it would be a label and two
 * apologies.
 */
function axisRow(data, axis, mine, country, selection) {
  const cell = (country.indicators || {})[axis.id];
  const hasCell = Object.prototype.hasOwnProperty.call(country.indicators || {}, axis.id);
  const theirs = hasCell ? cell.value : undefined;
  const yours = mine[axis.id];

  const youHave = yours !== null && yours !== undefined;
  const themHave = theirs !== null && theirs !== undefined;
  if (!youHave && !themHave && !hasCell) return '';

  const marks = [];
  if (youHave) {
    marks.push(`<span class="ax-mk ax-you" style="left:${markerPct(axis, yours).toFixed(2)}%"></span>`);
  }
  if (themHave) {
    marks.push(`<span class="ax-mk ax-them" style="left:${markerPct(axis, theirs).toFixed(2)}%"></span>`);
  }

  const keys = [];
  if (youHave) {
    keys.push(`<span class="ax-k"><i class="ax-sw ax-sw-you" aria-hidden="true"></i>Your design ${esc(fmt(axis, yours))}</span>`);
  } else {
    keys.push('<span class="ax-k ax-k-flat">Your design: none of your thirteen choices sets this.</span>');
  }

  if (themHave) {
    const when = cell.year ? `, ${esc(cell.year)}` : '';
    keys.push(`<span class="ax-k"><i class="ax-sw ax-sw-them" aria-hidden="true"></i>${esc(country.name)} ${esc(fmt(axis, theirs))}${when}</span>`);
  } else if (hasCell) {
    const why = cell.na_reason ? sentence(cell.na_reason) : 'The figure does not apply.';
    keys.push(`<span class="ax-k ax-k-flat">${esc(country.name)}: ${esc(why)}</span>`);
  } else {
    keys.push(`<span class="ax-k ax-k-flat">${esc(country.name)}: not measured on this axis.</span>`);
  }

  const note = provenance(data, selection, axis);

  return `
  <div class="ax">
    <p class="ax-name">${esc(axis.label)} <span class="ax-unit">${esc(axis.unit)}</span></p>
    <div class="ax-track">${marks.join('')}</div>
    <p class="ax-ends"><span>${esc(fmt(axis, axis.bounds[0]))}</span><span>${esc(fmt(axis, axis.bounds[1]))}</span></p>
    <p class="ax-key">${keys.join('')}</p>
    ${note ? `<p class="ax-prov">${esc(note)}</p>` : ''}
  </div>`;
}

/* The panel ----------------------------------------------------------------- */

/**
 * @param {object} data       parsed data.json
 * @param {Array}  ranked     rank(data, selection) from match.js
 * @param {object} selection  domain id -> option id
 * @param {object} [pos]      domain id -> continuous slider position, so the
 *                            axis rows read where the thumbs actually are
 * @returns {string} HTML for #result
 */
export function renderReveal(data, ranked, selection, pos) {
  if (!ranked || !ranked.length) {
    return '<p class="rv-empty">No country is coded yet, so there is nothing to match against.</p>';
  }

  const best = ranked[0];
  const country = data.countries.find((c) => c.code === best.code) || { name: best.name, indicators: {} };
  const total = data.domains.length;
  const exact = best.matched === total;

  // Borrowed from match.js rather than recomputed here. Redistribution is
  // summed across three domains and a second implementation of that rule would
  // eventually disagree with the one the ranking was built from.
  const mine = axisValues(data, selection, pos);

  const runner = ranked[1];
  const runnerLine = runner
    ? `Next closest: ${esc(runner.name)}, ${runner.matched} of ${total}.`
    : '';

  const diverge = exact
    ? `<p class="dv-none">Nowhere. Every one of the ${total} choices is the policy ${esc(country.name)} actually has. Change something above and this is where it will show up.</p>`
    : best.divergences.map((row) => divergenceRow(data, row, country.name)).join('');

  const agreeNames = best.agreements.map((a) => a.domainName);
  const agree = agreeNames.length
    ? `<p class="ag-list">${esc(agreeNames.join(', '))}.</p>`
    : `<p class="ag-list">Nothing. You and ${esc(country.name)} differ in all ${total} domains.</p>`;

  const rows = data.axes
    .map((axis) => axisRow(data, axis, mine, country, selection))
    .filter(Boolean)
    .join('');

  return `
  <div class="rv">
    <p class="rv-eyebrow">${exact ? 'Exact match' : 'Closest match'}</p>
    <h2 class="rv-country">${esc(country.name)}</h2>

    <p class="rv-score">You matched on <strong class="rv-n">${best.matched}</strong> of ${total} domains.</p>
    ${runnerLine ? `<p class="rv-next">${runnerLine}</p>` : ''}

    <h3>Where You Diverge</h3>
    ${diverge}

    <h3>Your Country on the Measured Axes</h3>
    <p class="ax-cap">Fourteen measures, your design against ${esc(country.name)}.</p>
    <div class="axes">${rows}</div>

    <h3>Where You Agree</h3>
    ${agree}

    <p class="rv-method">The match is a count of the domains where your choice is the policy ${esc(country.name)} actually has. Your own figures on the axes above are estimates taken from the countries that run each policy. ${esc(country.name)}'s figures are measurements, and each carries the year it was taken.</p>
  </div>`;
}
