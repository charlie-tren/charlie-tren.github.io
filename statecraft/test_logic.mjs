// node --test test_logic.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { budgets, blockers, REFORM_POOL } from './budget.js';
import { axisValues, rank } from './match.js';
import { encode, decode, countryForTimezone, detectTimezone } from './state.js';

const here = dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(readFileSync(join(here, 'data.json'), 'utf8'));

const byCode = (code) => data.countries.find((c) => c.code === code);
const domain = (id) => data.domains.find((d) => d.id === id);
const option = (domainId, optionId) => domain(domainId).options.find((o) => o.id === optionId);

test('data.json has the shape the modules assume', () => {
  assert.equal(data.domains.length, 13);
  assert.equal(data.countries.length, 20);
  assert.equal(data.axes.length, 14);
  assert.equal(data.fallback, 'AU');
});

// 1. Every country can afford to be itself.
test('all twenty countries can afford to be themselves', () => {
  const financiallyOver = [];

  for (const country of data.countries) {
    const b = budgets(data, country.choices, country.choices);
    assert.equal(b.political.used, 0, `${country.code} should spend no political capital on its own status quo`);
    assert.equal(b.social.used, 0, `${country.code} should spend no social capital on its own status quo`);
    assert.equal(b.changedCount, 0, `${country.code} has changed nothing`);
    if (b.financial.over) financiallyOver.push(country.code);
  }

  // TWENTY OF TWENTY, and the UAE was the one that used to fail. Two changes got
  // it here and the order matters, because only the first was a data fix.
  //
  // First, tax_minimal raised 16.0% of GDP, which was a TAX TAKE standing in for
  // general government REVENUE. For a petrostate those are different things. It
  // now raises 27.8%, the IMF figure for 2024, cross-checked against the Article
  // IV surplus. That closed three-quarters of the gap, from -16.0 to -4.2.
  //
  // The residual -4.2 was NOT a revenue problem and must not be fixed by
  // reaching for a bigger revenue number: 2022 reads 32.55% and would have made
  // this test pass on its own, which is exactly the wrong reason to pick a year.
  // It was the same wrong-basis fault on the SPENDING side. The UAE's modelled
  // spend is 32.0% of GDP against IMF general government expenditure of 21.4%,
  // mostly because re_generous carries France's 14.0% pension outlay while
  // GPSSA covers Emirati and GCC nationals only, roughly an eighth of residents.
  //
  // So the second change is in budget.js, not in the data: financial capacity is
  // the tax revenue OR what the starting country already spends, whichever is
  // larger. A country manifestly manages to run its own settings, so those are
  // affordable by definition and only ADDITIONAL spending needs funding. That
  // also makes all three budgets say one thing: you inherit a country and you
  // pay for what you change.
  assert.deepEqual(financiallyOver, []);
  assert.equal(data.countries.length, 20);

  // The floor only ever binds for the UAE. Nineteen countries raise more in tax
  // than they spend, so their capacity is untouched by it, and this asserts that
  // rather than assuming it: if the floor ever starts propping up a second
  // country, something has gone wrong in the cost model and should be looked at.
  const propped = data.countries.filter((c) => {
    const b = budgets(data, c.choices, c.choices);
    return b.financial.inherited > b.financial.taxRevenue;
  }).map((c) => c.code);
  assert.deepEqual(propped, ['AE']);

  const ae = budgets(data, byCode('AE').choices, byCode('AE').choices);
  assert.equal(ae.financial.taxRevenue, 27.8, 'IMF general government revenue, UAE 2024');
  assert.equal(ae.financial.capacity, 32.0, 'floored at what the UAE already spends');
  assert.equal(ae.financial.left, 0);
  assert.deepEqual(blockers(ae), []);

  // And the floor must not become a way to spend freely: one dearer choice on
  // top of the UAE's own settings still goes over.
  const greedy = { ...byCode('AE').choices, healthcare: 'hc_public' };
  assert.ok(budgets(data, greedy, byCode('AE').choices).financial.over,
    'the floor must not stop the financial budget binding');
});

// 2. Changing one domain charges exactly that option's cost, and changing back charges nothing.
test('changing one domain charges exactly that option, and changing back charges nothing', () => {
  const au = byCode('AU');
  assert.equal(au.choices.housing, 'ho_market');

  const reformed = { ...au.choices, housing: 'ho_singapore' };
  const b = budgets(data, reformed, au.choices);
  const ho = option('housing', 'ho_singapore');

  assert.equal(ho.political, 70);
  assert.equal(ho.social, 10);
  assert.equal(b.political.used, ho.political);
  assert.equal(b.social.used, ho.social);
  assert.equal(b.political.left, REFORM_POOL - 70);
  assert.equal(b.changedCount, 1);
  assert.equal(b.changed[0].domain, 'housing');

  // Financial moves by the difference in cost, not by the full new cost.
  const baseB = budgets(data, au.choices, au.choices);
  assert.equal(
    b.financial.used,
    Math.round((baseB.financial.used - option('housing', 'ho_market').financial + ho.financial) * 10) / 10,
  );

  const back = budgets(data, { ...reformed, housing: 'ho_market' }, au.choices);
  assert.equal(back.political.used, 0);
  assert.equal(back.social.used, 0);
  assert.equal(back.changedCount, 0);
});

// 3. The pool binds.
test('the political pool binds when every domain is changed to its dearest option', () => {
  const dk = byCode('DK');
  const dearest = {};
  for (const d of data.domains) {
    dearest[d.id] = d.options.reduce((a, b) => (b.political > a.political ? b : a)).id;
  }
  const b = budgets(data, dearest, dk.choices);
  assert.ok(b.political.used > REFORM_POOL, `expected over ${REFORM_POOL}, got ${b.political.used}`);
  assert.ok(b.political.over);
  assert.ok(blockers(b).includes('political'));

  // And the pool is not so tight that a couple of reforms already blow it.
  const twoReforms = { ...dk.choices, housing: 'ho_singapore', energy: 'en_car_free' };
  assert.equal(budgets(data, twoReforms, dk.choices).political.over, false);
});

// 4. A country matches itself on all thirteen domains and tops its own ranking.
test('every country matches itself on all thirteen domains and ranks itself first', () => {
  for (const country of data.countries) {
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
  for (const country of data.countries) {
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
