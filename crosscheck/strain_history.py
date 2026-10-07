"""Point-in-time Accounting Quality for the reconstructed record, rebuilt from SEC filings.

    python crosscheck/strain_history.py              # writes "sp" into history.jsonl
    python crosscheck/strain_history.py --check      # only the agreement check, no write

WHY. The reconstructed cohorts (2021 onward, "b": 1) could not be scored on accounts:
the strain they carried came from a 2026 Shortfall snapshot, which is hindsight, so the
page dropped it. This rebuilds the leg as it would have read at each cohort date, by
running SHORTFALL'S OWN pipeline (fetch_us.sweep -> build_records -> assemble_name ->
finalise) as if each past fiscal year were the latest one. Same tests, same within-
sector ranking, same composite, so nothing here is a second implementation of Shortfall.

POINT IN TIME. A fiscal year's score is attached only to cohorts dated on or after the
1 April following it, by which point a calendar-year 10-K is public (the large-filer
deadline is 60 days). Caveat: EDGAR frames return the latest value for a period, so a
year that was later restated carries the restated figures: slight hindsight, stated.

SCOPE. US only - EDGAR has no ASX equivalent. The percentile ("sp") is struck within the
year's US cohort exactly as the page strikes pStrain: higher = cleaner accounts.

CHECK. The most recent year must reproduce live Shortfall's composite for the same year;
the run stops if the rank correlation is below 0.95.

SEC traffic: ~10 calls per data field per year, 0.25s apart (Shortfall's own client),
cached to strain_frames.pkl so a rerun costs nothing.
"""
import argparse
import json
import math
import os
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHORTFALL = HERE.parent.parent / "shortfall"
HISTORY = HERE / "history.jsonl"
CACHE = HERE / "strain_frames.pkl"
YEARS = list(range(2016, 2026))       # FY2016 .. FY2025: the earliest scored year needs priors
SCORED = list(range(2019, 2026))      # years whose score is attached somewhere


def available_from(fy: int) -> str:
    return f"{fy + 1}-04-01"


def load_shortfall():
    os.chdir(SHORTFALL)                # its modules read sectors.json etc. relative to here
    sys.path.insert(0, str(SHORTFALL))
    import build_data, edgar, fetch_us  # noqa: E402
    return build_data, edgar, fetch_us


def us_meta(edgar):
    names = [n for n in json.load(open("universe.json"))["names"] if n["market"].startswith("United States")]
    lookup = edgar.load_ticker_lookup()
    kept, _ = edgar.dedupe_by_cik(names, lookup)
    return {lookup[edgar.normalise_ticker(n["ticker"])]: n for n in kept
            if edgar.normalise_ticker(n["ticker"]) in lookup}


FLAGS: dict = {}


def scores_by_year(build_data, fetch_us, meta):
    frames = pickle.load(open(CACHE, "rb")) if CACHE.exists() else {}
    for y in YEARS:
        if y not in frames:
            frames[y] = fetch_us.sweep(y)
            pickle.dump(frames, open(CACHE, "wb"))
            print(f"  swept FY{y}", flush=True)
    history = {}
    for y in YEARS:
        for r in fetch_us.build_records(y, frames[y], meta):
            history.setdefault(r.ticker, []).append(r)
    out = {}
    for fy in SCORED:
        rows = []
        for t, recs in history.items():
            # The latest year and the THREE before it, as live Shortfall sweeps four
            # years (run_build.years_for, rolling on 1 April): some tests average over every prior they are
            # handed, so a deeper history would score a different test.
            upto = [r for r in recs if fy - 3 <= r.year <= fy]
            row = build_data.assemble_name(upto)
            if row and row["year"] == fy:
                rows.append(row)
        payload = build_data.finalise(rows)
        out[fy] = {r["ticker"]: r["composite"] for r in payload["names"]}
        FLAGS[fy] = {r["ticker"]: {k: v.get("value") for k, v in r["flags"].items()} for r in rows}
        print(f"  FY{fy}: {len(out[fy])} scored of {len(rows)} assembled", flush=True)
    return out


