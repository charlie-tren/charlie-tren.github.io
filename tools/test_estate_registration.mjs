/* Estate-wide check on the registrations a new project needs, using files in this
   repo only - no network, so it can run on every push.

   tools/test_estate_head.mjs already covers the analytics beacon, which is the
   registration that was silently missing on five properties. The other three in the
   standing rule were enforced by nothing:

     1. a card in index.html, or a route to the page from one
     2. an entry in tools/shoot_thumbnails.py, so the card has a picture
     3. an entry in site-stats/sections.json - NOT checked here, it lives in a
        private repo this workflow has no credential for. Still the one that gets
        forgotten. See the note at the bottom.

   Plus the live/in-progress invariant, which has actually broken: Shortfall was
   given its "Live" badge and left sitting below the in-progress marker, so the page
   showed a live card inside the in-progress block. Nothing lists the cards against
   the marker, so nobody saw it.

     node tools/test_estate_registration.mjs
*/
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (p) => readFileSync(path.join(ROOT, p), "utf8");
const index = read("index.html");

/* Read the estate list out of the head check's source rather than importing it:
   importing runs that file's top-level fetch of all twenty live sites, and this
   check exists to be cheap enough for every push. One literal, still, so the two
   cannot drift. */
const headSrc = read("tools/test_estate_head.mjs");
const SITES = Object.fromEntries(
  [...headSrc.slice(headSrc.indexOf("const SITES = {")).matchAll(/"([^"]+)":\s+"(https:\/\/[^"]+)"/g)]
    .map((m) => [m[1], m[2]]));

const fails = [];
const check = (ok, msg) => { if (!ok) fails.push(msg); };

/* -------------------------------------------------------------- the cards */

const MARKER = "<!-- In progress from here down. -->";
check(index.includes(MARKER), `the in-progress marker is gone from index.html`);
const [above, below] = index.split(MARKER);

const CARD = /<a class="proj" href="([^"]+)">([\s\S]*?)<\/a>/g;
const cards = [];
for (const half of [["live", above], ["wip", below ?? ""]]) {
  for (const m of half[1].matchAll(CARD)) {
    cards.push({
      side: half[0],
      href: m[1],
      name: (m[2].match(/class="name[^"]*">([^<]+)</) ?? [, "?"])[1],
      badge: (m[2].match(/class="status s-(live|wip)"/) ?? [, "?"])[1],
      img: (m[2].match(/<img src="([^"]+)"/) ?? [, null])[1],
    });
  }
}
check(Object.keys(SITES).length > 15,
      `only ${Object.keys(SITES).length} sites parsed out of test_estate_head.mjs - the SITES literal has moved`);
check(cards.length > 8, `only ${cards.length} cards parsed out of index.html - the markup shape has changed`);

for (const c of cards) {
  /* A "Live" badge below the marker, or an "In progress" one above it, is half a
     move. Both halves are edits a person makes by hand and the second is the one
     that gets dropped. */
  check(c.badge === (c.side === "live" ? "live" : "wip"),
        `${c.name}: badge is "${c.badge}" but the card sits in the ${c.side} block`);

  /* A card with no picture, or a picture that is not there, is a broken card. */
  check(c.img && existsSync(path.join(ROOT, c.img)),
        `${c.name}: thumbnail ${c.img ?? "(none)"} is not in the repo`);
}

/* ------------------------------------------------- the thumbnail registry */

const shoot = read("tools/shoot_thumbnails.py");
const shootSites = shoot.slice(shoot.indexOf("SITES = {")).split(/^\}/m)[0];
const registered = new Set(
  [...shootSites.matchAll(/^\s*"([a-z0-9-]+)":/gm)].map((m) => m[1]));
/* DISMISS, READY, SCHEME and ANCHOR sit below SITES and are keyed by the same slugs.
   Reading to the end of the file put every slug in this set, so the check passed
   whatever was in it - a probe that renamed a SITES key raised nothing. */
check(registered.size > 10 && registered.size < 25,
      `${registered.size} thumbnail slugs parsed - the SITES literal in shoot_thumbnails.py has moved`);

for (const c of cards) {
  /* The card names its own picture, so the slug is whatever assets/<slug>.webp is.
     A card whose slug is not in shoot_thumbnails.py keeps whatever image was placed
     by hand, for ever: the weekly job will never re-shoot it. */
  const slug = (c.img ?? "").replace(/^assets\//, "").replace(/\.\w+$/, "");
  check(registered.has(slug),
        `${c.name}: assets/${slug} is not registered in tools/shoot_thumbnails.py, so it will never be re-shot`);
}

/* -------------------------------------------- every live site is reachable */

/* A project does not have to have a card - Inequality is reached from Pendulum and
   Spectrum and Split the Room from Beyond Small Talk, which is deliberate, they are
   parts of those projects rather than projects beside them. What it must not be is
   unreachable: live, instrumented, counted, and linked from nothing. */
const hubPath = (url) => {
  const u = new URL(url);
  return u.hostname === "charlietrenorden.com" ? u.pathname.split("/")[1] || "" : null;
};
const linksIn = (html) => new Set(
  [...html.matchAll(/href="([^"]+)"/g)].map((m) => m[1]));

const firstHop = linksIn(index);
const reachable = new Set();
for (const href of firstHop) {
  const seg = href.replace(/^https:\/\/charlietrenorden\.com/, "").replace(/^\//, "").split("/")[0];
  reachable.add(href);
  if (!seg || href.startsWith("http") && !href.includes("charlietrenorden.com")) continue;
  const child = path.join(ROOT, seg, "index.html");
  if (existsSync(child)) for (const h of linksIn(readFileSync(child, "utf8"))) reachable.add(h);
}
const reaches = (url) => {
  const seg = hubPath(url);
  if (seg === null) return [...reachable].some((h) => h.includes(new URL(url).hostname));
  return [...reachable].some((h) => {
    const c = h.replace(/^https:\/\/charlietrenorden\.com/, "").replace(/^\.\.\//, "/").replace(/^\//, "");
    return c.split("/")[0] === seg;
  });
};

for (const [name, url] of Object.entries(SITES)) {
  if (url === "https://charlietrenorden.com/") continue;
  check(reaches(url), `${name} (${url}) is live but nothing on the hub, or one hop from it, links to it`);
}

/* ------------------------------------------------------------------ report */

console.log(`${cards.length} cards, ${registered.size} thumbnail slugs, ${Object.keys(SITES).length - 1} live sites checked`);
if (fails.length) {
  console.error(`\n${fails.length} problem${fails.length > 1 ? "s" : ""}:`);
  for (const f of fails) console.error(`  - ${f}`);
  process.exit(1);
}
console.log("all registrations present");
console.log("\nNOT checked here: site-stats/sections.json, which lives in a private repo.\n" +
            "An unmapped path still reports, it just files itself under Hub /<segment>, so\n" +
            "nothing breaks and nobody notices. Check it by hand when adding a project.");
