// Statecraft matching. No DOM access: this module is pure so it can be tested in node.

import { TAX_DOMAIN, clampRate, valuesAt } from './budget.js';

// redistribution is contributed to by several domains and must be summed.
// Every other axis is set directly by its own domain's option.
const SUMMED_AXES = new Set(['redistribution']);

/** The axis the tax domain sets. The rate overrides it wherever one is given. */
function taxAxisOf(data) {
  const domain = (data.domains || []).find((d) => d.id === TAX_DOMAIN);
  return domain ? domain.axis : null;
}

/**
 * The visitor's value on every axis.
 * An axis nothing sets, or one set to null, comes back null. That means
 * "does not apply" and must never be treated as zero.
 *
 * `pos` is optional and is the continuous slider position per domain. Where a
 * domain has one, its axis contributions are read between the two options the
 * position sits between, so the fingerprint moves with the thumb rather than
 * snapping at the boundary. Where it does not, the option's own values are
 * used, which is the same thing at an integer position. THE MATCHING IS STILL
 * DONE ON THE SELECTION: rank() below compares option ids and nothing here
 * changes that.
 *
 * `rate` is optional and is the headline tax rate the visitor has set. Where it
 * is given it WINS on the tax axis, over whatever the tax option carries.
 *
 * THE TAX AXIS IS THE SLIDER, NOT THE OPTION, and the two are not the same
 * number. A tax option's tax_take is derived at build time as the median
 * measured take of the countries running that regime, so tax_nordic ships 42.45
 * against a labelled stop at 46. Reading the option here left the fingerprint's
 * tax spoke, which plots the raw rate, and the reveal's tax axis row, which read
 * the option, printing two different figures for one quantity: a visitor on 46
 * saw a spoke at 46 above a line saying 42.5. The rate is the honest one. It is
 * what the visitor actually chose and it is what the budget is computed from,
 * and putting the override here rather than at each caller means the chart, the
 * reveal and the match cannot disagree about it.
 */
export function axisValues(data, selection, pos, rate) {
  const out = {};
  for (const axis of data.axes) out[axis.id] = null;

  for (const domain of data.domains) {
    const chosen = (domain.options || []).find((o) => o.id === selection[domain.id]);
    if (!chosen || !chosen.axis) continue;

    const p = pos ? pos[domain.id] : undefined;
    const tween = Number.isFinite(Number(p)) ? valuesAt(data, domain.id, p) : null;
    const source = tween ? tween.axis : chosen.axis;

    for (const [axisId, value] of Object.entries(source)) {
      if (value === null || value === undefined) continue;
      if (SUMMED_AXES.has(axisId)) {
        out[axisId] = (out[axisId] === null ? 0 : out[axisId]) + value;
      } else {
        out[axisId] = value;
      }
    }
  }

  const taxAxis = taxAxisOf(data);
  if (taxAxis && Number.isFinite(Number(rate))) out[taxAxis] = clampRate(rate);

  return out;
}

/**
 * Mean absolute difference between the visitor's axis values and a country's
 * measured indicators, each normalised by that axis's own bounds span so that
 * g/kWh and a 0-to-1 index contribute comparably. Axes where either side is
 * null or missing are skipped. Infinity if nothing could be compared.
 */
function axisDistance(data, mine, country) {
  let total = 0;
  let n = 0;
  for (const axis of data.axes) {
    const yours = mine[axis.id];
    const cell = (country.indicators || {})[axis.id];
    const theirs = cell ? cell.value : undefined;
    if (yours === null || yours === undefined) continue;
    if (theirs === null || theirs === undefined) continue;
    const span = axis.bounds[1] - axis.bounds[0];
    if (!span) continue;
    total += Math.abs(yours - theirs) / span;
    n += 1;
  }
  return n === 0 ? Infinity : total / n;
}

/**
 * The countries that can be an answer.
 *
 * THIS GUARD IS LOAD-BEARING AND WAS ADDED 30/08/2026 with the twenty-five
 * measured-only countries. Those carry indicators but no `choices`, so they
 * score zero on the count, which is NOT enough on its own to keep them out of
 * the result: rank() sorts by count and then by axis distance, so a design that
 * matches no country in any domain leaves the whole field tied at zero and a
 * measured-only country can win the tiebreak on distance alone and be presented
 * as the answer. Such a design is reachable, since five options are tagged to no
 * country at all. Filtering here rather than at each caller means every consumer
 * of rank() gets the guarantee, and check_coverage.mjs cannot report a win for a
 * country the page could never legitimately name.
 */
export function matchable(data) {
  return (data.countries || []).filter((c) => c.matchable);
}

/**
 * One row per matchable country, sorted by matched descending then distance
 * ascending. The match is a COUNT. Distance is only a tiebreak.
 *
 * `rate` is the visitor's headline tax rate and is threaded through to the
 * tiebreak. Without it the tax slider had NO EFFECT ON THE MATCH AT ALL: the
 * distance is taken over the measured axes, tax_take is one of them, and this
 * function was calling axisValues with no rate, so every position on a
 * continuous control collapsed onto the six labelled stops before the tiebreak
 * ever saw it. It is a parameter rather than a module-level value because
 * check_coverage.mjs ranks thousands of designs that never touch the page's
 * state, and a global would have made those runs read whatever the last caller
 * happened to leave behind.
 *
 * Callers with no rate to hand may omit it, and the tax option's own axis value
 * is used, which is the behaviour that was there before.
 */
export function rank(data, selection, rate) {
  const mine = axisValues(data, selection, undefined, rate);

  const rows = matchable(data).map((country) => {
    const agreements = [];
    const divergences = [];

    for (const domain of data.domains) {
      const yourId = selection[domain.id];
      const theirId = country.choices[domain.id];
      const yours = (domain.options || []).find((o) => o.id === yourId);
      const theirs = (domain.options || []).find((o) => o.id === theirId);

      if (yourId !== undefined && yourId === theirId) {
        agreements.push({ domain: domain.id, domainName: domain.name, option: yours });
      } else {
        divergences.push({
          domain: domain.id,
          domainName: domain.name,
          yours: yours || null,
          theirs: theirs || null,
          yourCountries: yours ? yours.holders || [] : [],
        });
      }
    }

    return {
      code: country.code,
      name: country.name,
      matched: agreements.length,
      agreements,
      divergences,
      distance: axisDistance(data, mine, country),
    };
  });

  rows.sort((a, b) => (b.matched - a.matched) || (a.distance - b.distance));
  return rows;
}
