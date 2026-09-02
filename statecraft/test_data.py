"""Validations for the Statecraft data. Every one of these must be able to fail:
each is proven against a deliberately broken fixture in the task that adds it."""

import itertools

from axes import AXES


def test_fourteen_axes_each_fully_described():
    assert len(AXES) == 14
    ids = [a["id"] for a in AXES]
    assert len(set(ids)) == 14, "axis ids must be unique"
    for a in AXES:
        # .get rather than [] throughout: indexing raises KeyError before the
        # assertion's message is built, so a missing key fails with the key name
        # and not with the axis it belongs to. The whole value of these checks is
        # that the red names the thing that is wrong.
        assert a.get("label"), f"{a['id']} has no label"
        assert a.get("unit"), f"{a['id']} has no unit"
        assert a.get("source"), f"{a['id']} has no source"
        assert a.get("direction") in ("higher", "lower", "neither"), \
            f"{a['id']} has no usable direction"
        lo, hi = a.get("bounds", (0, 0))
        assert lo < hi, f"{a['id']} bounds are not ordered"


from policies import DOMAINS

TAX_DOMAIN = "tax"


def test_every_option_is_fully_costed():
    for d in DOMAINS:
        assert d["options"], f"{d['id']} has no options"
        assert 4 <= len(d["options"]) <= 6, f"{d['id']} has {len(d['options'])} options"
        for o in d["options"]:
            assert o.get("label"), f"{o['id']} has no label"
            assert o.get("detail"), f"{o['id']} has no detail"
            # An option no country holds is fine and deliberate: UBI, absolute
            # free speech, a car-free country and the age cap are the aspirational
            # half of the menu, and the reveal says so in as many words.
            # test_the_menu_stays_grounded holds that share down.
            #
            # There used to be an assertion here that the option carried a
            # `countries` list. It checked that a hand-maintained copy of the
            # matrix EXISTED, never that it was current, so it passed every day of
            # the year that copy spent going stale. The tag lists were deleted on
            # 02/09/2026 and holders() reads the matrix instead.
            pol = o.get("political")
            assert pol is not None and 0 <= pol <= 100, f"{o['id']} political out of range"
            soc = o.get("social")
            assert soc is not None and 0 <= soc <= 100, f"{o['id']} social out of range"
            if d["id"] == TAX_DOMAIN:
                assert "rate" in o, f"{o['id']} is a tax option with no rate"
                assert "financial" not in o, f"{o['id']} must not also carry a financial cost"
                assert "revenue" not in o, (
                    f"{o['id']} still carries `revenue`, which was one number doing "
                    f"two jobs: it is `rate`, a headline tax take, plus the starting "
                    f"country's nonTaxRevenue")
            else:
                assert "financial" in o, f"{o['id']} has no financial cost"
                assert "rate" not in o, f"{o['id']} is not a tax option"
                assert "revenue" not in o, f"{o['id']} is not a tax option"


TAX_SLIDER = (12, 55)


def test_every_tax_rate_sits_on_the_slider_and_matches_its_own_axis():
    """The tax domain is a RATE now, not a menu, and the six options are the
    labelled stops the slider lands on. Two things have to hold or the slider and
    the reveal disagree.

    First, every stop must be reachable: a stop outside 12 to 55 is an option no
    visitor can select and a cell the reveal can still print.

    Second, the stop's rate must equal its own hand tax_take axis value. They are
    the same claim written twice, and they drifted apart once already: tax_minimal
    carried 27.8 against an axis of 16.0, because the field was carrying general
    government revenue rather than a tax take. That is what the split into `rate`
    plus `nonTaxRevenue` fixed, and this is the check that stops it recurring.

    THE SECOND CHECK IS AGAINST WHAT SHIPS, not against the hand value. It read
    `o["axis"]["tax_take"]` off policies.py, which is the number BEFORE
    build_data.py derives it from the countries holding the option, so the
    derivation walked straight through the check that exists to catch the two
    drifting apart. data.json is what the page loads, and the effective value is
    what it carries."""
    lo, hi = TAX_SLIDER
    tax = next(d for d in DOMAINS if d["id"] == TAX_DOMAIN)
    rates = [o["rate"] for o in tax["options"]]
    assert rates == sorted(rates), f"tax stops are out of order: {rates}"
    assert len(set(rates)) == len(rates), f"two tax stops share a rate: {rates}"
    shipped = {oid: eff for oid, (eff, _h, _b) in effective_axis_values().items()}
    basis_of = {oid: b for oid, (_e, _h, b) in effective_axis_values().items()}
    for o in tax["options"]:
        assert lo <= o["rate"] <= hi, (
            f"{o['id']} sits at {o['rate']}, off a slider that runs {lo} to {hi}")
        ships = shipped[o["id"]]["tax_take"]
        assert o["rate"] == ships, (
            f"{o['id']} raises {o['rate']} but ships {ships} on the tax_take "
            f"axis [{basis_of[o['id']]}]; those are the same number said twice")


