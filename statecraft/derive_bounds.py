"""Re-derive the axis plotting bounds from everything that occupies each axis.

RUN THIS AFTER ADDING COUNTRIES OR CHANGING OPTION VALUES, then paste the result
into axes.py. It does not write; deciding a bound is a judgement and the file
records the decision, not the script's opinion.

The rule, unchanged from the 30/08/2026 derivation: bounds are the observed span
padded by about 6%, snapped OUTWARD to the axis's own precision, and never
rounded to a nice number. A nice number is how education_spend came to sit on
(0, 10) for data spanning 2.2 to 7.3, which let the education spoke travel 11% of
its ring across the whole option range while the visitor moved the slider.

WHAT OCCUPIES AN AXIS is three things and all of them must fit inside the bounds:
  - every country's measured cell, matchable or measured only, because the reveal
    plots the answer country's figures on the same tracks;
  - every option's EFFECTIVE axis value, which is what the page plots as the
    visitor's own design. Effective, not hand, because the hand value is not what
    is drawn;
  - THE TAX SLIDER'S OWN ENDS, 12 and 55. The tax spoke is the one axis the page
    does not read from an option: chart.js plots clampRate(view.rate), the raw
    rate the visitor set, which runs past the dearest option's 47 all the way to
    55. Deriving tax_take from the options alone produced an upper bound of 49.5
    on 30/08/2026, which would have clamped every rate above it and shown a
    visitor taxing at 55 a spoke that says 49.5.

TWO AXES HAVE A CEILING THAT IS NOT IN THE DATA. The V-Dem expression index is
defined on 0 to 1 and bargaining coverage is a percentage of employees, so
padding above the observed maximum invents territory the measure cannot reach.
They are capped rather than padded, which is not the same as rounding to a nice
number: 1 and 100 are the definition of the scale, not a tidy-looking choice.

A value outside the bounds is clamped to the edge by chart.js and read by the
visitor as a fact, which is the silent failure this exists to prevent.
"""

import itertools

from axes import AXES
from build_data import effective_axis_values
from countries import COUNTRIES
from policies import DOMAINS

PAD = 0.06

# The tax slider's ends, from budget.js. The page plots the raw rate on the
# tax_take spoke, so these are occupants of that axis as surely as any option is.
TAX_SLIDER = (12, 55)

# Where the measure itself stops. Padding cannot go past these.
CEILING = {"expression": 1.0, "bargaining": 100.0}

# The step each axis is snapped outward to. It is the precision the axis is
# quoted in, not a tidiness preference: rounding grid carbon to the nearest 0.1
# would be false precision and rounding the V-Dem index to the nearest 10 would
# collapse it.
STEP = {
    "tax_take": 0.5, "health_public": 1, "education_spend": 0.1,
    "social_housing": 0.5, "pension_spend": 0.5, "grid_carbon": 10,
    "expression": 0.01, "disproportionality": 0.5, "bargaining": 1,
    "military_burden": 0.5, "foreign_born": 1, "incarceration": 10,
    "family_spend": 0.1, "redistribution": 0.01,
}

# Axes whose measure cannot go below zero. Padding below the minimum must not
# invent negative territory on a track that is a share or a count.
NON_NEGATIVE = {
    "tax_take", "health_public", "education_spend", "social_housing",
    "pension_spend", "grid_carbon", "expression", "disproportionality",
    "bargaining", "military_burden", "foreign_born", "incarceration",
    "family_spend", "redistribution",
}


def occupants(axis_id):
    """Every value plotted on this axis, with a label saying where it came from.

    A SUMMED AXIS IS NOT PLOTTED ONE OPTION AT A TIME. Redistribution is the sum
    of the tax, work and family contributions, so listing each contribution
    separately builds a population whose maximum is one contribution and whose
    real maximum is three. That is how (0, 0.27) came to be derived from a
    plotted value that reached 0.44: the bound was fitted to a quantity nobody
    plots. Every reachable combination is enumerated instead, which is 180
    designs and cheap.
    """
    out = []
    for c in COUNTRIES:
        cell = c["indicators"].get(axis_id)
        if cell and cell.get("value") is not None:
            out.append((cell["value"], c["code"]))
    effective = effective_axis_values()
    if any(a["id"] == axis_id and a.get("summed") for a in AXES):
        contributors = [
            [(o["id"], effective[o["id"]][0].get(axis_id, 0.0)) for o in d["options"]]
            for d in DOMAINS
            if any(effective[o["id"]][0].get(axis_id) is not None for o in d["options"])
        ]
        for combo in itertools.product(*contributors):
            out.append((round(sum(v for _, v in combo), 10),
                        " + ".join(i for i, _ in combo)))
    else:
        for option_id, (eff, _hand, _basis) in effective.items():
            value = eff.get(axis_id)
            if value is not None:
                out.append((value, option_id))
    if axis_id == "tax_take":
        out.append((TAX_SLIDER[0], "slider min"))
        out.append((TAX_SLIDER[1], "slider max"))
    return sorted(out)


def snap(value, step, up):
    n = value / step
    n = -((-n) // 1) if up else n // 1
    return round(n * step, 10)


def derive(axis):
    got = occupants(axis["id"])
    if not got:
        return None
    values = [v for v, _ in got]
    lo_obs, hi_obs = min(values), max(values)
    pad = PAD * (hi_obs - lo_obs)
    step = STEP[axis["id"]]
    lo = snap(lo_obs - pad, step, up=False)
    hi = snap(hi_obs + pad, step, up=True)
    if axis["id"] in NON_NEGATIVE and lo < 0:
        lo = 0
    if axis["id"] in CEILING:
        hi = min(hi, CEILING[axis["id"]])
    return lo, hi, got


def main():
    print(f"padding {PAD:.0%} of the observed span, snapped outward\n")
    changed = []
    for axis in AXES:
        result = derive(axis)
        if result is None:
            print(f"{axis['id']:20} NO OCCUPANTS")
            continue
        lo, hi, got = result
        old = tuple(axis["bounds"])
        new = (lo, hi)
        mark = "" if old == new else "   <-- CHANGED"
        if old != new:
            changed.append((axis["id"], old, new))
        print(f"{axis['id']:20} {str(old):>16} -> {str(new):<16} "
              f"span {got[0][0]:g} ({got[0][1]}) to {got[-1][0]:g} ({got[-1][1]}){mark}")
    print()
    if not changed:
        print("no bound moved")
    for axis_id, old, new in changed:
        print(f"CHANGED {axis_id}: {old} -> {new}")


if __name__ == "__main__":
    main()
