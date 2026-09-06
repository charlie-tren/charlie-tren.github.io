"""Checks on the shipped data.json that do not need the workbook.

    python test_data.py

build_data.py reads `source/International Property.xlsx`, which is gitignored, so CI
cannot rebuild data.json and diff it. What CI can do is check the parts of data.json
that have a second copy in the repo - the PwC rates - and the invariants the page's
arithmetic depends on.

The one that matters most is the merge. Every tax figure on the page comes from
rates_pwc.json via build_data.py, and if that merge ever drifts the page shows a rate
the source file does not carry, with no visible symptom: a wrong percentage looks
exactly like a right one. Thirty-four rows were read off PwC by hand to get these; a
silent drift would throw that away.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)
    return ok


data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
pwc = json.loads((HERE / "rates_pwc.json").read_text(encoding="utf-8"))

countries = data["countries"]
by_name = {c["country"]: c for c in countries}
rates = {k: v for k, v in pwc.items() if not k.startswith("_")}

# --- the two files describe the same 34 markets ---------------------------------
check(len(countries) == 34, f"expected 34 markets, data.json has {len(countries)}")
check(len(by_name) == len(countries), "data.json has a duplicated country name")
check(set(by_name) == set(rates),
      f"data.json and rates_pwc.json disagree on which markets exist: "
      f"only in data {sorted(set(by_name) - set(rates))}, "
      f"only in pwc {sorted(set(rates) - set(by_name))}")

# --- the merge is exact ----------------------------------------------------------
for name, src in sorted(rates.items()):
    row = by_name.get(name)
    if row is None:
        continue
    for kind in ("rent", "cgt"):
        for field in ("rate", "basis", "note"):
            want = (src.get(kind) or {}).get(field)
            got = row.get(f"{kind}_{field}")
            check(want == got,
                  f"{name}: {kind}_{field} is {got!r} in data.json but {want!r} in "
                  f"rates_pwc.json - build_data.py's merge has drifted")

# --- a rate must never be readable as zero when it is unknown --------------------
# app.js sorts an unusable rate last rather than as zero, "which would rank 'unknown'
# as 'tax free'". That only holds if a null basis never claims to be a usable one.
RENT_USABLE = {"gain", "gross", "net", "exempt"}
CGT_USABLE = {"gain", "exempt", "none"}
for name, src in sorted(rates.items()):
    for kind, usable in (("rent", RENT_USABLE), ("cgt", CGT_USABLE)):
        blk = src.get(kind) or {}
        basis, rate = blk.get("basis"), blk.get("rate")
        if basis in usable:
            check(rate is not None,
                  f"{name}: {kind} basis {basis!r} is one the page does arithmetic on, "
                  f"but the rate is null - the page would read it as a missing number "
                  f"on a market it thinks it can calculate")
        if rate is None:
            check(basis not in usable,
                  f"{name}: {kind} has no rate but claims basis {basis!r}")

# --- every market carries what the table and the map need ------------------------
REQUIRED = ["country", "gross_yield", "net_yield", "price_aud", "ease", "ease_parts",
            "ownership", "visa", "repatriation"]
for c in countries:
    for f in REQUIRED:
        check(c.get(f) not in (None, ""),
              f"{c.get('country')}: {f} is empty, and the table has a column for it")
    check(isinstance(c.get("ease"), (int, float)) and 0 <= c["ease"] <= 100,
          f"{c.get('country')}: ease is {c.get('ease')!r}, not a 0-100 score")

# --- every source the page cites has somewhere to point --------------------------
# Four rows carry "Various" rather than one page, and the renderer used to linkify
# that into href="https://Various" - five dead links on a page whose whole claim is
# that the numbers were checked. It now only linkifies something hostname-shaped, so
# what has to hold is that a row is EITHER followable OR honestly unlinked, never a
# link that goes nowhere. A fifth row was worse: two hosts in one field, semicolon
# separated, which could never have resolved.
import re

HOSTLIKE = re.compile(r"^(https?://)?[a-z0-9-]+(\.[a-z0-9-]+)+([/?#]|$)", re.I)
UNLINKED_OK = {"Various"}

for s in data["sources"]:
    for f in ("measure", "name", "url"):
        check(s.get(f), f"a source row is missing {f}: {s}")
    u = s.get("url", "")
    check(HOSTLIKE.match(u) or u in UNLINKED_OK,
          f"{s['measure']}: url is {u!r} - not a hostname the page can link to, and "
          f"not the plain 'Various' the renderer knows to leave as text")
    check(";" not in u and " " not in u.strip(),
          f"{s['measure']}: url {u!r} has more than one destination in it, so it "
          f"cannot resolve to anything")

if fails:
    print(f"FAILED ({len(fails)})")
    for f in fails:
        print("  -", f)
    sys.exit(1)

scale_rent = sum(1 for v in rates.values() if (v.get("rent") or {}).get("rate") is None)
scale_cgt = sum(1 for v in rates.values() if (v.get("cgt") or {}).get("rate") is None)
print(f"{len(countries)} markets, merge exact against rates_pwc.json")
print(f"shown as 'scale' rather than a rate: rent {scale_rent}, capital gains "
      f"{scale_cgt} - by design, those markets tax on a progressive schedule")
