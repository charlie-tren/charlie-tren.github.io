"""Turn bbg_eps_2021.csv into reconstructed cohorts for 2021-2024 (15 quarter-ends).

    python ingest_history.py            # writes into history.jsonl
    python ingest_history.py --dry-run

POINT-IN-TIME LEGS ONLY. Each cohort carries the drift leg (the 90-day estimate change
over the quarter, less the price change over the same quarter, and the estimate change
itself) and the price-momentum leg (12-month return to the cohort date). No strain and
no DCF reading: neither exists as it stood then, and the page scores a reconstructed day
without them anyway. Lines are flagged "b": 1 (reconstructed) and "x": 1 (the extended
2021-2024 record), so the table's "move since first scored" can ignore them while the
forward-test chart uses them.

REGENERATED, NOT APPENDED. Every run deletes the "x" lines and writes them again from the
whole CSV, because each batch (pull_history.py) adds names to cohort dates that already
exist, and percentiles have to be struck across every name on the date.

PRICES: Yahoo, split-adjusted close (yfinance auto_adjust=False "Close"), the last close
on or before each date, cached to prices_2021.json. Split-adjusted matters over five
years: an unadjusted series turns a 10-for-1 split into a 90% fall.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build  # noqa: E402

CSV = HERE / "bbg_eps_2021.csv"
PRICES = HERE / "prices_2021.json"
QUARTERS = ["2021-03-31", "2021-06-30", "2021-09-30", "2021-12-31", "2022-03-31", "2022-06-30",
            "2022-09-30", "2022-12-31", "2023-03-31", "2023-06-30", "2023-09-30", "2023-12-31",
            "2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"]
COHORTS = QUARTERS[1:]


def year_before(q: str) -> str:
    y, m, d = q.split("-")
    return f"{int(y) - 1}-{m}-{d}"


def quarter_end(d: str) -> str:
    """Bloomberg returns the last TRADING day for a quarter that ends on a weekend
    (2022-12-30, 2023-09-29); snap it to the calendar quarter-end the cohorts use."""
    y, m = int(d[:4]), int(d[5:7])
    qm = ((m - 1) // 3 + 1) * 3
    return {3: f"{y}-03-31", 6: f"{y}-06-30", 9: f"{y}-09-30", 12: f"{y}-12-31"}[qm]


def read_eps(path: Path = CSV) -> dict:
    out: dict = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                out.setdefault(row["ticker"], {})[quarter_end(row["date"])] = float(row["best_eps"])
            except (ValueError, KeyError):
                continue
    return out


def fetch_prices(tickers: list, path: Path = PRICES) -> dict:
    cached = json.load(open(path, encoding="utf-8")) if path.exists() else {}
    need = [t for t in tickers if t not in cached]
    if need:
        import yfinance as yf
        import pandas as pd
        px = yf.download(need, start="2020-03-01", end="2025-01-10", auto_adjust=False, progress=False)["Close"]
        if isinstance(px, pd.Series):
            px = px.to_frame(need[0])
        dates = sorted(set(QUARTERS) | {year_before(q) for q in COHORTS})
        for t in need:
            if t not in px.columns:
                continue
            s = px[t].dropna()
            cached[t] = {}
            for q in dates:
                upto = s[s.index <= pd.Timestamp(q)]
                if len(upto):
                    cached[t][q] = round(float(upto.iloc[-1]), 4)
        json.dump(cached, open(path, "w", encoding="utf-8"), indent=0)
    return cached


def cohort_lines(eps: dict, prices: dict) -> list:
    lines = []
    for k, date in enumerate(COHORTS):
        prev, yb = QUARTERS[k], year_before(date)
        rows = []
        for t in sorted(eps):
            e, p = eps[t], prices.get(t, {})
            if not (e.get(date) and e.get(prev) and p.get(date) and p.get(prev)):
                continue
            if e[prev] <= 0 or e[date] <= 0:
                continue   # a change through zero is not a percentage
            rev = (e[date] / e[prev] - 1) * 100
            chg = (p[date] / p[prev] - 1) * 100
            mom = (p[date] / p[yb] - 1) if p.get(yb) else None
            rows.append({"t": t, "gap": rev - chg, "rev": rev, "mom": mom})
        g = build._percentiles([r["gap"] for r in rows])
        e = build._percentiles([r["rev"] for r in rows])
        m = [None] * len(rows)
        for mkt in ("AX", "US"):
            idx = [i for i, r in enumerate(rows) if r["t"].endswith(".AX") == (mkt == "AX")]
            for i, pct in zip(idx, build._percentiles([rows[i]["mom"] for i in idx])):
                m[i] = pct
        for r, pg, pe, pm in zip(rows, g, e, m):
            lines.append({"d": date, "t": r["t"], "s": None, "r": pg, "v": None, "e": pe, "m": pm,
                          "p": prices[r["t"]][date], "c": "AUD" if r["t"].endswith(".AX") else "USD",
                          "b": 1, "x": 1})
        print(f"{date}: {len(rows)} names")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    eps = read_eps()
    prices = fetch_prices(sorted(eps))
    print(f"eps for {len(eps)} names, prices for {sum(1 for t in eps if t in prices)}")
    new = cohort_lines(eps, prices)
    old = [l for l in build.HISTORY.read_text(encoding="utf-8").splitlines() if l.strip()]
    kept = [l for l in old if '"x":1' not in l]
    if args.dry_run:
        print(f"would replace {len(old) - len(kept)} extended lines with {len(new)}")
        return 0
    merged = sorted(kept + [json.dumps(r, separators=(",", ":")) for r in new], key=lambda l: json.loads(l)["d"])
    build.HISTORY.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print(f"replaced {len(old) - len(kept)} extended lines with {len(new)}; record starts {json.loads(merged[0])['d']}; "
          f"{len(kept)} other lines kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
