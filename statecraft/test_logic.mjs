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
test('every country can afford to be itself, with the UAE the one financial exception', () => {
  const financiallyOver = [];

  for (const country of data.countries) {
    const b = budgets(data, country.choices, country.choices);
    assert.equal(b.political.used, 0, `${country.code} should spend no political capital on its own status quo`);
    assert.equal(b.social.used, 0, `${country.code} should spend no social capital on its own status quo`);
    assert.equal(b.changedCount, 0, `${country.code} has changed nothing`);
    if (b.financial.over) financiallyOver.push(country.code);
  }

  // THIS ASSERTION WAS MEANT TO FLIP TO TWENTY OF TWENTY ON 2026-08-30 AND IT
  // DOES NOT, so it still reads nineteen and the reason is recorded here rather
  // than smoothed over by relaxing the check.
  //
  // The revenue half of the fault is fixed. tax_minimal raised 16.0% of GDP,
  // which was a TAX TAKE standing in for general government REVENUE, and for a
  // petrostate those are different things. It now raises 27.8%, the IMF's
  // general government revenue figure for the UAE in 2024. That moved the UAE
  // from 16.0 minus 32.0 = -16.0 to 27.8 minus 32.0 = -4.2, so roughly
  // three-quarters of the shortfall was the wrong-basis revenue number.
  //
  // The residual -4.2 is the SAME CLASS OF FAULT on the spending side, and it is
  // left alone because fixing it belongs to the retirement domain and would move
  // France too. The UAE's modelled spend is 32.0% of GDP against an IMF general
  // government expenditure figure of 21.4% for 2024. The single biggest cause is
  // re_generous at 14.0% of GDP, which is France's pension outlay: policies.py's
  // own comment beside the AE tag already records that GPSSA covers Emirati and
  // GCC nationals only, roughly an eighth of residents, so the UAE cannot be
  // spending anything like 14% of GDP on it. Put the retirement cell on a
  // coverage-weighted basis and the UAE clears comfortably.
  //
  // Asserted explicitly, as before, so the exception cannot silently spread to a
  // twenty-first country or to a second one of the twenty.
  assert.deepEqual(financiallyOver, ['AE']);
  assert.equal(data.countries.length - financiallyOver.length, 19);

  const ae = budgets(data, byCode('AE').choices, byCode('AE').choices);
  assert.equal(ae.financial.capacity, 27.8, 'IMF general government revenue, UAE 2024');
  assert.ok(ae.financial.left < 0);
  assert.deepEqual(blockers(ae), ['financial']);

  // The gap must not widen back out. This is the number to watch: if the
  // retirement cell is ever put on the right basis, this goes positive and the
  // assertions above become the twenty-of-twenty they were always meant to be.
  assert.equal(ae.financial.left, -4.2);
  assert.ok(ae.financial.left > -16.0, 'the revenue fix must not regress');
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