def test_the_menu_stays_grounded():
    """An option no country holds is allowed and is the aspirational half of the
    menu. Too many of them and the page stops being a comparison with real
    countries and becomes a wishlist, which is the failure this guards. Print the
    share rather than only asserting on it: a bare pass here says nothing about
    which way the number is drifting.

    COUNTED OFF THE MATRIX. It used to be counted off each option's `countries`
    tag list, a second hand-maintained answer to a question the matrix already
    answered. By 02/09/2026 the two disagreed: the tags named 190 of the 585
    matrix cells. The tag lists were deleted rather than repaired, and this is
    one of the checks that used to read them."""
    from build_data import holders
    options = [(d["id"], o) for d in DOMAINS for o in d["options"]]
    empty = [o["id"] for did, o in options if not holders(did, o["id"])]
    share = len(empty) / len(options)
    print(f"\noptions no country holds: {len(empty)} of {len(options)} "
          f"({share:.0%}) {empty}")
    assert share <= 0.20, f"the menu has drifted into a wishlist: {empty}"


def test_option_ids_are_globally_unique():
    ids = [o["id"] for d in DOMAINS for o in d["options"]]
    assert len(set(ids)) == len(ids), "option ids collide across domains"


def test_a_null_axis_value_is_does_not_apply_not_missing():
    """Electoral disproportionality is meaningless without competitive elections.
    None means the measure does not apply. A missing key would mean the option
    forgot to set its own domain's axis, which is a different fault and is
    caught by test_every_domain_moves_its_own_axis."""
    for d in DOMAINS:
        for o in d["options"]:
            assert d["axis"] in o["axis"], f"{o['id']} does not set {d['axis']}"


def test_thirteen_domains_in_a_fixed_order():
    expected = ["tax", "healthcare", "education", "housing", "retirement", "energy",
                "speech", "voting", "work", "defence", "immigration", "justice", "family"]
    assert [d["id"] for d in DOMAINS] == expected, (
        "domain order is the URL encoding order: reordering breaks every shared link")


from countries import COUNTRIES


def matchable():
    """The countries that can be the answer. The ONE definition of the split.

    Everything downstream reads this rather than testing `choices` itself, so
    there is a single place the rule lives and no caller has to decide whether
    an empty dict means 'measured only' or 'someone forgot'."""
    return [c for c in COUNTRIES if c["matchable"]]


def measured_only():
    return [c for c in COUNTRIES if not c["matchable"]]


def test_matchable_agrees_with_choices():
    """`matchable` is stored rather than derived so the page can read it without
    inferring intent from an empty dict. Stored means it can drift, and the two
    disagreeing is the fault that would let a country with no matrix be offered
    as an answer. The field must also BE a bool: a truthy string would pass every
    other check in this file and be wrong."""
    for c in COUNTRIES:
        m = c.get("matchable")
        assert isinstance(m, bool), (
            f"{c['code']} matchable is {m!r}, which is not True or False")
        assert m == bool(c["choices"]), (
            f"{c['code']} is matchable={m} but has {len(c['choices'])} choices; "
            f"those are the same claim said twice and they disagree")
    print(f"\n{len(matchable())} matchable, {len(measured_only())} measured only: "
          f"{sorted(c['code'] for c in measured_only())}")


