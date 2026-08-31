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
    pos: posFromSelection(data, country.choices),
    locked: [],
  };
}

/* Continuous positions ------------------------------------------------------
 *
 * THE SLIDER IS A POSITION, NOT AN INDEX. `pos[domainId]` is a real number from
 * 0 to rungs-1 along that domain's ladder, and it is part of the state.
 *
 * Added 01/09/2026. The thumb had been continuous since the first build and
 * everything downstream read the SNAPPED option, so the money and the shape
 * jumped the moment the thumb crossed a boundary while the thumb itself glided.
 * Healthcare was the case that made it obvious: its five options cost 2.5, 7.0,
 * 7.5, 8.5 and 9.0 per cent of GDP, so one crossing moved the budget 4.5 points
 * for a hair of thumb travel. A control whose output stairs while its input
 * glides reads as broken, and the owner read it that way.
 *
 * WHAT INTERPOLATES AND WHAT DOES NOT, because the split is the whole design:
 *
 *   THE NUMBERS INTERPOLATE. financial, political, social and every axis value
 *   are read linearly between floor(pos) and ceil(pos). Sixty per cent of the
 *   way from compulsory medical savings to mandatory insurance costs sixty per
 *   cent of the way between the two, and plots there. You are part way between
 *   two systems and you pay part way.
 *
 *   THE IDENTITY SNAPS. The option is rungs[Math.round(pos)], ties going up,
 *   and that is what the label says, what rank() matches on and what the URL
 *   carries. There is no such country as sixty per cent of mandatory insurance,
 *   so the reveal cannot be asked to name one.
 *
 *   A NULL AXIS DOES NOT INTERPOLATE. Only vo_none does this, whose
 *   disproportionality is null because a state with no elections has no
 *   disproportionality, not because it has none of it. Averaging a real number
 *   with "does not apply" would invent a reading. The rule is: if both sides
 *   are numbers, interpolate; otherwise take the NEAREST option's value, which
 *   is null exactly when the nearest option is the null one. So the axis blinks
 *   in and out at the same boundary the label does, which is the boundary where
 *   the visitor stops having elections.
 *
 * The tax domain has no ladder and no position. Its slider was already
 * continuous in the rate and is untouched.
 */

const lerp = (a, b, t) => a + (b - a) * t;

/** A finite number, or null. Missing and null are the same thing here. */
function numberOrNull(map, key) {
  const v = map ? map[key] : undefined;
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
}

/**
 * A domain's options, cheapest to dearest by financial cost. This is the order
 * the slider runs in, the order a position is measured along, and the order the
 * cascade steps down.
 *
 * The sort is stable, so two options at the same cost keep their data.json
 * order rather than swapping about between engines.
 */
export function ladder(data, domainId) {
  const domain = (data.domains || []).find((d) => d.id === domainId);
  if (!domain || domain.id === TAX_DOMAIN) return [];
  return (domain.options || []).slice().sort((a, b) => (a.financial || 0) - (b.financial || 0));
}

/** Where an option sits on its own ladder. 0 for anything not on one. */
export function posOfOption(data, domainId, optionId) {
  const i = ladder(data, domainId).findIndex((o) => o.id === optionId);
  return i < 0 ? 0 : i;
}

/** A position held inside its own ladder, and never NaN. */
export function clampPos(data, domainId, p) {
  const rungs = ladder(data, domainId);
  if (!rungs.length) return 0;
  const n = Number(p);
  if (!Number.isFinite(n)) return 0;
  return Math.min(rungs.length - 1, Math.max(0, n));
}

/** The integer positions a selection implies. Tax has no ladder and is absent. */
export function posFromSelection(data, selection) {
  const out = {};
  for (const domain of data.domains || []) {
    if (domain.id === TAX_DOMAIN) continue;
    out[domain.id] = posOfOption(data, domain.id, (selection || {})[domain.id]);
  }
  return out;
}

/**
 * Every domain's position for a state: what the state carries where it carries
 * one, and the integer its selection implies where it does not.
 *
 * A state built before positions existed, or one written by hand in a test, is
 * therefore read as sitting exactly on its options, which is what it meant.
 *
 * THE SELECTION IS THE ARBITER WHERE THE TWO DISAGREE. A position whose nearest
 * rung is not the option the state names describes a different design from the
 * one the state names, and there is no way to tell which half is the mistake.
 * Taking the selection means the obvious edit still does the obvious thing:
 * `{...state, selection: {...state.selection, housing: 'ho_singapore'}}` moves
 * housing to Singapore rather than pricing it at wherever the old thumb was.
 * applyChange writes both together, so this only fires on a hand-built state.
 */
