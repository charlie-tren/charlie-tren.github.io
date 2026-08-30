// Statecraft URL state. No DOM access: this module is pure so it can be tested
// in node.
//
// The hash is CC-xxxxxxxxxxxxx: the two-letter starting country, a hyphen, then
// one base36 character per domain giving the index of the chosen option within
// that domain, in data.domains order.
//
// THE TAX RATE IS A SEPARATE FIELD, appended as "-rr". It used to be implied by
// the tax option index, and once the rate went continuous that stopped being
// true: 34 and 38 both land on the same stop and both would have restored as
// the stop's own rate, which is not the design the visitor shared. The rate is
// carried as base36 of twice the rate, so the whole slider fits in two
// characters at the half point the slider steps in, and an old thirteen-digit
// hash still decodes with no rate at all.

import { TAX } from './budget.js';

/** Two base36 characters holding a rate to the nearest half point. */
function rateChars(rate) {
  const n = Math.round(Math.min(TAX.MAX, Math.max(TAX.MIN, Number(rate))) * 2);
  return n.toString(36).padStart(2, '0');
}

/**
 * @param {object} data parsed data.json
 * @param {string} startCode two-letter country code
 * @param {object} selection domain id -> option id
 * @param {number} [taxRate] the headline rate, appended when given
 * @returns {string} e.g. "AU-2130103201110-1w"
 */
export function encode(data, startCode, selection, taxRate) {
  const digits = data.domains.map((domain) => {
    const i = (domain.options || []).findIndex((o) => o.id === selection[domain.id]);
    return (i < 0 ? 0 : i).toString(36);
  });
  const head = `${String(startCode).toUpperCase()}-${digits.join('')}`;
  return Number.isFinite(Number(taxRate)) && taxRate !== undefined && taxRate !== null
    ? `${head}-${rateChars(taxRate)}`
    : head;
}

/**
 * @returns {{start: string, selection: object, taxRate: number|null}|null}
 *          null for anything malformed. It never throws.
 */
export function decode(data, hash) {
  try {
    if (typeof hash !== 'string') return null;
    const raw = hash.replace(/^#/, '');
    const m = /^([A-Za-z]{2})-([0-9a-zA-Z]+)(?:-([0-9a-zA-Z]{2}))?$/.exec(raw);
    if (!m) return null;

    const start = m[1].toUpperCase();
    if (!data.countries.some((c) => c.code === start)) return null;

    const digits = m[2];
    if (digits.length !== data.domains.length) return null;

    const selection = {};
    for (let i = 0; i < data.domains.length; i += 1) {
      const domain = data.domains[i];
      const index = parseInt(digits[i], 36);
      if (!Number.isInteger(index)) return null;
      const option = (domain.options || [])[index];
      if (!option) return null;
      selection[domain.id] = option.id;
    }

    let taxRate = null;
    if (m[3] !== undefined) {
      const n = parseInt(m[3], 36);
      if (!Number.isInteger(n)) return null;
      const rate = n / 2;
      // A rate outside the slider is not a rate this page could have written,
      // so the whole hash is treated as malformed rather than quietly clamped.
      if (rate < TAX.MIN || rate > TAX.MAX) return null;
      taxRate = rate;
    }

    return { start, selection, taxRate };
  } catch (err) {
    return null;
  }
}

/** IANA timezone to country code, falling back to data.fallback. */
export function countryForTimezone(data, tz) {
  if (typeof tz === 'string') {
    const hit = data.timezones[tz];
    if (hit && data.countries.some((c) => c.code === hit)) return hit;
  }
  return data.fallback;
}

/** @returns {string|null} the browser's timezone, or null if it cannot be read. */
export function detectTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
  } catch (err) {
    return null;
  }
}
