"""One-off, 07/10/2026: add the price-momentum leg ("m") to the RECONSTRUCTED days of the
record ("b": 1), so the forward test can score them on more than estimate revisions.

Why it is allowed when the strain and DCF legs are not: a 12-month share-price return as
at a date uses only prices up to that date, so it carries no hindsight. Strain came from
a later Shortfall snapshot and the DCF leg divides today's model value by the old price;
the page still drops those two for a reconstructed day.

Method: Yahoo monthly closes (adjusted). For a scoring date d, the end price is the last
monthly bar whose month has ENDED on or before d, and the start price is the bar twelve
months earlier. Ranked within market (ASX vs US) among the names on that date, as the
live leg is. The live leg reads Shortfall's 12-month return to the latest close, so the
two differ by up to a month at the end; stated, not hidden.

Only lines with "b": 1 are touched, and only by adding "m". Observed days are left
exactly as written. Rerunning is a no-op: a line that already has "m" is kept.

Run:  python crosscheck/backfill_momentum.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402

HISTORY = HERE / "history.jsonl"


def month_end_bar(index: pd.DatetimeIndex, d: pd.Timestamp):
    """The last monthly bar whose month ended on or before d (bars are labelled by month start)."""
    ok = [t for t in index if (t + pd.offsets.MonthEnd(0)) <= d]
    return ok[-1] if ok else None


def main() -> int:
    lines = [json.loads(l) for l in HISTORY.read_text(encoding="utf-8").splitlines() if l.strip()]
    targets = [r for r in lines if r.get("b") and r.get("m") is None]
    if not targets:
        print("nothing to do: every reconstructed line already has m")
        return 0
    tickers = sorted({r["t"] for r in targets})
    dates = sorted({r["d"] for r in targets})
    import yfinance as yf
    raw = yf.download(tickers, start="2024-01-01", interval="1mo", auto_adjust=True, progress=False, threads=True)
    px = raw["Close"]
    ret: dict = {}
    for d in dates:
        dt = pd.Timestamp(d)
        end = month_end_bar(px.index, dt)
        if end is None:
            continue
        start = end - pd.DateOffset(months=12)
        if start not in px.index:
            continue
        r = (px.loc[end] / px.loc[start] - 1).dropna()
        ret[d] = r.to_dict()
    added = 0
    by_date: dict = {}
    for r in targets:
        by_date.setdefault(r["d"], []).append(r)
    for d, rows in by_date.items():
        rr = ret.get(d, {})
        for mkt in ("AX", "US"):
            group = [r for r in rows if r["t"].endswith(".AX") == (mkt == "AX")]
            pcts = build._percentiles([rr.get(r["t"]) for r in group])
            for r, p in zip(group, pcts):
                if p is not None:
                    r["m"] = p
                    added += 1
    before = HISTORY.read_text(encoding="utf-8").splitlines()
    out = [json.dumps(r, separators=(",", ":")) for r in lines]
    # Observed lines must come back byte-identical.
    changed_observed = sum(1 for a, b, r in zip(before, out, lines) if not r.get("b") and a != b)
    assert changed_observed == 0, f"{changed_observed} observed lines would change"
    assert len(out) == len(before)
    HISTORY.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"added m to {added} of {len(targets)} reconstructed lines across {len(by_date)} dates; "
          f"{sum(1 for r in lines if not r.get('b'))} observed lines untouched")
    for d in dates:
        n = sum(1 for r in by_date[d] if r.get("m") is not None)
        print(f"  {d}: {n}/{len(by_date[d])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
