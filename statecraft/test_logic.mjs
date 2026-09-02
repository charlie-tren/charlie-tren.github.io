// node --test test_logic.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  budgets, blockers, capacityOf, optionForRate, rateForOption, realisedRevenue,
  spendOf, startingState, REFORM_POOL, TAX, reformCost,
  clampPos, financialAt, posFromSelection, posOfOption, positionsOf, valuesAt,
} from './budget.js';
import { applyChange, ladder, setLock, setTaxRate } from './cascade.js';
import { axisValues, rank, matchable } from './match.js';
import { encode, decode, countryForTimezone, detectTimezone } from './state.js';

const here = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(join(here, 'data.json'), 'utf8'));

const byCode = (code) => data.countries.find((c) => c.code === code);

// THE COUNTRIES THAT CAN BE AN ANSWER. data.countries is forty-five rows and
// ALL FORTY-FIVE now carry a policy matrix, since Uruguay, Taiwan, Saudi
// Arabia, Qatar, Kuwait, Malta, Cyprus and Panama were coded on 31/08/2026 and
// the measured-only pool added on 30/08/2026 is empty.
//
// THIS FILTER IS NOT NOW REDUNDANT AND MUST NOT BE REMOVED. It reads the flag
// rather than counting the rows, so it costs nothing while the pool is empty
// and it is the only thing standing between an `choices: {}` row and the reveal
// on the day the next country is added. The guard being currently unexercised
// is exactly why the test below feeds it a synthetic empty row. Every test that
// starts from a country's choices, encodes them into a URL, or asks what a
// country matches runs over THIS list, because a row with no matrix has nothing
// to start from. Reading it through match.js rather than filtering here keeps
// one definition of the split in one place.
const MATCHABLE = matchable(data);
const domain = (id) => data.domains.find((d) => d.id === id);
const option = (domainId, optionId) => domain(domainId).options.find((o) => o.id === optionId);
const one = (n) => Math.round(n * 10) / 10;

/** A state built by hand, for the cases where the point is an illegal position. */
const stateOf = (code, overrides = {}) => ({ ...startingState(data, code), ...overrides });

test('data.json has the shape the modules assume', () => {
  assert.equal(data.domains.length, 13);
  assert.equal(data.countries.length, 45);
  assert.equal(MATCHABLE.length, 45);
  assert.equal(data.countries.filter((c) => !c.matchable).length, 0);
  assert.equal(data.axes.length, 14);
  assert.equal(data.fallback, 'AU');

  // The flag and the matrix are the same claim said twice, and the JS reads the
  // flag. Python asserts this too; it is repeated here because it is what every
  // guard below depends on and data.json is the artefact the page actually loads.
  for (const c of data.countries) {
    assert.equal(typeof c.matchable, 'boolean', `${c.code} matchable is not a boolean`);
    assert.equal(
      c.matchable,
      Object.keys(c.choices).length > 0,
      `${c.code} is matchable=${c.matchable} with ${Object.keys(c.choices).length} choices`,
    );
    if (c.matchable) assert.equal(Object.keys(c.choices).length, 13, `${c.code} needs 13 choices`);
  }
  assert.equal(data.fallback, 'AU');
});

// A MEASURED-ONLY COUNTRY IS NEVER AN ANSWER.
//
// The count alone does not deliver this. rank() sorts by matched descending and
// then by distance ascending, so on a design that agrees with no country in any
// domain the entire field ties at zero and the sort falls through to distance,
// where a measured-only country with a close set of indicators wins. That design
// is reachable: five options are tagged to no country at all, so a visitor who
// picks the aspirational menu builds one. The guard is the filter in match.js
// and this is the test that it is doing the work.
//
// THE REAL POOL EMPTIED ON 31/08/2026 when the last eight rows were coded, and
// this test was rewritten rather than deleted. A guard with nothing left to
// exclude reads exactly like a guard that works, so the exclusion is now
// asserted against a SYNTHETIC measured-only row spliced into a copy of the
// data, built to be the adversary the real ones were: indicators sitting at the
// dead centre of every axis, so it wins any distance tiebreak it is allowed
// into. If someone deletes the filter in match.js, this fails. It also fails if
// a future measured-only country is added and the filter has rotted, because
// the same assertions run over the real rows alongside the fake one.
test('rank never returns a country with no policy matrix', () => {
  const midpoint = Object.fromEntries(data.axes.map((a) => [
    a.id, { value: (a.bounds[0] + a.bounds[1]) / 2, year: 2026, source: 'synthetic test fixture' },
  ]));
  const probe = {
    code: 'ZZ', name: 'Nowhere', timezones: [], nonTaxRevenue: 0.0,
    matchable: false, choices: {}, indicators: midpoint,
  };
  const spiked = { ...data, countries: [...data.countries, probe] };
  const unmatchable = new Set(
    spiked.countries.filter((c) => !c.matchable).map((c) => c.code),
  );
  assert.ok(unmatchable.has('ZZ'), 'the fixture must itself be measured only');
  assert.equal(matchable(spiked).length, MATCHABLE.length, 'the fixture must not be matchable');

  // Every matchable country's own design.
  for (const country of MATCHABLE) {
    const rows = rank(spiked, country.choices);
    assert.equal(rows.length, MATCHABLE.length);
    for (const row of rows) {
      assert.ok(!unmatchable.has(row.code), `${row.code} was ranked against ${country.code}`);
    }
  }

  // The adversarial case: a design nothing in the matrix shares, built from the
  // untagged options wherever one exists. Without the filter this is where a
  // measured-only country wins on the distance tiebreak.
  const untagged = {};
  for (const d of data.domains) {
    const aspirational = d.options.find((o) => (o.countries || []).length === 0);
    if (aspirational) untagged[d.id] = aspirational.id;
  }
  assert.ok(Object.keys(untagged).length >= 4, 'expected several untagged options');
  const rows = rank(spiked, untagged);
  assert.equal(rows.length, MATCHABLE.length);
  for (const row of rows) {
    assert.ok(!unmatchable.has(row.code), `${row.code} won an all-aspirational design`);
  }

  // An empty selection matches nothing anywhere, so every row ties at zero and
  // the sort is decided entirely by distance. The winner must still be one of
  // the forty-five.
  const empty = rank(spiked, {});
  assert.equal(empty[0].matched, 0, 'an empty design should agree with nobody');
  assert.ok(!unmatchable.has(empty[0].code), `${empty[0].code} won an empty design`);
});

// KUWAIT'S BUDGET NEVER BINDS, AND THAT IS THE DATA BEING RIGHT.
//
// Its nonTaxRevenue is 58.2, from an IMF general government revenue figure of
// 74.2% of GDP against a modelled spend of 40.1. Most of that gap is Kuwait
// Investment Authority income, which the IMF imputes into general government
// because Kuwait does not publish accounts at that level. The UAE's own 27.8
// comes from the same indicator and the same call, so the column is consistent;
// the two states simply book sovereign fund returns differently.
//
// The consequence is that a visitor starting in Kuwait can buy the whole menu,
// and dragging tax to the floor still leaves them about 30 points spare. The
// financial constraint does nothing there. Political capital and public patience
// still bind, so the page works, but the tax slider is inert for that one start.
//
// This is asserted rather than left as a comment because nothing else fails on
// it: a country with unlimited money passes every other check in this file. The
// test exists so that if a later data change gives a SECOND country that much
// headroom, someone finds out from a red test rather than from the page feeling
// slack. If Kuwait itself is ever re-sourced onto a budgetary-central-government
// basis, this is the test that should be updated in the same commit.
test('Kuwait is the one country whose budget never binds, and only Kuwait', () => {
  const spare = (code, rate) => {
    const base = startingState(data, code);
    const at = rate === undefined ? base : setTaxRate(data, base, rate).state;
    const f = budgets(data, at).financial;
    return f.capacity - f.used;
  };

  const loose = MATCHABLE
    .map((c) => ({ code: c.code, spare: spare(c.code) }))
    .filter((r) => r.spare > 20)
    .map((r) => r.code);
  assert.deepEqual(loose, ['KW'],
    `expected Kuwait alone to have more than 20 points of spare budget, got ${loose.join(', ')}`);

  // Even emptied to the bottom of the slider it cannot be made to run short.
  assert.ok(spare('KW', TAX.MIN) > 20,
    'Kuwait at the floor of the tax slider should still have money to spare');

  // Every other country CAN be pushed into deficit by the tax slider, which is
  // what makes the control mean something for the other forty-four.
  const alsoImmune = MATCHABLE
    .filter((c) => c.code !== 'KW' && spare(c.code, TAX.MIN) > 5)
    .map((c) => c.code);
  assert.deepEqual(alsoImmune, [],
    `these cannot be pushed into deficit either: ${alsoImmune.join(', ')}`);

  // And the political pool still binds there, so Kuwait is not unconstrained.
  assert.equal(budgets(data, startingState(data, 'KW')).political.capacity, REFORM_POOL);
});

