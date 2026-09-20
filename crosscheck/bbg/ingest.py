"""Turn bbg_eps.csv into reconstructed history lines: five quarterly cohorts of the
199-name sample, three legs each, from 30 June 2025.

    python ingest.py            # needs bbg_eps.csv beside it, writes into history.jsonl
    python ingest.py --dry-run  # prints what it would write

WHAT EACH LEG IS AT A COHORT DATE
  - Drift: the 90-day estimate change is the blended-forward consensus at the
    quarter-end over the one before, and the price change is the close at the
    quarter-end over the one before, so the gap is the same arithmetic the page
    uses (estimate change less price change) on quarterly steps. Genuine as of
    each date, modulo the field being Bloomberg's 12-month blend rather than
    Yahoo's current-year figure.
  - Shortfall: the composite as Shortfall holds it today, from the accounts it
    holds today. For a cohort dated before those accounts were published this leg
    is look-ahead: a name whose FY2025 statements came out in February 2026 is
    scored on them at June 2025. Stated here and on the chart ("reconstructed").
  - DCF: today's published value per share over the close on the day. Today's
    model, that day's price; same liberty as the August backfill.
  Percentiles are struck within the sample on each date, as the page strikes them
  within its universe, so a fifth is a fifth of the 199.

PRICES come from Yahoo (yfinance, unadjusted close, native currency), cached to
prices.json so a rerun costs nothing. The move a cohort line measures is then
Yahoo close to Yahoo close until the daily record takes over, where it is DCF
Studio's price; the seam is a few cents on a quote, not a basis change.

Rerunning is a no-op for any cohort date already in the record.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build  # noqa: E402

SAMPLE = json.load(open(HERE / "sample.json", encoding="utf-8"))
CSV = HERE / "bbg_eps.csv"
PRICES = HERE / "prices.json"
QUARTERS = ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30"]
COHORTS = QUARTERS[1:]   # each needs the quarter before it for the 90-day change


def read_eps(path: Path = CSV) -> dict:
    """{ticker: {date: eps}} from the pull's CSV."""
    out: dict = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                out.setdefault(row["ticker"], {})[row["date"]] = float(row["best_eps"])
            except (ValueError, KeyError):
                continue
    return out


def fetch_prices(tickers: list, path: Path = PRICES) -> dict:
    """{ticker: {quarter_end: close}} - the last close on or before each date."""
    if path.exists():
        return json.load(open(path, encoding="utf-8"))
    import yfinance as yf
    import pandas as pd

    px = yf.download(tickers, start="2025-03-01", end="2026-07-05", auto_adjust=False, progress=False)["Close"]
    out: dict = {}
    for t in tickers:
        if t not in px.columns:
            continue
        s = px[t].dropna()
        out[t] = {}
        for q in QUARTERS:
            upto = s[s.index <= pd.Timestamp(q)]
            if len(upto):
                out[t][q] = round(float(upto.iloc[-1]), 4)
    json.dump(out, open(path, "w", encoding="utf-8"), indent=0)
    return out


def currency(ticker: str) -> str:
    return "AUD" if ticker.endswith(".AX") else "USD"


def cohort_lines(eps: dict, prices: dict, names: list, value: dict) -> list:
    """History lines for every cohort date, three legs, percentiles within the sample."""
    lines = []
    by_name = {n["ticker"]: n for n in names}
    for k, date in enumerate(COHORTS):
        prev = QUARTERS[k]
        drift = []
        for t in SAMPLE["tickers"]:
            e, p = eps.get(t, {}), prices.get(t, {})
            if not (e.get(date) and e.get(prev) and p.get(date) and p.get(prev)) or t not in by_name:
                continue
            if e[prev] <= 0 or e[date] <= 0:
                continue   # a change through zero is not a percentage
            rev = (e[date] / e[prev] - 1) * 100
            chg = (p[date] / p[prev] - 1) * 100
            drift.append({"ticker": t, "rev": round(rev, 2), "price": round(chg, 2), "gap": rev - chg})
        dcf = {t: value[t] / prices[t][date] for t in value if t in prices and prices[t].get(date)}
        rows = build.join([by_name[d["ticker"]] for d in drift], drift, dcf)
        for r in rows:
            lines.append(json.dumps({
                "d": date, "t": r["ticker"],
                "s": r["pStrain"], "r": r["pDrift"], "v": r["pDcf"], "e": r.get("pRev"),
                "p": prices[r["ticker"]][date], "c": currency(r["ticker"]), "b": 1,
            }, separators=(",", ":")))
        print(f"{date}: {len(rows)} names, {sum(1 for r in rows if r['dcf'] is not None)} with a DCF reading")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not CSV.exists():
        print(f"{CSV.name} not found: run pull_eps.py on the Terminal machine first")
        return 1
    eps = read_eps()
    prices = fetch_prices(SAMPLE["tickers"])
    names = [n for n in build.parse_shortfall(build.fetch(build.SHORTFALL_URL)) if n["ticker"] in SAMPLE["bloomberg"]]
    dcf_now = json.loads(build.fetch(build.DCF_URL))
    value = {t: ratio * dcf_now["prices"][t][0] for t, ratio in dcf_now["ratios"].items() if t in dcf_now["prices"]}
    print(f"eps for {len(eps)} names, prices for {len(prices)}, shortfall for {len(names)}, dcf for {sum(1 for t in SAMPLE['tickers'] if t in value)}")

    existing = set()
    if build.HISTORY.exists():
        with open(build.HISTORY, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    existing.add(json.loads(line)["d"])
    skip = [d for d in COHORTS if d in existing]
    if skip:
        print("already recorded, skipped:", ", ".join(skip))
    lines = [l for l in cohort_lines(eps, prices, names, value) if json.loads(l)["d"] not in existing]
    if args.dry_run or not lines:
        print(f"{len(lines)} lines{' (dry run, nothing written)' if args.dry_run else ''}")
        return 0
    old = build.HISTORY.read_text(encoding="utf-8") if build.HISTORY.exists() else ""
    merged = sorted([l for l in old.splitlines() if l.strip()] + lines, key=lambda l: json.loads(l)["d"])
    build.HISTORY.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} lines; the record now starts {json.loads(merged[0])['d']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
