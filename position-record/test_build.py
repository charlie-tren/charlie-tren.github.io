"""Tests for the Position Record build.

The two that matter are the guard and the arithmetic. A positions page that publishes a
stale price beside a stop level tells a reader a position is safe when it has already
been taken out, and an R that disagrees with the entry and stop is the whole unit of the
page being wrong.
"""
import json, subprocess, sys, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_r_matches_entry_and_stop():
    """1R is entry to stop. Recomputed from the raw fields rather than trusting enrich()."""
    sys.path.insert(0, str(HERE))
    from build import enrich
    for direction, entry, stop, price, want in [
        ("Long", 100.0, 90.0, 90.0, -1.0),      # at the stop
        ("Long", 100.0, 90.0, 110.0, 1.0),      # one R up
        ("Short", 100.0, 110.0, 90.0, 1.0),     # a short works the other way
        ("Short", 100.0, 110.0, 110.0, -1.0),
    ]:
        got = enrich({"direction": direction, "entry": entry, "stop": stop,
                      "target": None}, price)["r"]
        assert abs(got - want) < 1e-9, f"{direction} {entry}/{stop}@{price}: {got} != {want}"


def test_stop_left_never_negative():
    """Past the stop the bar is empty, not inverted."""
    sys.path.insert(0, str(HERE))
    from build import enrich
    row = enrich({"direction": "Long", "entry": 100.0, "stop": 90.0, "target": None}, 80.0)
    assert row["stop_left"] == 0.0


def test_a_nan_price_is_never_published():
    """yfinance can hand back a NaN close for a name it half-knows, and NaN survives
    round(), json.dump and every sum after it - the page printed "¥nan / +nan%".
    A NaN already in the cache is dropped too, so the miss is loud rather than sticky."""
    sys.path.insert(0, str(HERE))
    from build import usable
    assert not usable({"price": float("nan")})
    assert not usable({"price": 0})
    assert usable({"price": 1099.0})


def test_every_position_is_its_own_tbody_with_its_sort_keys():
    """Sorting reorders tbodies, so a position that is not one loses its reasoning
    the moment a column is clicked."""
    import re
    page = (HERE / "index.html").read_text(encoding="utf-8")
    src = json.loads((HERE / "positions.json").read_text(encoding="utf-8"))
    bodies = re.findall(r'<tbody class="pos"(.*?)</tbody>', page, re.S)
    assert len(bodies) == len(src["open"]), f"{len(bodies)} tbodies for {len(src['open'])} positions"
    for b in bodies:
        for key in ("name", "side", "opened", "carry", "left", "r"):
            assert f'data-{key}="' in b, f"tbody missing data-{key}"
        assert b.count("<tr") == 2, "a position row and its reasoning row"


def test_every_column_sorts_and_has_a_key_to_sort_on():
    """A header carrying the arrow is a promise. Each one needs the matching
    data attribute on every tbody, or clicking it silently does nothing."""
    import re
    page = (HERE / "index.html").read_text(encoding="utf-8")
    head = re.search(r"<thead>(.*?)</thead>", page, re.S).group(1)
    labelled = [c.strip() for c in re.findall(r"<th[^>]*>(.+?)</th>", head, re.S)]
    sortable = re.findall(r'<th[^>]*data-sort="([a-z]+)"[^>]*>(.+?)</th>', head, re.S)
    assert {lbl.strip() for _, lbl in sortable} == set(labelled), "a column with no sort"
    bodies = re.findall(r'<tbody class="pos"(.*?)>', page, re.S)
    assert bodies
    for key, lbl in sortable:
        for b in bodies:
            assert f'data-{key}="' in b, f"{lbl.strip()} sorts on a key no row carries"


def test_the_reasoning_ships_visible_and_is_collapsed_by_the_script():
    """A reader with no JavaScript must get the reasoning, not a dead button. So the
    rows render open and the script closes them, never the other way round."""
    page = (HERE / "index.html").read_text(encoding="utf-8")
    assert 'class="why"' in page and "<li>" in page
    assert 'hidden' not in page.split('<tr class="why">')[1][:200], "shipped already closed"
    assert 'aria-expanded="true"' in page, "the button must ship in its open state"
    assert "_set(false);" in page, "nothing collapses the rows on load"


def test_build_refuses_to_publish_without_a_price():
    """Proved by breaking it, because a guard whose red has never been seen is not a
    guard. A blank distance-to-stop reads as 'not close' rather than as 'unknown'."""
    src_p, cache_p, out_p = HERE / "positions.json", HERE / "prices.json", HERE / "index.html"
    src_before, cache_before = src_p.read_text(encoding="utf-8"), cache_p.read_text(encoding="utf-8")
    digest_before = hashlib.md5(out_p.read_bytes()).hexdigest()
    try:
        broken = json.loads(src_before)
        for p in broken["open"]:
            p["symbol"] = "NOSUCHTICKER.XX"
        src_p.write_text(json.dumps(broken, indent=2), encoding="utf-8")
        cache_p.write_text("{}", encoding="utf-8")
        r = subprocess.run([sys.executable, str(HERE / "build.py")], capture_output=True, text=True)
        assert r.returncode != 0, "build published with no price at all"
        assert hashlib.md5(out_p.read_bytes()).hexdigest() == digest_before, "index.html was overwritten"
    finally:
        src_p.write_text(src_before, encoding="utf-8")
        cache_p.write_text(cache_before, encoding="utf-8")
