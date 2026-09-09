"""Render crosscheck/index.html from Shortfall's and Consensus Drift's published data.

Run: python crosscheck/build.py

WHAT THIS IS. Shortfall says whether a company's reported profit looks real. Consensus
Drift says whether its price has kept up with what analysts expect. Both are already
live, both are already joined by ticker for the cross-site links, and neither can show
the one thing that needs both: a company whose accounts look strained AND whose price has
not caught up, against one whose accounts look strained and whose optimism is already
in the price. Those are different situations and today nothing on the estate can tell
them apart.

WHY A BUILD STEP RATHER THAN A FETCH. Both sources are static files on the same domain,
so the page could fetch them. It does not, for the reason CFA Companion stopped fetching:
every request is a chance to fail in a browser nobody can debug from here, and this page
is useless without both files. They are baked in, so the page works with the network
gone and cannot half-load.

THE GUARD, AND IT IS THE POINT OF THE FILE. A join is silent when it goes wrong. If
Shortfall publishes a broken build with forty names in it, the honest output is a page
with forty rows, which looks like a working page. So the previous run's counts are kept
in counts.json and a run that would drop either universe below half of what it last saw
refuses to write anything at all. The same rule the peers module already applies to the
cross-site links, applied to the thing that consumes them.
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html.j2"
OUT = HERE / "index.html"
COUNTS = HERE / "counts.json"
# The manifest the sibling sites read to decide whether to offer a link here. Same
# contract as shortfall/tickers.json and consensus-drift/tickers.json: an unavailable
# target is OMITTED rather than greyed, so each site has to be able to check first.
MANIFEST = HERE / "tickers.json"

SHORTFALL_URL = "https://charlietrenorden.com/shortfall/data.js"
DRIFT_URL = "https://charlietrenorden.com/consensus-drift/"

# Below this share of the previous run, the source is treated as broken rather than
# smaller. Half is deliberately loose: these universes move by tens as coverage changes,
# and a guard that fires on ordinary drift gets switched off by the third time it cries.
MIN_SHARE_OF_PREVIOUS = 0.5

# Consensus Drift's own cut, reused rather than reinvented. A page that drew its bands
# at different points from the site it takes them from would be two answers to one
# question. Positive gap means the PRICE IS BEHIND what analysts expect.
GAP_BAND = 10.0


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "crosscheck-build"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def parse_shortfall(js: str) -> list[dict]:
    """`window.SHORTFALL = {...};` - take the object and read `names`.

    NOT `disclosed`, which is the 17 companies carrying a disclosed event and is the
    obvious wrong key to reach for: it parses, it is a list of the same shape, and it
    would silently build a 17-row page.
    """
    start = js.index("{")
    data = json.loads(js[start:].rstrip().rstrip(";"))
    return data["names"]


def parse_drift(html: str) -> list[dict]:
    """Consensus Drift inlines its rows as <script id="rows" type="application/json">."""
    m = re.search(r'<script id="rows"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise ValueError("consensus-drift published no #rows block")
    return json.loads(m.group(1))


def reading(gap: float) -> str:
    if gap >= GAP_BAND:
        return "behind"
    if gap <= -GAP_BAND:
        return "ahead"
    return "inline"


def join(names: list[dict], drift: list[dict]) -> list[dict]:
    """One row per company present in BOTH, on the plain Yahoo-suffixed ticker.

    The key was settled by the cross-site link work: all three sites already use it and
    Consensus Drift's universe contains no duplicate tickers, so no market qualifier is
    needed.
    """
    by_ticker = {d["ticker"]: d for d in drift}
    rows = []
    for n in names:
        d = by_ticker.get(n["ticker"])
        if d is None:
            continue
        gap = float(d["gap"])
        rows.append({
            "ticker": n["ticker"],
            "name": n["name"],
            "sector": n["sector"],
            "market": n["market"],
            # Higher = more accounting strain, ranked within a sector cohort by
            # Shortfall itself. Carried across rather than recomputed.
            "strain": round(float(n["composite"]), 1),
            # How many of the six tests could be run at all. A composite off two tests
            # is a weaker claim than one off six and the table has to be able to say so.
            "applicable": int(n["applicable"]),
            "gap": round(gap, 1),
            "reading": reading(gap),
            "mcap": d.get("mcap"),
            "analysts": d.get("analysts"),
        })
    rows.sort(key=lambda r: (-r["strain"], r["ticker"]))
    return rows


def check_universes(n_short: int, n_drift: int, n_join: int) -> None:
    """Refuse to publish a page built on a source that has collapsed."""
    previous = json.loads(COUNTS.read_text(encoding="utf-8")) if COUNTS.exists() else {}
    for label, now in (("shortfall", n_short), ("drift", n_drift), ("joined", n_join)):
        was = previous.get(label)
        if was and now < was * MIN_SHARE_OF_PREVIOUS:
            raise SystemExit(
                f"REFUSING TO WRITE: {label} published {now} against {was} last run, "
                f"below {MIN_SHARE_OF_PREVIOUS:.0%}. That is a broken upstream build, "
                f"not a smaller universe. {OUT.name} is unchanged."
            )
    COUNTS.write_text(
        json.dumps({"shortfall": n_short, "drift": n_drift, "joined": n_join}, indent=2)
        + "\n",
        encoding="utf-8",
    )


def corners(rows: list[dict]) -> dict:
    """The four situations, counted. The page states these, so they are computed once."""
    top = sorted(rows, key=lambda r: -r["strain"])[: max(1, len(rows) // 4)]
    cut = top[-1]["strain"] if top else 0
    out = {"cut": cut}
    for key, test in (
        ("strained_behind", lambda r: r["strain"] >= cut and r["reading"] == "behind"),
        ("strained_ahead", lambda r: r["strain"] >= cut and r["reading"] == "ahead"),
        ("clean_behind", lambda r: r["strain"] < cut and r["reading"] == "behind"),
        ("clean_ahead", lambda r: r["strain"] < cut and r["reading"] == "ahead"),
    ):
        out[key] = sum(1 for r in rows if test(r))
    return out


def main() -> int:
    names = parse_shortfall(fetch(SHORTFALL_URL))
    drift = parse_drift(fetch(DRIFT_URL))
    rows = join(names, drift)
    check_universes(len(names), len(drift), len(rows))

    from jinja2 import Template

    html = Template(TEMPLATE.read_text(encoding="utf-8")).render(
        rows_json=json.dumps(rows, separators=(",", ":")),
        n=len(rows),
        n_shortfall=len(names),
        n_drift=len(drift),
        corners=corners(rows),
        built=datetime.now(timezone.utc).strftime("%d %B %Y"),
    )
    OUT.write_text(html, encoding="utf-8")
    MANIFEST.write_text(
        json.dumps({
            "site": "Crosscheck",
            "url": "https://charlietrenorden.com/crosscheck/",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "tickers": sorted(r["ticker"] for r in rows),
        }, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"{OUT}: {len(rows)} companies from {len(names)} x {len(drift)}")
    print(f"{MANIFEST}: {len(rows)} tickers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
