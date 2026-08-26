"""Render research/index.html from reports.json plus a live price for each name.

Run: python research/build.py

WHY A BUILD STEP: the page states a current price and a return since the call. Typed by
hand those are wrong within a day, and a stale "current price" on a page about
investment calls is worse than no price at all.

GUARD BEFORE WRITE: if a quote cannot be fetched, the previous one in prices.json is
reused and the page says when it was taken. The page is only refused outright if there
is no price at all for a name, because a row with a blank return would read as flat.

TARGET is optional per report and is NOT recomputed here. It is a judgement made in the
research at a point in time, so it belongs in reports.json beside the call rather than
being derived from a live price - a target that moved with the market would be worthless
as a record of what was actually claimed.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORTS = HERE / "reports.json"
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
                "price": round(float(hist["Close"].iloc[-1]), 4),
                "asof": str(hist.index[-1].date()),
            }
            fresh.append(sym)
        except Exception as exc:                       # noqa: BLE001 - any failure is the same failure
            print(f"  ! {sym}: {type(exc).__name__}: {exc}"[:120])
            if sym in cache:
                kept.append(sym)
    return fresh, kept


def tone(call):
    """Map a rating to a colour class. Direction, not decoration: green for a positive
    call, grey for a neutral one, red for a negative one, and a softer treatment where
    the wording hedges. Derived from the call TEXT so a new rating colours itself, with
    an explicit "tone" in reports.json winning if one is set."""
    if not call:
        return "none"
    c = call.lower()
    if any(w in c for w in ("sell", "reduce", "avoid", "underweight")):
        return "neg"
    if any(w in c for w in ("modest", "weak", "small", "tentative")):
        return "pos-soft"
    if any(w in c for w in ("buy", "accumulate", "overweight", "add")):
        return "pos"
    return "neutral"


def main():
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    data = json.loads(REPORTS.read_text(encoding="utf-8"))
    reports = data["reports"]
    cache = load_prices()

    symbols = sorted({r["symbol"] for r in reports if r.get("call_price")})
    fresh, kept = fetch(symbols, cache)
    print(f"  {len(fresh)} fetched, {len(kept)} reused from cache")

    missing = [s for s in symbols if s not in cache]
    if missing:
        sys.exit(f"ERROR: no price at all for {missing}. index.html left untouched.")

    rows = []
    for r in reports:
        row = dict(r)
        row["tone"] = r.get("tone") or tone(r.get("call"))
        q = cache.get(r["symbol"])
        if r.get("call_price") and q:
            row["price"] = q["price"]
            row["asof"] = q["asof"]
            row["ret"] = (q["price"] / r["call_price"] - 1) * 100
        rows.append(row)

    # newest first, so the most recent call leads
    rows.sort(key=lambda r: r["date"], reverse=True)

    def money(v, cur):
        return f"{cur}{v:,.2f}"

    env = Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(["html"]))
    env.filters["money"] = money
    html = env.get_template(TEMPLATE.name).render(
        rows=rows,
        built=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
        asof=max((r.get("asof") or "") for r in rows),
    )
    OUT.write_text(html, encoding="utf-8", newline="\n")
    PRICES.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"  wrote {OUT.relative_to(HERE.parent)} - {len(rows)} rows")


if __name__ == "__main__":
    main()
