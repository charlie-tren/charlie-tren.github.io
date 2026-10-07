"""Extend the consensus-EPS history back to 2021 for the forward test, in batches.

Run on the Terminal machine:   PYTHONIOENCODING=utf-8 python pull_history.py --batch 1

WHY BATCHES. Charlie, 07/10/2026: 5 years back, as economically as possible. BQL is not
licensed on this login, so every pull is a HistoricalDataRequest on the hit meter, which
Bloomberg counts at worst as securities x fields x dates and does not let us read back.
The 199-name sample is split once, at random and stratified by market (US / ASX), into
two halves; half A goes in two batches of ~50 (batch 1 today, batch 2 the next day), and
half B (batches 3 and 4) is next month's TODO. A random half is a fair sample of the
199; picking names by today's score would rebuild hindsight into the test.

COST, sized before writing this (bloomberg-data-pull skill): ~50 securities x 1 field x
16 quarter-ends (2021-03-31 to 2024-12-31) = ~800 hits worst case per batch. Every
request is appended to bbg_usage.csv with that arithmetic, the only after-the-fact
record available (no live meter; the CSC report is not reachable on this login).

FIELD. BEST_EPS with BEST_FPERIOD_OVERRIDE=1BF, as pull_eps.py: the blended-forward
12-month consensus, point-in-time at each quarter-end. Each quarter-end doubles as the
"90 days earlier" value for the next, so 16 dates give 15 cohorts.

Never resubmit a batch "to retry": a failed request may still count. A batch already in
the CSV is refused.
"""
import argparse
import csv
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE = json.load(open(HERE / "sample.json", encoding="utf-8"))
SPLIT = HERE / "history_split.json"
OUT = HERE / "bbg_eps_2021.csv"
USAGE = HERE / "bbg_usage.csv"
FIELD = "BEST_EPS"
OVERRIDE = {"BEST_FPERIOD_OVERRIDE": "1BF"}
START, END = "2021-03-31", "2024-12-31"
N_DATES = 16
SEED = 20261007


def split() -> dict:
    """The fixed split: half A (batches 1, 2) and half B (batches 3, 4), stratified by market."""
    if SPLIT.exists():
        return json.load(open(SPLIT, encoding="utf-8"))
    rng = random.Random(SEED)
    halves = {"A": [], "B": []}
    for mkt in ("US", "AX"):
        names = sorted(t for t in SAMPLE["tickers"] if t.endswith(".AX") == (mkt == "AX"))
        rng.shuffle(names)
        cut = (len(names) + 1) // 2
        halves["A"] += names[:cut]
        halves["B"] += names[cut:]
    out = {"seed": SEED, "drawn": "2026-10-07", "stratified_by": "market"}
    for h, b1, b2 in (("A", "1", "2"), ("B", "3", "4")):
        names = sorted(halves[h])
        rng.shuffle(names)
        mid = len(names) // 2
        out[b1], out[b2] = sorted(names[:mid]), sorted(names[mid:])
    json.dump(out, open(SPLIT, "w", encoding="utf-8"), indent=1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, choices=["1", "2", "3", "4"])
    args = ap.parse_args()
    names = split()[args.batch]
    have = set()
    if OUT.exists():
        with open(OUT, encoding="utf-8", newline="") as fh:
            have = {r["ticker"] for r in csv.DictReader(fh)}
    todo = [t for t in names if t not in have]
    if not todo:
        print(f"batch {args.batch} is already in {OUT.name}; refusing to pull it again")
        return 1
    tickers = [SAMPLE["bloomberg"][t] for t in todo]
    back = {SAMPLE["bloomberg"][t]: t for t in todo}
    worst = len(tickers) * 1 * N_DATES
    print(f"batch {args.batch}: {len(tickers)} securities x 1 field x {N_DATES} dates = {worst} hits worst case")

    from xbbg import blp
    import pandas as pd
    df = blp.bdh(tickers, FIELD, START, END, Per="Q", Days="A", Fill="P", **OVERRIDE)
    try:
        long = df.to_native().to_pandas().rename(columns={"value": "best_eps"})
    except AttributeError:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{t}__{f}" for t, f in df.columns]
        long = df.reset_index().melt(id_vars=df.index.name or "index", var_name="col", value_name="best_eps")
        long = long.rename(columns={long.columns[0]: "date"})
        long["ticker"] = long["col"].str.split("__").str[0]
    long["ticker"] = long["ticker"].map(back)
    long = long.dropna(subset=["best_eps", "ticker"])
    long["date"] = pd.to_datetime(long["date"]).dt.strftime("%Y-%m-%d")
    new = not OUT.exists()
    long[["ticker", "date", "best_eps"]].sort_values(["ticker", "date"]).to_csv(OUT, mode="a", header=new, index=False)
    got = long["ticker"].nunique()
    first = not USAGE.exists()
    with open(USAGE, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if first:
            w.writerow(["utc", "script", "batch", "securities", "fields", "dates", "worst_case_hits", "rows_returned", "names_returned"])
        w.writerow([datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "pull_history.py", args.batch,
                    len(tickers), 1, N_DATES, worst, len(long), got])
    print(f"appended {len(long)} rows for {got} of {len(tickers)} names to {OUT.name}; logged to {USAGE.name}")
    missing = sorted(set(todo) - set(long["ticker"]))
    if missing:
        print("no data for:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
