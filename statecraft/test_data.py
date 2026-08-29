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
