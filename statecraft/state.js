// Statecraft URL state. No DOM access: this module is pure so it can be tested
// in node. The hash is CC-xxxxxxxxxxxxx: the two-letter starting country, a
// hyphen, then one base36 character per domain giving the index of the chosen
// option within that domain, in data.domains order.

/** @returns {string} e.g. "AU-2130103201110" */
export function encode(data, startCode, selection) {
  const digits = data.domains.map((domain) => {
    const i = (domain.options || []).findIndex((o) => o.id === selection[domain.id]);
    return (i < 0 ? 0 : i).toString(36);
  });
  return `${String(startCode).toUpperCase()}-${digits.join('')}`;
}

/** @returns {{start: string, selection: object}|null} null for anything malformed. It never throws. */
export function decode(data, hash) {
  try {
    if (typeof hash !== 'string') return null;
    const raw = hash.replace(/^#/, '');
    const m = /^([A-Za-z]{2})-([0-9a-zA-Z]+)$/.exec(raw);
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
    return { start, selection };
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
