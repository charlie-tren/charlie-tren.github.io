// Statecraft budgets. No DOM access: this module is pure so it can be tested in node.
//
// All three budgets say the same thing: you inherit a country and you pay for
// what you CHANGE.
//
// Political and Social are charged only on domains moved off the starting
// country. A country does not spend political capital maintaining its own
// status quo, it spends it on reform. Staying put costs nothing; switching to
// option Y costs Y's political and Y's social. That rule applies to a change the
// visitor made and to one the cascade in cascade.js made on their behalf, which
// is the same thing said once: somebody still has to pass it.
//
// Financial is in % of GDP. Capacity is what the chosen tax rate REALISES, plus
// the non-tax revenue the starting country has, floored at what that country
// already spends.
//
// THE FLOOR IS THE POINT and it stays. A country manifestly manages to run its
// own settings, so those are affordable by definition and only ADDITIONAL
// spending has to be funded. Without it the United Arab Emirates could not be
// revealed at all. Its coded choices cost 32.0% of GDP against a general
// government revenue of 27.8%, so a visitor whose timezone is Asia/Dubai arrived
// at a page whose primary action was already disabled before they had touched
// anything. That gap is an artefact of pricing every option once, on figures
// that mostly describe European states: the IMF puts actual UAE general
// government expenditure at 21.4% of GDP, well inside its revenue. Raising the
// revenue to close it would have meant inventing a number to paper over a cost
// model, which is the mistake this project has already made twice. Nineteen of
// twenty countries are unaffected, because their revenue already exceeds their
// own spending.

export const REFORM_POOL = 250;

export const TAX_DOMAIN = 'tax';

/**
 * THE TAX CURVE. One named place, and the calibration is written out here so a
 * later session cannot retune it without seeing what it was fitted to.
 *
 * `rate` is the HEADLINE take: total tax revenue as a share of GDP, the same
 * basis as the tax_take axis and the same basis the twenty countries are
 * measured on. What the state actually collects is less, and increasingly less,
 * because people work less, avoid more and move money:
 *
 *     realised(rate) = rate - LEAK * max(0, rate - KINK) ** 2
 *
 * MIN and MAX are the ends of the slider. They are the observed spread in this
 * project's own data and not a guess: across the twenty countries the measured
 * total tax take runs from 12.1 (Singapore) to 46.1 (France), and nothing in the
 * set sustains much above that. The slider runs a little past the top of the
 * observed range on purpose, so a visitor can try a rate no country holds and
 * find out what it does and does not buy, which is the whole exercise.
 *
 * KINK is where the leak starts. Below about 30 the observed countries show no
 * sign of the take fighting itself, so the curve is the identity there and a
 * point of rate is a point of revenue.
 *
 * LEAK is set so the curve reads:
 *
 *     12 -> 12.0    30 -> 30.0    34 -> 33.8    40 -> 39.0
 *     46 -> 43.4    50 -> 46.0    55 -> 48.8
 *
 * The two anchors that matter are 46 -> 43.4, which says the highest-taxing
 * country in the set gives up about three points of GDP to collect what it
 * collects, and the marginal point at the top: d(realised)/d(rate) is
 * 1 - 2 * LEAK * (rate - KINK), which at 55 is 0.5. The last point of headline
 * tax raises about half a point of revenue. The curve is monotonic over the
 * whole slider, since it only turns over at rate = KINK + 1 / (2 * LEAK) = 80,
 * so pushing the slider up never lowers the budget. That is deliberate: a
 * Laffer peak inside the playable range would make a control that sometimes
 * takes money away when you push it up, and no visitor would read that as
 * anything but a bug.
 */
export const TAX = Object.freeze({ MIN: 12, MAX: 55, KINK: 30, LEAK: 0.01 });

const round1 = (n) => Math.round(n * 10) / 10;

