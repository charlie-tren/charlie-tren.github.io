"""Tests for classify.py, the prose-to-ordinal rules behind the Ease column.

This file exists because the first version of those rules read three columns
BACKWARDS and nothing caught it. "Free. No capital controls." matched the
substring "capital control" and scored the United Kingdom as having them. "No
property-based golden visa." matched "golden visa" and gave the Netherlands a
residency route it does not offer. "Foreigners cannot own land. Can own condo
freehold" matched "cannot" and closed two markets that are open to apartments.

Every one of those produced a confident, plausible-looking score. The only thing
that found them was printing all thirty-four rows and reading them, which is not
a thing that happens on a schedule. So the sentences that were misread are
fixtures now, and each rule is tested in BOTH directions - a negation test that
only checks the positive case passes just as happily on a rule that ignores
negation entirely.

    python test_classify.py
"""
import sys

import classify as C

# (input, function, expected score, what it is testing)
CASES = [
    # --- repatriation: the negation bug that gave the UK capital controls -----
    ("Free. No capital controls.", C.repatriation, 3, "negated keyword is not a hit"),
    ("Generally free. No capital controls.", C.repatriation, 3, "same, with a qualifier"),
    ("Capital controls. Repatriation can be difficult and slow.", C.repatriation, 0, "un-negated keyword still hits"),
    ("Generally free with BSP registration.", C.repatriation, 2, "conditional on registration"),
    ("Free (eurozone).", C.repatriation, 3, "plain free"),

    # --- visa: the negation bug that gave the Netherlands a golden visa -------
    ("No property-based golden visa.", C.visa, 0, "negated scheme name is not a hit"),
    ("No property-based golden visa. Standard EU residence permit routes.", C.visa, 0, "negated, with a real route after it"),
    ("MM2H programme (long-stay visa). Not a property-based golden visa per se.", C.visa, 1,
     "a real long-stay route, correctly NOT counted as property-based"),
    ("Golden Visa: EUR 250-800K (tiered by region). 5yr renewable residency.", C.visa, 3, "un-negated scheme name hits"),
    ("Golden Visa: property route CLOSED. Fund route from EUR 500K.", C.visa, 1, "a closed route is worse than none advertised"),
    ("EB-5 investor visa (USD 800K+). No property-specific visa.", C.visa, 2, "investor route, property route denied"),
    # the five markets that describe the relationship without naming a scheme
    ("Yes - USD 150K property (1yr) or USD 300K (5yr permit)", C.visa, 3, "property-to-residency without a brand"),
    ("Yes - USD 400K property = direct citizenship (3yr hold)", C.visa, 3, "property-to-citizenship without a brand"),
    ("Property purchase in designated area can provide residency visa.", C.visa, 3, "same, phrased as a sentence"),
    ("Property in ITC can qualify for residency visa (min ~OMR 50K).", C.visa, 3, "same again"),
    ("No property-based visa. Standard residence permit routes.", C.visa, 0, "must NOT match the pattern above"),

    # --- ownership: the clause-boundary bug that closed Thailand -------------
    ("Foreigners cannot own land. Can own condo freehold (49% foreign quota per building).",
     C.ownership, 2, "a negator does not reach across a full stop"),
    ("Foreigners cannot own land. Can own condo units (40% foreign cap per building).",
     C.ownership, 2, "same shape, different wording"),
    ("No restrictions on foreign buyers. Full freehold.", C.ownership, 3, "open"),
    ("No federal restrictions on foreign buyers. Some states have agricultural land limits.",
     C.ownership, 3, "open, federal phrasing"),
    ("Foreigners have equal property rights. Full freehold. No restrictions.", C.ownership, 3, "open, equal-rights phrasing"),
    ("Foreigners cannot directly own within 50km of coast. Must use a bank trust (fideicomiso).",
     C.ownership, 1, "trust structure required"),
    ("Foreigners can buy freehold above state minimum prices (MYR 600K-1M).",
     C.ownership, 1, "price floor"),
    ("EU/EEA nationals free to buy. Non-EU foreigners need permit from local government.",
     C.ownership, 2, "permit"),

    # --- the numeric bands ---------------------------------------------------
    (1.5, C.liquidity, 3, "quickest band"),
    (9.0, C.liquidity, 1, "slow band"),
    (3.0, C.costs, 3, "cheapest band"),
    (13.5, C.costs, 0, "dearest band"),
    (96.0, C.rights, 3, "strongest rights"),
    (40.0, C.rights, 0, "weakest rights"),
]


def main():
    failures = []
    for value, fn, want, why in CASES:
        got, label = fn(value)
        if got != want:
            failures.append(f"  {fn.__name__}({value!r:.70}) -> {got} ({label!r}), wanted {want}  [{why}]")

    # A negation rule that ignores negation passes every positive case, so assert
    # the pair explicitly: same keyword, opposite polarity, different score.
    pairs = [
        (C.repatriation, "Capital controls in force.", "No capital controls."),
        (C.visa, "Golden Visa: EUR 250K.", "No golden visa."),
    ]
    for fn, positive, negative in pairs:
        if fn(positive)[0] == fn(negative)[0]:
            failures.append(f"  {fn.__name__} scores {positive!r} and {negative!r} the same - negation is being ignored")

    print(f"{len(CASES) + len(pairs)} checks, {len(failures)} failed")
    if failures:
        print("\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