// 1. Every country can afford to be itself.
test('all forty-five countries can afford to be themselves', () => {
  const financiallyOver = [];

  for (const country of MATCHABLE) {
    const b = budgets(data, startingState(data, country.code));
    assert.equal(b.political.used, 0, `${country.code} should spend no political capital on its own status quo`);
    assert.equal(b.social.used, 0, `${country.code} should spend no social capital on its own status quo`);
    assert.equal(b.changedCount, 0, `${country.code} has changed nothing`);
    if (b.financial.over) financiallyOver.push(country.code);
  }

  // TWENTY OF TWENTY, and the UAE was the one that used to fail. Three changes
  // got it here and the order matters, because only two were data fixes.
  //
  // First, tax_minimal raised 16.0% of GDP, which was a TAX TAKE standing in for
  // general government REVENUE. For a petrostate those are different things. It
  // was raised to 27.8%, the IMF figure for 2024, cross-checked against the
  // Article IV surplus, and that closed three-quarters of the gap.
  //
  // Second, and this is the fix the 27.8 was standing in for: a state's income
  // is tax PLUS non-tax income, and one field cannot be both. The tax option now
  // carries a headline RATE of 16.0 and the UAE's row carries a nonTaxRevenue of
  // 11.8, which is the hydrocarbon and investment income no tax-to-GDP series
  // captures. 16.0 realised is 16.0, and 16.0 plus 11.8 is the same 27.8. The
  // difference is that the oil now survives a change of tax policy, which is the
  // only reading of it that was ever true.
  //
  // The residual gap was NOT a revenue problem and must not be fixed by reaching
  // for a bigger revenue number: 2022 reads 32.55% and would have made this test
  // pass on its own, which is exactly the wrong reason to pick a year. It was
  // the same wrong-basis fault on the SPENDING side. The UAE's modelled spend is
  // 32.0% of GDP against IMF general government expenditure of 21.4%, mostly
  // because re_generous carries France's 14.0% pension outlay while GPSSA covers
  // Emirati and GCC nationals only, roughly an eighth of residents.
  //
  // So the third change is in budget.js, not in the data: financial capacity is
  // what the state raises OR what the starting country already spends, whichever
  // is larger. A country manifestly manages to run its own settings, so those
  // are affordable by definition and only ADDITIONAL spending needs funding.
  // That also makes all three budgets say one thing: you inherit a country and
  // you pay for what you change.
  // STILL EMPTY WITH NINE MORE COUNTRIES IN IT, checked 30/08/2026 when
  // Ireland, Italy, Spain, Portugal, Austria, Belgium, Greece, Luxembourg and
  // Iceland were coded. None of the nine needed a nonTaxRevenue or the floor to
  // pay for its own status quo.
  // STILL EMPTY WITH EIGHT MORE, checked 30/08/2026 when Czechia, Poland,
  // Slovakia, Slovenia, Croatia, Lithuania, Latvia and Hungary were coded. None
  // of the eight needed a nonTaxRevenue or the floor to pay for its own status
  // quo, which is the expected result: all eight measure a tax take of 33% to
  // 38% of GDP against modelled spends below that.
  // STILL EMPTY WITH THE LAST EIGHT, checked 31/08/2026, and this is the one
  // batch where it was in doubt. Six of the eight needed the floor rather than
  // clearing on their own, which is recorded below, but the floor is what stops
  // "needs a top-up" becoming "cannot afford itself" and none of the eight is
  // over.
  assert.deepEqual(financiallyOver, []);
  assert.equal(MATCHABLE.length, 45);

  // The floor only ever binds for the UAE. Nineteen countries raise more than
  // they spend, so their capacity is untouched by it, and this asserts that
  // rather than assuming it: if the floor ever starts propping up a second
  // country, something has gone wrong in the cost model and should be looked at.
  //
  // TWO COUNTRIES ARE PROPPED UP NOW, and the second one arrived with the tax
  // curve rather than with a data change, so it is worth saying what it is.
  // France runs tax_continental, a headline 43, which realises 41.3. Its modelled
  // spend is 42.2, so it is 0.9 short of funding itself out of tax and the floor
  // carries it. Under the old flat 43 it cleared by 0.8.
  //
  // That is not a fault to tune away. France genuinely does not fund its
  // spending out of revenue: general government expenditure has exceeded revenue
  // every year for half a century, and the 2024 deficit was 5.8% of GDP. A model
  // in which the highest-spending country in the set balances its books would be
  // the wrong answer arriving quietly. The two floored countries are exactly the
  // two that do not pay for themselves out of tax, one on oil and one on debt.
  //
  // A THIRD would be worth looking at, because the next closest is Israel at 3.3
  // points of headroom and nothing else is inside 4.
  // THE SET CHANGED when starting rates moved from the option's hand-set number
  // to each country's own measured tax take, and both moves are explicable
  // rather than drift.
  //
  // France came OFF the floor: it measures 46.1 against the 43.0 its option
  // carried, so it now raises more than the model spends and pays for itself.
  //
  // Singapore went ON: it taxes 12.1% of GDP, the lowest measured figure in the
  // set by a wide margin, while the model prices its choices at 19.5. That is
  // the same shape as the UAE's oil rather than a fault. Singapore funds
  // healthcare and housing largely out of compulsory CPF savings, which are not
  // tax and appear in no tax-to-GDP series. Giving it a nonTaxRevenue would be
  // the tidier fix and it is not made here, because it would mean inventing a
  // figure rather than sourcing one.
  const propped = MATCHABLE
    .filter((c) => budgets(data, startingState(data, c.code)).financial.floored)
    .map((c) => c.code);
  //
  // TWO MORE ARRIVED ON 30/08/2026 with the nine new matrices, and both are the
  // same shape as Singapore rather than a fault in their cells.
  //
  // Ireland needs the largest top-up in the file, 5.1 points. Its measured tax
  // take is 21.7% of GDP, and that denominator is a GDP inflated by roughly
  // two-fifths by multinational intellectual property and contract
  // manufacturing that no Irish resident consumes. On the CSO's modified gross
  // national income basis the take is closer to 35%. The model prices Ireland's
  // own choices at 26.8, which is what a country taxing 35% of GNI* can plainly
  // afford. The floor is doing exactly what it was built for: reading the
  // wrong-basis revenue figure as the artefact it is.
  //
  // Spain is the marginal case at 0.6 points and needs no special explanation.
  // It runs a persistent general government deficit, so a model in which it
  // funds itself out of tax to the last tenth would be the surprising result.
  //
  // SIX MORE ARRIVED ON 31/08/2026 AND THE LIST MORE THAN DOUBLED. That is the
  // largest single change to this assertion and it is not drift, so the top-up
  // each one needs is written down beside it. Two shapes, and only one of them
  // is about the countries:
  //
  //   THE THREE GULF STATES WERE THE UAE'S CASE WITHOUT THE UAE'S FIX, and
  //   they needed the three largest top-ups in the file by a distance: Kuwait
  //   24.0 points of GDP, Qatar 19.0 and Saudi Arabia 13.5. Their oil was
  //   being carried by the top-up because their nonTaxRevenue was 0.0 while the
  //   UAE's was 11.8, which said the wrong thing: a top-up means a country
  //   spends more than the model says it raises, and for a petrostate the true
  //   statement is that it raises more, from something that is not tax.
  //
  //   THAT IS CLOSED AS OF 31/08/2026. All three now carry a sourced
  //   nonTaxRevenue on the UAE's construct, general government total revenue
  //   less the 16.0 they start on, from the same IMF indicator and year that
  //   reproduces the UAE's 27.8. Saudi Arabia 11.1, Qatar 10.7, Kuwait 58.2,
  //   with the sources and the Kuwait caveat above the Saudi Arabia row in
  //   countries.py. The top-ups fall accordingly and are asserted below.
  //
  //   KUWAIT COMES OFF THIS LIST ENTIRELY. Its general government revenue of
  //   74.2% of GDP exceeds what the model prices its own choices at, 40.1, so
  //   there is nothing left for the floor to do and it starts with about 34
  //   points spare. That is the sourced figure rather than a tuned one, and
  //   roughly thirty of those points are IMF-estimated sovereign fund
  //   investment income that Kuwait's own budget never sees. See the row.
  //
  //   WHAT IS STILL OPEN FOR THE THREE IS THE tax_take CELL, not this column.
  //   IMF WoRLD, whose tax-plus-contributions total reproduces the OECD figure
  //   to a tenth on five countries that have both, publishes no social
  //   contributions line for any of the three, so the total cannot be formed
  //   from it. UNU-WIDER's GRD reads Cyprus at 28.2% of GDP for 2023 against
  //   the 36.0 the OECD basis gives, nearly eight points out where the answer
  //   is known, and has no Qatar observation after 2008. So all three still
  //   start on tax_minimal's 16.0, which is also the number subtracted above.
  //
  //   PANAMA, URUGUAY AND MALTA are the Singapore shape: a real measured tax
  //   take that is genuinely low. Panama needs 10.5 points on a measured take of
  //   11.3% of GDP, THE LOWEST IN THE FILE, with roughly half the labour force
  //   informal and outside it. Uruguay needs 2.3 on 27.3 and Malta 4.1 on 28.7,
  //   both of which run deficits, and both are smaller top-ups than Ireland's.
  //
  // TAIWAN IS ON THE LIST AS OF 31/08/2026 AND IT WAS NOT BEFORE, which is the
  // measurement arriving rather than anything changing in Taiwan. Both it and
  // Cyprus used to start at tax_anglo's 34.0 for want of a measured take, and
  // the note that stood here said so and called it luck of the option. Both now
  // carry a cell.
  //
  //   TAIWAN measures 20.3% of GDP against the 34.0 it inherited, so its
  //   starting rate falls 13.7 points and it needs an 11.9-point top-up where it
  //   needed none. That is not a new problem, it is the old one becoming
  //   visible: the model prices Taiwan's own choices at 32.2 and Taiwan does not
  //   raise 32.2. Conscription and the single-payer NHI are both cheap in a way
  //   the menu cannot price, and its 20.3 is itself an upper bound. See the
  //   cell.
  //
  //   CYPRUS measures 36.1 against the same 34.0, so it moves the other way,
  //   gains 2.1 points of capacity and stays off the list with 6.1 points of
  //   headroom.
  //
  // THE FLOOR IS THE HONEST MECHANISM AND THE MISSING INDICATOR IS THE PROBLEM.
  // A country with no measured take inherits its option's number, and whether
  // that flatters or punishes it is pure luck of which option it sits on. Three
  // rows are still in that position and they are the Gulf three above.
  assert.deepEqual(propped, ['SG', 'AE', 'IE', 'ES', 'UY', 'TW', 'SA', 'QA', 'MT', 'PA']);

  // THE GULF FOUR, PINNED. The three sourced nonTaxRevenue figures land here
  // and nowhere else a test can see them, so the top-up each one leaves behind
  // is asserted rather than described. The UAE is the control: it did not move
  // when the other three were sourced, and if it ever does, the construct has
  // been changed under it.
  for (const [code, nonTax, topUp, capacity] of [
    ['AE', 11.8, 4.2, 32.0],
    ['SA', 11.1, 2.4, 29.5],
    ['QA', 10.7, 8.3, 35.0],
    ['KW', 58.2, 0.0, 74.2],
  ]) {
    const f = budgets(data, startingState(data, code)).financial;
    assert.equal(f.nonTaxRevenue, nonTax, `${code} nonTaxRevenue`);
    assert.equal(f.topUp, topUp, `${code} top-up`);
    assert.equal(f.capacity, capacity, `${code} capacity`);
  }
  // Kuwait is the one that funds itself: its revenue exceeds its own modelled
  // spend, so the floor is inert there and it is the only Gulf row off the list.
  assert.equal(budgets(data, startingState(data, 'KW')).financial.floored, false);

  const ae = budgets(data, startingState(data, 'AE'));
  assert.equal(ae.financial.capacity, 32.0, 'floored at what the UAE already spends');
  assert.equal(ae.financial.left, 0);
  assert.deepEqual(blockers(ae), []);

  // And the floor must not become a way to spend freely: one dearer choice on
  // top of the UAE's own settings still goes over.
  const greedy = stateOf('AE');
  greedy.selection = { ...greedy.selection, healthcare: 'hc_public' };
  assert.ok(budgets(data, greedy).financial.over,
    'the floor must not stop the financial budget binding');
});

