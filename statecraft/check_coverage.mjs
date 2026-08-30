// Does the reveal actually discriminate?
//
// The whole page rests on the nearest neighbour being interesting. If almost
// every design lands on one country, or if some countries can never be the
// answer at all, the reveal is decoration. A spread check on the matrix cannot
// see this, because it is a property of the option costs and the match together.
//
// ONLY MATCHABLE COUNTRIES ARE IN SCOPE. The twenty-five measured-only rows
// added 30/08/2026 have no `choices`, so they can neither be drawn as a starting
// design nor be named as an answer. Counting them would report twenty-five
// countries as "never the answer" as though that were a fault in the match.
//
// Run: node check_coverage.mjs

import { readFileSync } from 'node:fs';
import { rank, matchable } from './match.js';
import { budgets, blockers, rateForOption } from './budget.js';

const data = JSON.parse(readFileSync(new URL('./data.json', import.meta.url)));
const DOMAINS = data.domains;
const COUNTRIES = matchable(data);

// A deterministic generator, so this reports the same numbers twice running and
// a change in the output means a change in the data rather than a new dice roll.
let seed = 20260830;
function rnd() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const DRAWS = 3000;
const winners = new Map();
const runnersUp = new Map();
let blocked = 0;
let matchedTotal = 0;

for (let i = 0; i < DRAWS; i += 1) {
  // Start from a real country, then reform a random handful of domains, which
  // is what a visitor actually does. A uniformly random selection over all
  // thirteen domains would be a country nobody would build.
  const start = COUNTRIES[Math.floor(rnd() * COUNTRIES.length)];
  const selection = { ...start.choices };
  const reforms = 1 + Math.floor(rnd() * 8);
  for (let r = 0; r < reforms; r += 1) {
    const d = DOMAINS[Math.floor(rnd() * DOMAINS.length)];
    selection[d.id] = d.options[Math.floor(rnd() * d.options.length)].id;
  }

  // The draw picks a tax option rather than a rate, so the rate is that stop's
  // own headline take. A design drawn this way is what the cascade would have
  // had to pay for, not what it settled on: this script asks whether the reveal
  // discriminates, so it discards an unaffordable design rather than cutting it
  // back to one.
  const b = budgets(data, {
    start: start.code,
    taxRate: rateForOption(data, selection.tax),
    selection,
    locked: [],
  });
  if (blockers(b).length) { blocked += 1; continue; }

  const ranked = rank(data, selection);
  winners.set(ranked[0].code, (winners.get(ranked[0].code) || 0) + 1);
  runnersUp.set(ranked[1].code, (runnersUp.get(ranked[1].code) || 0) + 1);
  matchedTotal += ranked[0].matched;
}

const played = DRAWS - blocked;
const table = [...winners.entries()].sort((a, b) => b[1] - a[1]);
const never = COUNTRIES.filter((c) => !winners.has(c.code)).map((c) => c.code);
const top = table[0];

console.log(`${DRAWS} designs drawn, ${blocked} over budget and discarded, ${played} revealed.`);
console.log(`Mean match: ${(matchedTotal / played).toFixed(1)} of ${DOMAINS.length} domains.\n`);
console.log('Wins, most to least:');
for (const [code, n] of table) {
  const name = COUNTRIES.find((c) => c.code === code).name;
  const bar = '#'.repeat(Math.round((n / played) * 120));
  console.log(`  ${code}  ${String(n).padStart(4)}  ${((n / played) * 100).toFixed(1).padStart(5)}%  ${bar} ${name}`);
}
console.log(`\nNever the answer: ${never.length ? never.join(', ') : `none, all ${COUNTRIES.length} matchable countries can win`}`);
console.log(`Most common answer takes ${((top[1] / played) * 100).toFixed(1)}% of designs.`);
console.log(`Never the runner-up either: ${COUNTRIES.filter((c) => !runnersUp.has(c.code)).map((c) => c.code).join(', ') || 'none'}`);
