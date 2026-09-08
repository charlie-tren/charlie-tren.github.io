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
import classify
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

# --- the merge is exact WHERE PWC HAS A RATE -------------------------------------
# It used to require data.json to equal rates_pwc.json field for field, including
# its nulls. That is what made 32 tax cells unfixable without failing the suite:
# PwC not stating a rate had become a requirement that the page not show one. PwC
# still WINS wherever it carries a rate - that is what this asserts - but where it
# is silent, resolve_taxes fills the cell from the market's own tax note and the
# check for that lives in resolve_taxes.apply(check=True), below.
for name, src in sorted(rates.items()):
    row = by_name.get(name)
    if row is None:
        continue
    for kind in ("rent", "cgt"):
        want_rate = (src.get(kind) or {}).get("rate")
        if not isinstance(want_rate, (int, float)):
            continue
        for field in ("rate", "basis", "note"):
            want = (src.get(kind) or {}).get(field)
            got = row.get(f"{kind}_{field}")
            check(want == got,
                  f"{name}: {kind}_{field} is {got!r} in data.json but {want!r} in "
                  f"rates_pwc.json - PwC wins where it states a rate, and this drifted")

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

# WHAT THIS USED TO SAY, and why it is worth the extra thirty lines:
#
#   print("shown as 'scale' rather than a rate: rent 21, capital gains 11
#          - by design, those markets tax on a progressive schedule")
#
# It was not by design and over half of them were not progressive. Albania's cell
# reads "15%", Hungary's "15% flat", Malaysia's "30% flat", Oman's "0%", Greece's
# gain cell reads "Exempt". The rate was in data.json all along, in the column
# beside PwC's null, and the page was rendering the null as "scale". A test that
# ASSERTS a comfortable reason for a gap will hide it for as long as it runs; this
# one counts, names, and re-derives instead.

import resolve_taxes  # noqa: E402

if resolve_taxes.apply(check=True) != 0:
    print("FAILED: data.json no longer agrees with the sources - run resolve_taxes.py")
    sys.exit(1)

import re  # noqa: E402

no_rate = [(c["country"], kind, c[f"{kind}_range"],
            c["rental_tax_text"] if kind == "rent" else c["cgt_text"])
           for c in countries for kind in ("rent", "cgt") if c[f"{kind}_rate"] is None]

# EVERY tax cell shows a figure. A cell with neither a rate nor a range would be
# blank, and a blank in this column reads as missing data rather than as a range.
blank = [(n, k) for n, k, rng, _ in no_rate if not rng]
if blank:
    print(f"FAILED: {len(blank)} cell(s) have neither a rate nor a range: {blank[:5]}")
    sys.exit(1)

# Every number in a displayed range must appear in the source text. This is the
# check that would have caught the two real bugs in building them: a range regex
# that read "15-45%" as a flat 45 because only the second number carried the
# percent sign, and a deemed cell whose 5.5% deemed RETURN was being read as the
# bottom of a tax range.
for name, kind, rng, text in no_rate:
    for n in re.findall(r"\d+(?:\.\d+)?", rng):
        check(n in (text or ""),
              f"{name} {kind}: shows {rng} but {n} is not in the source cell {text!r}")

# And no word may reach the column. The vocabulary is gone on purpose.
words = [(n, k, rng) for n, k, rng, _ in no_rate if re.search(r"[a-z]", rng, re.I)]
if words:
    print(f"FAILED: a tax cell still shows a word rather than figures: {words[:3]}")
    sys.exit(1)

# --- the published ease score must be reproducible from its own six parts -------
# The note on the page states the formula (six parts, 0 to 3, out of 18) and
# derives the divisor from the data. If a seventh part or a wider band is ever
# added, the note follows automatically and this catches any score that does not.
cap = max(p["score"] for c in countries for p in c["ease_parts"].values())
for c in countries:
    ps = c["ease_parts"]
    want = round(sum(p["score"] for p in ps.values()) / (len(ps) * cap) * 100)
    check(c["ease"] == want,
          f"{c['country']}: ease is {c['ease']} but its {len(ps)} parts sum to {want}")
check(len({len(c["ease_parts"]) for c in countries}) == 1,
      "the markets do not all carry the same number of ease parts")

src = {}
for c in countries:
    for kind in ("rent", "cgt"):
        src[c[f"{kind}_src"]] = src.get(c[f"{kind}_src"], 0) + 1

print(f"{len(countries)} markets, merge exact against rates_pwc.json")
print(f"{len(countries) * 2} tax cells: " + ", ".join(f"{v} {k}" for k, v in sorted(src.items())))
print(f"  {len(no_rate)} show the source's own range: "
      + ", ".join(f"{n} {rng}" for n, _, rng, _ in no_rate[:5]) + ", ...")

# PwC and the workbook disagreeing is a finding, not a rounding difference. It is
# printed rather than failed because PwC wins by precedence either way, but a
# reader of this output should know the two sources are 15 points apart on Georgia.
gaps = []
for c in countries:
    for kind, tkey in (("rent", "rental_tax_text"), ("cgt", "cgt_text")):
        if c[f"{kind}_src"] != "pwc":
            continue
        alt, _ = classify.tax_from_text(c.get(tkey))
        if alt is not None and abs(alt - c[f"{kind}_rate"]) > 0.6:
            gaps.append(f"{c['country']} {kind}: PwC {c[f'{kind}_rate']} vs cell {alt}")
if gaps:
    print(f"  PwC and the cell disagree on {len(gaps)}, PwC used: " + "; ".join(gaps))