// 1a. THE CURVE. Seven calibration points, and the two shape properties the rest
// of the design leans on.
test('realised revenue matches its calibration and is monotonic and concave', () => {
  const points = [[12, 12.0], [30, 30.0], [34, 33.8], [40, 39.0], [46, 43.4], [50, 46.0], [55, 48.8]];
  for (const [rate, expected] of points) {
    assert.equal(one(realisedRevenue(rate)), expected, `realised(${rate})`);
  }

  // Monotonic: pushing the slider up never lowers the budget. A control that
  // sometimes takes money away when you push it up reads as a bug, whatever the
  // economics say, so the curve must not turn over inside the slider.
  let last = -Infinity;
  let lastGain = Infinity;
  for (let r = TAX.MIN; r <= TAX.MAX; r += 0.5) {
    const v = realisedRevenue(r);
    assert.ok(v > last, `realised must rise: ${r} gave ${v} after ${last}`);
    if (last > -Infinity) {
      const gain = v - last;
      // Concave: each half point of headline tax buys no more than the one
      // before it. Strictly less once past the kink, and equal below it.
      assert.ok(gain <= lastGain + 1e-9, `realised must be concave, ${r} gained ${gain} after ${lastGain}`);
      lastGain = gain;
    }
    last = v;
  }

  // The last point of tax raises about half a point of revenue.
  assert.equal(one(realisedRevenue(TAX.MAX) - realisedRevenue(TAX.MAX - 1)), 0.5);

  // Off the ends of the slider the value is held, not extrapolated. A negative
  // capacity from a rate of 900 is not a state of the world worth modelling.
  assert.equal(realisedRevenue(-40), realisedRevenue(TAX.MIN));
  assert.equal(realisedRevenue(900), realisedRevenue(TAX.MAX));
  assert.equal(realisedRevenue('nonsense'), realisedRevenue(TAX.MIN));
});

// 1b. Moved here from test_data.py, because the claim now needs the curve and
// the curve lives in JavaScript.
test('the financial budget still binds at the top of the slider', () => {
  const dearest = data.domains
    .filter((d) => d.id !== 'tax')
    .reduce((sum, d) => sum + Math.max(...d.options.map((o) => o.financial)), 0);

  assert.ok(dearest > realisedRevenue(TAX.MAX), `the dearest possible country costs `
    + `${one(dearest)}% of GDP and the dearest tax rate realises `
    + `${one(realisedRevenue(TAX.MAX))}%: the budget never binds`);

  // KNOWN AND REPORTED, not asserted away: add the UAE's 11.8 of non-tax revenue
  // and the top of the slider DOES fund the dearest menu in every domain. That
  // is the correct behaviour of a petrostate that also taxes like Denmark, and
  // it is why the political pool has to be the binding constraint at the top
  // rather than the money.
  const petro = realisedRevenue(TAX.MAX) + Math.max(...MATCHABLE.map((c) => c.nonTaxRevenue));
  assert.ok(petro > dearest, 'if this ever fails the non-tax figure has moved and '
    + 'the comment above is stale');
});