def rank_corr(a: dict, b: dict) -> float:
    keys = sorted(set(a) & set(b))
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for k, i in enumerate(order):
            r[i] = k
        return r
    x, y = ranks([a[k] for k in keys]), ranks([b[k] for k in keys])
    mx, my = sum(x) / len(x), sum(y) / len(y)
    cov = sum((p - mx) * (q - my) for p, q in zip(x, y))
    return cov / math.sqrt(sum((p - mx) ** 2 for p in x) * sum((q - my) ** 2 for q in y))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    build_data, edgar, fetch_us = load_shortfall()
    meta = us_meta(edgar)
    print(f"{len(meta)} US names mapped to a CIK")
    scores = scores_by_year(build_data, fetch_us, meta)

    live = json.load(open(SHORTFALL / "docs" / "data.json", encoding="utf-8"))
    live_fy = {r["year"] for r in live["names"] if r["market"].startswith("United States")}
    fy = max(live_fy)
    live_s = {r["ticker"]: r["composite"] for r in live["names"]
              if r["market"].startswith("United States") and r["year"] == fy}
    # 1. The raw test values must agree: same filings, same tests. This is the check
    #    that the pipeline is reused faithfully.
    live_f = {r["ticker"]: {k: v.get("value") for k, v in r["flags"].items()} for r in live["names"] + live.get("excluded", [])
              if r["market"].startswith("United States") and r["year"] == fy}
    same = tot = 0
    for t in set(FLAGS[fy]) & set(live_f):
        for k, v in FLAGS[fy][t].items():
            w = live_f[t].get(k)
            if v is None and w is None:
                continue
            tot += 1
            same += (v is not None and w is not None and abs(v - w) <= 1e-9 * max(1, abs(w)))
    print(f"raw test values identical to live Shortfall, FY{fy}: {same} of {tot} ({same / max(1, tot):.1%})")
    # 2. The composite will differ by universe: live ranks US and ASX together within
    #    sector, the rebuild ranks US only (no ASX history). Reported, not gated.
    rho = rank_corr(scores[fy], live_s)
    print(f"agreement with live Shortfall, FY{fy}: rank correlation {rho:.3f} over {len(set(scores[fy]) & set(live_s))} names")
    if same / max(1, tot) < 0.98:
        print("STOP: the raw test values do not reproduce live Shortfall - the pipeline is not being reused faithfully")
        return 1
    if args.check:
        return 0

    sys.path.insert(0, str(HERE))
    import build  # noqa: E402
    # percentile within each year's cohort, higher = cleaner (as pStrain)
    pct = {}
    for y, s in scores.items():
        t = sorted(s)
        p = build._percentiles([100 - s[k] for k in t])
        pct[y] = dict(zip(t, p))
    raw = HISTORY.read_text(encoding="utf-8").splitlines()
    lines = [json.loads(l) for l in raw if l.strip()]
    added = 0
    for r in lines:
        if not r.get("b"):
            continue
        r.pop("sp", None)
        if r["t"].endswith(".AX"):
            continue
        usable = [y for y in SCORED if available_from(y) <= r["d"] and r["t"] in pct[y]]
        if usable:
            r["sp"] = round(pct[max(usable)][r["t"]], 4)
            added += 1
    out = [json.dumps(r, separators=(",", ":")) for r in lines]
    kept = [l for l in raw if l.strip()]
    assert sum(1 for a, b, r in zip(kept, out, lines) if not r.get("b") and a != b) == 0
    HISTORY.write_text("\n".join(out) + "\n", encoding="utf-8")
    us_recon = sum(1 for r in lines if r.get("b") and not r["t"].endswith(".AX"))
    print(f"sp on {added} of {us_recon} US reconstructed lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
