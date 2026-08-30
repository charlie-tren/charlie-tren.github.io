"""How far can each spoke of the fingerprint actually move?

The reveal draws thirteen spokes, one per domain, each scaled by that domain's
axis bounds. A domain whose options all sit within a narrow band of a wide axis
draws a spoke that barely moves however hard the visitor pulls the slider, and
the graphic sits still while the policy changes. That is the failure the bounds
derivation exists to prevent, and widening a bound to fit a new country's extreme
is exactly what can reintroduce it: the extreme is real, and the options that
were spread across the old range are now bunched inside the new one.

TRAVEL is the span of a domain's own effective option values divided by the span
of its axis, as a share of the ring. FLOOR is 15%: below that the spoke is
decoration.

    python check_travel.py
"""

from axes import AXES
from build_data import effective_axis_values
from policies import DOMAINS

FLOOR = 0.15


def travel():
    bounds = {a["id"]: a["bounds"] for a in AXES}
    effective = effective_axis_values()
    rows = []
    for d in DOMAINS:
        axis = d["axis"]
        lo, hi = bounds[axis]
        values = []
        for o in d["options"]:
            v = effective[o["id"]][0].get(axis)
            if v is not None:
                values.append((v, o["id"]))
        if len(values) < 2:
            continue
        values.sort()
        share = (values[-1][0] - values[0][0]) / (hi - lo)
        rows.append((share, d["id"], axis, (lo, hi), values))
    rows.sort()
    return rows


def main():
    rows = travel()
    print(f"spoke travel as a share of the ring, floor {FLOOR:.0%}\n")
    thin = []
    for share, domain, axis, (lo, hi), values in rows:
        mark = "   BELOW FLOOR" if share < FLOOR else ""
        if share < FLOOR:
            thin.append(domain)
        print(f"  {share:>4.0%}  {domain:<12} {axis:<20} bounds ({lo}, {hi})  "
              f"options {values[0][0]:g} to {values[-1][0]:g}{mark}")
    print()
    print(f"{len(thin)} domain(s) below the floor: {thin or 'none'}")


if __name__ == "__main__":
    main()