// 2. Changing one domain charges exactly that option's cost, and changing back charges nothing.
test('changing one domain charges exactly that option, and changing back charges nothing', () => {
  const au = byCode('AU');
  assert.equal(au.choices.housing, 'ho_market');

  const start = startingState(data, 'AU');
  const reformed = { ...start.selection, housing: 'ho_singapore' };
  const b = budgets(data, { ...start, selection: reformed });
  const ho = option('housing', 'ho_singapore');

  // The raw costs in policies.py are on the scale they were calibrated on; the
  // meters are on the pool's scale. Comparing the two directly is comparing two
  // units, which is what this used to do before the pool became 100.
  assert.equal(ho.political, 70);
  assert.equal(ho.social, 10);
  assert.equal(b.political.used, Math.round(reformCost(ho.political)));
  assert.equal(b.social.used, Math.round(reformCost(ho.social)));
  assert.equal(b.political.left, Math.round(REFORM_POOL - reformCost(70)));
  assert.equal(b.changedCount, 1);
  assert.equal(b.changed[0].domain, 'housing');

  // Financial moves by the difference in cost, not by the full new cost.
  const baseB = budgets(data, start);
  assert.equal(
    b.financial.used,
    one(baseB.financial.used - option('housing', 'ho_market').financial + ho.financial),
  );

  const back = budgets(data, { ...start, selection: { ...reformed, housing: 'ho_market' } });
  assert.equal(back.political.used, 0);
  assert.equal(back.social.used, 0);
  assert.equal(back.changedCount, 0);
});

// 3. The pool binds.
test('the political pool binds when every domain is changed to its dearest option', () => {
  const start = startingState(data, 'DK');
  const dearest = {};
  for (const d of data.domains) {
    dearest[d.id] = d.options.reduce((a, b) => (b.political > a.political ? b : a)).id;
  }
  const b = budgets(data, {
    ...start, selection: dearest, taxRate: rateForOption(data, dearest.tax),
  });
  assert.ok(b.political.used > REFORM_POOL, `expected over ${REFORM_POOL}, got ${b.political.used}`);
  assert.ok(b.political.over);
  assert.ok(blockers(b).includes('political'));

  // And the pool is not so tight that a couple of reforms already blow it.
  const twoReforms = { ...start.selection, housing: 'ho_singapore', energy: 'en_car_free' };
  assert.equal(budgets(data, { ...start, selection: twoReforms }).political.over, false);
});

// 4. A country matches itself on all thirteen domains and tops its own ranking.
test('every country matches itself on all thirteen domains and ranks itself first', () => {
  for (const country of MATCHABLE) {
    const rows = rank(data, country.choices);
    const self = rows.find((r) => r.code === country.code);
    assert.equal(self.matched, 13, `${country.code} should match itself on all 13`);
    assert.equal(self.agreements.length, 13);
    assert.equal(self.divergences.length, 0);
    assert.equal(rows[0].code, country.code, `${country.code} should be its own top result, got ${rows[0].code}`);
  }
});

// 5. Ties break on distance, not arbitrarily.
test('rows are ordered by matched descending then distance ascending', () => {
  const rows = rank(data, byCode('AU').choices);
  let tieSeen = false;
  for (let i = 1; i < rows.length; i += 1) {
    assert.ok(rows[i - 1].matched >= rows[i].matched, 'matched must be descending');
    if (rows[i - 1].matched === rows[i].matched) {
      tieSeen = true;
      assert.ok(
        rows[i - 1].distance <= rows[i].distance,
        `tie on ${rows[i].matched} matched should break on distance: ${rows[i - 1].code} ${rows[i - 1].distance} then ${rows[i].code} ${rows[i].distance}`,
      );
    }
  }
  assert.ok(tieSeen, 'expected at least one tie on matched count');

  // A country ranked above another on distance alone really is nearer on the axes.
  const nz = rows.find((r) => r.code === 'NZ');
  assert.ok(Number.isFinite(nz.distance) && nz.distance > 0);
});

// 6. Divergences surface the countries that do what you chose.
test('divergences name the countries that already do what you chose', () => {
  const au = byCode('AU');
  const selection = { ...au.choices, housing: 'ho_singapore' };
  const rows = rank(data, selection);

  const us = rows.find((r) => r.code === 'US');
  const housing = us.divergences.find((d) => d.domain === 'housing');
  assert.ok(housing, 'housing should diverge from the US once you pick the Singapore model');
  assert.equal(housing.yours.id, 'ho_singapore');
  assert.equal(housing.theirs.id, 'ho_market');
  assert.ok(housing.yourCountries.includes('SG'), 'Singapore should be named as doing what you chose');
  assert.deepEqual(housing.yourCountries, option('housing', 'ho_singapore').countries);
  assert.equal(housing.domainName, domain('housing').name);

  // Singapore itself now agrees with you on housing, so it is not a divergence there.
  const sg = rows.find((r) => r.code === 'SG');
  assert.ok(sg.agreements.some((a) => a.domain === 'housing'));
});

// 7. URL state round-trips.
test('URL state round-trips for every country', () => {
  for (const country of MATCHABLE) {
    const hash = encode(data, country.code, country.choices);
    assert.match(hash, /^[A-Z]{2}-[0-9a-z]{13}$/, `bad hash for ${country.code}: ${hash}`);
    const back = decode(data, hash);
    assert.ok(back, `${hash} should decode`);
    assert.equal(back.start, country.code);
    assert.deepEqual(back.selection, country.choices);
  }
  // A leading # is tolerated.
  const au = byCode('AU');
  assert.deepEqual(decode(data, '#' + encode(data, 'AU', au.choices)).selection, au.choices);
});

// 8. A garbled hash decodes to null rather than throwing.
test('malformed hashes decode to null and never throw', () => {
  const bad = [
    'not-a-real-hash',
    'ZZ-000000000000',            // unknown country code
    '',
    null,
    undefined,
    'AU-0000',                    // wrong length
    'AU-00000000000000',          // wrong length
    'AU-zzzzzzzzzzzzz',           // index out of range
    'AU',
    'AU-',
    '1234',
    {},
    42,
  ];
  for (const h of bad) {
    assert.equal(decode(data, h), null, `${JSON.stringify(h)} should decode to null`);
  }
});

// 9. Timezones resolve.
test('timezones resolve, with an unknown zone falling back', () => {
  assert.equal(countryForTimezone(data, 'Australia/Brisbane'), 'AU');
  assert.equal(countryForTimezone(data, 'Europe/Copenhagen'), 'DK');
  assert.equal(countryForTimezone(data, 'Asia/Tokyo'), 'JP');
  assert.equal(countryForTimezone(data, 'Mars/Olympus_Mons'), data.fallback);
  assert.equal(countryForTimezone(data, null), data.fallback);
  assert.equal(countryForTimezone(data, undefined), data.fallback);

  const tz = detectTimezone();
  assert.ok(tz === null || typeof tz === 'string');
});

// 10. An axis that does not apply is not plotted as zero.
test('an axis that does not apply comes back null, not zero', () => {
  const ae = byCode('AE');
  assert.equal(ae.choices.voting, 'vo_none');
  assert.equal(option('voting', 'vo_none').axis.disproportionality, null);

  const values = axisValues(data, ae.choices);
  assert.equal(values.disproportionality, null);
  assert.notEqual(values.disproportionality, 0);

  // The measured side is null too, with a stated reason.
  assert.equal(ae.indicators.disproportionality.value, null);
  assert.ok(ae.indicators.disproportionality.na_reason);

  // A null axis is skipped in the distance rather than counted as zero. Against
  // the UAE, whose measured disproportionality is also null, changing your
  // voting system cannot move the distance at all. Against New Zealand, which
  // has a measured value, it must.
  const withElections = { ...ae.choices, voting: 'vo_proportional' };
  const before = rank(data, ae.choices);
  const after = rank(data, withElections);
  const aeBefore = before.find((r) => r.code === 'AE').distance;
  const aeAfter = after.find((r) => r.code === 'AE').distance;
  assert.ok(Number.isFinite(aeBefore) && Number.isFinite(aeAfter));
  assert.equal(aeBefore, aeAfter, 'a null-on-both-sides axis must not enter the distance');

  assert.ok(byCode('NZ').indicators.disproportionality.value !== null);
  assert.notEqual(
    before.find((r) => r.code === 'NZ').distance,
    after.find((r) => r.code === 'NZ').distance,
  );
});