def test_every_country_has_exactly_one_option_in_every_domain():
    """THIRTEEN CELLS OR NONE, never some.

    A matchable country must cover every domain exactly once, which is what the
    match counts. A measured-only country must have NO cells at all: it is on the
    page for its axes and is not an answer.

    Half a matrix is neither and is a real fault, so it fails here rather than
    being waved through by a weaker 'some or none'. It is the shape a
    part-finished country would have, and it would silently score a low match
    against every design instead of being excluded."""
    domain_ids = {d["id"] for d in DOMAINS}
    options_by_domain = {d["id"]: {o["id"] for o in d["options"]} for d in DOMAINS}
    for c in matchable():
        assert set(c["choices"]) == domain_ids, (
            f"{c['code']} covers {sorted(set(c['choices']))}, needs {sorted(domain_ids)}")
        for dom, opt in c["choices"].items():
            assert opt in options_by_domain[dom], f"{c['code']}.{dom} = {opt} is not an option"
    for c in measured_only():
        assert c["choices"] == {}, (
            f"{c['code']} is measured only but carries {sorted(c['choices'])}; a "
            f"part-filled matrix is a fault, not a third kind of country")


def test_a_measured_only_country_can_never_be_a_match():
    """The match is a count over `choices`, so a country with none of them can
    only ever score zero. That is NOT enough on its own: rank() sorts by count
    and then by axis distance, so on a design that matches no country in any
    domain the whole field ties at zero and a measured-only country can win the
    tiebreak. The guard that stops it is in match.js and is asserted against the
    real ranker in test_logic.mjs. What is asserted HERE is the data half: that
    no measured-only country carries anything the count could read."""
    for c in measured_only():
        assert not c["choices"], f"{c['code']} would score against the matrix"
        assert c["indicators"], (
            f"{c['code']} has no choices and no indicators either, so it is on the "
            f"page for nothing")


# DELETED 02/09/2026: test_option_country_tags_name_a_country_that_holds_that_option.
#
# It checked that each option's `countries` tag list agreed with the `choices`
# matrix. Every tag did agree, right up to the day the tag lists were deleted,
# and that is the point: agreement was never the problem. The tags were written
# when the matrix held twenty countries and were never extended as it grew to
# forty-five, so they named 190 of the 585 cells. True, and a third of the truth.
#
# A test that can only catch a WRONG tag cannot catch a MISSING one, and missing
# was the failure mode the whole time. Nothing validates the tags now because
# there are no tags: build_data.holders() reads the matrix, which is the only
# record of who holds what.


def test_every_country_carries_a_non_tax_revenue():
    """A state's income is tax plus non-tax income, and the second term is a fact
    about the country a visitor inherits rather than a policy they choose. The
    field must be PRESENT on all forty-five, not merely present where it is
    interesting: a missing key would read as zero, and zero is a claim.

    Non-negative because a negative would mean the state pays to exist, which is
    not a thing this model can price. Nineteen of the twenty matchable countries
    are genuinely zero to the nearest tenth of a point of GDP. The UAE is the
    case the field exists for and its sourcing is on its own row.

    ALL TWENTY-FIVE MEASURED-ONLY ROWS ARE 0.0 BECAUSE THE FIGURE COULD NOT BE
    SOURCED, not because it is believed to be nothing. Saudi Arabia, Qatar and
    Kuwait are the UAE's case and the reasoning is written out above their rows
    in countries.py. The field is inert for them in any event: it is inherited
    from the STARTING country and a measured-only country can never be one."""
    for c in COUNTRIES:
        assert "nonTaxRevenue" in c, (
            f"{c['code']} has no nonTaxRevenue; a missing key would be read as "
            f"zero, and zero is a claim about the country")
        v = c["nonTaxRevenue"]
        assert isinstance(v, (int, float)) and not isinstance(v, bool), \
            f"{c['code']} nonTaxRevenue is {v!r}, which is not a number"
        assert v >= 0, f"{c['code']} nonTaxRevenue is {v}, which is negative"
    non_zero = {c["code"]: c["nonTaxRevenue"] for c in COUNTRIES if c["nonTaxRevenue"]}
    print(f"\nnon-tax revenue, % of GDP: {non_zero}")


