/* Split the Room and Spectrum keep separate copies of the statement list: the page
   needs its own so it works with no backend, and the room needs its own so every
   player is served the same statement in the same order. Nothing enforces that they
   agree, so this does.

   Checks the LIVE worker, not a local file, because the deployed list is what
   players actually get. A worker outage therefore fails this - that is intended,
   since a silent divergence is the thing worth catching.

     node tools/test_statements.mjs
*/
import { readFileSync } from "node:fs";

const WORKER = process.env.SPECTRUM_API || "https://spectrum.charlietrenorden.com";
const PAGE = new URL("../split-the-room/index.html", import.meta.url);

function pageStatements() {
  const html = readFileSync(PAGE, "utf8");
  const m = html.match(/window\.ROOM\s*=\s*\{\s*items:\s*(\[[\s\S]*?\])\s*\}\s*;/);
  if (!m) throw new Error("could not find window.ROOM.items in split-the-room/index.html");
  return JSON.parse(m[1]);
}

const fails = [];
const check = (label, ok, detail) => {
  console.log(`${ok ? "PASS  " : "FAIL  "}${label}${ok || !detail ? "" : `\n        ${detail}`}`);
  if (!ok) fails.push(label);
};

const page = pageStatements();
const res = await fetch(`${WORKER}/api/statements`);
if (!res.ok) {
  console.error(`FAIL  could not reach ${WORKER}/api/statements (HTTP ${res.status})`);
  process.exit(1);
}
const { statements: worker } = await res.json();

check("the page has statements", page.length > 0, `got ${page.length}`);
check("no duplicates on the page", new Set(page).size === page.length,
  `${page.length - new Set(page).size} repeated`);
check("no duplicates in the room", new Set(worker).size === worker.length,
  `${worker.length - new Set(worker).size} repeated`);
check("same count", page.length === worker.length, `page ${page.length}, room ${worker.length}`);

const onlyPage = page.filter((x) => !worker.includes(x));
const onlyWorker = worker.filter((x) => !page.includes(x));
check("nothing only on the page", onlyPage.length === 0, onlyPage.join("\n        "));
check("nothing only in the room", onlyWorker.length === 0, onlyWorker.join("\n        "));

/* Every statement must read as a proposition, or it cannot be answered on a
   disagree-to-agree axis - a question can only be answered on the solo page. */
const questions = page.filter((x) => x.trim().endsWith("?"));
check("no questions in the list", questions.length === 0, questions.join("\n        "));

console.log(`\n${fails.length ? `${fails.length} FAILED` : `all checks passed, ${page.length} statements`}`);
process.exit(fails.length ? 1 : 0);