// 11. redistribution is summed, not overwritten.
test('redistribution is summed across every contributing domain', () => {
  const au = byCode('AU');
  const values = axisValues(data, au.choices);

  const parts = [
    option('tax', 'tax_anglo').axis.redistribution,       // 0.11
    option('work', 'wo_bargaining').axis.redistribution,  // 0.06
    option('family', 'fa_targeted').axis.redistribution,  // 0.02
  ];
  assert.deepEqual(parts, [0.11, 0.06, 0.02]);

  const expected = parts.reduce((a, b) => a + b, 0);
  assert.ok(Math.abs(values.redistribution - expected) < 1e-9, `got ${values.redistribution}`);
  for (const p of parts) {
    assert.ok(values.redistribution > p, `${values.redistribution} should exceed the single contribution ${p}`);
  }

  // Every other axis is set by its own domain, not accumulated.
  assert.equal(values.tax_take, option('tax', 'tax_anglo').axis.tax_take);
  assert.equal(values.social_housing, option('housing', 'ho_market').axis.social_housing);
});

/* The cascade ------------------------------------------------------------- */

/** Every domain locked except the ones named. */
function lockAllExcept(state, ...open) {
  return data.domains
    .map((d) => d.id)
    .filter((id) => !open.includes(id))
    .reduce((s, id) => setLock(s, id, true), state);
}

const cutOn = (r, domainId) => r.cuts.find((c) => c.domain === domainId) || null;

// 12. The lock is absolute.
test('a locked domain never moves, however large the overspend', () => {
  // Australia buys a universal basic income, which still fits. Then everything
  // is locked but justice, which can give up 0.75 at the very most, and the tax
  // rate is dropped to the bottom of the slider. The overspend is several times
  // anything the cascade can cover, which is the point: the pressure has nowhere
  // to go but the locks.
  const rich = applyChange(data, startingState(data, 'AU'), 'work', 'wo_ubi');
  const start = lockAllExcept(rich.state, 'justice', 'tax');
  const r = setTaxRate(data, start, TAX.MIN);

  assert.ok(r.shortfall > 5, `expected a large shortfall, got ${r.shortfall}`);
  for (const d of data.domains) {
    if (d.id === 'justice' || d.id === 'tax') continue;
    assert.equal(r.state.selection[d.id], start.selection[d.id],
      `${d.id} is locked and must not have moved`);
  }
  assert.equal(r.cuts.filter((c) => c.domain !== 'justice').length, 0);

  // And a locked domain cannot be moved by hand either. A lock that only stops
  // the cascade is a lock the visitor undoes by accident.
  const refused = applyChange(data, start, 'housing', 'ho_singapore');
  assert.equal(refused.ok, false);
  assert.equal(refused.reason, 'locked');
  assert.deepEqual(refused.state.selection, start.selection);
});

// 13. The control does not fight the user.
test('the domain just moved is never cut by its own cascade', () => {
  const start = startingState(data, 'AU');

  // Work to a universal basic income is the single dearest move on the board:
  // 1.8 to 9.0, which is 7.2 of GDP against Australia's 4.8 of headroom. It does
  // not fit, so it pays for itself out of everything else, and work itself must
  // survive its own cascade.
  //
  // This used to fit with room to spare, on 9.1 of headroom, because every
  // country tagged to `tax_anglo` started at that option's hand-set 34 rather
  // than at its own measured take. Australia measures 29.5. The old headroom is
  // why the cascade fired on only 3.7% of moves and the mechanic was invisible.
  const first = applyChange(data, start, 'work', 'wo_ubi');
  assert.equal(first.state.selection.work, 'wo_ubi', 'the moved domain must stick');
  assert.ok(first.cuts.length > 0, 'and something else must have paid for it');
  assert.equal(cutOn(first, 'work'), null, 'the moved domain must not be cut');

  // Now the rate comes down underneath it and the cascade has to find more.
  const r = setTaxRate(data, first.state, 26);
  assert.ok(r.cuts.length > 0, 'the rate cut should have forced a cascade');
  assert.equal(cutOn(r, 'tax'), null, 'the tax slider must not cut itself');

  // And the same the other way round: move work while the money is already tight
  // and work itself is untouched by the cascade it causes.
  const tight = setTaxRate(data, start, 26);
  const moved = applyChange(data, tight.state, 'work', 'wo_ubi');
  assert.equal(moved.state.selection.work, 'wo_ubi', 'the moved domain must stick');
  assert.equal(cutOn(moved, 'work'), null, 'the moved domain must not be cut');
  assert.ok(moved.cuts.length > 0, 'something else should have paid for it');
});

// 14. Same in, same out.
test('the cascade is deterministic', () => {
  const start = startingState(data, 'SE');
  const tight = setTaxRate(data, start, 33).state;

  const once = applyChange(data, tight, 'retirement', 're_generous');
  const twice = applyChange(data, tight, 'retirement', 're_generous');
  assert.deepEqual(once, twice);
  assert.ok(once.cuts.length > 0, 'a test of determinism needs something to have happened');

  // Not just twice in a row from one object: rebuilding the state from scratch
  // has to land in the same place too, or the result depends on the history and
  // not on the position.
  const rebuilt = applyChange(data, setTaxRate(data, startingState(data, 'SE'), 33).state,
    'retirement', 're_generous');
  assert.deepEqual(rebuilt.state.selection, once.state.selection);
  assert.deepEqual(rebuilt.cuts, once.cuts);
});

// 15. The big programmes pay the most.
test('the cut is allocated in proportion to what each domain spends', () => {
  // Australia taxed down to 26 has a little over a point of headroom. Retirement
  // is then on 5.0 and justice on 0.9, everything else is locked, and moving
  // healthcare to a national service costs 2.0, so the cascade has to find the
  // difference. Proportional targets put nearly all of it on retirement, and its
  // first step down covers the lot.
  //
  // This used to run at the very bottom of the slider and lean on the floor
  // holding capacity at what Australia already spends. The floor is now a fixed
  // top-up measured at the starting country's own rate rather than a running
  // max, precisely so that the bottom half of the slider is not inert, so there
  // is no longer a rate at which headroom is conveniently exactly zero.
  const broke = setTaxRate(data, startingState(data, 'AU'), 26);
  assert.ok(broke.budgets.financial.left > 0 && broke.budgets.financial.left < 2,
    'a small known headroom, so the move below has to be part paid for');
  assert.deepEqual(broke.cuts, [], 'and nothing cut on the way there');
  const start = lockAllExcept(broke.state, 'retirement', 'justice', 'healthcare');
  const r = applyChange(data, start, 'healthcare', 'hc_public');

  const big = cutOn(r, 'retirement');
  const small = cutOn(r, 'justice');
  assert.ok(big, 'the bigger spender should have been cut');
  assert.equal(small, null, 'the smaller spender should not have been touched at all');
  assert.ok(big.saved >= (small ? small.saved : 0),
    'the bigger spender must give up at least as much as the smaller one');
  assert.equal(r.ok, true);

  // The step is down its own ladder, one rung, and the rung below is the next
  // strictly cheaper option rather than the next one in the file.
  const rungs = ladder(data, 'retirement');
  const from = rungs.findIndex((o) => o.id === big.from);
  const to = rungs.findIndex((o) => o.id === big.to);
  assert.ok(to < from, 'a cut must move down the ladder');
  assert.equal(big.steps, 1);
});

// 16. The tax slider buys something, and less of it the higher it goes.
test('raising the rate raises capacity, and buys less at the top than the bottom', () => {
  const au = startingState(data, 'AU');
  const at = (rate) => capacityOf(data, { ...au, taxRate: rate });

  // Above the floor, capacity is strictly increasing in the rate.
  for (let r = 30; r < TAX.MAX; r += 1) {
    assert.ok(at(r + 1).capacity > at(r).capacity,
      `capacity must rise from ${r} to ${r + 1}`);
  }

  // The marginal point is worth less the higher you are. Measured on what is
  // raised rather than on capacity, because below a country's own spending the
  // floor is what binds and the rate moves nothing.
  const low = at(21).raised - at(20).raised;
  const high = at(51).raised - at(50).raised;
  assert.equal(one(low), 1.0, 'below the kink a point of tax is a point of revenue');
  assert.ok(high < low, `the marginal point at 50 (${one(high)}) must buy less than at 20 (${one(low)})`);
  assert.equal(one(high), 0.6);

  // And it buys real policy, not just a bigger number. From Australia's own rate
  // to the top of the slider funds the dearest option in several domains at once.
  const rich = setTaxRate(data, au, TAX.MAX).state;
  const headroom = capacityOf(data, rich).capacity - spendOf(data, rich.selection);
  assert.ok(headroom > 20, `expected the top of the slider to fund real change, got ${one(headroom)}`);
});

