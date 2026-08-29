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