def test_every_indicator_cell_is_sourced_and_dated():
    axis_ids = {a["id"] for a in AXES}
    for c in COUNTRIES:
        for axis, cell in c["indicators"].items():
            assert axis in axis_ids, f"{c['code']} has an unknown axis {axis}"
            assert "value" in cell, f"{c['code']}.{axis} has no value"
            assert cell.get("year"), f"{c['code']}.{axis} has no year"
            assert cell.get("source"), f"{c['code']}.{axis} has no source"
            if cell["value"] is None:
                assert cell.get("na_reason"), (
                    f"{c['code']}.{axis} is null with no reason: 'does not apply' must "
                    f"say why, and 'no data' is a missing key instead")


COVERAGE_FLOOR = 0.89


def test_indicator_coverage_is_reported_not_assumed():
    """Not every cell exists, and that is allowed. What is not allowed is nobody
    knowing how many are missing. This prints the denominator and fails only
    below the floor.

    THE FLOOR MOVED FROM 0.85 TO 0.89 ON 30/08/2026, WHICH IS A RISE. Adding
    twenty-five measured-only countries was expected to pull coverage down and
    did not. The launch twenty read 269 of 280 (96.1%) and the twenty-five read
    301 of 350 (86.0%), for 570 of 630 (90.5%) overall. The floor sits just under
    the real figure, so a later addition that quietly drops coverage fails here
    rather than being absorbed by a slack threshold.

    WHERE THE SIXTY MISSING CELLS ARE. Fifty-eight of the sixty are the six
    OECD-sourced axes (tax_take, social_housing, pension_spend, family_spend,
    redistribution, bargaining) on countries the OECD does not publish. The other
    two are Taiwan's education_spend and health_public. By country: TW 8, then AE
    6, SA 6, QA 6, KW 6, CY 6, SG 5, UY 5, PA 5, MT 4, HR 2, GR 1. Forty-nine of
    the sixty are on the new measured-only rows and eleven are the launch set's
    own long-standing gaps, which are Singapore and the UAE.

    NONE OF THAT CHANGED ON 31/08/2026 when the last eight rows were coded, and
    that is the point: coding a matrix adds no indicator cells, so the total is
    still 570 of 630. What changed is only which line of the breakdown they are
    counted on, since all forty-five are now matchable and the measured-only
    group is empty.

    TAIWAN IS THE THINNEST ROW IN THE FILE at 6 of 14. It is in none of the World
    Bank, WHO GHED or OECD collections, all three of which exclude it, so what it
    has comes from the six that do cover it: Ember, V-Dem, SIPRI, UN DESA,
    Gallagher and the World Prison Brief.

    NOT ONE CELL WAS INVENTED TO HOLD THIS NUMBER. A missing key is 'no data',
    the page omits that track, and that is the correct outcome."""
    axis_ids = [a["id"] for a in AXES]

    def share(group):
        total = len(group) * len(axis_ids)
        have = sum(1 for c in group for a in axis_ids if a in c["indicators"])
        return have, total

    have, total = share(COUNTRIES)
    mh, mt = share(matchable())
    oh, ot = share(measured_only())
    print(f"\nindicator coverage: {have} of {total} cells ({100 * have / total:.1f}%)")
    print(f"  matchable      {mh} of {mt} ({100 * mh / mt:.1f}%)")
    # THE MEASURED-ONLY GROUP IS EMPTY FROM 31/08/2026 and this line divided by
    # its size, so the whole build refused to write on a report of a number
    # rather than on anything being wrong. The line is kept rather than deleted:
    # the category still exists and the next country added arrives in it, and a
    # report that disappears the moment the group empties is how a later
    # regression goes unnoticed.
    print(f"  measured only  {oh} of {ot}"
          + (f" ({100 * oh / ot:.1f}%)" if ot else " (none left to code)"))
    thin = sorted((sum(1 for a in axis_ids if a in c["indicators"]), c["code"])
                  for c in COUNTRIES)[:5]
    print("  thinnest rows  " + ", ".join(f"{code} {n}/14" for n, code in thin))
    assert have / total >= COVERAGE_FLOOR, (
        f"coverage has fallen to {have}/{total}; the reveal plots empty tracks below this")


