"""Derive history.json from CMC account statement exports.

Run: python position-record/build_history.py "C:/path/to/History*.csv"

The exports themselves are NOT committed: they carry the running account balance on
every row and a lot else besides. What is committed is this script and its output, so
the numbers on the page can be re-derived by anyone holding the same statements.

WHAT IT COMPUTES

  Cash flows       Payment In and Withdrawal rows. Net contributions against the
                   current balance is the only honest measure of what the account did,
                   because two withdrawals took money off the table rather than losing it.

  Costs            Commission Charge, Holding Cost and Market Data rows, summed. These
                   are the finding: they are 56% of the loss, and every dollar of the
                   commission is on share CFDs, which is why the page splits it that way.

  Trades           Paired by order number: an opening trade row and the last closing row
                   sharing it. R is computable only where a stop was recorded at or near
                   the open, which is roughly half of them, so the field is nullable and
                   the page must not print a zero in its place.

CAVEAT THE PAGE MUST CARRY: the paired trades do not sum to the cash-flow loss. They
miss positions opened or closed outside the export windows, and they exclude the costs
above. The cash-flow figure is the account's real result; the trade list is a partial
view of how it got there, and is labelled as such.
"""
import csv, glob, io, json, sys, collections, datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent / "history.json"

OPEN_T = {"Buy Trade", "Sell Trade", "SE Order Buy Trade", "SE Order Sell Trade",
          "Limit Order Buy Trade", "Limit Order Sell Trade"}
CLOSE_T = {"Close Trade", "Stop Loss", "Take Profit", "Liquidation"}
COST_T = {"Commission Charge", "Holding Cost", "Market Data Charge", "Market Data Rebate"}


def num(s):
    s = (s or "").strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def when(s):
    return datetime.datetime.strptime(s.strip(), "%d %b %Y %H:%M:%S")


def load(patterns):
    """Statement exports overlap, so rows are deduped on the fields that identify an
    event. Balance is deliberately not in the key: the same event can be restated."""
    rows, seen = [], set()
    for pat in patterns:
        for f in sorted(glob.glob(pat)):
            for r in list(csv.reader(io.open(f, encoding="utf-8-sig")))[1:]:
                if len(r) < 22:
                    continue
                k = (r[0], r[1], r[2], r[3], r[5], r[6], r[7])
                if k in seen:
                    continue
                seen.add(k)
                rows.append(r)
    rows.sort(key=lambda r: when(r[0]))
    return rows


def is_share_cfd(product):
    """FX pairs, cash indices and cash commodities carry no commission at CMC. Everything
    else here is a share CFD. Checked against the data: 205 commission charges, all on
    this side of the split, none on the other."""
    p = product.strip()
    if len(p) == 7 and p[3] == "/" and p.replace("/", "").isalpha() and p.isupper():
        return False
    return not any(t in p for t in ("Cash", " Index", "225", " 40 ", " 30 "))


