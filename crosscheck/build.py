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
# Published by dcf-studio's own daily job, which runs the model in Node rather than
# asking its 609 pages over HTTP. Ratios only: implied value over market price.
DCF_URL = "https://dcf.charlietrenorden.com/valuations.json"

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


def parse_dcf(text: str) -> dict:
    """DCF Studio's published ratios: implied value per share over market price."""
    return json.loads(text).get("ratios", {})


def dcf_cuts(ratios: list[float]) -> tuple[float, float]:
    """The two tercile boundaries of the model's own distribution.

    Cut against ITSELF, not against 1.0. The model runs systematically below market
    prices - median 0.61x over the 506 it can value, p10 0.20x, p90 1.70x - so a
    boundary at parity would put 75% of the estate in one band and say nothing. What
    the reader can use is where a company sits among the others.
    """
    s = sorted(ratios)
    if not s:
        return (0.0, 0.0)
    return (s[len(s) // 3], s[2 * len(s) // 3])


def dcf_band(ratio: float | None, cuts: tuple[float, float]) -> str | None:
    """Where this company sits in that distribution, in words rather than a score.

    Words, and not a 0-100 percentile, for two reasons. The table already carries a
    0-100 headed Shortfall where 100 is the WORST, and a second 0-100 beside it where
    100 is the best would be read wrong by anyone moving quickly. And a rank printed as
    a number invites being treated as a measurement, when the honest claim is only an
    ordering. The column sorts on the underlying ratio, so nothing is lost.

    A HIGHER ratio is cheaper: the model puts the shares further above their price.
    """
    if ratio is None:
        return None
    lo, hi = cuts
    # Half-open at the bottom, closed at the top. Inclusive at BOTH ends puts the two
    # boundary companies in the outer bands and leaves the middle third short, which on
    # a six-item set came out 3/1/2 rather than 2/2/2.
    if ratio < lo:
        return "dearer"
    if ratio >= hi:
        return "cheaper"
    return "middle"


def has_dcf(rows: list[dict]) -> bool:
    """Whether the column is worth rendering at all.

    Degrade to LESS, never to a column of blanks: a blank column reads as "the model
    had no opinion on any of these", which is a claim, where an absent column reads as
    what it is. The floor is a share rather than a count because ranking a handful of
    companies against each other says nothing - 103 of the 609 are already dropped as
    implausible, so a thin file is a broken run, not a quiet model.
    """
    if not rows:
        return False
    return sum(1 for r in rows if r.get("dcf") is not None) >= len(rows) * 0.25


def _percentiles(values: list[float | None]) -> list[float | None]:
    """Each value's position in its own distribution, 0 to 1, ties sharing a position.

    Percentiles rather than the raw numbers, because the three measures have nothing
    in common numerically: Shortfall is 0-100, the gap spans about 270 percentage
    points, and the DCF ratio sits mostly between 0.1 and 2. Averaged raw, the gap
    would decide the entire ordering by virtue of having the widest range.
    """
    present = sorted(v for v in values if v is not None)
    if not present:
        return [None] * len(values)
    if len(present) == 1:
        return [None if v is None else 0.5 for v in values]

    # RANK position, not (v - min) / (max - min). Min-max scaling is the obvious way to
    # write this and it hands the ordering to outliers: the gap runs from -211.1 to
    # +56.7, so one distressed name at the bottom compresses every other company into
    # the top fifth of the range and the measure stops discriminating between them.
    # A rank percentile is unaffected by how far the extremes sit from the pack, which
    # is the property this needs - all three inputs are heavy-tailed.
    import bisect

    n = len(present)
    out = []
    for v in values:
        if v is None:
            out.append(None)
            continue
        # Ties share a position: the midpoint of the block of equal values, so that a
        # column with many repeated readings does not order them by accident.
        lo = bisect.bisect_left(present, v)
        hi = bisect.bisect_right(present, v)
        out.append(((lo + hi - 1) / 2) / (n - 1))
    return out


# A rank percentile is exactly 0 for the last name, and log(0) is not a number. The
# floor is half a rank step at n = 100, small enough that the bottom name still scores
# under anything above it and large enough that one leg cannot zero a company outright.
P_FLOOR = 0.005


def drift_leg(p_gap, p_rev):
    """Price behind estimates AND estimates rising, as one percentile-scaled leg."""
    if p_gap is None:
        return None
    if p_rev is None:
        return p_gap
    return (max(p_gap, P_FLOOR) * max(p_rev, P_FLOOR)) ** 0.5


def combine(*legs, weights=None):
    """Weighted geometric mean of the legs that are present, 0 to 1."""
    import math

    weights = weights or [1.0] * len(legs)
    num = den = 0.0
    for p, w in zip(legs, weights):
        if p is None or w <= 0:
            continue
        num += w * math.log(max(p, P_FLOOR))
        den += w
    return math.exp(num / den) if den else 0.0


def rank_rows(rows: list[dict]) -> list[dict]:
    """Order the table by how far the three measures agree, and stamp a rank on each.

    ONE AXIS, oriented so higher is more attractive on all three: accounts that are not
    strained, a price that sits behind analyst estimates, and a model value above the
    market price. The top of the table is where all three point the same way and the
    bottom is where they point the other way. That is coherent precisely because the
    measures are close to independent - r = +0.087 between the first two - so agreement
    between them is information rather than one number counted three times.

    Shortfall is FLIPPED, because its own scale runs the other way: 100 is the most
    strained company, not the best. Carrying it through unflipped would have put the
    worst accounts on the estate at the top of the page.

    A missing component is averaged over the ones that are there rather than scored
    zero. 103 of the 609 have no DCF reading, and scoring the absence would rank them
    by data coverage instead of by anything about the companies.

    GEOMETRIC mean, not arithmetic, since 12/09/2026. The page's claim is agreement,
    and an arithmetic mean lets one leg pay for another: FIX sat in the top 50 on
    percentiles 99 / 96 / 28. A geometric mean cannot be rescued by one strong leg,
    which is what "all three point the same way" means in arithmetic. Measured on the
    day: 45 of the top 50 unchanged, and the five that left were exactly the ones with
    a leg under the 30th percentile.

    The drift leg needs the estimates to be RISING, not only the price to be behind
    them. "Price behind estimates" was satisfied by a price falling faster than the
    estimates it trailed: 24 of the top 50 had falling estimates. So the leg is the
    geometric mean of two percentiles, the gap and the estimate change itself, and a
    name with estimates going down cannot score high on it whatever the price did.
    """
    strain = _percentiles([100 - r["strain"] for r in rows])
    gap = _percentiles([r["gap"] for r in rows])
    rev = _percentiles([r.get("rev") for r in rows])
    dcf = _percentiles([r.get("dcf") for r in rows])
    for r, s, g, e, d in zip(rows, strain, gap, rev, dcf):
        # Shipped per row so the page can REWEIGHT live without carrying the whole
        # distribution three times over and re-ranking 609 rows on every slider move.
        r["pStrain"], r["pDrift"], r["pRev"], r["pDcf"] = s, g, e, d
        r["complete"] = None not in (s, g, d)
        r["score"] = combine(s, drift_leg(g, e), d)
    ordered = sorted(rows, key=lambda r: (-r["score"], r["ticker"]))
    for i, r in enumerate(ordered, 1):
        r["rank"] = i
    return ordered


def join(names: list[dict], drift: list[dict], dcf: dict | None = None) -> list[dict]:
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
            # The two moves the drift is the difference OF. Carried so the cell can say
            # what it is made of on hover - a lone "+15.8" says a distance without
            # saying between what and what.
            "rev": d.get("rev"),
            "pxchg": d.get("price"),
            # Carried for the cross-plot's other axes. Measured over the 609 before
            # adding them, so these are the pairs that actually relate rather than a
            # pile of selectable noise: size against short interest is rho -0.65,
            # analyst count against how many accounting tests can be run is +0.49, and
            # a company's one-year return against its DCF ratio is -0.23.
            "short_int": n.get("short_interest"),
            "ret_1y": n.get("ret_1y"),
            "mcap": d.get("mcap"),
            "analysts": d.get("analysts"),
            "dcf": (dcf or {}).get(n["ticker"]),
        })
    # Banded after the loop, because the cuts are a property of the whole set rather
    # than of any one company.
    cuts = dcf_cuts([r["dcf"] for r in rows if r["dcf"] is not None])
    for r in rows:
        r["dcfband"] = dcf_band(r["dcf"], cuts)
    # Ordered by the three measures combined rather than by Shortfall alone. Sorting on
    # one of three columns made that column the page's opinion by default, which is the
    # opposite of what a cross-tab is for.
    return rank_rows(rows)


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


