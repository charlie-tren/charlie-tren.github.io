// Statecraft budgets. No DOM access: this module is pure so it can be tested in node.
//
// Financial is absolute. The tax choice sets capacity in % of GDP and every
// other domain's option spends against it.
//
// Political and Social are paid ONLY on domains changed from the starting
// country. A country does not spend political capital maintaining its own
// status quo, it spends it on reform. Staying on your start country's option
// costs nothing; switching to option Y costs Y's political and Y's social.

export const REFORM_POOL = 250;

const round1 = (n) => Math.round(n * 10) / 10;

/**
 * @param {object} data   parsed data.json
 * @param {object} selection  domain id -> option id, the current design
 * @param {object} baseline   domain id -> option id, the starting country's choices
 */
export function budgets(data, selection, baseline) {
  const base = baseline || {};

  let capacity = 0;
  let spend = 0;
  let political = 0;
  let social = 0;
  const changed = [];

  for (const domain of data.domains) {
    const chosen = (domain.options || []).find((o) => o.id === selection[domain.id]);
    if (!chosen) continue;

    if (typeof chosen.revenue === 'number') {
      capacity += chosen.revenue;
    }
    if (typeof chosen.financial === 'number') {
      spend += chosen.financial;
    }

    if (base[domain.id] !== undefined && base[domain.id] !== chosen.id) {
      changed.push({ domain: domain.id, domainName: domain.name, from: base[domain.id], to: chosen.id });
      political += chosen.political || 0;
      social += chosen.social || 0;
    }
  }

  const financialLeft = round1(capacity - spend);

  return {
    financial: {
      capacity: round1(capacity),
      used: round1(spend),
      left: financialLeft,
      over: financialLeft < 0,
      unit: '% of GDP',
    },
    political: {
      capacity: REFORM_POOL,
      used: political,
      left: REFORM_POOL - political,
      over: political > REFORM_POOL,
      unit: 'points',
    },
    social: {
      capacity: REFORM_POOL,
      used: social,
      left: REFORM_POOL - social,
      over: social > REFORM_POOL,
      unit: 'points',
    },
    changed,
    changedCount: changed.length,
  };
}

/** Which budget keys are over. */
export function blockers(b) {
  return ['financial', 'political', 'social'].filter((k) => b[k] && b[k].over);
}
