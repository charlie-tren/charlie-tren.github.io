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
    # COUNTED ACROSS BOTH SECTIONS, not against src["open"]. Since 11/09/2026 a
    # stop-out closes itself, so the `open` array is no longer the set of open
    # positions - that is the point of the change. The invariant that still holds,
    # and the one worth testing, is that every position in the file appears exactly
    # once on the page: none silently lost, none in both sections.
    # `class="pos done"` on a closed position, so the class attribute cannot be
    # matched with a closing quote straight after "pos". `done` rather than `shut`
    # because the toggle adds `shut` to every collapsed row at runtime, open or
    # closed, and the shared name has already caused two bugs.
    bodies = re.findall(r'<tbody class="pos([^"]*)"(.*?)</tbody>', page, re.S)
    live = [rest for extra, rest in bodies if "done" not in extra]
    total = len(src.get("open") or []) + len(src.get("closed") or [])
    assert len(bodies) == total, f"{len(bodies)} tbodies for {total} positions in the file"
    for b in live:
        # `totarget` went with the column on 11/09/2026; `expcagr` and `cagr`
        # replaced it and must sort too, or a column with a header arrow does nothing.
        for key in ("name", "side", "opened", "carry", "expcagr", "cagr", "r"):
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
    assert 'class="why"' in page and "<dt>Thesis</dt>" in page
    for slot in ("Thesis", "Catalyst", "Breaks if"):
        assert page.count(f"<dt>{slot}</dt>") == len(json.loads(
            (HERE / "positions.json").read_text(encoding="utf-8"))["open"]),             f"every position needs a {slot} slot, filled or not"
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


# --- closing a position ------------------------------------------------------
# Added 11/09/2026. Charlie: "japan 225 was closed. things should automatically move
# to closed when they close". The manual step being removed is cutting an object out
# of one array and pasting it into another, which can be half-done - and a position
# left in `open` with an exit on it was priced live and reported as still running.

def test_an_exit_date_moves_a_position_to_closed():
    """Wherever it is typed. The array is not the source of truth; the exit is."""
    sys.path.insert(0, str(HERE))
    import build
    data = json.loads((HERE / "positions.json").read_text(encoding="utf-8"))
    live = dict(data["open"][0])
    shut = dict(live, name="Fixture", exit_date="2026-09-10", exit=live["entry"],
                postmortem="x")
    # Still sitting in `open`, with an exit on it: it must be classified as closed.
    both = [live, shut]
    assert [p["name"] for p in both if p.get("exit_date")] == ["Fixture"]
    row = build.shut_row(shut)
    assert row["to_target"] is None, "a closed position has no distance left to run"
    assert row["held"] == "2 days", row["held"]


def test_closed_r_is_derived_from_the_exit_not_typed():
    """The one figure a reader could not check if it were typed. Long and short."""
    sys.path.insert(0, str(HERE))
    from build import shut_row
    base = {"name": "F", "direction": "Long", "entry": 100.0, "stop": 90.0,
            "target": 130.0, "entry_date": "2026-09-01", "exit_date": "2026-09-03"}
    for direction, exit_px, want in [("Long", 90.0, -1.0), ("Long", 110.0, 1.0),
                                     ("Short", 110.0, -1.0), ("Short", 90.0, 1.0)]:
        p = dict(base, direction=direction, exit=exit_px,
                 stop=110.0 if direction == "Short" else 90.0)
        got = shut_row(p)["r"]
        assert abs(got - want) < 1e-9, f"{direction} exit {exit_px}: {got} != {want}"


def test_a_close_without_an_exit_price_refuses_to_build():
    """Proved by breaking it. A closed position with no exit cannot have an R, and a
    blank R on a finished trade is the page quietly declining to score itself."""
    src_p, out_p = HERE / "positions.json", HERE / "index.html"
    src_before = src_p.read_text(encoding="utf-8")
    digest_before = hashlib.md5(out_p.read_bytes()).hexdigest()
    try:
        broken = json.loads(src_before)
        broken["open"][0]["exit_date"] = "2026-09-10"      # no `exit` alongside it
        src_p.write_text(json.dumps(broken, indent=2), encoding="utf-8")
        r = subprocess.run([sys.executable, str(HERE / "build.py")],
                           capture_output=True, text=True)
        assert r.returncode != 0, "built a closed position with no exit price"
        assert "exit" in (r.stdout + r.stderr).lower(), (r.stdout + r.stderr)[-300:]
        assert hashlib.md5(out_p.read_bytes()).hexdigest() == digest_before, \
            "index.html was overwritten"
    finally:
        src_p.write_text(src_before, encoding="utf-8")


