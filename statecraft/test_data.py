"""Validations for the Statecraft data. Every one of these must be able to fail:
each is proven against a deliberately broken fixture in the task that adds it."""

from axes import AXES


def test_fourteen_axes_each_fully_described():
    assert len(AXES) == 14
    ids = [a["id"] for a in AXES]
    assert len(set(ids)) == 14, "axis ids must be unique"
    for a in AXES:
        assert a["label"], f"{a['id']} has no label"
        assert a["unit"], f"{a['id']} has no unit"
        assert a["source"], f"{a['id']} has no source"
        assert a["direction"] in ("higher", "lower", "neither")
        lo, hi = a["bounds"]
        assert lo < hi, f"{a['id']} bounds are not ordered"
