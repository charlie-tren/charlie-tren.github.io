"""Pull a quarterly consensus-EPS history for the 199-name sample from Bloomberg.

Runs on a machine with the Terminal logged in:   PYTHONIOENCODING=utf-8 python pull_eps.py
(blpapi from Bloomberg's own index plus xbbg, installed into Python 3.14 on 20/09/2026)
Writes bbg_eps.csv beside this file (ticker, date, best_eps). Commit the CSV; the
ingest step (ingest.py) turns it into history lines here, no Terminal needed.

COST, sized before writing this (bloomberg-data-pull skill, usage_limits.md):
  199 securities x 1 field x 7 quarterly dates = 1,393 hits if BDH counts dates,
  199 if it does not. One request, no retries. The probe below costs one hit and
  is there so a wrong field name or override fails on ONE name, not 199.

FIELD. BEST_EPS with BEST_FPERIOD_OVERRIDE=1BF: the blended-forward 12-month
consensus, which rolls smoothly through fiscal year-ends. The fiscal-year figure
(1FY) jumps the day the year rolls, and a 90-day change that straddles a roll is
the roll, not a revision. Consensus Drift runs on Yahoo's current-year estimate,
so the reconstructed leg is a close cousin of the live one rather than the same
number; the chart says "reconstructed" over that span for this reason as well.

Never resubmit "to retry": a failed request may still count. If it errors, read
the error, fix the cause, and run once more.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE = json.load(open(HERE / "sample.json", encoding="utf-8"))
OUT = HERE / "bbg_eps.csv"
START, END = "2025-03-31", "2026-06-30"   # seven quarter-ends inclusive
FIELD = "BEST_EPS"
OVERRIDE = {"BEST_FPERIOD_OVERRIDE": "1BF"}


def main() -> int:
    if OUT.exists():
        print(f"{OUT.name} already exists; delete it deliberately before pulling again")
        return 1
    from xbbg import blp
    import pandas as pd

    tickers = [SAMPLE["bloomberg"][t] for t in SAMPLE["tickers"]]
    back = {v: k for k, v in SAMPLE["bloomberg"].items()}

    # Probe: one name, one date, so a bad override fails for one hit.
    probe = blp.bdh(tickers[:1], FIELD, "2026-06-30", "2026-06-30", Per="Q", **OVERRIDE)
    print("probe:\n", probe)
    if probe is None or len(probe) == 0:
        print("probe returned nothing: check the field and override on FLDS <GO> before spending 199 more")
        return 1

    df = blp.bdh(tickers, FIELD, START, END, Per="Q", Days="A", Fill="P", **OVERRIDE)
    print(type(df))
    # The return shape varies by install (bloomberg-data-pull skill, 11/09/2026): a
    # Narwhals frame over a pyarrow table in long form here, a pandas MultiIndex
    # elsewhere. Print, then branch.
    try:
        long = df.to_native().to_pandas()          # ticker, date, field, value
        long = long.rename(columns={"value": "best_eps"})
    except AttributeError:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{t}__{f}" for t, f in df.columns]
        long = df.reset_index().melt(id_vars=df.index.name or "index", var_name="col", value_name="best_eps")
        long = long.rename(columns={long.columns[0]: "date"})
        long["ticker"] = long["col"].str.split("__").str[0]
    long["ticker"] = long["ticker"].map(back)
    long = long.dropna(subset=["best_eps", "ticker"])
    long["date"] = pd.to_datetime(long["date"]).dt.strftime("%Y-%m-%d")
    long[["ticker", "date", "best_eps"]].sort_values(["ticker", "date"]).to_csv(OUT, index=False)
    got = long["ticker"].nunique()
    print(f"wrote {OUT.name}: {len(long)} rows, {got} of {len(tickers)} names")
    missing = sorted(set(SAMPLE["tickers"]) - set(long["ticker"]))
    if missing:
        print("no data for:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