def test_every_domain_moves_its_own_axis_and_every_axis_is_moved():
    """No domain is unmeasured and no axis is decoration. A domain with no axis
    has no evidence behind it in the reveal; an axis nothing can move is a
    number on the page for its own sake."""
    domain_axes = {d["axis"] for d in DOMAINS}
    moved = set()
    for d in DOMAINS:
        for o in d["options"]:
            moved.update(o["axis"].keys())
    for a in AXES:
        if a["domain"] is not None:
            assert a["id"] in domain_axes, f"{a['id']} is claimed by no domain"
        assert a["id"] in moved, f"{a['id']} is moved by no option"


def test_the_financial_budget_actually_binds_at_the_bottom_of_the_slider():
    """If the leanest tax rate can fund the most expensive selection in every
    other domain, the constraint is theatre and the whole point of difference
    is gone.

    THIS CHECK USED TO CARRY THE WHOLE CLAIM and it no longer can, because
    capacity is no longer a number in this file. It is realised(rate) plus
    nonTaxRevenue, and the realisation curve lives in budget.js, which Python
    cannot read without keeping a second copy of the constants. Copying them
    here would mean the curve could be retuned in one place and validated
    against the other. So the harder half of the claim, that the budget still
    binds at the TOP of the slider, is asserted in test_logic.mjs next to the
    curve itself, and what stays here is the half the data alone can settle."""
    leanest_rate = min(o["rate"] for d in DOMAINS if d["id"] == "tax"
                       for o in d["options"])
    dearest_spend = sum(max(o["financial"] for o in d["options"])
                        for d in DOMAINS if d["id"] != "tax")
    assert dearest_spend > leanest_rate, (
        f"the dearest possible country costs {dearest_spend:.1f}% of GDP and the "
        f"leanest tax rate is {leanest_rate:.1f}%: the budget never binds")


def test_no_option_is_strictly_dominated():
    """An option cheaper on all three budgets than another in the same domain
    would make that other option one nobody rationally picks. Report them; this
    is a calibration signal, not necessarily a fault, because an option may be
    dearer and still wanted."""
    dominated = []
    for d in DOMAINS:
        if d["id"] == "tax":
            continue
        for a in d["options"]:
            for b in d["options"]:
                if a["id"] == b["id"]:
                    continue
                if (a["financial"] <= b["financial"] and a["political"] <= b["political"]
                        and a["social"] <= b["social"]
                        and (a["financial"], a["political"], a["social"])
                        != (b["financial"], b["political"], b["social"])):
                    dominated.append((b["id"], "dominated by", a["id"]))
    print(f"\nstrictly dominated options: {dominated}")
    assert len(dominated) <= 6, f"too many dominated options to be deliberate: {dominated}"


from build_data import effective_axis_values

# Axes no single option owns. match.js SUMS these across every domain that
# contributes one, so the number on the track is the sum and never any one
# option's share of it.
SUMMED_AXES = {"redistribution"}


def contributing_domains(axis_id):
    """The domains whose options put a value on a summed axis."""
    return [d for d in DOMAINS
            if any(o["axis"].get(axis_id) is not None for o in d["options"])]


