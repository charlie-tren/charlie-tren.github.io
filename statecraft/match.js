// Statecraft matching. No DOM access: this module is pure so it can be tested in node.

// redistribution is contributed to by several domains and must be summed.
// Every other axis is set directly by its own domain's option.
const SUMMED_AXES = new Set(['redistribution']);

/**
 * The visitor's value on every axis.
 * An axis nothing sets, or one set to null, comes back null. That means
 * "does not apply" and must never be treated as zero.
 */
export function axisValues(data, selection) {
  const out = {};
  for (const axis of data.axes) out[axis.id] = null;

  for (const domain of data.domains) {
    const chosen = (domain.options || []).find((o) => o.id === selection[domain.id]);
    if (!chosen || !chosen.axis) continue;

    for (const [axisId, value] of Object.entries(chosen.axis)) {
      if (value === null || value === undefined) continue;
      if (SUMMED_AXES.has(axisId)) {
        out[axisId] = (out[axisId] === null ? 0 : out[axisId]) + value;
      } else {
        out[axisId] = value;
      }
    }
  }
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
 * One row per country, sorted by matched descending then distance ascending.
 * The match is a COUNT. Distance is only a tiebreak.
 */
export function rank(data, selection) {
  const mine = axisValues(data, selection);

  const rows = data.countries.map((country) => {
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
          yourCountries: yours ? yours.countries || [] : [],
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