// 17. The UAE runs on something that is not tax.
test('the UAE capacity comes from non-tax revenue and is not attributed to tax', () => {
  const ae = startingState(data, 'AE');
  const b = budgets(data, ae);

  assert.equal(b.financial.taxRate, 16.0, 'the headline tax take, not the revenue');
  assert.equal(b.financial.realisedTax, 16.0, 'below the kink, so it realises in full');
  assert.equal(b.financial.nonTaxRevenue, 11.8, 'hydrocarbon and investment income');
  assert.equal(one(b.financial.realisedTax + b.financial.nonTaxRevenue), 27.8,
    'IMF general government revenue, UAE 2024');

  // The tax side of the page must agree with the tax side of the budget. If the
  // 11.8 were still being carried as tax, the axis and the rate would disagree
  // by exactly that, which is the fault this split fixed.
  assert.equal(option('tax', 'tax_minimal').rate, 16.0);
  assert.equal(option('tax', 'tax_minimal').axis.tax_take, 16.0);
  assert.equal(axisValues(data, ae.selection).tax_take, 16.0);

  // FORTY-ONE OF THE FORTY-FIVE CARRY NOTHING, so the field is not a fudge
  // factor. The four that carry it are the four Gulf monarchies, and each is
  // general government total revenue less the 16.0 the country starts on, on
  // one indicator and one year. Saudi Arabia, Qatar and Kuwait were 0.0 until
  // 31/08/2026 because the figure had not been sourced; it has been now, and
  // this asserts that the exception list has not grown past those four.
  const gulf = new Set(['AE', 'SA', 'QA', 'KW']);
  const others = MATCHABLE.filter((c) => !gulf.has(c.code));
  assert.deepEqual([...new Set(others.map((c) => c.nonTaxRevenue))], [0]);
  assert.deepEqual(
    MATCHABLE.filter((c) => c.nonTaxRevenue).map((c) => [c.code, c.nonTaxRevenue]),
    [['AE', 11.8], ['SA', 11.1], ['QA', 10.7], ['KW', 58.2]],
  );

  // THE OIL SURVIVES A CHANGE OF TAX POLICY, which is the whole point of moving
  // it off the tax option. A visitor who taxes the UAE like Denmark keeps it.
  const nordic = setTaxRate(data, ae, 46).state;
  const after = budgets(data, nordic);
  assert.equal(after.financial.nonTaxRevenue, 11.8);

  // The top-up is a CONSTANT, measured once at the UAE's own rate, so it is
  // still here at 46 and capacity is revenue plus it. Written as a running
  // max(raised, inherited) instead, the whole bottom of the slider did nothing,
  // because inherited spend sat above realised revenue the entire way down.
  assert.equal(one(after.financial.topUp), one(b.financial.topUp));
  assert.equal(one(after.financial.capacity),
    one(realisedRevenue(46) + 11.8 + after.financial.topUp));
  assert.ok(after.financial.capacity > b.financial.capacity + 20,
    'taxing a petrostate properly should be transformative, not marginal');

  // And the slider now cuts both ways: taxing the UAE at the floor of the range
  // takes real money off it, where the old running max swallowed the whole move.
  const stripped = budgets(data, setTaxRate(data, ae, TAX.MIN).state);
  assert.ok(stripped.financial.capacity < b.financial.capacity - 3,
    'cutting tax must reduce what you have to spend');
});

// 18. It says so rather than spinning.
test('a cascade that cannot cover the overspend reports it', () => {
  // Israel has 3.3 of headroom and a universal basic income costs 7.6 more than
  // what it runs now. Justice is the only thing left unlocked to pay for it and
  // it is worth 0.75 all the way down, so the cascade runs out.
  const start = lockAllExcept(startingState(data, 'IL'), 'justice', 'work');
  const r = applyChange(data, start, 'work', 'wo_ubi');

  assert.equal(r.ok, false);
  assert.equal(r.reason, 'shortfall');
  assert.ok(r.shortfall > 0, 'the shortfall must be reported as a number');
  assert.ok(r.budgets.financial.over, 'and the budget must still read as over');

  // The state it hands back is the one it reached, cuts and all, rather than a
  // refusal: the visitor is over budget and can see by how much, and what the
  // attempt already cost them.
  assert.equal(r.state.selection.justice, ladder(data, 'justice')[0].id,
    'the one unlocked domain should have been taken all the way down');
  assert.equal(one(r.budgets.financial.exact.left), -r.shortfall);
});

// 19. Cuts are reforms too, except when they are reversals.
test('cascaded cuts are charged, and a cut back to the starting option is free', () => {
  const au = startingState(data, 'AU');
  assert.equal(au.selection.housing, 'ho_market');

  // Put Australia on the Singapore housing model first, then lock everything but
  // housing and retirement so the cascade has exactly one place to look.
  const withFlats = applyChange(data, au, 'housing', 'ho_singapore');
  assert.equal(withFlats.state.selection.housing, 'ho_singapore');
  assert.equal(withFlats.budgets.political.used,
    Math.round(reformCost(option('housing', 'ho_singapore').political)));

  // A small squeeze: the rate comes down to 26 with housing the only thing that
  // can move, which is 0.8 to find. Housing steps part way down and stops on an
  // option that is not Australia's own, so it is a reform and it is charged. The
  // tax stop the slider landed on is charged too, and both are named here rather
  // than netted off, because the sum is the thing being tested.
  const squeeze = setTaxRate(data, lockAllExcept(withFlats.state, 'housing', 'tax'), 26);
  const partial = cutOn(squeeze, 'housing');
  assert.ok(partial, 'housing should have paid for the tax cut');
  assert.notEqual(partial.to, 'ho_market', 'this case is the part-way cut');
  assert.ok(partial.steps > 1, 'and it took more than one rung');
  // Both sides on the POOL's scale. The meter is scaled through reformCost and
  // the raw option numbers are not, so summing raw ones and comparing was
  // comparing two units once the pool became 100.
  assert.equal(
    squeeze.budgets.political.used,
    Math.round(reformCost(option('tax', squeeze.state.selection.tax).political)
      + reformCost(option('housing', partial.to).political)),
    'a cut that lands somewhere new is a reform and someone has to pass it',
  );

  // A big squeeze: housing is pushed all the way back to what Australia already
  // does, and that is a reversal rather than a reform, so it costs nothing.
  const pinned = lockAllExcept(withFlats.state, 'housing', 'retirement');
  const shove = applyChange(data, pinned, 'retirement', 're_generous');
  const full = cutOn(shove, 'housing');
  assert.ok(full, 'housing should have been cut');
  assert.equal(full.to, 'ho_market', 'and cut all the way back to the starting option');
  assert.equal(full.from, 'ho_singapore');
  assert.equal(full.steps, 4);
  assert.equal(
    shove.budgets.political.used,
    Math.round(reformCost(option('retirement', 're_generous').political)),
    "a cut back to the country's own option must be charged nothing",
  );
  assert.equal(shove.budgets.changedCount, 1);
});

/* Continuous slider positions ----------------------------------------------
 *
 * Added 01/09/2026 with the change that made the twelve categorical sliders
 * continuous. The complaint was precise: with healthcare the slider is gradual
 * but the budget and the radar jump dramatically at certain thresholds. Test 22
 * below is the one that says whether that is fixed, and it is written as a
 * number rather than as an impression.
 */

const LADDERED = data.domains.filter((d) => ladder(data, d.id).length);

// 18. THE OLD ANSWERS DID NOT MOVE. Every option, in every domain, priced at
// its own integer position, must come back at exactly its own cost. This is the
// check that the interpolation is a new path through the same numbers and not a
// new set of numbers.
test('at an integer position every cost is exactly that option cost', () => {
  let checked = 0;
  for (const d of LADDERED) {
    const rungs = ladder(data, d.id);
    rungs.forEach((option, i) => {
      const v = valuesAt(data, d.id, i);
      assert.equal(v.optionId, option.id, `${d.id} position ${i} should be ${option.id}`);
      assert.equal(v.financial, option.financial || 0, `${d.id} ${option.id} financial`);
      assert.equal(v.political, option.political || 0, `${d.id} ${option.id} political`);
      assert.equal(v.social, option.social || 0, `${d.id} ${option.id} social`);
      for (const [axisId, value] of Object.entries(option.axis || {})) {
        if (value === null) {
          assert.equal(v.axis[axisId], undefined, `${d.id} ${option.id} ${axisId} must stay absent`);
        } else {
          assert.equal(v.axis[axisId], value, `${d.id} ${option.id} ${axisId}`);
        }
      }
      checked += 1;
    });
  }
  const taxOptions = data.domains.find((d) => d.id === 'tax').options.length;
  assert.equal(checked, 69 - taxOptions, 'every option on a ladder was priced');

  // And the same thing one level up: a whole design priced at its positions is
  // the same number as the same design priced at its options.
  for (const country of MATCHABLE) {
    const start = startingState(data, country.code);
    assert.equal(
      spendOf(data, start.selection, start.pos),
      spendOf(data, start.selection),
      `${country.code} costs the same either way`,
    );
  }
});

