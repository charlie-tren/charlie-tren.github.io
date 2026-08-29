"""Does each option's country tag list agree on that option's own axis?

Every option implies a position on its domain's axis, and it carries a list of
countries said to do it. Take the countries in the matrix that hold the option,
read their measured value on that axis, and take the range. Divide by the axis's
plotting bounds so options in different units are comparable, and print anything
above THRESHOLD.

A HIGH SPREAD IS A QUESTION, NOT A VERDICT. It means one of three things, and
they need different fixes:

  1. a matrix cell is a false claim about a country, and moving the cell to a
     different option is the fix. That is what this check caught on 2026-08-29,
     when en_hydro turned out to be carrying NL, JP and SG, none of which has a
     clean grid, and en_nuclear was carrying Korea, whose reactors are 31% of
     generation against 56% for coal and gas together;
  2. the option names an INSTRUMENT and the axis measures an OUTCOME, in which
     case the spread is the finding and there is nothing to fix;
  3. the axis is measuring something other than what the domain is about, which
     is the expensive one, because it means the reveal plots the wrong track.

FOUR ENTRIES ARE KNOWN-HONEST VARIATION and are labelled as such in the output.
Do not "fix" them:

  vo_fptp       the Gallagher index measures disproportionality of outcome, not
                the voting system. Two-party FPTP scores low and multi-party
                FPTP scores high. US 1.01 and UK 23.64 are both correct.
  de_conscript  Korea and Israel both genuinely conscript. They spend very
                different shares of GDP doing it.
  hc_insurance  Switzerland's 33.1% public share is a WHO classification
                artefact: compulsory Swiss cover counts as compulsory PRIVATE
                insurance, not government. The cell is right.
  ju_tough      "long sentences, high imprisonment" is a spectrum, and 128 to
                542 per 100,000 is a wide but defensible band.

A fifth, en_carbon_tax, is case 2 above and is annotated in policies.py: pricing
carbon is not the same claim as having decarbonised, so a priced grid burning oil
shale sits beside a priced grid running on hydro.

Run it after any change to the matrix, the tags or the indicator values.

    python check_spread.py
"""

from axes import AXES
from countries import COUNTRIES
from policies import DOMAINS

THRESHOLD = 0.50

# Reviewed and left alone. See the docstring for why each one is real.
KNOWN_HONEST = {
    "vo_fptp": "the index measures the outcome, not the system",
    "de_conscript": "both conscript, at very different cost",
    "hc_insurance": "the Swiss figure is a WHO classification artefact",
    "ju_tough": "a wide but defensible band",
}


def spreads(threshold=THRESHOLD):
    """Yield (share, domain_id, option_id, hand_value, [(code, value), ...])."""
    bounds = {a["id"]: a["bounds"] for a in AXES}
    measured = {c["code"]: c["indicators"] for c in COUNTRIES}
    out = []
    for d in DOMAINS:
        axis = d["axis"]
        lo, hi = bounds[axis]
        for o in d["options"]:
            hand = o["axis"].get(axis)
            found = []
            for code in o["countries"]:
                cell = measured.get(code, {}).get(axis)
                # None is "does not apply" and a missing key is "no data".
                # Neither can be ranged, and both are silently skipped here
                # rather than counted as zero.
                if cell and cell.get("value") is not None:
                    found.append((code, cell["value"]))
            if len(found) < 2:
                continue
            values = [v for _, v in found]
            share = (max(values) - min(values)) / (hi - lo)
            if share >= threshold:
                out.append((share, d["id"], o["id"], hand,
                            sorted(found, key=lambda p: p[1])))
    out.sort(reverse=True, key=lambda r: r[0])
    return out


def main():
    rows = spreads()
    if not rows:
        print(f"no option spreads at or above {THRESHOLD:.0%} of the axis range")
        return
    print(f"option spreads at or above {THRESHOLD:.0%} of the axis range\n")
    for share, domain, option, hand, found in rows:
        note = KNOWN_HONEST.get(option)
        tail = f"   KNOWN HONEST: {note}" if note else ""
        print(f"  {share:>3.0%}  {domain:<12} {option:<20} hand={hand}{tail}")
        print("        " + " ".join(f"{code}:{value:g}" for code, value in found))
    flagged = [r[2] for r in rows if r[2] not in KNOWN_HONEST]
    print(f"\n{len(rows)} over threshold, {len(flagged)} not already reviewed: "
          f"{flagged or 'none'}")


if __name__ == "__main__":
    main()
