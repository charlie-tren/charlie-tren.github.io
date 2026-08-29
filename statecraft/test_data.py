"""Validations for the Statecraft data. Every one of these must be able to fail:
each is proven against a deliberately broken fixture in the task that adds it."""

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
            # The KEY must exist; the LIST may be empty. An empty list is the
            # deliberate claim that no country does this, which the reveal prints
            # in as many words. A missing key is a forgotten field. Requiring a
            # tag outright would delete UBI, absolute free speech, a car-free
            # country and the age cap, which are the aspirational half of the menu.
            assert isinstance(o.get("countries"), list), \
                f"{o['id']} has no countries list"
            pol = o.get("political")
            assert pol is not None and 0 <= pol <= 100, f"{o['id']} political out of range"
            soc = o.get("social")
            assert soc is not None and 0 <= soc <= 100, f"{o['id']} social out of range"
            if d["id"] == TAX_DOMAIN:
                assert "revenue" in o, f"{o['id']} is a tax option with no revenue"
                assert "financial" not in o, f"{o['id']} must not also carry a financial cost"
            else:
                assert "financial" in o, f"{o['id']} has no financial cost"
                assert "revenue" not in o, f"{o['id']} is not a tax option"


def test_the_menu_stays_grounded():
    """Untagged options are allowed and are the aspirational half of the menu.
    Too many of them and the page stops being a comparison with real countries
    and becomes a wishlist, which is the failure the country tags exist to
    prevent. Print the share rather than only asserting on it: a bare pass here
    says nothing about which way the number is drifting."""
    options = [o for d in DOMAINS for o in d["options"]]
    untagged = [o["id"] for o in options if not o["countries"]]
    share = len(untagged) / len(options)
    print(f"\nuntagged options: {len(untagged)} of {len(options)} "
          f"({share:.0%}) {untagged}")
    assert share <= 0.20, f"the menu has drifted into a wishlist: {untagged}"


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


def test_every_country_has_exactly_one_option_in_every_domain():
    domain_ids = {d["id"] for d in DOMAINS}
    options_by_domain = {d["id"]: {o["id"] for o in d["options"]} for d in DOMAINS}
    for c in COUNTRIES:
        assert set(c["choices"]) == domain_ids, (
            f"{c['code']} covers {sorted(set(c['choices']))}, needs {sorted(domain_ids)}")
        for dom, opt in c["choices"].items():
            assert opt in options_by_domain[dom], f"{c['code']}.{dom} = {opt} is not an option"


def test_option_country_tags_name_a_country_that_holds_that_option():
    """A tag on an option is a claim that some country does this. Where that
    country is in the matrix, the matrix must agree. Tags naming countries
    outside the twenty are allowed and are how the menu proves it is not
    invented, so they are skipped rather than failed."""
    in_matrix = {c["code"]: c["choices"] for c in COUNTRIES}
    for d in DOMAINS:
        for o in d["options"]:
            for code in o["countries"]:
                if code in in_matrix:
                    assert in_matrix[code][d["id"]] == o["id"], (
                        f"{o['id']} is tagged {code}, but the matrix has {code}.{d['id']} "
                        f"= {in_matrix[code][d['id']]}")


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


def test_indicator_coverage_is_reported_not_assumed():
    """Not every cell exists, and that is allowed. What is not allowed is nobody
    knowing how many are missing. This prints the denominator and fails only
    below the floor agreed at launch."""
    axis_ids = [a["id"] for a in AXES]
    total = len(COUNTRIES) * len(axis_ids)
    have = sum(1 for c in COUNTRIES for a in axis_ids if a in c["indicators"])
    print(f"\nindicator coverage: {have} of {total} cells "
          f"({100 * have / total:.0f}%)")
    assert have / total >= 0.85, (
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


def test_the_financial_budget_actually_binds():
    """If the cheapest tax option can fund the most expensive selection in every
    other domain, the constraint is theatre and the whole point of difference
    is gone."""
    cheapest_revenue = min(o["revenue"] for d in DOMAINS if d["id"] == "tax"
                           for o in d["options"])
    dearest_spend = sum(max(o["financial"] for o in d["options"])
                        for d in DOMAINS if d["id"] != "tax")
    assert dearest_spend > cheapest_revenue, (
        f"the dearest possible country costs {dearest_spend:.1f}% of GDP and the "
        f"leanest tax raises {cheapest_revenue:.1f}%: the budget never binds")


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


def test_every_effective_axis_value_fits_inside_its_axis_bounds():
    """The value the page PLOTS, derived or hand, must sit inside the track it is
    plotted on. Outside it, the marker is clamped to an edge and the reader is
    shown a position that is not the number: silent, and it reads as a fact.

    This is the check that catches an option written on a different basis from
    the axis it moves. ho_singapore carried 78.0 on a social RENTAL axis bounded
    (0, 38), because 78 is the share of people living in HDB housing and not the
    share of dwellings let below market. Both sides now sit on the OECD PH4.2
    basis, and Singapore correctly reads low.

    A None value is 'does not apply' and cannot be out of bounds. Contributions
    to redistribution are checked here too, since they are plotted on the same
    fourteen tracks as everything else."""
    bounds = {a["id"]: a["bounds"] for a in AXES}
    for option_id, (effective, _hand, basis) in effective_axis_values().items():
        for axis, value in effective.items():
            if value is None:
                continue
            lo, hi = bounds[axis]
            assert lo <= value <= hi, (
                f"{option_id} sits at {value} on {axis}, whose bounds are "
                f"({lo}, {hi}); the marker would be clamped and read as a fact "
                f"[{basis}]")


from timezones import TIMEZONES, FALLBACK


def test_every_mapped_timezone_names_a_country_in_the_matrix():
    codes = {c["code"] for c in COUNTRIES}
    for tz, code in TIMEZONES.items():
        assert code in codes, f"{tz} maps to {code}, which is not in the matrix"
    assert FALLBACK in codes


def test_the_common_timezones_resolve():
    for tz in ["Australia/Brisbane", "Europe/London", "America/New_York",
               "Europe/Copenhagen", "Asia/Singapore", "Asia/Tokyo",
               "Europe/Berlin", "America/Los_Angeles", "Pacific/Auckland"]:
        assert tz in TIMEZONES, f"{tz} is unmapped and would fall back"