// 19. Halfway is halfway, in all three currencies.
test('halfway between two options costs the mean of the two', () => {
  for (const d of LADDERED) {
    const rungs = ladder(data, d.id);
    for (let i = 0; i + 1 < rungs.length; i += 1) {
      const lo = rungs[i];
      const hi = rungs[i + 1];
      const mid = valuesAt(data, d.id, i + 0.5);
      const near = (a, b, what) => assert.ok(
        Math.abs(a - b) < 1e-9,
        `${d.id} ${lo.id} to ${hi.id} ${what}: got ${a}, expected ${b}`,
      );
      near(mid.financial, ((lo.financial || 0) + (hi.financial || 0)) / 2, 'financial');
      near(mid.political, ((lo.political || 0) + (hi.political || 0)) / 2, 'political');
      near(mid.social, ((lo.social || 0) + (hi.social || 0)) / 2, 'social');

      // And every axis both sides carry a number for.
      for (const axisId of Object.keys(lo.axis || {})) {
        const a = lo.axis[axisId];
        const b = (hi.axis || {})[axisId];
        if (typeof a !== 'number' || typeof b !== 'number') continue;
        near(mid.axis[axisId], (a + b) / 2, axisId);
      }
    }
  }

  // The worked example from the brief: part way from compulsory medical savings
  // towards mandatory insurance costs part way between the two, and is neither.
  const savings = option('healthcare', 'hc_savings');
  const insurance = option('healthcare', 'hc_insurance');
  const from = posOfOption(data, 'healthcare', 'hc_savings');
  const to = posOfOption(data, 'healthcare', 'hc_insurance');
  assert.equal(to - from, 2, 'this example runs across two rungs');
  const sixty = valuesAt(data, 'healthcare', from + 0.6 * (to - from));
  assert.ok(sixty.financial > savings.financial && sixty.financial < insurance.financial,
    `${sixty.financial} should sit between ${savings.financial} and ${insurance.financial}`);
});

// 20. The identity snaps, and everything that names a policy agrees on which.
test('the option is the nearer one either side of a midpoint, and the label agrees', () => {
  const au = startingState(data, 'AU');

  for (const d of LADDERED) {
    const rungs = ladder(data, d.id);
    for (let i = 0; i + 1 < rungs.length; i += 1) {
      const below = valuesAt(data, d.id, i + 0.49);
      const above = valuesAt(data, d.id, i + 0.51);
      assert.equal(below.optionId, rungs[i].id, `${d.id} ${i + 0.49} should still be ${rungs[i].id}`);
      assert.equal(above.optionId, rungs[i + 1].id, `${d.id} ${i + 0.51} should be ${rungs[i + 1].id}`);
      assert.equal(below.option.label, rungs[i].label);
      assert.equal(above.option.label, rungs[i + 1].label);

      // What applyChange records, which is what the page shows and the URL
      // carries, is the same option.
      const moved = applyChange(data, au, d.id, i + 0.51);
      assert.equal(moved.moved.to, rungs[i + 1].id, `${d.id} moved.to`);
      assert.equal(moved.state.selection[d.id], rungs[i + 1].id, `${d.id} selection`);
    }
  }

  // And rank() matches on it. A design sitting just past the midpoint agrees
  // with the countries that run the DEARER option, not the cheaper one.
  const rungs = ladder(data, 'healthcare');
  const i = rungs.findIndex((o) => o.id === 'hc_insurance');
  const justBelow = applyChange(data, au, 'healthcare', i + 0.49).state;
  const justAbove = applyChange(data, au, 'healthcare', i + 0.51).state;
  assert.equal(justBelow.selection.healthcare, 'hc_insurance');
  assert.equal(justAbove.selection.healthcare, rungs[i + 1].id);
  const agreesOn = (state, code) => rank(data, state.selection)
    .find((r) => r.code === code).agreements.some((a) => a.domain === 'healthcare');
  const dearerCountry = (rungs[i + 1].countries || [])[0];
  assert.ok(dearerCountry, 'the dearer option is somewhere');
  assert.equal(agreesOn(justAbove, dearerCountry), true,
    'past the midpoint you are matched on the dearer option');
  assert.equal(agreesOn(justBelow, dearerCountry), false,
    'and before it you are not');
});

// 21. Nothing about positions may stop a country being itself. The
// forty-five-country check again, run through the position path this time,
// since startingState now carries positions and budgets() prices them.
test('every country can still afford to be itself at its own positions', () => {
  for (const country of MATCHABLE) {
    const start = startingState(data, country.code);
    const b = budgets(data, start);
    assert.equal(b.political.used, 0, `${country.code} political`);
    assert.equal(b.social.used, 0, `${country.code} social`);
    assert.equal(b.financial.over, false, `${country.code} financial`);

    // Every position is exactly an integer, so a country sits ON its options.
    for (const d of LADDERED) {
      const p = start.pos[d.id];
      assert.equal(p, Math.round(p), `${country.code} ${d.id} should be on a rung, got ${p}`);
      assert.equal(ladder(data, d.id)[p].id, country.choices[d.id], `${country.code} ${d.id}`);
    }
    assert.deepEqual(positionsOf(data, start), posFromSelection(data, country.choices));
  }
  assert.equal(MATCHABLE.length, 45);
});

// 22. THE COMPLAINT, AS A NUMBER.
//
// Dragging one slider from one end to the other, in the hundredths the thumb
// actually steps in, the budget must move in one direction only and no single
// step may exceed STEP_THRESHOLD points of GDP.
//
// The measurement is taken with no cascade, which is not a simplification: mid
// drag the page holds the position as a preview and cuts nothing until the
// visitor lets go, so this IS what the meter does under a finger.
//
// WHAT THE NUMBERS WERE. Before this change the same drag moved in whole
// options, so the largest step was the largest gap between two adjacent rungs:
//
//     healthcare        4.5 points, from hc_savings to hc_mixed
//     work              6.8 points, the worst of the twelve
//
// After it the largest step is a hundredth of that gap, because the thumb steps
// in hundredths of a rung:
//
//     healthcare        0.045
//     work              0.068
//
// The threshold is 0.07, which is the worst domain figure with a little air. It
// is deliberately tight enough that reverting any part of the interpolation
// fails this test rather than merely looking worse.
const STEP_THRESHOLD = 0.07;

test('the budget moves monotonically and in small steps across a whole slider', () => {
  const start = startingState(data, 'AU');
  let worst = { domain: null, step: 0 };
  const byDomain = new Map();

  for (const d of LADDERED) {
    const rungs = ladder(data, d.id);
    let previous = null;
    let direction = 0;
    let largest = 0;

    for (let n = 0; n <= (rungs.length - 1) * 100; n += 1) {
      const p = n / 100;
      const at = {
        ...start,
        selection: { ...start.selection, [d.id]: valuesAt(data, d.id, p).optionId },
        pos: { ...start.pos, [d.id]: p },
      };
      const used = budgets(data, at).financial.exact.used;
      if (previous !== null) {
        const step = used - previous;
        if (Math.abs(step) > 1e-12) {
          const sign = step > 0 ? 1 : -1;
          if (direction === 0) direction = sign;
          assert.equal(sign, direction,
            `${d.id} turned round at position ${p}: the budget must not fall while the slider rises`);
        }
        largest = Math.max(largest, Math.abs(step));
      }
      previous = used;
    }

    byDomain.set(d.id, largest);
    if (largest > worst.step) worst = { domain: d.id, step: largest };
    assert.ok(largest <= STEP_THRESHOLD + 1e-9,
      `${d.id} jumps ${largest.toFixed(3)} points in one step of the thumb, over the ${STEP_THRESHOLD} allowed`);
  }

  // The two figures the complaint is judged on, asserted so they cannot drift
  // back up quietly.
  assert.ok(Math.abs(byDomain.get('healthcare') - 0.045) < 1e-6,
    `healthcare largest step ${byDomain.get('healthcare')}`);
  assert.equal(worst.domain, 'work');
  assert.ok(Math.abs(worst.step - 0.068) < 1e-6, `work largest step ${worst.step}`);

  // And the size of the jump that was there before: the largest gap between two
  // adjacent rungs, which is what a snapped slider moved by.
  const gapOf = (id) => {
    const rungs = ladder(data, id);
    let gap = 0;
    for (let i = 1; i < rungs.length; i += 1) {
      gap = Math.max(gap, Math.abs((rungs[i].financial || 0) - (rungs[i - 1].financial || 0)));
    }
    return gap;
  };
  assert.ok(Math.abs(gapOf('healthcare') - 4.5) < 1e-9);
  assert.ok(Math.abs(gapOf('work') - 6.8) < 1e-9);
  // A hundred to one, which is the whole change stated in one line.
  assert.ok(Math.abs(gapOf('work') / 100 - worst.step) < 1e-9);
});

