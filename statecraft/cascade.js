// Statecraft's cascade. No DOM access: this module is pure so it can be tested
// in node.
//
// A visitor moves one slider. If that puts them over the money, something else
// has to give, and this decides what. It is the whole difference between a form
// that goes red at you and a government that has to find the money.
//
// THE FIVE RULES, in the order they bind:
//
//   1. A LOCKED domain never moves. Not by the cascade, and not by hand either:
//      a lock the visitor can move through by accident is not a lock. The UI
//      should show a locked slider as locked rather than letting it slide and
//      then refusing.
//   2. THE DOMAIN JUST MOVED IS NEVER THE ONE CUT. A control that undoes the
//      thing you just did with it is a control that fights you.
//   3. The cut is allocated IN PROPORTION to each unlocked domain's current
//      spend, so the big programmes give up the most. Targets are fixed once,
//      off the overspend as it stands, and then met by whole steps.
//   4. A domain gives way by STEPPING DOWN ITS OWN LADDER, one option at a time,
//      cheapest-to-dearest by financial cost. You cannot have 40% of mandatory
//      insurance, so nothing here is continuous except the tax rate.
//   5. If the overspend cannot be covered, that is REPORTED and the loop stops.
//      `ok` is false and `shortfall` says by how much. It never spins.
//
// Determinism is a property this file has to have, not one it is tested into:
// there is no randomness, no iteration over object keys in an order the engine
// chooses, and every tie is broken by an explicit rule ending in the fixed
// domain order from data.json. The same state and the same move give the same
// result, every time, on any engine.
//
// WHAT THE CUTS COST. Nothing is charged here. budget.js charges political
// capital and public patience on every domain that differs from the starting
// country, and it does not care who moved it, because cutting a programme is a
// reform too and somebody still has to pass it. The corollary is the useful
// half: a cut that lands back on the starting country's own option is free,
// because that is not a reform, it is a reversal.

import {
  TAX_DOMAIN,
  budgets,
  capacityOf,
  clampRate,
  optionForRate,
  rateForOption,
  spendOf,
  taxStops,
} from './budget.js';

const EPS = 1e-9;
const round1 = (n) => Math.round(n * 10) / 10;

/** Domain ids in data.json order. The last tiebreak, and the only arbitrary one. */
const orderOf = (data) => data.domains.map((d) => d.id);

export function isLocked(state, domainId) {
  return (state.locked || []).includes(domainId);
}

/** A new state with `domainId` locked or unlocked. Never mutates. */
export function setLock(state, domainId, locked) {
  const now = (state.locked || []).filter((id) => id !== domainId);
  if (locked) now.push(domainId);
  return { ...state, locked: now };
}

export function toggleLock(state, domainId) {
  return setLock(state, domainId, !isLocked(state, domainId));
}

/**
 * A domain's options, cheapest to dearest by financial cost. This is the order
 * the slider runs in, and the order the cascade steps down.
 *
 * The sort is stable, so two options at the same cost keep their data.json
 * order rather than swapping about between engines.
 */
export function ladder(data, domainId) {
  const domain = data.domains.find((d) => d.id === domainId);
  if (!domain || domain.id === TAX_DOMAIN) return [];
  return (domain.options || []).slice().sort((a, b) => (a.financial || 0) - (b.financial || 0));
}

/** The nearest STRICTLY cheaper option below `optionId`, or null at the bottom. */
function cheaperThan(rungs, optionId) {
  const i = rungs.findIndex((o) => o.id === optionId);
  if (i < 0) return null;
  const here = rungs[i].financial || 0;
  for (let j = i - 1; j >= 0; j -= 1) {
    if ((rungs[j].financial || 0) < here - EPS) return rungs[j];
  }
  // Ties are skipped rather than stepped through. A step that saves nothing
  // would still be charged political capital, which is a cut that costs and
  // buys nothing.
  return null;
}

function financialOf(data, domainId, optionId) {
  const domain = data.domains.find((d) => d.id === domainId);
  const o = domain ? (domain.options || []).find((x) => x.id === optionId) : null;
  return o && typeof o.financial === 'number' ? o.financial : 0;
}

function nameOf(data, domainId) {
  const domain = data.domains.find((d) => d.id === domainId);
  return domain ? domain.name : domainId;
}

/**
 * Pay for an overspend out of the unlocked domains.
 * @returns {{selection: object, cuts: object[], shortfall: number}}
 */
