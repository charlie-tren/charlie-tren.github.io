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
//
// THE SLIDER POSITIONS ARE A SEPARATE FIELD TOO, added 01/09/2026, and for the
// same reason one step further on: the twelve categorical sliders are now
// continuous as well, so the option index no longer says where the thumb is.
// A design sixty per cent of the way from one health system to the next costs
// and plots sixty per cent of the way between them, and a link that dropped
// that would restore a different country to the one that was shared.
//
// HOW IT IS CARRIED, and the shape is chosen for what it does to OLD links.
// The thirteen digits keep their exact meaning: the index of the SNAPPED
// option, which is round(pos). The fractional part is a separate optional
// segment, "-p" followed by one triplet per domain that is actually off its
// rung. A triplet is the domain's base36 index then two base36 characters
// holding the offset in hundredths of a rung, biased by fifty, so 50 is dead
// on the rung, 00 is half a rung below and 99 is very nearly half a rung above.
// Hundredths because the slider steps in hundredths, so a link round-trips a
// thumb position exactly rather than nearly.
//
// The consequences are the ones worth having. A design whose thumbs all sit on
// their options writes precisely the hash it wrote yesterday, so nothing that
// was ever shared has changed shape. An OLD hash, which has no p segment at
// all, decodes to integer positions, which is exactly what its author meant:
// they were on their options because there was nowhere else to be. And a
// visitor who has nudged two sliders pays six characters for it rather than the
// twenty-four a fixed-width field would have cost.

import { TAX, ladder, posOfOption, clampPos } from './budget.js';

/** Two base36 characters holding a rate to the nearest half point. */
function rateChars(rate) {
  const n = Math.round(Math.min(TAX.MAX, Math.max(TAX.MIN, Number(rate))) * 2);
  return n.toString(36).padStart(2, '0');
}

// The offset field: 0 to 99, biased by 50, in hundredths of a rung. Capped at
// 99 rather than 100 so the offset can never reach a full half rung upwards,
// which would decode to a position that rounds to a DIFFERENT option from the
// one the thirteen digits name.
const OFF_BIAS = 50;
const OFF_MAX = 99;

/**
 * The "-p..." segment for a set of positions, or '' when every thumb is on its
 * own rung, which is the common case and the one that must cost nothing.
 */
function posChars(data, selection, pos) {
  if (!pos) return '';
  const out = [];
  data.domains.forEach((domain, i) => {
    const rungs = ladder(data, domain.id);
    if (!rungs.length) return;
    const p = Number(pos[domain.id]);
    if (!Number.isFinite(p)) return;
    const held = clampPos(data, domain.id, p);
    // Measured from the rung the thirteen digits already name, so the two
    // fields cannot describe different options.
    const anchor = posOfOption(data, domain.id, selection[domain.id]);
    const n = Math.min(OFF_MAX, Math.max(0, Math.round((held - anchor) * 100) + OFF_BIAS));
    if (n === OFF_BIAS) return;
    out.push(i.toString(36) + n.toString(36).padStart(2, '0'));
  });
  return out.length ? `-p${out.join('')}` : '';
}

/**
 * @param {object} data parsed data.json
 * @param {string} startCode two-letter country code
 * @param {object} selection domain id -> option id
 * @param {number} [taxRate] the headline rate, appended when given
 * @param {object} [pos] domain id -> continuous slider position
 * @returns {string} e.g. "AU-2130103201110-p3ba-1w"
 */
export function encode(data, startCode, selection, taxRate, pos) {
  const digits = data.domains.map((domain) => {
    const i = (domain.options || []).findIndex((o) => o.id === selection[domain.id]);
    return (i < 0 ? 0 : i).toString(36);
  });
  const head = `${String(startCode).toUpperCase()}-${digits.join('')}${posChars(data, selection, pos)}`;
  return Number.isFinite(Number(taxRate)) && taxRate !== undefined && taxRate !== null
    ? `${head}-${rateChars(taxRate)}`
    : head;
}

/**
 * @returns {{start: string, selection: object, pos: object, taxRate: number|null}|null}
 *          null for anything malformed. It never throws.
 */
export function decode(data, hash) {
  try {
    if (typeof hash !== 'string') return null;
    const raw = hash.replace(/^#/, '');
    const m = /^([A-Za-z]{2})-([0-9a-zA-Z]+)(?:-[pP]([0-9a-zA-Z]+))?(?:-([0-9a-zA-Z]{2}))?$/.exec(raw);
    if (!m) return null;

    // MATCHABLE, not merely present. A hash naming a measured-only country
    // would restore a start with no thirteen choices behind it, so the whole
    // hash is treated as malformed and the page opens on the visitor's own
    // timezone instead of on a country with nothing in it.
    const start = m[1].toUpperCase();
    if (!data.countries.some((c) => c.code === start && c.matchable)) return null;

    const digits = m[2];
    if (digits.length !== data.domains.length) return null;

    const selection = {};
    const pos = {};
    for (let i = 0; i < data.domains.length; i += 1) {
      const domain = data.domains[i];
      const index = parseInt(digits[i], 36);
      if (!Number.isInteger(index)) return null;
      const option = (domain.options || [])[index];
      if (!option) return null;
      selection[domain.id] = option.id;
      // The default is the option's own rung. AN OLD HASH THEREFORE RESTORES
      // EXACT POSITIONS, which is what its author meant: before this field
      // existed there was nowhere between two options to be.
      if (ladder(data, domain.id).length) pos[domain.id] = posOfOption(data, domain.id, option.id);
    }

    if (m[3] !== undefined) {
      const body = m[3];
      if (body.length % 3 !== 0) return null;
      const seen = new Set();
      for (let i = 0; i < body.length; i += 3) {
        const which = parseInt(body[i], 36);
        if (!Number.isInteger(which)) return null;
        const domain = data.domains[which];
        if (!domain) return null;
        // Two triplets for one domain would be two answers to one question, and
        // no version of this page writes that.
        if (seen.has(which)) return null;
        seen.add(which);
        const rungs = ladder(data, domain.id);
        if (!rungs.length) return null;
        const n = parseInt(body.slice(i + 1, i + 3), 36);
        if (!Number.isInteger(n) || n < 0 || n > OFF_MAX) return null;
        const offset = (n - OFF_BIAS) / 100;
        const held = clampPos(data, domain.id, pos[domain.id] + offset);
        // The offset must not have moved the thumb onto a different option
        // from the one the digits name, or the hash contradicts itself.
        if (rungs[Math.round(held)].id !== selection[domain.id]) return null;
        pos[domain.id] = held;
      }
    }

    let taxRate = null;
    if (m[4] !== undefined) {
      const n = parseInt(m[4], 36);
      if (!Number.isInteger(n)) return null;
      const rate = n / 2;
      // A rate outside the slider is not a rate this page could have written,
      // so the whole hash is treated as malformed rather than quietly clamped.
      if (rate < TAX.MIN || rate > TAX.MAX) return null;
      taxRate = rate;
    }

    return { start, selection, pos, taxRate };
  } catch (err) {
    return null;
  }
}

/** IANA timezone to country code, falling back to data.fallback. */
export function countryForTimezone(data, tz) {
  if (typeof tz === 'string') {
    const hit = data.timezones[tz];
    if (hit && data.countries.some((c) => c.code === hit && c.matchable)) return hit;
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
