// Statecraft budgets. No DOM access: this module is pure so it can be tested in node.
//
// All three budgets say the same thing: you inherit a country and you pay for
// what you CHANGE.
//
// Political and Social are charged only on domains moved off the starting
// country. A country does not spend political capital maintaining its own
// status quo, it spends it on reform. Staying put costs nothing; switching to
// option Y costs Y's political and Y's social.
//
// Financial is in % of GDP and its capacity is the tax choice's revenue OR what
// the starting country already spends, whichever is larger. The floor is the
// point: a country manifestly manages to run its own settings, so those are
// affordable by definition and only ADDITIONAL spending has to be funded.
//
// Without the floor the United Arab Emirates could not be revealed at all. Its
// coded choices cost 32.0% of GDP against a sourced revenue of 27.8%, so a
// visitor whose timezone is Asia/Dubai arrived at a page whose primary action
// was already disabled before they had touched anything. That gap is an
// artefact of pricing every option once, on figures that mostly describe
// European states: the IMF puts actual UAE general government expenditure at
// 21.4% of GDP, well inside its revenue. Raising the revenue to close it would
// have meant inventing a number to paper over a cost model, which is the
// mistake this project has already made twice. Nineteen of twenty countries are
// unaffected, because their tax revenue already exceeds their own spending.

export const REFORM_POOL = 250;

const round1 = (n) => Math.round(n * 10) / 10;

/** What a set of choices costs in % of GDP, ignoring the tax domain. */
function spendOf(data, choices) {
  let total = 0;
  for (const domain of data.domains) {
    const o = (domain.options || []).find((x) => x.id === choices[domain.id]);
    if (o && typeof o.financial === 'number') total += o.financial;
  }
  return total;
}

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

  // The floor: whatever the starting country already spends is affordable,
  // because it is what that country does. Only extra spending needs funding.
  const inherited = spendOf(data, base);
  const effectiveCapacity = Math.max(capacity, inherited);
  const financialLeft = round1(effectiveCapacity - spend);

  return {
    financial: {
      capacity: round1(effectiveCapacity),
      used: round1(spend),
      left: financialLeft,
      over: financialLeft < 0,
      unit: '% of GDP',
      taxRevenue: round1(capacity),
      inherited: round1(inherited),
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