function cascade(data, state, movedDomain) {
  const selection = { ...state.selection };
  const before = { ...selection };
  const order = orderOf(data);

  // Capacity does not depend on anything the cascade can change, so it is read
  // once. Only spend moves.
  const capacity = capacityOf(data, state).capacity;
  let over = spendOf(data, selection) - capacity;
  if (over <= EPS) return { selection, cuts: [], shortfall: 0 };

  const eligible = data.domains
    .map((d) => d.id)
    .filter((id) => id !== TAX_DOMAIN && id !== movedDomain && !isLocked(state, id));

  const rungs = new Map(eligible.map((id) => [id, ladder(data, id)]));
  const canStep = (id) => cheaperThan(rungs.get(id), selection[id]) !== null;

  // Rule 3. Targets are fixed once, in proportion to what each domain is
  // spending at the moment the overspend appears, and over the domains that can
  // actually move. Recomputing them every step would let a domain that has
  // already paid be asked again on the same basis as one that has not.
  const movable = eligible.filter(canStep);
  const totalSpend = movable.reduce((sum, id) => sum + financialOf(data, id, selection[id]), 0);
  const target = new Map(movable.map((id) => [
    id,
    totalSpend > EPS
      ? over * (financialOf(data, id, selection[id]) / totalSpend)
      : over / movable.length,
  ]));
  const given = new Map(movable.map((id) => [id, 0]));
  const steps = new Map(movable.map((id) => [id, 0]));

  // Bounded by construction: every pass moves one domain strictly down its own
  // ladder and no domain ever moves back up, so the loop cannot run longer than
  // the total number of options. The cap is belt and braces, and if it were ever
  // hit the shortfall below would report it rather than the page hanging.
  const cap = data.domains.reduce((n, d) => n + (d.options || []).length, 0) + 1;
  for (let pass = 0; pass < cap && over > EPS; pass += 1) {
    const open = movable.filter(canStep);
    if (!open.length) break;

    open.sort((a, b) => {
      const deficit = (target.get(b) - given.get(b)) - (target.get(a) - given.get(a));
      if (Math.abs(deficit) > EPS) return deficit;
      const spend = financialOf(data, b, selection[b]) - financialOf(data, a, selection[a]);
      if (Math.abs(spend) > EPS) return spend;
      return order.indexOf(a) - order.indexOf(b);
    });

    const id = open[0];
    const next = cheaperThan(rungs.get(id), selection[id]);
    const saved = financialOf(data, id, selection[id]) - next.financial;
    selection[id] = next.id;
    given.set(id, given.get(id) + saved);
    steps.set(id, steps.get(id) + 1);
    over -= saved;
  }

  const cuts = order
    .filter((id) => before[id] !== selection[id])
    .map((id) => ({
      domain: id,
      domainName: nameOf(data, id),
      from: before[id],
      to: selection[id],
      steps: steps.get(id) || 0,
      saved: round1(financialOf(data, id, before[id]) - financialOf(data, id, selection[id])),
    }));

  return { selection, cuts, shortfall: over > EPS ? over : 0 };
}

function result(data, state, extra) {
  return {
    ok: true,
    reason: '',
    state,
    moved: null,
    cuts: [],
    shortfall: 0,
    budgets: budgets(data, state),
    ...extra,
  };
}

/**
 * Move one domain, and let the rest of the budget fall in behind it.
 *
 * @param {object} data parsed data.json
 * @param {{start: string, taxRate: number, selection: object, locked: string[]}} state
 * @param {string} domainId  the domain the visitor moved
 * @param {string|number} optionId
 *        For the twelve categorical domains, the option id to move to.
 *        For 'tax', either a rate (a number, 12 to 55, which is what the slider
 *        gives you) or the id of one of the six stops, which snaps the rate to
 *        that stop's headline take.
 * @returns {{
 *   ok: boolean,            // the move stuck and the money balances
 *   reason: string,         // '' | 'unknown-domain' | 'unknown-option' | 'locked' | 'shortfall'
 *   state: object,          // the new state; the old one is never mutated
 *   moved: object|null,     // {domain, domainName, from, to, fromRate?, toRate?}
 *   cuts: object[],         // [{domain, domainName, from, to, steps, saved}], data.json order
 *   shortfall: number,      // % of GDP still unfunded, 0 when covered
 *   budgets: object,        // budgets() for the new state, so the UI need not recompute
 * }}
 */
export function applyChange(data, state, domainId, optionId) {
  const domain = data.domains.find((d) => d.id === domainId);
  if (!domain) return result(data, state, { ok: false, reason: 'unknown-domain' });
  if (isLocked(state, domainId)) return result(data, state, { ok: false, reason: 'locked' });

  const next = { ...state, selection: { ...state.selection }, locked: [...(state.locked || [])] };
  let moved;

  if (domainId === TAX_DOMAIN) {
    let rate;
    if (typeof optionId === 'number' && Number.isFinite(optionId)) {
      rate = clampRate(optionId);
    } else if (taxStops(data).some((o) => o.id === optionId)) {
      rate = rateForOption(data, optionId);
    } else {
      return result(data, state, { ok: false, reason: 'unknown-option' });
    }
    const from = state.selection[TAX_DOMAIN];
    next.taxRate = rate;
    next.selection[TAX_DOMAIN] = optionForRate(data, rate);
    moved = {
      domain: TAX_DOMAIN,
      domainName: domain.name,
      from,
      to: next.selection[TAX_DOMAIN],
      fromRate: capacityOf(data, state).rate,
      toRate: rate,
    };
  } else {
    const option = (domain.options || []).find((o) => o.id === optionId);
    if (!option) return result(data, state, { ok: false, reason: 'unknown-option' });
    moved = {
      domain: domainId,
      domainName: domain.name,
      from: state.selection[domainId],
      to: optionId,
    };
    next.selection[domainId] = optionId;
  }

  const { selection, cuts, shortfall } = cascade(data, next, domainId);
  next.selection = selection;

  return {
    ok: shortfall === 0,
    reason: shortfall ? 'shortfall' : '',
    state: next,
    moved,
    cuts,
    shortfall: round1(shortfall),
    budgets: budgets(data, next),
  };
}

/** The tax slider. Sugar for applyChange(data, state, 'tax', rate). */
export function setTaxRate(data, state, rate) {
  return applyChange(data, state, TAX_DOMAIN, Number(rate));
}