/** The slider value, held on the slider. */
export function clampRate(rate) {
  const r = Number(rate);
  if (!Number.isFinite(r)) return TAX.MIN;
  return Math.min(TAX.MAX, Math.max(TAX.MIN, r));
}

/** What a headline take of `rate` actually collects, in % of GDP. */
export function realisedRevenue(rate) {
  const r = clampRate(rate);
  const excess = Math.max(0, r - TAX.KINK);
  return r - TAX.LEAK * excess * excess;
}

/** The tax options, cheapest rate first. These are the labelled stops on the slider. */
export function taxStops(data) {
  const domain = data.domains.find((d) => d.id === TAX_DOMAIN);
  return (domain ? domain.options || [] : []).slice().sort((a, b) => a.rate - b.rate);
}

/**
 * The tax option a rate lands on: the nearest stop, ties going to the lower.
 *
 * The rate is continuous and the reveal is not. A country is matched on which of
 * the six tax regimes you are running, and the political and social cost of tax
 * reform is that option's cost, so a rate has to name one. Ties go down rather
 * than to the nearer-in-some-other-sense stop because a rule that reads the same
 * every time is worth more here than a cleverer one.
 */
export function optionForRate(data, rate) {
  const r = clampRate(rate);
  const stops = taxStops(data);
  let best = stops[0];
  let bestGap = Infinity;
  for (const stop of stops) {
    const gap = Math.abs(stop.rate - r);
    if (gap < bestGap - 1e-9) {
      best = stop;
      bestGap = gap;
    }
  }
  return best ? best.id : undefined;
}

/** The headline rate a tax option sits at. */
export function rateForOption(data, optionId) {
  const stop = taxStops(data).find((o) => o.id === optionId);
  return stop ? stop.rate : TAX.MIN;
}

export function countryOf(data, code) {
  return data.countries.find((c) => c.code === code) || null;
}

/**
 * The state a visitor starts in: the country's own settings, its own tax rate,
 * nothing locked.
 *
 * @param {object} data parsed data.json
 * @param {string} code two-letter country code
 * @returns {{start: string, taxRate: number, selection: object, locked: string[]}}
 */
/**
 * The rate a country actually starts on.
 *
 * ITS OWN MEASURED TAX TAKE WHERE THERE IS ONE, not its option's rate. An
 * option's rate is one hand-set number standing for every country tagged to it,
 * and `tax_anglo` alone carries ten countries whose real takes run from
 * Singapore's 12.1 to Japan's 34.1. Starting all ten at 34 handed Australia 9.1
 * points of headroom it does not have, and the effect was to disable the
 * cascade: a visitor could push almost anything to its dearest option and never
 * see a thing get cut to pay for it, which is the whole mechanic.
 *
 * On measured rates the mean headroom across the twenty falls from 8.4 to 4.5,
 * which is about what a real government runs. The UAE has no measured take, so
 * it keeps its option's 16.0 and its oil is carried separately as nonTaxRevenue.
 */
export function startingRate(data, country) {
  const cell = country && country.indicators ? country.indicators.tax_take : null;
  if (cell && typeof cell.value === 'number') return cell.value;
  return rateForOption(data, country.choices[TAX_DOMAIN]);
}

export function startingState(data, code) {
  const country = countryOf(data, code) || countryOf(data, data.fallback);
  return {
    start: country.code,
    taxRate: startingRate(data, country),
    selection: { ...country.choices },
    locked: [],
  };
}

/** What a set of choices costs in % of GDP. The tax domain carries no spend. */
export function spendOf(data, selection) {
  let total = 0;
  for (const domain of data.domains) {
    const o = (domain.options || []).find((x) => x.id === (selection || {})[domain.id]);
    if (o && typeof o.financial === 'number') total += o.financial;
  }
  return total;
}

