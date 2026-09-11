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
  "Worst Case Scenario": "https://charlietrenorden.com/worst-case-scenario/",
  "Lexicon":           "https://charlietrenorden.com/lexicon/",
  "Photocopy":         "https://charlietrenorden.com/photocopy/",
  "Woop Woop":         "https://charlietrenorden.com/woop-woop/",
  "Shortfall":         "https://charlietrenorden.com/shortfall/",
  "Consensus Drift":   "https://charlietrenorden.com/consensus-drift/",
  "The Lindy Effect":  "https://charlietrenorden.com/lindy-effect/",
  "Pendulum":          "https://charlietrenorden.com/pendulum/",
  "CFA Companion":     "https://charlietrenorden.com/cfa-companion/",
  "Ghostwriters":      "https://charlietrenorden.com/ghostwriters/",
  "Statecraft":        "https://charlietrenorden.com/statecraft/",
  "Property Atlas":    "https://charlietrenorden.com/property-atlas/",
  "Bookmark":          "https://charlietrenorden.com/bookmark/",
  "Pendulum: Inequality": "https://charlietrenorden.com/inequality/",
  "Equity Research":   "https://charlietrenorden.com/research/",
  "Position Record":   "https://charlietrenorden.com/position-record/",
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

  /* CANONICAL. Fifteen of the twenty-five properties had none on 10/09/2026,
     found by checking five homepages by hand - which is the reason this is a
     test now. Two things make it matter here more than on a normal site.
     Several projects are reachable at BOTH a path on the apex and their own
     subdomain, or at their deploy origin as well as the custom domain
     (dcf-studio.vercel.app and crowdwise-live.vercel.app both answer 200), so
     without one tag Google is choosing between duplicates on its own. And DCF
     Studio carries its whole assumption set in the query string, so one company
     has an unbounded number of URLs.

     Photocopy and One Story are template-fixed and land on their next scheduled
     render rather than on a push here, so they are enumerated rather than
     waived: the reverse assertion below turns the exemption itself into a
     failure once they deploy, which is what makes the list shrink. */
  /* Emptied 11/09/2026: both Photocopy and One Story now emit a canonical, and
     this test fails on a STALE exemption as loudly as on a missing tag, which is
     what surfaced it. Kept as an empty set rather than deleted, because the next
     new property will need somewhere to sit while its canonical is written. */
  const NO_CANONICAL_YET = new Set([]);
  const canonical = head.match(/<link[^>]*rel="canonical"[^>]*href="([^"]+)"/i)?.[1];
  if (!NO_CANONICAL_YET.has(name)) {
    check(`${name}: has a canonical URL`, !!canonical,
      "the apex path, the subdomain and the deploy origin all index separately");
  } else if (canonical) {
    check(`${name}: fixed - remove it from NO_CANONICAL_YET`, false,
      "it now has a canonical, so the exemption is stale");
  }
  /* An absolute URL on our own domain: a relative or a stray localhost
     canonical is worse than none, since it points the index somewhere real.
     The trailing slash is optional - Crowdwise names its bare origin, which is
     the same document, and requiring one failed a correct tag. */
  if (canonical) {
    check(`${name}: canonical is an absolute URL on this estate`,
      /^https:\/\/[a-z0-9.-]*charlietrenorden\.com(\/|$)/.test(canonical), canonical);
  }

  /* A DECLARED CARD SLOT MUST HAVE AN IMAGE. Not "every page needs a card" -
     several deliberately have none. This is the pairing that renders BROKEN:
     twitter:card=summary_large_image tells X and Slack to reserve a large image
     slot, and with no og:image they draw the slot empty, so the share looks
     like a dead page. statecraft/make_card.py exists because of exactly this
     and says so in its first paragraph; the-aftertimes/card.py is a second
     instance, and CFA Companion was the third, found by this sweep and fixed in
     the same change that added this check - which is why the set is empty. Keep
     it: an enumerated exemption is how the next one stays visible and countable
     while a card gets drawn, rather than being waived or left red. */
  const EMPTY_CARD_SLOT = new Set([]);
  const largeCard = /<meta[^>]*name="twitter:card"[^>]*content="summary_large_image"/i.test(head);
  const hasOgImage = /<meta[^>]*property="og:image"/i.test(head);
  if (largeCard && !EMPTY_CARD_SLOT.has(name)) {
    check(`${name}: declares a large card and has an og:image`, hasOgImage,
      "X and Slack reserve the slot and render it empty");
  } else if (largeCard && hasOgImage) {
    check(`${name}: fixed - remove it from EMPTY_CARD_SLOT`, false,
      "it now has an og:image, so the exemption is stale");
  }

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

  /* PRESENCE, not just alpha. This block used to be one `icons.length > 0` and
     then a loop checking the alpha of whatever happened to exist - so a page
     carrying a single SVG passed every assertion in the file. Statecraft went
     Live on 08/09/2026 that way and Property Atlas had been like it for ten
     days: a blank tab in Safari and older Chrome, under a green run whose own
     summary line said "own icons". */
  const hrefs = icons.map((m) => m[0].match(/href="([^"]+)"/)?.[1] || "");
  const raster = hrefs.some((h) => /\.(png|ico)(\?|$)/i.test(h));
  check(`${name}: has a raster favicon, not only an SVG`, raster,
    "Safari and older Chrome do not read an SVG favicon, so the tab is blank");

  /* apple-touch is missing on eight properties and each is a twenty-minute
     rasterise. Enumerated rather than warned about, so a NEW one fails
     immediately and the debt is visible and countable instead of being a line
     in a report nobody re-reads. Delete a name as you fix it; the list only
     shrinks. */
  const NO_APPLE_YET = new Set([
    "Beyond Small Talk", "Crowdwise", "DCF Studio", "Lexicon",
    "Shortfall", "Spectrum", "Split the Room", "Worst Case Scenario",
  ]);
  const hasApple = icons.some((m) => m[1].toLowerCase() === "apple-touch-icon");
  if (!NO_APPLE_YET.has(name)) {
    check(`${name}: has an apple-touch icon`, hasApple,
      "iOS has nothing to mask, so a home-screen shortcut gets a screenshot");
  } else if (hasApple) {
    check(`${name}: fixed - remove it from NO_APPLE_YET`, false,
      "it now has an apple-touch icon, so the exemption is stale");
  }

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
/* Every homepage card on one of our own domains must be in SITES. The list is
   hand-maintained on purpose - it also holds sub-pages and shared cards that have
   no card of their own - so this checks the direction that actually goes wrong:
   a project gets carded and nobody adds it here. */
{
  const { readFileSync } = await import("node:fs");
  const home = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const cards = [...home.matchAll(
    /<a class="proj" href="([^"]+)"[\s\S]{0,400}?class="name[^"]*">(?:<svg[\s\S]*?<\/svg>)?([^<]+)<\/span>/g)];
  const known = new Set(Object.keys(SITES));
  for (const [, href, rawName] of cards) {
    const name = rawName.trim();
    if (!/charlietrenorden\.com|^\/|^[a-z-]+\/$/.test(href)) continue;  // off-estate, e.g. Substack
    check(`${name}: carded on the homepage and covered by this test`, known.has(name),
      `add "${name}": "${href}" to SITES - a carded project with no head check is how ` +
      `Property Atlas shipped an SVG-only favicon for ten days`);
  }
}

console.log(`all ${Object.keys(SITES).length} properties pass: title, description, canonical, ` +
            `no empty card slots, own icons, correct alpha`);