export function positionsOf(data, state) {
  const held = (state || {}).pos || {};
  const selection = (state || {}).selection || {};
  const out = {};
  for (const domain of data.domains || []) {
    if (domain.id === TAX_DOMAIN) continue;
    const rungs = ladder(data, domain.id);
    const named = posOfOption(data, domain.id, selection[domain.id]);
    const p = held[domain.id];
    if (!Number.isFinite(Number(p))) {
      out[domain.id] = named;
      continue;
    }
    const clamped = clampPos(data, domain.id, p);
    const lands = rungs.length ? rungs[Math.round(clamped)] : null;
    out[domain.id] = lands && lands.id === selection[domain.id] ? clamped : named;
  }
  return out;
}

/**
 * What a domain reads at a position: the interpolated costs and axis values,
 * and the option the position IS.
 *
 * @returns {null} for a domain with no ladder, which is tax and nothing else.
 */
export function valuesAt(data, domainId, p) {
  const rungs = ladder(data, domainId);
  if (!rungs.length) return null;

  const pos = clampPos(data, domainId, p);
  const lo = rungs[Math.floor(pos)];
  const hi = rungs[Math.ceil(pos)];
  const t = pos - Math.floor(pos);
  // Ties go up, so a thumb exactly on a boundary reads as the dearer option.
  // Any fixed rule does; this one is Math.round's and needs no second thought.
  const option = rungs[Math.round(pos)];

  const axis = {};
  const keys = new Set([...Object.keys(lo.axis || {}), ...Object.keys(hi.axis || {})]);
  for (const key of keys) {
    const a = numberOrNull(lo.axis, key);
    const b = numberOrNull(hi.axis, key);
    if (a !== null && b !== null) {
      axis[key] = lerp(a, b, t);
      continue;
    }
    // One side does not apply. Take the nearest option's reading, and where
    // that is the null one leave the key out: an absent key is how a whole
    // option already says "does not apply", and axisValues treats the two the
    // same, so the summed axis keeps behaving as it does today.
    const near = numberOrNull(option.axis, key);
    if (near !== null) axis[key] = near;
  }

  return {
    pos,
    t,
    lo,
    hi,
    option,
    optionId: option.id,
    financial: lerp(lo.financial || 0, hi.financial || 0, t),
    political: lerp(lo.political || 0, hi.political || 0, t),
    social: lerp(lo.social || 0, hi.social || 0, t),
    axis,
  };
}

/** The interpolated financial cost of one domain at one position. */
export function financialAt(data, domainId, p) {
  const v = valuesAt(data, domainId, p);
  return v ? v.financial : 0;
}

/** The option a position IS: rungs[round(pos)]. */
export function optionAt(data, domainId, p) {
  const v = valuesAt(data, domainId, p);
  return v ? v.option : null;
}

/**
 * What a set of choices costs in % of GDP. The tax domain carries no spend.
 *
 * `pos` is optional. A domain with a position is priced at that position; one
 * without is priced at its option, which is the same number when the position
 * is the option's own integer.
 */
export function spendOf(data, selection, pos) {
  let total = 0;
  for (const domain of data.domains) {
    const p = pos ? pos[domain.id] : undefined;
    if (Number.isFinite(Number(p))) {
      const v = valuesAt(data, domain.id, p);
      if (v) {
        total += v.financial;
        continue;
      }
    }
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
  const pos = positionsOf(data, state);

  let spend = 0;
  let political = 0;
  let social = 0;
  const changed = [];

  for (const domain of data.domains) {
    const chosen = (domain.options || []).find((o) => o.id === selection[domain.id]);
    if (!chosen) continue;

    // The position where there is one, the option where there is not. Tax has
    // no ladder, so it always falls through to its option, which carries no
    // financial cost and its own political and social.
    const v = valuesAt(data, domain.id, pos[domain.id]);
    const financial = v ? v.financial : (typeof chosen.financial === 'number' ? chosen.financial : 0);
    spend += financial;

    // WHAT COUNTS AS CHANGED IS THE IDENTITY, NOT THE POSITION, and that is
    // deliberate. The cost model charges you the price of the option you moved
    // TO rather than a difference, so leaving your own system is an inherently
    // discrete decision and there is one step in the political and social
    // meters wherever that rule is put. Putting it at the identity boundary
    // means a domain drifting inside its own option is still free, which is
    // what "a country spends nothing on its own status quo" says, and every
    // other part of the drag is continuous because the interpolated cost is.
    if (base[domain.id] !== undefined && base[domain.id] !== chosen.id) {
      changed.push({ domain: domain.id, domainName: domain.name, from: base[domain.id], to: chosen.id });
      political += v ? v.political : (chosen.political || 0);
      social += v ? v.social : (chosen.social || 0);
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