// 23. A CUT IS A DECISION, NOT A DRIFT. The visitor thumb is continuous and the
// cascade is not: it steps whole rungs and it lands on whole rungs.
test('a cut from the cascade lands on an integer position', () => {
  const au = startingState(data, 'AU');
  const start = applyChange(data, au, 'housing', 'ho_singapore').state;

  // Housing is put part way up its own ladder, so the cut starts from a
  // fractional position, and retirement is then shoved to its dearest option to
  // force one.
  const rungs = ladder(data, 'housing');
  const top = rungs.length - 1;
  const drifted = applyChange(data, lockAllExcept(start, 'housing', 'retirement'), 'housing', top - 0.4);
  assert.ok(Math.abs(drifted.state.pos.housing - (top - 0.4)) < 1e-9, 'the thumb stayed where it was put');

  const shove = applyChange(data, drifted.state, 'retirement', 're_generous');
  const cut = cutOn(shove, 'housing');
  assert.ok(cut, 'housing should have paid for it');
  const landed = shove.state.pos.housing;
  assert.equal(landed, Math.round(landed), `a cut landed on ${landed}, which is not a rung`);
  assert.equal(ladder(data, 'housing')[landed].id, shove.state.selection.housing);
  assert.ok(landed < top - 0.4, 'and it landed below where it started');

  // What the cut reports it saved is measured from where the domain stood, not
  // from the rung above it.
  const expected = financialAt(data, 'housing', top - 0.4) - financialAt(data, 'housing', landed);
  assert.ok(Math.abs(cut.saved - Math.round(expected * 10) / 10) < 1e-9,
    `saved ${cut.saved}, expected ${expected}`);
});

// 24. The URL carries the position, and an old link still means what it meant.
test('the URL round-trips a fractional position and old hashes still decode', () => {
  const au = byCode('AU');
  const start = startingState(data, 'AU');

  // A fractional position on two domains at once, and a rate.
  const pos = { ...start.pos, healthcare: start.pos.healthcare + 0.37, defence: 0.5 };
  const selection = {
    ...start.selection,
    healthcare: ladder(data, 'healthcare')[Math.round(pos.healthcare)].id,
    defence: ladder(data, 'defence')[Math.round(0.5)].id,
  };
  const hash = encode(data, 'AU', selection, 31.5, pos);
  assert.match(hash, /^AU-[0-9a-z]{13}-p[0-9a-z]{6}-[0-9a-z]{2}$/, hash);

  const back = decode(data, hash);
  assert.ok(back, `${hash} should decode`);
  assert.equal(back.start, 'AU');
  assert.deepEqual(back.selection, selection);
  assert.equal(back.taxRate, 31.5);
  for (const d of LADDERED) {
    assert.ok(Math.abs(back.pos[d.id] - pos[d.id]) < 1e-9,
      `${d.id}: ${back.pos[d.id]} should be ${pos[d.id]}`);
  }

  // A design whose thumbs are all on their rungs writes exactly the hash it
  // wrote before positions existed. Nothing anybody has already shared has
  // changed shape.
  assert.equal(encode(data, 'AU', au.choices, undefined, start.pos), encode(data, 'AU', au.choices));

  // AN OLD HASH, with no position field at all, restores EXACT positions. That
  // is what its author meant: before this change there was nowhere between two
  // options to be.
  for (const country of MATCHABLE) {
    const old = encode(data, country.code, country.choices);
    assert.match(old, /^[A-Z]{2}-[0-9a-z]{13}$/, old);
    const restored = decode(data, old);
    assert.ok(restored, `${old} should decode`);
    assert.deepEqual(restored.selection, country.choices);
    assert.deepEqual(restored.pos, posFromSelection(data, country.choices),
      `${country.code} should restore on its own rungs`);
    for (const d of LADDERED) {
      assert.equal(restored.pos[d.id], Math.round(restored.pos[d.id]));
    }
  }
  // Including the older form with a rate on the end and no positions.
  const withRate = decode(data, `${encode(data, 'AU', au.choices)}-1w`);
  assert.ok(withRate);
  assert.deepEqual(withRate.pos, posFromSelection(data, au.choices));
  assert.equal(withRate.taxRate, parseInt('1w', 36) / 2);

  // Malformed position fields decode to null rather than throwing, same as
  // everything else in the hash.
  const stem = encode(data, 'AU', au.choices);
  for (const bad of [
    `${stem}-p`,          // empty field
    `${stem}-p12`,        // not a whole triplet
    `${stem}-p1234`,      // nor is this
    `${stem}-pz50`,       // no such domain
    `${stem}-p02z`,       // offset out of range
    `${stem}-p150p150`,   // the same domain twice
    `${stem}-p150-p150`,  // two position fields
  ]) {
    assert.equal(decode(data, bad), null, `${bad} should decode to null`);
  }
});

// 25. THE NULL AXIS DOES NOT INTERPOLATE, and vo_none is the only option in the
// file that has one.
test('a null axis is taken from the nearer option and never averaged', () => {
  const rungs = ladder(data, 'voting');
  assert.equal(rungs[0].id, 'vo_none', 'vo_none is the bottom rung');
  assert.equal(rungs[0].axis.disproportionality, null);
  const neighbour = rungs[1];
  assert.equal(typeof neighbour.axis.disproportionality, 'number');

  // Below the midpoint the nearest option is the null one, so there is no
  // reading. A state with no elections does not have a small disproportionality,
  // it does not have one at all.
  const low = valuesAt(data, 'voting', 0.4);
  assert.equal(low.optionId, 'vo_none');
  assert.equal(low.axis.disproportionality, undefined, 'must not be a number');

  // Above it the nearest option has a reading, and it is that option OWN value
  // rather than a fraction of it. Six tenths of the way up must not read as six
  // tenths of the neighbour number: that would be an interpolation from a null,
  // which is a measurement nobody made.
  const high = valuesAt(data, 'voting', 0.6);
  assert.equal(high.optionId, neighbour.id);
  assert.equal(high.axis.disproportionality, neighbour.axis.disproportionality);
  assert.notEqual(high.axis.disproportionality, 0.6 * neighbour.axis.disproportionality);

  // And it reaches the axis values the chart and the reveal are drawn from,
  // where an absent key and a null both mean the same thing: does not apply.
  const ae = byCode('AE');
  assert.equal(ae.choices.voting, 'vo_none');
  const pos = posFromSelection(data, ae.choices);
  assert.equal(axisValues(data, ae.choices, { ...pos, voting: 0.4 }).disproportionality, null);
  assert.equal(
    axisValues(data, { ...ae.choices, voting: neighbour.id }, { ...pos, voting: 0.6 }).disproportionality,
    neighbour.axis.disproportionality,
  );

  // Every other axis in the file has a number on both sides of every boundary,
  // so this rule fires in exactly one place and the test knows where.
  const nulls = [];
  for (const d of data.domains) {
    for (const o of d.options || []) {
      for (const [axisId, value] of Object.entries(o.axis || {})) {
        if (value === null) nulls.push(`${d.id}.${o.id}.${axisId}`);
      }
    }
  }
  assert.deepEqual(nulls, ['voting.vo_none.disproportionality']);
});
