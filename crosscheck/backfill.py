"""One-off: reconstruct the daily record back to 9 August 2026 from the sibling sites'
own committed snapshots, so the forward test starts five weeks before day one.

Run once, 20/09/2026. Rerunning is a no-op: a date already in the record is skipped.

WHAT IS RECONSTRUCTED, AND HOW HONESTLY
  - Drift: Consensus Drift commits data/latest.json weekly ("Weekly refresh"), each
    carrying the 90-day estimate change, the 90-day price change AND the price on the
    day, per company. Those are what the page reads today, at those dates. Genuine.
  - Shortfall: docs/data.json from the nearest committed snapshot at or before the
    date, else the earliest there is (14/08). The composite is built from annual
    accounts, so it barely moves week to week; using a five-day-later snapshot for
    9 August is a small, stated liberty.
  - DCF: the model's value per share is held at what DCF Studio publishes TODAY and
    divided by the price on the day. The accounts behind it were public throughout,
    but the MODEL is today's (Blume beta and the capex floor changed on 12/09), so
    the DCF leg carries look-ahead of a modelling kind, not of an information kind.
  Every reconstructed line carries "b": 1, and the chart labels the reconstructed
  span, so nobody reads five weeks of backfill as five weeks of observation.

The prices are Consensus Drift's price_now on each date, in the company's own
currency (USD for the US names, AUD for the ASX ones - the same basis as DCF
Studio's prices, which the daily lines use), so the first-to-latest move is between
two prices in one currency.
"""
import json
import subprocess
import sys
from pathlib import Path

import build

HERE = Path(__file__).resolve().parent
ESTATE = HERE.parent.parent
CD = ESTATE / "consensus-drift"
SF = ESTATE / "shortfall"

# Weekly refresh dates before the daily record began on 2026-09-12. The Shortfall
# snapshot used for each is the nearest at or before it.
DATES = ["2026-08-09", "2026-08-16", "2026-08-23", "2026-08-30", "2026-09-06"]


def git_show(repo: Path, date: str, path: str) -> str:
    rev = subprocess.run(["git", "-C", str(repo), "rev-list", "-1", f"--before={date}T23:59:59Z", "origin/main", "--", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    if not rev:
        rev = subprocess.run(["git", "-C", str(repo), "rev-list", "--reverse", "origin/main", "--", path],
                             capture_output=True, text=True, check=True).stdout.split()[0]
        print(f"  {path}: nothing at or before {date}, using the earliest ({rev[:8]})")
    return subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, text=True, check=True).stdout


def drift_rows(latest: dict) -> list[dict]:
    """latest.json names -> the shape the page's #rows carry, plus the price."""
    out = []
    for n in latest["names"]:
        if n.get("revision_pct") is None or n.get("price_chg_pct") is None:
            continue
        out.append({
            "ticker": n["ticker"], "rev": n["revision_pct"], "price": n["price_chg_pct"],
            "gap": n["revision_pct"] - n["price_chg_pct"], "mcap": n.get("mcap_bn"),
            "analysts": n.get("analysts"), "px": n.get("price_now"), "ccy": n.get("mcap_ccy"),
        })
    return out


def main() -> int:
    for r in (CD, SF):
        subprocess.run(["git", "-C", str(r), "fetch", "-q", "origin"], check=True)
    dcf_now = json.loads(build.fetch(build.DCF_URL))
    sector_now = {n["ticker"]: n["sector"] for n in build.parse_shortfall(build.fetch(build.SHORTFALL_URL))}
    value = {t: ratio * dcf_now["prices"][t][0] for t, ratio in dcf_now["ratios"].items() if t in dcf_now["prices"]}

    existing = set()
    if build.HISTORY.exists():
        with open(build.HISTORY, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    existing.add(json.loads(line)["d"])

    new_lines = []
    for date in DATES:
        if date in existing:
            print(f"{date}: already recorded, skipped")
            continue
        print(date)
        names = json.loads(git_show(SF, date, "docs/data.json"))["names"]
        # Sector arrived in Shortfall's data on 24/08; earlier snapshots take it from
        # the current file. A company not in today's file has no sector and is left out.
        for n in names:
            n.setdefault("sector", sector_now.get(n["ticker"]))
        names = [n for n in names if n.get("sector")]
        drift = drift_rows(json.loads(git_show(CD, date, "data/latest.json")))
        px = {d["ticker"]: (d["px"], d["ccy"]) for d in drift if d.get("px")}
        dcf = {t: value[t] / px[t][0] for t in value if t in px and px[t][0]}
        rows = build.join(names, drift, dcf)
        print(f"  {len(rows)} rows, {sum(1 for r in rows if r['dcf'] is not None)} with a DCF reading")
        for r in rows:
            p = px.get(r["ticker"])
            new_lines.append(json.dumps({
                "d": date, "t": r["ticker"],
                "s": r["pStrain"], "r": r["pDrift"], "v": r["pDcf"], "e": r.get("pRev"),
                "p": p[0] if p else None, "c": p[1] if p else None, "b": 1,
            }, separators=(",", ":")))
    if not new_lines:
        print("nothing to add")
        return 0
    # Prepend, so the file stays in date order and the same-day guard in
    # append_history (which reads the whole file) is unaffected.
    old = build.HISTORY.read_text(encoding="utf-8") if build.HISTORY.exists() else ""
    build.HISTORY.write_text("\n".join(new_lines) + "\n" + old, encoding="utf-8")
    print(f"wrote {len(new_lines)} reconstructed lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