def cash_flows(rows):
    events = []
    for r in rows:
        if r[1] in ("Payment In", "Withdrawal"):
            events.append({"date": when(r[0]).date().isoformat(), "kind": r[1],
                           "amount": num(r[14]) or 0.0})
    uniq, seen = [], set()
    for e in events:
        k = (e["date"], e["kind"], e["amount"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    return uniq


def costs(rows):
    out = collections.defaultdict(float)
    n = collections.Counter()
    by_side = collections.defaultdict(float)
    bytime = collections.defaultdict(list)
    for r in rows:
        bytime[r[0]].append(r)
    for r in rows:
        if r[1] not in COST_T:
            continue
        v = num(r[20]) if r[1] == "Holding Cost" else num(r[14])
        v = v or 0.0
        out[r[1]] += v
        n[r[1]] += 1
        if r[1] == "Commission Charge":
            peers = [x for x in bytime[r[0]]
                     if x[1] != "Commission Charge" and x[5] not in ("", "-", "Account")]
            prod = peers[0][5] if peers else r[5]
            by_side["share" if is_share_cfd(prod) else "macro"] += v
    return dict(out), dict(n), dict(by_side)


def trades(rows):
    by_order = collections.defaultdict(list)
    stops = collections.defaultdict(list)
    for r in rows:
        if r[1] in OPEN_T or r[1] in CLOSE_T:
            by_order[r[2]].append(r)
        if r[9] not in ("", "-"):
            stops[r[2]].append((when(r[0]), num(r[9])))

    out = []
    for order, evs in by_order.items():
        opens = [e for e in evs if e[1] in OPEN_T]
        closes = [e for e in evs if e[1] in CLOSE_T]
        if not opens or not closes:
            continue
        op, cl = opens[0], closes[-1]
        ep, xp = num(op[7]), num(cl[7])
        if ep is None or xp is None or ep == 0:
            continue
        direction = "Short" if "Sell" in op[1] else "Long"
        sign = 1 if direction == "Long" else -1

        # The stop that was live at the open. A stop set later is a trail, not the risk
        # that was accepted, so R measured against it would flatter the trade.
        stop = None
        for t, s in sorted(stops.get(order, []), key=lambda x: x[0]):
            if t <= when(op[0]) + datetime.timedelta(seconds=90):
                stop = s
        r_mult = None
        if stop and abs(ep - stop) > 1e-12:
            r_mult = round((xp - ep) * sign / abs(ep - stop), 2)

        out.append({
            "product": op[5].strip(),
            "direction": direction,
            "entry_date": when(op[0]).date().isoformat(),
            "exit_date": when(cl[0]).date().isoformat(),
            "hold_days": (when(cl[0]) - when(op[0])).days,
            "move_pct": round((xp - ep) / ep * 100 * sign, 2),
            "r": r_mult,
        })
    out.sort(key=lambda t: t["exit_date"], reverse=True)
    return out


def main():
    patterns = sys.argv[1:] or ["C:/Users/charl/Downloads/History*.csv"]
    rows = load(patterns)
    if not rows:
        sys.exit(f"ERROR: no statement rows matched {patterns}. history.json left untouched.")

    flows = cash_flows(rows)
    cost, ncost, comm_side = costs(rows)
    tr = trades(rows)

    paid_in = sum(f["amount"] for f in flows if f["kind"] == "Payment In")
    taken_out = sum(f["amount"] for f in flows if f["kind"] == "Withdrawal")
    balances = [(when(r[0]), num(r[15])) for r in rows if num(r[15]) is not None]
    peak = max(balances, key=lambda b: b[1])

    data = {
        "_generated_by": "position-record/build_history.py from CMC account statement exports",
        "_caveat": ("The paired trades do not sum to the cash-flow result: they miss "
                    "positions opened or closed outside the export windows, and they "
                    "exclude commission and holding costs. Net contributions against "
                    "the balance is the account's real result."),
        "first_row": when(rows[0][0]).date().isoformat(),
        "last_row": when(rows[-1][0]).date().isoformat(),
        "paid_in": round(paid_in, 2),
        "paid_in_count": sum(1 for f in flows if f["kind"] == "Payment In"),
        "taken_out": round(taken_out, 2),
        "net_in": round(paid_in + taken_out, 2),
        # Prose on the page quotes this. Computed, never typed: the sentence about paying
        # commission to hold something for a few days is only true while it stays small.
        "median_hold_days": (sorted(t["hold_days"] for t in tr)[len(tr) // 2]) if tr else None,
        "peak_balance": round(peak[1], 2),
        "peak_date": peak[0].date().isoformat(),
        "zeroed": sorted({d.date().isoformat() for d, b in balances if b == 0.0}),
        "costs": {
            "commission": round(cost.get("Commission Charge", 0), 2),
            "commission_charges": ncost.get("Commission Charge", 0),
            "commission_on_share_cfds": round(comm_side.get("share", 0), 2),
            "commission_on_macro": round(comm_side.get("macro", 0), 2),
            "holding": round(cost.get("Holding Cost", 0), 2),
            "holding_charges": ncost.get("Holding Cost", 0),
            "market_data": round(cost.get("Market Data Charge", 0) + cost.get("Market Data Rebate", 0), 2),
        },
        "trades": tr,
    }
    data["costs"]["total"] = round(
        data["costs"]["commission"] + data["costs"]["holding"] + data["costs"]["market_data"], 2)

    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"  {len(rows)} statement rows -> {len(tr)} paired trades, "
          f"{len([t for t in tr if t['r'] is not None])} with a stop at entry")
    print(f"  net in {data['net_in']:,.2f}   costs {data['costs']['total']:,.2f}   wrote {OUT.name}")


if __name__ == "__main__":
    main()
