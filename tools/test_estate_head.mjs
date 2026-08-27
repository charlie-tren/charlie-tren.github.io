/* Estate-wide check on the things that were quietly wrong on 20/08/2026 and that
   nothing would have caught: a favicon flattened onto white, an apple-touch icon
   that iOS paints black corners on, a page inheriting the hub's mark because it
   has no icon of its own, and a page with no description so Google writes its own
   snippet.

   Since 25/08/2026 it also checks the analytics beacon. Five live projects had
   silently never been instrumented - the stats dashboard showed six sites and looked
   healthy, because a site that reports nothing is indistinguishable from a site with
   no visitors. That is exactly the failure this file exists for.

   Every one of those is invisible until someone looks at a tab, which is why this
   exists as a test rather than a habit.

     node tools/test_estate_head.mjs
*/
const SITES = {
  "Hub":               "https://charlietrenorden.com/",
  "Beyond Small Talk": "https://charlietrenorden.com/beyond-small-talk/",
  "Split the Room":    "https://charlietrenorden.com/split-the-room/",
  "Spectrum":          "https://charlietrenorden.com/spectrum/",
  "Lexicon":           "https://charlietrenorden.com/lexicon/",
  "Photocopy":         "https://charlietrenorden.com/photocopy/",
  "Woop Woop":         "https://charlietrenorden.com/woop-woop/",
  "Shortfall":         "https://charlietrenorden.com/shortfall/",
  "Consensus Drift":   "https://charlietrenorden.com/consensus-drift/",
  "The Lindy Effect":  "https://charlietrenorden.com/lindy-effect/",
  "Pendulum":          "https://charlietrenorden.com/pendulum/",
  "CFA Companion":     "https://charlietrenorden.com/cfa-companion/",
  "Ghostwriters":      "https://charlietrenorden.com/ghostwriters/",
  "Pendulum: Inequality": "https://charlietrenorden.com/inequality/",
  "Equity Research":   "https://charlietrenorden.com/research/",
  "Crowdwise":         "https://crowdwise.charlietrenorden.com/",
  "DCF Studio":        "https://dcf.charlietrenorden.com/GOOGL",
  "One Story":         "https://one-story.charlietrenorden.com/",
  "The Aftertimes":    "https://aftertimes.charlietrenorden.com/",
  /* The APEX, not the old chronoscape. subdomain. That subdomain is the stale
     Cloudflare Pages project the site was migrated OFF on 20/08/2026, and it
     does not redirect: it answers 200 with a frozen copy of the whole site. So
     every check in this file was passing against a snapshot rather than against
     anything anyone deploys, and would never have caught a Chronoscape
     regression. Found 27/08/2026 when the gate assertion failed here and
     nowhere else. */
  "Chronoscape":       "https://charlietrenorden.com/chronoscape/iceland/",
};

/* PNG: walk the chunks to the first IDAT is overkill; the corner pixel is what
   matters and decoding a PNG without a library is not worth it. Instead we assert
   on the bytes we CAN read cheaply: an 8-bit RGBA PNG (colour type 6) can carry
   transparency, colour type 2 (RGB) cannot. A flattened apple-touch icon should be
   type 2 or have no alpha; a tab icon must be type 6. */
function pngColourType(buf) {
  if (buf.length < 26 || buf.readUInt32BE(0) !== 0x89504e47) return null;
  return buf[25];                       // IHDR colour type
}

const fails = [];
const check = (label, ok, detail) => {
  if (!ok) fails.push(`${label}${detail ? ` - ${detail}` : ""}`);
  return ok;
};

for (const [name, url] of Object.entries(SITES)) {
  let html;
  try {
    html = await (await fetch(url, { headers: { "User-Agent": "estate-head-check" } })).text();
  } catch (e) {
    check(`${name}: page unreachable`, false, e.message);
    continue;
  }
  const head = html.slice(0, 8000);

  const title = head.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1].trim();
  check(`${name}: has a <title>`, !!title);
  // House convention: the project name alone, or "page - project". Never a tagline.
  if (title) check(`${name}: title is not a tagline`, title.split(/\s+-\s+/).length <= 2, title);

  check(`${name}: has a meta description`,
    /<meta\s+name="description"\s+content="[^"]{20,}"/i.test(head));

  /* Checked against the WHOLE page, not `head`: the beacon is the last thing in
     <head> and on a big single-file page that sits well past the 8KB slice. */
  check(`${name}: reports to Cloudflare Web Analytics`,
    html.includes("static.cloudflareinsights.com/beacon.min.js"),
    "invisible to stats.charlietrenorden.com");

  /* Both beacons load through an inline gate now rather than from static tags, so
     the two checks either side of this one would pass on a page that still had the
     URLs written down and no longer loaded them. This asserts the gate itself is
     there. What it CANNOT check is whether the logic still works - a page that
     gated everyone out would pass all three - which is what site-stats'
     tests/test_gate.py watches the network for. */
  check(`${name}: loads its analytics through the gate`,
    html.includes("ct.nostats") && html.includes("navigator.webdriver"),
    "ungated, so Charlie and every agent count as audience");

  const icons = [...head.matchAll(/<link[^>]*rel="(icon|apple-touch-icon)"[^>]*>/gi)];
  check(`${name}: has its own icon tags`, icons.length > 0,
    "falls back to the hub's mark at /favicon.ico");

  for (const [tag, rel] of icons.map((m) => [m[0], m[1].toLowerCase()])) {
    const href = tag.match(/href="([^"]+)"/)?.[1];
    if (!href || href.endsWith(".svg")) continue;
    const abs = new URL(href, url).href;
    let buf;
    try {
      const r = await fetch(abs);
      if (!check(`${name}: ${href} resolves`, r.ok, `HTTP ${r.status}`)) continue;
      buf = Buffer.from(await r.arrayBuffer());
    } catch (e) { check(`${name}: ${href} fetch`, false, e.message); continue; }

    const ct = pngColourType(buf);
    if (ct === null) continue;                       // .ico - not parsed here
    // Masked icons must be FLATTENED: the platform rounds them itself and paints
    // transparency black. That covers apple-touch and Android's maskable set,
    // which is why android-chrome-*.png being opaque is correct, not a fault.
    const masked = rel === "apple-touch-icon" || /android-chrome|maskable/.test(href);
    if (masked) {
      check(`${name}: ${href} is flattened for masking`, ct === 2,
        `PNG colour type ${ct} (6 = has alpha; the platform will show black corners)`);
    } else {
      check(`${name}: ${href} keeps its alpha`, ct === 6,
        `PNG colour type ${ct} (2 = flattened, so the rounded corners are opaque)`);
    }
  }
}

if (fails.length) {
  console.error(`${fails.length} problem(s):\n` + fails.map((f) => `  ${f}`).join("\n"));
  process.exit(1);
}
console.log(`all ${Object.keys(SITES).length} properties pass: title, description, own icons, correct alpha`);