/** The rate a state is running, falling back to whatever its tax option implies. */
function rateOf(data, state) {
  if (typeof state.taxRate === 'number' && Number.isFinite(state.taxRate)) {
    return clampRate(state.taxRate);
  }
  return rateForOption(data, (state.selection || {})[TAX_DOMAIN]);
}

/**
 * Unrounded capacity, and where it came from. The cascade needs the exact
 * numbers: rounding twice is how a domain gets cut to cover a tenth of a point
 * that was never actually over.
 */
export function capacityOf(data, state) {
  const country = countryOf(data, state.start);
  const baseline = country ? country.choices : {};
  const nonTax = country && typeof country.nonTaxRevenue === 'number' ? country.nonTaxRevenue : 0;

  const rate = rateOf(data, state);
  const realisedTax = realisedRevenue(rate);
  const raised = realisedTax + nonTax;
  const inherited = spendOf(data, baseline);

  // THE TOP-UP IS FIXED AT THE COUNTRY YOU INHERITED, NOT RECOMPUTED AS YOU DRAG.
  //
  // The floor exists so a country can afford to be ITSELF: the UAE's modelled
  // spend is 32.0% of GDP against 27.8 of real income, because every option is
  // priced once on figures that mostly describe European states. That gap is a
  // property of the country you started from, so it is measured once, at that
  // country's OWN tax rate, and then carried as a constant.
  //
  // Written as max(raised, inherited) instead, it silently ate the bottom half
  // of the tax slider: dragging Australia from 34 down to 12 moved the budget by
  // nothing at all, because inherited spend was above realised revenue the whole
  // way down. Half the control did nothing, which is exactly the opposite of
  // what the slider was added to do. Fixed as a constant top-up, capacity now
  // tracks the rate one for one in both directions and a tax cut forces a
  // cascade, which is the point.
  // Measured at the country's OWN starting rate, which is its measured tax take
  // where it has one. Using the option's rate here instead would size the top-up
  // off a number the country never actually raises.
  const startRate = country ? startingRate(data, country) : 0;
  const topUp = Math.max(0, inherited - (realisedRevenue(startRate) + nonTax));

  return {
    rate,
    realisedTax,
    nonTaxRevenue: nonTax,
    raised,
    inherited,
    topUp,
    capacity: raised + topUp,
    floored: topUp > 0,
  };
}

/**
 * The three budgets for a state.
 *
 * @param {object} data parsed data.json
 * @param {{start: string, taxRate: number, selection: object, locked?: string[]}} state
 */
export function budgets(data, state) {
  const country = countryOf(data, state.start);
  const base = country ? country.choices : {};
  const selection = state.selection || {};

  let spend = 0;
  let political = 0;
  let social = 0;
  const changed = [];

  for (const domain of data.domains) {
    const chosen = (domain.options || []).find((o) => o.id === selection[domain.id]);
    if (!chosen) continue;

    if (typeof chosen.financial === 'number') spend += chosen.financial;

    if (base[domain.id] !== undefined && base[domain.id] !== chosen.id) {
      changed.push({ domain: domain.id, domainName: domain.name, from: base[domain.id], to: chosen.id });
      political += chosen.political || 0;
      social += chosen.social || 0;
    }
  }

  const cap = capacityOf(data, state);
  const left = cap.capacity - spend;

  return {
    financial: {
      capacity: round1(cap.capacity),
      used: round1(spend),
      left: round1(left),
      over: left < -1e-9,
      unit: '% of GDP',
      taxRate: round1(cap.rate),
      realisedTax: round1(cap.realisedTax),
      nonTaxRevenue: round1(cap.nonTaxRevenue),
      inherited: round1(cap.inherited),
      // The constant subsidy sized at the country you inherited. Surfaced so the
      // page can say where the money comes from, and so a test can assert it
      // does not move when the rate does.
      topUp: round1(cap.topUp),
      floored: cap.floored,
      // Unrounded, for anything that has to decide rather than display.
      exact: { capacity: cap.capacity, used: spend, left },
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
