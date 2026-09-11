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
    # How far the target still is, in R. R itself covers the other end: a position
    # at -1R is at its stop. Not a restatement of R, because each position has its
    # own reward-to-risk, so two rows on the same R can have very different left
    # to run.
    row["to_target"] = (row["reward_r"] - row["r"]) if row["reward_r"] is not None else None
    if p.get("entry_date"):                 # the ISO date stays on the row, for sorting
        y, m, d = p["entry_date"].split("-")
        row["opened"] = f"{d}/{m}/{y}"
        row["opened_short"] = f"{d}/{m}/{y[2:]}"
    row.update(track(row["r"], row["reward_r"]))
    return row


def track(r, reward_r):
    """Where entry and the current price sit on a stop-to-target track, as percents.

    IN R-SPACE, not in price. The stop is -1R by construction and the target is a
    fixed R, so one track carries entry, stop, target and distance-to-target at once -
    and a short needs no inversion, because the left end is the losing end for both
    directions. Plotting price would put a short's target to the LEFT of its stop and
    invite exactly the misreading the R unit exists to prevent.
    """
    if r is None or reward_r is None or reward_r <= -1:
        return {"pct_now": None, "pct_entry": None}
    span = reward_r + 1                       # -1R .. +reward_r
    return {"pct_now": max(0.0, min(100.0, (r + 1) / span * 100)),
            "pct_entry": 1 / span * 100}


def shut_row(p):
    """A closed position, with R measured to the EXIT rather than to a live price.

    R is derived here and never read from the file. A typed R is a number that can
    disagree with the entry, stop and exit sitting beside it, and on a page whose
    whole claim is the record it is the one figure nobody could check.
    """
    for field in ("exit", "exit_date"):
        if p.get(field) in (None, ""):
            sys.exit(f"ERROR: {p['name']} is closed but has no {field}.")
    sign = 1 if p["direction"] == "Long" else -1
    risk = abs(p["entry"] - p["stop"])
    row = dict(p)
    row["r"] = (p["exit"] - p["entry"]) * sign / risk if risk else None
    row["move_pct"] = (p["exit"] - p["entry"]) / p["entry"] * 100 * sign
    row["reward_r"] = (p["target"] - p["entry"]) * sign / risk if risk and p.get("target") else None
    row["to_target"] = None                   # it is over; there is no distance left
    row["price"] = p["exit"]
    for key, src in (("opened", "entry_date"), ("closed", "exit_date")):
        y, m, d = p[src].split("-")
        row[key] = f"{d}/{m}/{y}"
        row[key + "_short"] = f"{d}/{m}/{y[2:]}"
    held = _days(p["entry_date"], p["exit_date"])
    row["held"] = f"{held} day{'s' if held != 1 else ''}"
    row.update(track(row["r"], row["reward_r"]))
    return row


def _days(a: str, b: str) -> int:
    from datetime import date
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def main():
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    try:
        from jinja2 import Markup
    except ImportError:          # jinja2 >= 3.1 moved it back to markupsafe
        from markupsafe import Markup

    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    # A POSITION IS CLOSED BECAUSE IT HAS AN EXIT, not because it was typed into the
    # other array. Charlie closes one by adding exit_date, exit and postmortem to the
    # entry where it already sits; this moves it. Keeping the two lists as the source
    # of truth meant cutting an object from one array and pasting it into another by
    # hand, which is a step that can be half-done - and a position left in `open`
    # with an exit on it would have been priced live and reported as still running.
    both = list(data.get("open") or []) + list(data.get("closed") or [])
    openp = [p for p in both if not p.get("exit_date")]
    closed = [p for p in both if p.get("exit_date")]
    names = [p["name"] for p in both]
    if len(set(names)) != len(names):
        dupe = sorted({n for n in names if names.count(n) > 1})
        sys.exit(f"ERROR: the same position appears twice: {', '.join(dupe)}.")
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

    shut = sorted((shut_row(c) for c in closed),
                  key=lambda c: c["exit_date"], reverse=True)

    def px(v, dp, ccy=""):
        """A letter code needs a space before the digits; a glyph does not. CHF1.10
        reads as a typo, CHF 1.10 reads as a price."""
        gap = " " if ccy[-1:].isalpha() else ""
        return f"{ccy}{gap}{v:,.{int(dp)}f}"

    def rail(p):
        """The stop-to-target track, as markup. Empty when the geometry is unknown.

        Built here rather than in CSS because the two positions on it are data: a
        percentage along the track cannot be expressed as a class.
        """
        if p.get("pct_now") is None:
            return Markup("")
        cls = "up" if (p.get("r") or 0) >= 0 else "dn"
        now, ent = p["pct_now"], p["pct_entry"]
        lo, hi = sorted((ent, now))
        ends = (f'<span class="lo">{px(p["stop"], p["dp"], p["ccy"])}<i>stop</i></span>'
                f'<span class="hi">{px(p["target"], p["dp"], p["ccy"])}<i>target</i></span>')
        return Markup(
            f'<div class="rail" aria-hidden="true">'
            f'<span class="trk"></span>'
            f'<span class="fil {cls}" style="left:{lo:.2f}%;width:{hi - lo:.2f}%"></span>'
            f'<span class="tk" style="left:{ent:.2f}%"></span>'
            f'<span class="dot {cls}" style="left:{now:.2f}%"></span>'
            f'</div><div class="ends">{ends}</div>')

    env = Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(["html"]))
    env.filters["px"] = px
    env.globals["rail"] = rail
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