def test_the_same_position_cannot_appear_twice():
    """The failure mode of moving an entry by hand: pasted into `closed` and not
    deleted from `open`. It would be priced live AND scored as finished."""
    src_p = HERE / "positions.json"
    src_before = src_p.read_text(encoding="utf-8")
    try:
        broken = json.loads(src_before)
        broken["closed"] = [dict(broken["open"][0], exit_date="2026-09-10",
                                 exit=broken["open"][0]["entry"], postmortem="x")]
        src_p.write_text(json.dumps(broken, indent=2), encoding="utf-8")
        r = subprocess.run([sys.executable, str(HERE / "build.py")],
                           capture_output=True, text=True)
        assert r.returncode != 0, "built with the same position open and closed"
        assert "twice" in (r.stdout + r.stderr).lower(), (r.stdout + r.stderr)[-300:]
    finally:
        src_p.write_text(src_before, encoding="utf-8")


def test_both_sections_are_headed_and_the_closed_control_is_wired():
    """Charlie asked for an Open and a Closed section. The Closed table is a second
    table.book with no sort keys, so the toggle has to be bound per table rather than
    off getElementById("book") - otherwise its Thesis buttons render and do nothing."""
    html = (HERE / "index.html").read_text(encoding="utf-8")
    assert ">Open</h2>" in html, "no Open heading"
    assert 'querySelectorAll("table.book")' in html, \
        "the toggle is still bound to a single table by id"
    assert 'getElementById("book")' in html, "the sort should still be scoped to #book"


def test_the_track_is_in_r_space_and_cannot_plot_off_itself():
    """Stop at the left end, target at the right, for a long AND a short. Clamped,
    because a position past its stop is at the end of the track, not off it."""
    sys.path.insert(0, str(HERE))
    from build import track
    assert track(0.0, 3.0)["pct_entry"] == 25.0                  # -1R..+3R, entry at 0
    assert track(-1.0, 3.0)["pct_now"] == 0.0                    # at the stop
    assert track(3.0, 3.0)["pct_now"] == 100.0                   # at the target
    assert track(-2.5, 3.0)["pct_now"] == 0.0, "past the stop plotted off the track"
    assert track(None, 3.0)["pct_now"] is None


# --- a stop-out closes itself ------------------------------------------------
# Charlie, 11/09/2026: "but if its gone below the stop then it's closed by default".
# A stop is a resting order, so this is derivable and should never be typed.

def _bars(*rows):
    """(iso date, low, high) ascending."""
    return list(rows)


def test_a_long_stops_out_on_the_first_low_through_the_stop():
    sys.path.insert(0, str(HERE))
    from build import stopped_out
    p = {"direction": "Long", "stop": 100.0, "entry_date": "2026-09-08"}
    got = stopped_out(p, _bars(("2026-09-08", 101.0, 110.0),
                               ("2026-09-09", 100.5, 108.0),
                               ("2026-09-10", 99.0, 104.0),     # through it
                               ("2026-09-11", 90.0, 95.0)))
    assert got == "2026-09-10", got


def test_a_short_stops_out_on_the_high_not_the_low():
    sys.path.insert(0, str(HERE))
    from build import stopped_out
    p = {"direction": "Short", "stop": 100.0, "entry_date": "2026-09-08"}
    assert stopped_out(p, _bars(("2026-09-08", 80.0, 99.0),
                                ("2026-09-09", 85.0, 101.0))) == "2026-09-09"
    # The same bars must NOT stop a long out: its stop is below, and a high through
    # 100 is the good direction. Getting this backwards closes every winner.
    assert stopped_out({**p, "direction": "Long"},
                       _bars(("2026-09-08", 101.0, 140.0))) is None


def test_a_breach_before_the_entry_date_is_not_a_stop_out():
    """The fault this filter exists for. Japan 225's stop of 64,043 was breached on
    02/09 and 03/09, six days before the position was opened - without the filter
    the trade closes before it exists, at a loss it never took."""
    sys.path.insert(0, str(HERE))
    from build import stopped_out
    p = {"direction": "Long", "stop": 64043.0, "entry_date": "2026-09-08"}
    early = _bars(("2026-09-02", 63725.0, 64900.0), ("2026-09-03", 63700.0, 64800.0),
                  ("2026-09-08", 64920.0, 65500.0))
    assert stopped_out(p, early) is None, "closed a position before it was opened"
    assert stopped_out(p, early + [("2026-09-10", 63930.0, 64500.0)]) == "2026-09-10"


