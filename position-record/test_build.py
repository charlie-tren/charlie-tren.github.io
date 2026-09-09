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