def test_every_effective_axis_value_fits_inside_its_axis_bounds():
    """The value the page PLOTS, derived or hand, must sit inside the track it is
    plotted on. Outside it, the marker is clamped to an edge and the reader is
    shown a position that is not the number: silent, and it reads as a fact.

    This is the check that catches an option written on a different basis from
    the axis it moves. ho_singapore carried 78.0 on a social RENTAL axis bounded
    (0, 38), because 78 is the share of people living in HDB housing and not the
    share of dwellings let below market. Both sides now sit on the OECD PH4.2
    basis, and Singapore correctly reads low.

    A None value is 'does not apply' and cannot be out of bounds.

    A SUMMED AXIS IS CHECKED AS THE SUM, which is what this test used to claim
    and did not do. Redistribution is contributed to by the tax, work and family
    choices and match.js adds the three together; nothing ever plots one
    contribution on its own. Checking them one at a time asked whether 0.25 fits
    inside (0, 0.27), which it does, and never asked the question the axis is
    there to answer. The docstring said contributions were covered "since they
    are plotted on the same fourteen tracks", which was exactly the wrong
    inference: being on the same track is the reason the SUM is what has to
    fit."""
    bounds = {a["id"]: a["bounds"] for a in AXES}
    for option_id, (effective, _hand, basis) in effective_axis_values().items():
        for axis, value in effective.items():
            if value is None or axis in SUMMED_AXES:
                continue
            lo, hi = bounds[axis]
            assert lo <= value <= hi, (
                f"{option_id} sits at {value} on {axis}, whose bounds are "
                f"({lo}, {hi}); the marker would be clamped and read as a fact "
                f"[{basis}]")

    effective_of = {oid: eff for oid, (eff, _h, _b) in effective_axis_values().items()}
    for axis in sorted(SUMMED_AXES):
        lo, hi = bounds[axis]
        domains = contributing_domains(axis)
        assert len(domains) > 1, (
            f"{axis} is summed but only {len(domains)} domain contributes to it")

        # Every design a visitor can build out of the contributing domains, since
        # every one of them is reachable by dragging and each draws a marker.
        # Sorted worst first, so the red names the largest breach rather than
        # whichever one itertools reached first.
        designs = []
        for combo in itertools.product(*[d["options"] for d in domains]):
            total = sum(effective_of[o["id"]].get(axis) or 0 for o in combo)
            designs.append((total, [o["id"] for o in combo]))
        designs.sort(reverse=True)
        out = [d for d in designs if not lo <= d[0] <= hi]

        # The countries' OWN coded designs, which is what the page OPENS on. A
        # breach reachable only by dragging is a fault; one a visitor is handed
        # before they touch anything is the same fault, arriving sooner.
        starts = []
        for c in matchable():
            total = sum(effective_of[c["choices"][d["id"]]].get(axis) or 0
                        for d in domains if c["choices"].get(d["id"]))
            starts.append((total, c["code"], c["name"]))
        starts.sort(reverse=True)
        bad_starts = [s for s in starts if not lo <= s[0] <= hi]

        print(f"\n{axis}: bounds ({lo}, {hi}), {len(domains)} contributing "
              f"domains, {len(designs)} reachable designs.\n"
              f"  highest sum {designs[0][0]:.2f} from {designs[0][1]}\n"
              f"  {len(out)} of {len(designs)} designs outside the bounds\n"
              f"  worst starting country {starts[0][2]} at {starts[0][0]:.2f}, "
              f"{len(bad_starts)} of {len(starts)} countries outside on arrival")

        assert not out, (
            f"{len(out)} of {len(designs)} reachable designs fall outside the "
            f"{axis} bounds ({lo}, {hi}). The worst is "
            f"{' + '.join(designs[0][1])} at {designs[0][0]:.2f}. "
            f"{len(bad_starts)} of {len(starts)} countries are outside on their "
            f"own coded design before the visitor touches anything, the worst "
            f"being {starts[0][2]} at {starts[0][0]:.2f}. Every one of these "
            f"markers is clamped to the end of the track and read as a fact")


from timezones import TIMEZONES, FALLBACK


def test_every_mapped_timezone_names_a_matchable_country():
    """The page OPENS on the country a timezone resolves to, which means loading
    that country's thirteen choices as the starting design. A measured-only
    country here would open the page on nothing at all, so timezones.py filters
    the map to matchable countries and this is the check on that filter."""
    codes = {c["code"] for c in matchable()}
    for tz, code in TIMEZONES.items():
        assert code in codes, (
            f"{tz} maps to {code}, which cannot be a starting country")
    assert FALLBACK in codes


def test_the_common_timezones_resolve():
    for tz in ["Australia/Brisbane", "Europe/London", "America/New_York",
               "Europe/Copenhagen", "Asia/Singapore", "Asia/Tokyo",
               "Europe/Berlin", "America/Los_Angeles", "Pacific/Auckland"]:
        assert tz in TIMEZONES, f"{tz} is unmapped and would fall back"
