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
import json, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "positions.json"
HISTORY = HERE / "history.json"
PRICES = HERE / "prices.json"
TEMPLATE = HERE / "template.html.j2"
OUT = HERE / "index.html"


def load_prices():
    if PRICES.exists():
        return json.loads(PRICES.read_text(encoding="utf-8"))
    return {}


def fetch(symbols, cache):
    """Update the cache in place. A failure leaves the previous value alone."""
    import yfinance as yf
    fresh, kept = [], []
    for sym in symbols:
        try:
            hist = yf.Ticker(sym).history(period="5d", auto_adjust=False)
            if not len(hist):
                raise ValueError("no rows")
            cache[sym] = {
                "price": round(float(hist["Close"].iloc[-1]), 5),
                "asof": str(hist.index[-1].date()),
            }
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

    # The record before this page existed. Written by build_history.py from the account
    # statements; absent is allowed, so the page still builds on a machine without them.
    hist = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else None
    if hist:
        # Derived here rather than stored, so the balance and the arithmetic can never
        # disagree: net_in is a fact about the statements, balance is a fact about today.
        bal = data["account"]["balance_aud"]
        hist["balance"] = bal
        hist["net_pnl"] = round(bal - hist["net_in"], 2)
        hist["net_pnl_pct"] = round(100 * (bal - hist["net_in"]) / hist["net_in"], 1)
        c = hist["costs"]
        hist["cost_share_of_loss"] = round(100 * abs(c["total"]) / abs(hist["net_pnl"]))
        hist["with_r"] = sum(1 for t in hist["trades"] if t["r"] is not None)
        wins = [t for t in hist["trades"] if t["move_pct"] > 0]
        hist["win_pct"] = round(100 * len(wins) / len(hist["trades"]))
        rs = [t["r"] for t in hist["trades"] if t["r"] is not None]
        hist["mean_r"] = round(sum(rs) / len(rs), 2) if rs else None

    def px(v, dp):
        return f"{v:,.{int(dp)}f}"

    def aud(v):
        """Sign in front of the currency, not between it and the digits: -A$4,690.50
        reads as a negative amount of money, A$-4,690.50 reads as a typo."""
        return f"{'-' if v < 0 else ''}A${abs(v):,.2f}"

    env = Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(["html"]))
    env.filters["px"] = px
    env.filters["aud"] = aud
    html = env.get_template(TEMPLATE.name).render(
        rows=rows,
        closed=shut,
        hist=hist,
        built=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
        asof=max((r.get("asof") or "") for r in rows) if rows else "",
    )
    OUT.write_text(html, encoding="utf-8", newline="\n")
    PRICES.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"  wrote {OUT.relative_to(HERE.parent)} - {len(rows)} open, {len(shut)} closed, "
          f"{len(hist['trades']) if hist else 0} historical")


if __name__ == "__main__":
    main()