HISTORY = HERE / "history.jsonl"


def parse_dcf_prices(text: str) -> dict:
    """The price each DCF ratio was struck against: {ticker: [price, currency]}."""
    return json.loads(text).get("prices", {})


def append_history(rows: list[dict], prices: dict, date: str, path: Path = HISTORY) -> int:
    """One line per company per build: the three component percentiles and the price.

    WHY. Nothing available today correlates strongly with a composite of three
    near-independent measures - scanned 12/09/2026 across the page's own fields,
    Shortfall's underlying ratios and 25 Yahoo fields on all 494, and the best
    non-arithmetic result was EV/EBITDA at rho -0.31. That is structural: a composite
    dilutes anything tied to one of its inputs by root three. The one thing that
    SHOULD relate to it is what the price does afterwards, and that cannot be measured
    without a record of what the score said and when. This is that record.

    COMPONENTS, NOT THE SCORE. The weights are user-adjustable on the page, so writing
    the equal-weight score would freeze one weighting for ever. Writing the three
    inputs lets any weighting be tested against what followed.

    ONE LINE PER DAY. The build can run twice in a day - a manual dispatch after the
    cron, a rebase that re-runs it - and a second line for the same date would
    double-count that day in every later average. A date already present is skipped.

    Compact keys because this file grows by ~600 lines a day for as long as the site
    exists: d date, t ticker, s/r/v the strain, drift and value percentiles, p price,
    c currency.
    """
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                # Compact separators, so no space after the colon - matching the writer
                # below exactly. With a space here the check never matched and every
                # rebuild in a day added a second copy, which the test caught.
                if line.startswith('{"d":"%s"' % date):
                    return 0
    written = 0
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            p = prices.get(r["ticker"])
            fh.write(json.dumps({
                "d": date, "t": r["ticker"],
                "s": r["pStrain"], "r": r["pDrift"], "v": r["pDcf"],
                "e": r.get("pRev"),
                "p": p[0] if p else None, "c": p[1] if p else None,
            }, separators=(",", ":")) + "\n")
            written += 1
    return written


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
    # Best effort, and deliberately the ONLY one of the three that is. Shortfall and
    # Consensus Drift are the page; without either there is nothing to render and the
    # run should fail loudly. DCF Studio is a third column on top, so a bad day there
    # costs a column rather than the site - and the column disappears rather than
    # filling with blanks, which would read as the model declining to answer.
    prices: dict = {}
    try:
        dcf_text = fetch(DCF_URL)
        dcf = parse_dcf(dcf_text)
        prices = parse_dcf_prices(dcf_text)
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: no DCF ratios ({type(exc).__name__}: {exc}); "
              f"the column will be omitted", file=sys.stderr)
        dcf = None

    rows = join(names, drift, dcf)
    check_universes(len(names), len(drift), len(rows))
    # After the guard, so a collapsed source never writes a day of nonsense into the
    # record. Before the page, so a template error cannot cost the day's line.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    recorded = append_history(rows, prices, today)
    print(f"{HISTORY.name}: {recorded} lines for {today}"
          + ("" if recorded else " (already recorded)"))

    from jinja2 import Template

    html = Template(TEMPLATE.read_text(encoding="utf-8")).render(
        rows_json=json.dumps(rows, separators=(",", ":")),
        n=len(rows),
        n_shortfall=len(names),
        n_drift=len(drift),
        n_dcf=sum(1 for r in rows if r["dcf"] is not None),
        has_dcf=has_dcf(rows),
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
    n_dcf = sum(1 for r in rows if r["dcf"] is not None)
    print(f"{OUT}: {len(rows)} companies from {len(names)} x {len(drift)}"
          f", {n_dcf} with a DCF reading"
          f"{'' if has_dcf(rows) else ' (column OMITTED - too few)'}")
    print(f"{MANIFEST}: {len(rows)} tickers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
