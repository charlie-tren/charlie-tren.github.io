"""Fill the tax cells PwC's guides did not state, and name what is left.

    python resolve_taxes.py           # patch data.json in place
    python resolve_taxes.py --check   # fail if data.json is out of step

WHAT THIS FIXED. rates_pwc.json carries `rate: null` for 21 of 34 rent cells and
11 of 34 gain cells, each noted "not stated for non-residents on PwC". The page
printed the word "scale" for every one, and test_data.py reported them as
"by design, those markets tax on a progressive schedule". Over half were nothing
of the kind: Albania's cell reads "15%", Hungary's "15% flat", Malaysia's
"30% flat", Oman's "0%", Greece's gain cell reads "Exempt". The figure was
already in data.json, in the column beside the null, and the page was reading the
null. Charlie: "why does table have scale, none. surely we can find this data".

THE ORDER OF PRECEDENCE, and nothing else may set a rate:
  1. rates_pwc.json, where PwC was actually read.
  2. rates_workbook.json, for the eight cells that needed a judgement rather
     than a parser. Each carries its quote and which stated rule applied.
  3. classify.tax_from_text, for any cell stating one rate plainly. Narrow on
     purpose: a range, a slash, an "or" or a deemed basis is left alone.
Anything still unresolved gets a WORD that says which kind of unresolved it is -
banded, deemed, 2 regimes - because "scale" was standing in for three different
answers.

IDEMPOTENT BY CONSTRUCTION: every value is re-derived from `rental_tax_text` and
`cgt_text`, which this script never writes. Running it twice cannot compound,
which is the failure a previous --apply pass on another project shipped.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import classify

HERE = Path(__file__).parent
DATA = HERE / "data.json"
PWC = HERE / "rates_pwc.json"
WORKBOOK = HERE / "rates_workbook.json"

KINDS = (("rent", "rental_tax_text"), ("cgt", "cgt_text"))


def resolve(country: dict, pwc: dict, wb: dict) -> dict:
    """The four fields each tax kind contributes, for one market."""
    out = {}
    for kind, tkey in KINDS:
        entry = (pwc.get(country["country"]) or {}).get(kind) or {}
        rate, basis, src = entry.get("rate"), entry.get("basis"), "pwc"

        if not isinstance(rate, (int, float)):
            hand = (wb.get(country["country"]) or {}).get(kind)
            if hand:
                rate, basis, src = hand["rate"], hand["basis"], "workbook"
            else:
                rate, basis = classify.tax_from_text(country.get(tkey))
                src = "text" if rate is not None else "none"

        out[f"{kind}_rate"] = rate
        out[f"{kind}_basis"] = basis
        out[f"{kind}_src"] = src

        # NO SINGLE RATE MEANS A RANGE, NOT A WORD. This used to write "banded",
        # "deemed" or "2 regimes", and Charlie asked what they meant and why they
        # were formatted differently from the numbers. Fair: they were a glossary
        # standing in front of figures the source had already stated. A cell with
        # no one rate now shows the span the source gives - "15-45%", "25 / 35%" -
        # and needs no explaining. `_low` is the bottom of it and is what the
        # column sorts on, because the bottom is stated and a midpoint is not.
        hand = (wb.get(country["country"]) or {}).get(kind) or {}
        if rate is not None:
            out[f"{kind}_range"], out[f"{kind}_low"] = "", None
        elif hand.get("range"):
            out[f"{kind}_range"], out[f"{kind}_low"] = hand["range"], hand.get("low")
        else:
            rng, low = classify.tax_range(country.get(tkey))
            out[f"{kind}_range"], out[f"{kind}_low"] = rng or "", low
    return out


def apply(check: bool = False) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    pwc = json.loads(PWC.read_text(encoding="utf-8"))
    wb = json.loads(WORKBOOK.read_text(encoding="utf-8"))

    #: Fields this script used to write and no longer manages. Without this they
    #: sit in data.json for ever holding their last value: the retired `_word`
    #: keys stayed behind after the words were replaced by ranges, and test_data
    #: went on printing "9 banded, 2 deemed" off values nothing produced any more.
    RETIRED = ("rent_word", "cgt_word")

    stale = []
    for c in data["countries"]:
        for dead in RETIRED:
            if dead in c:
                stale.append(f"{c['country']}.{dead}: dropped")
                if not check:
                    del c[dead]
        want = resolve(c, pwc, wb)
        for k, v in want.items():
            if c.get(k) != v:
                stale.append(f"{c['country']}.{k}: {c.get(k)!r} -> {v!r}")
            c[k] = v

    if check:
        if stale:
            print(f"data.json is out of step with the sources, {len(stale)} field(s):")
            for line in stale[:8]:
                print("  " + line)
            return 1
        print("data.json agrees with rates_pwc.json, rates_workbook.json and the cell text")
        return 0

    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    have = {k: 0 for k in ("pwc", "workbook", "text", "none")}
    ranges = 0
    for c in data["countries"]:
        for kind, _ in KINDS:
            have[c[f"{kind}_src"]] += 1
            if c[f"{kind}_range"]:
                ranges += 1
    total = len(data["countries"]) * 2
    print(f"{total} tax cells: {have['pwc']} from PwC, {have['workbook']} judged, "
          f"{have['text']} read off the cell")
    print(f"  {total - ranges} show one rate, {ranges} show the range the source states, "
          f"0 show a word")
    print(f"  changed {len(stale)} field(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(apply(check="--check" in sys.argv[1:]))