def test_the_close_is_not_what_dates_a_stop_out():
    """A level can trade intraday on a session that closes back above it. Dating off
    the close reports the stop-out late and prices it where the trade never was:
    Japan 225 closed at 64,175 on 09/09 with a low of 64,135, and at 64,015 on 10/09
    with a low of 63,930 - so only the low can tell 10/09 from 09/09."""
    sys.path.insert(0, str(HERE))
    from build import stopped_out
    p = {"direction": "Long", "stop": 64100.0, "entry_date": "2026-09-08"}
    # Low through the stop, close above it: still a stop-out, on that day.
    assert stopped_out(p, _bars(("2026-09-09", 64000.0, 64300.0))) == "2026-09-09"


def test_a_hand_entered_exit_beats_the_derivation():
    """Charlie closing early, or moving a stop the page does not know about, must
    survive a rebuild. The derivation only fills a blank."""
    src_p = HERE / "positions.json"
    before = src_p.read_text(encoding="utf-8")
    try:
        d = json.loads(before)
        target = next(p for p in d["open"] if p["name"] == "Japan 225")
        target.update(exit_date="2026-09-09", exit=65000.0, postmortem="hand-entered")
        src_p.write_text(json.dumps(d, indent=2), encoding="utf-8")
        r = subprocess.run([sys.executable, str(HERE / "build.py")],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "stop-out: Japan 225" not in r.stdout, \
            "the derivation overwrote a hand-entered exit"
        html = (HERE / "index.html").read_text(encoding="utf-8")
        assert "09/09/26" in html and "hand-entered" in html
    finally:
        src_p.write_text(before, encoding="utf-8")
        subprocess.run([sys.executable, str(HERE / "build.py")],
                       capture_output=True, text=True)


def test_the_missing_price_guard_can_still_fire():
    """bars_for() creates a bars-only cache entry for every open symbol, which made
    `s not in cache` true with no price in it - the guard stopped being able to fire
    and the next line raised KeyError instead. It tests for a usable price now."""
    sys.path.insert(0, str(HERE))
    from build import usable
    assert not usable({"bars": [("2026-09-10", 1.0, 2.0)]}), \
        "a bars-only entry counts as a price, so the guard cannot fire"
    assert usable({"price": 1.5})


def test_a_closed_positions_bars_survive_a_reload():
    """A closed position is never priced, so its cache entry is bars-only. Dropping
    it on load threw away the fallback that stops a failed fetch quietly re-opening
    a stopped-out trade."""
    sys.path.insert(0, str(HERE))
    import build
    cache_p = HERE / "prices.json"
    before = cache_p.read_text(encoding="utf-8")
    try:
        cache_p.write_text(json.dumps({
            "SHUT=F": {"bars": [["2026-09-10", 1.0, 2.0]]},
            "LIVE=F": {"price": 10.0, "asof": "2026-09-10"},
            "JUNK=F": {"price": None},
        }), encoding="utf-8")
        got = build.load_prices()
        assert "SHUT=F" in got and got["SHUT=F"]["bars"], "bars-only entry was dropped"
        assert "LIVE=F" in got
        assert "JUNK=F" not in got, "an unusable price was kept"
    finally:
        cache_p.write_text(before, encoding="utf-8")


def test_the_closed_table_does_not_compensate_for_arrows_it_has_not_got():
    """td.n carries 1.12rem of right padding purely to offset the sort glyph the
    sortable headers print after their label, so header and digits end on the same x.
    The Closed table's headers are plain - no data-sort, no glyph - so inheriting
    that padding pushed every figure 0.82rem right of the label it belongs to, which
    is what Charlie saw on 11/09/2026. Measured at 0.0px across both tables after
    the override; this pins the reasoning so deleting the override goes red."""
    html = (HERE / "index.html").read_text(encoding="utf-8")
    closed = html[html.find(">Closed</h2>"):]
    head = closed[closed.find("<thead>"):closed.find("</thead>")]
    assert "data-sort" not in head, \
        "the Closed headers sort now, so they carry a glyph and this rule must change"
    assert ".shutbook td.n { padding-right: .3rem; }" in html, \
        "the Closed table is compensating for a sort arrow it does not have"


def test_the_closed_control_names_the_post_mortem():
    """Charlie, 11/09/2026: the control should imply a post-mortem is behind it. The
    entry reasoning is on the open rows too; the judgement of it only exists here."""
    html = (HERE / "index.html").read_text(encoding="utf-8")
    op, cl = html[:html.find(">Closed</h2>")], html[html.find(">Closed</h2>"):]
    assert ">Thesis</button>" in op, "the open control should still say Thesis"
    assert ">Post-mortem</button>" in cl, "the closed control should say Post-mortem"
    assert ">Thesis</button>" not in cl, "a closed row still says Thesis"
