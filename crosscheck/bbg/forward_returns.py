"""Add each reconstructed line's 1-month forward move ("f1") from daily prices.

    python crosscheck/bbg/forward_returns.py      # after ingest_history.py, every time

Why: the 1-Month Move chart (Charlie, 07/10/2026) takes every SCORING date - the
reconstructed quarter-ends and the August weekly cohorts - splits that date's names into
quintiles at the current weights, and plots each quintile's move over the next month.
The record itself only holds prices at its own dates (quarterly before 2025), so the
month has to come from daily closes: the last close on or before the scoring date, to
the last close on or before 30 calendar days later. Split-adjusted (yfinance
auto_adjust=False "Close"). A line whose month has not finished yet gets no "f1".

Only "b": 1 lines are touched, and only the "f1" key; observed lines come back
byte-identical (asserted). ingest_history.py regenerates the "x" lines without "f1", so
run this after it.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
HISTORY = HERE.parent / "history.jsonl"
CACHE = HERE / "daily_closes.pkl"


def main() -> int:
    raw = HISTORY.read_text(encoding="utf-8").splitlines()
    lines = [json.loads(l) for l in raw if l.strip()]
    recon = [r for r in lines if r.get("b")]
    tickers = sorted({r["t"] for r in recon})
    first = min(r["d"] for r in recon)
    if CACHE.exists():
        px = pd.read_pickle(CACHE)
        missing = [t for t in tickers if t not in px.columns]
    else:
        px, missing = None, tickers
    if missing or px is None or px.index.max() < pd.Timestamp(date.today() - timedelta(days=3)):
        import yfinance as yf
        got = yf.download(tickers, start=(pd.Timestamp(first) - pd.Timedelta(days=10)).strftime("%Y-%m-%d"),
                          auto_adjust=False, progress=False, threads=True)["Close"]
        px = got
        px.to_pickle(CACHE)
    today = pd.Timestamp(date.today())
    added = cleared = 0
    for r in recon:
        d = pd.Timestamp(r["d"])
        end = d + pd.Timedelta(days=30)
        r.pop("f1", None)
        if end > today or r["t"] not in px.columns:
            cleared += 1
            continue
        s = px[r["t"]].dropna()
        a, b = s[s.index <= d], s[s.index <= end]
        if len(a) and len(b) and b.index[-1] > a.index[-1]:
            r["f1"] = round(float(b.iloc[-1] / a.iloc[-1] - 1), 5)
            added += 1
    out = [json.dumps(r, separators=(",", ":")) for r in lines]
    kept = [l for l in raw if l.strip()]
    changed_obs = sum(1 for a, b, r in zip(kept, out, lines) if not r.get("b") and a != b)
    assert changed_obs == 0, f"{changed_obs} observed lines would change"
    HISTORY.write_text("\n".join(out) + "\n", encoding="utf-8")
    dates = sorted({r["d"] for r in recon if "f1" in r})
    print(f"f1 on {added} of {len(recon)} reconstructed lines ({cleared} month not finished or no price); "
          f"{len(dates)} start dates, {dates[0]} .. {dates[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
