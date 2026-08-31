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
//      cheapest-to-dearest by financial cost, and it LANDS ON A WHOLE RUNG. The
//      visitor's own thumb is continuous as of 01/09/2026 and a cut is not: a
//      drag is a drift and a cut is a decision, so the cascade closes a hospital
//      rather than shaving three per cent off one. The position it starts from
//      may be fractional, and what the cut saves is measured from there.
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
  clampPos,
  clampRate,
  financialAt,
  ladder,
  optionForRate,
  posOfOption,
  positionsOf,
  rateForOption,
  spendOf,
  taxStops,
} from './budget.js';

// The ladder moved to budget.js, because a position is measured along it and
// budget.js is what prices a position. It is still exported from here: this is
// where callers have always imported it from and there is one definition.
export { ladder } from './budget.js';

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
  const pos = positionsOf(data, state);
  const before = { ...selection };
  const beforePos = { ...pos };
  const order = orderOf(data);

  // Capacity does not depend on anything the cascade can change, so it is read
  // once. Only spend moves.
  const capacity = capacityOf(data, state).capacity;
  let over = spendOf(data, selection, pos) - capacity;
  if (over <= EPS) return { selection, pos, cuts: [], shortfall: 0 };

  const eligible = data.domains
    .map((d) => d.id)
    .filter((id) => id !== TAX_DOMAIN && id !== movedDomain && !isLocked(state, id));

  const rungs = new Map(eligible.map((id) => [id, ladder(data, id)]));
  const canStep = (id) => cheaperThan(rungs.get(id), selection[id]) !== null;

  // Rule 3. Targets are fixed once, in proportion to what each domain is
  // spending at the moment the overspend appears, and over the domains that can
  // actually move. Recomputing them every step would let a domain that has
  // already paid be asked again on the same basis as one that has not.
  // Priced at each domain's POSITION, not at its option, so a domain sitting
  // part way up its ladder is asked for its share of what it is actually
  // spending.
  const movable = eligible.filter(canStep);
  const totalSpend = movable.reduce((sum, id) => sum + financialAt(data, id, pos[id]), 0);
  const target = new Map(movable.map((id) => [
    id,
    totalSpend > EPS
      ? over * (financialAt(data, id, pos[id]) / totalSpend)
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
      const spend = financialAt(data, b, pos[b]) - financialAt(data, a, pos[a]);
      if (Math.abs(spend) > EPS) return spend;
      return order.indexOf(a) - order.indexOf(b);
    });

    const id = open[0];
    const next = cheaperThan(rungs.get(id), selection[id]);
    // Rule 4. The saving is measured from where the domain actually sits, which
    // may be part way up a rung, and it lands ON the rung below.
    const saved = financialAt(data, id, pos[id]) - (next.financial || 0);
    selection[id] = next.id;
    pos[id] = rungs.get(id).indexOf(next);
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
      // From where it stood to where it landed, so a domain cut from part way
      // up a rung reports what the visitor's budget actually got back.
      saved: round1(financialAt(data, id, beforePos[id]) - financialAt(data, id, pos[id])),
    }));

  return { selection, pos, cuts, shortfall: over > EPS ? over : 0 };
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
 *        For the twelve categorical domains, EITHER a position (a number, 0 to
 *        rungs-1, which is what the slider gives you) or an option id, which is
 *        the same as that option's own integer position.
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

  const next = {
    ...state,
    selection: { ...state.selection },
    pos: positionsOf(data, state),
    locked: [...(state.locked || [])],
  };
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
    const rungs = ladder(data, domainId);
    if (!rungs.length) return result(data, state, { ok: false, reason: 'unknown-option' });

    let position;
    if (typeof optionId === 'number' && Number.isFinite(optionId)) {
      // A position off the slider. It is held inside the ladder rather than
      // refused, because a thumb cannot leave its own track.
      position = clampPos(data, domainId, optionId);
    } else {
      const option = (domain.options || []).find((o) => o.id === optionId);
      if (!option) return result(data, state, { ok: false, reason: 'unknown-option' });
      position = posOfOption(data, domainId, optionId);
    }
    const landed = rungs[Math.round(position)];

    moved = {
      domain: domainId,
      domainName: domain.name,
      from: state.selection[domainId],
      to: landed.id,
      fromPos: positionsOf(data, state)[domainId],
      toPos: position,
    };
    next.selection[domainId] = landed.id;
    next.pos[domainId] = position;
  }

  const { selection, pos, cuts, shortfall } = cascade(data, next, domainId);
  next.selection = selection;
  next.pos = pos;

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
