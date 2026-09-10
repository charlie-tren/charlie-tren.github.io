"""Render positions/index.html from positions.json plus a live price for each holding.

Run: python position-record/build.py

WHY A BUILD STEP: the page states a live price and a distance to the stop. Typed by
hand those are wrong within a day, and a stale price beside a stop level is worse than
no price - it tells a reader a position is safe when it has already been taken out.

GUARD BEFORE WRITE: a failed fetch reuses the previous quote from prices.json and the
page says when it was taken. If there is no price at all for an open position the build
exits non-zero and index.html is left untouched, because a blank distance-to-stop reads
as "not close" rather than as "unknown".

SYMBOLS: Japan 225 is NIY=F, the yen Nikkei future, not ^N225. The spot index closes
with Tokyo while CMC's cash CFD tracks the future, so ^N225 measures about 0.8% away
from the platform - enough to put the stop distance visibly wrong.
"""
import json, math, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "positions.json"
PRICES = HERE / "prices.json"
TEMPLATE = HERE / "template.html.j2"
OUT = HERE / "index.html"


def usable(q):
    p = q.get("price")
    return isinstance(p, (int, float)) and not isinstance(p, bool) and math.isfinite(p) and p > 0


def load_prices():
    """A NaN that reached the file is not a price to reuse: drop it, so the
    missing-price guard fires instead of republishing "nan" for ever."""
    if PRICES.exists():
        cache = json.loads(PRICES.read_text(encoding="utf-8"))
        return {k: v for k, v in cache.items() if usable(v)}
    return {}


def fetch(symbols, cache):
    """Update the cache in place. A failure leaves the previous value alone."""
    import yfinance as yf
    fresh, kept = [], []
    for sym in symbols:
        try:
            hist = yf.Ticker(sym).history(period="5d", auto_adjust=False)
            if len(hist):
                hist = hist.dropna(subset=["Close"])
            if not len(hist):
                raise ValueError("no rows")
            # yfinance hands back a NaN close for a name it half-knows, and NaN
            # survives round(), json.dump and every sum after it.
            close = round(float(hist["Close"].iloc[-1]), 5)
            if not math.isfinite(close) or close <= 0:
                raise ValueError(f"close is {close!r}")
            cache[sym] = {"price": close, "asof": str(hist.index[-1].date())}
            fresh.append(sym)
        except Exception as exc:                       # noqa: BLE001 - any failure is the same failure
            print(f"  ! {sym}: {type(exc).__name__}: {exc}"[:120])
            if sym in cache:
                kept.append(sym)
    return fresh, kept


def enrich(p, price):
    """Derive everything the page shows from entry, stop and the live price.

    R is the unit throughout: 1R is the entry-to-stop distance, so a reader can compare
    a peso position with an index position without knowing the size of either, and the
    page discloses no position size and no account balance.
    """
    sign = 1 if p["direction"] == "Long" else -1
    risk = abs(p["entry"] - p["stop"])
    row = dict(p)
    row["move_pct"] = (price - p["entry"]) / p["entry"] * 100 * sign
    row["r"] = (price - p["entry"]) * sign / risk if risk else None
    row["price"] = price
    # Distance left to the stop, as a share of the original risk. 1.00 means untouched,
    # 0.00 means it is at the stop. This is the number that decides whether a position
    # is still live in any meaningful sense, and it is not visible from the P&L.
    row["stop_left"] = max(0.0, (price - p["stop"]) * sign / risk) if risk else None
    row["reward_r"] = (p["target"] - p["entry"]) * sign / risk if risk and p.get("target") else None
    return row


def main():
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    openp, closed = data["open"], data.get("closed", [])
    cache = load_prices()

    symbols = sorted({p["symbol"] for p in openp})
    fresh, kept = fetch(symbols, cache)
    print(f"  {len(fresh)} fetched, {len(kept)} reused from cache")

    missing = [s for s in symbols if s not in cache]
    if missing:
        sys.exit(f"ERROR: no price at all for {missing}. index.html left untouched.")

    rows = [enrich(p, cache[p["symbol"]]["price"]) for p in openp]
    for r, p in zip(rows, openp):
        r["asof"] = cache[p["symbol"]]["asof"]
    rows.sort(key=lambda r: r["entry_date"], reverse=True)

    shut = sorted(closed, key=lambda c: c["exit_date"], reverse=True)

    def px(v, dp, ccy=""):
        """A letter code needs a space before the digits; a glyph does not. CHF1.10
        reads as a typo, CHF 1.10 reads as a price."""
        gap = " " if ccy[-1:].isalpha() else ""
        return f"{ccy}{gap}{v:,.{int(dp)}f}"

    env = Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(["html"]))
    env.filters["px"] = px
    html = env.get_template(TEMPLATE.name).render(
        rows=rows,
        closed=shut,
        built=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
    )
    OUT.write_text(html, encoding="utf-8", newline="\n")
    PRICES.write_text(json.dumps(cache, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(f"  wrote {OUT.relative_to(HERE.parent)} - {len(rows)} open, {len(shut)} closed")


if __name__ == "__main__":
    main()
