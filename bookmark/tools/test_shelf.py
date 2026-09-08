"""Invariants for the shelf and the pipelines that fill it.

    python -m pytest tools/test_shelf.py -q

Every test here exists because the thing it checks was wrong in a shipped
version. None of them touch the network: they read books.js and exercise the
pure functions, so the suite is worth running before every deploy.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import fetch_descriptions as F                                     # noqa: E402
import harvest_books as H                                          # noqa: E402
import redescribe as R                                             # noqa: E402
import fetch_settings as S                                         # noqa: E402


# --------------------------------------------------------------- the shelf ----

@pytest.fixture(scope="module")
def shelf() -> list[dict]:
    """books.js as data. Parsed by regex rather than by running it, so a broken
    file fails HERE rather than in the browser."""
    src = (ROOT / "books.js").read_text(encoding="utf-8")
    body = src[src.index("window.SHELF = ["):]
    out = []
    for m in re.finditer(
            r'\{t:"((?:[^"\\]|\\.)*)",a:"((?:[^"\\]|\\.)*)",y:(-?\d+)'
            r'(?:,set:\[([^\]]*)\])?,f:"(\w+)",tags:\[([^\]]*)\],mood:\[([^\]]*)\],'
            r'len:"(\w)",sty:"(\w+)",dem:(\d)(,soft:1)?,why:"((?:[^"\\]|\\.)*)",'
            r'src:"([^"]*)"\}', body):
        # UNESCAPED, because books.js is JS source and a title can contain a
        # quote - Sue Grafton's '"B" Is for Burglar' does. Comparing the raw
        # capture against a value node has already parsed makes three real books
        # look missing.
        def un(x: str) -> str:
            return x.replace('\\"', '"').replace("\\\\", "\\")

        out.append({
            "t": un(m.group(1)), "a": un(m.group(2)), "y": int(m.group(3)),
            "set": re.findall('"([^"]+)"', m.group(4) or ""),
            "f": m.group(5),
            "tags": re.findall('"([^"]+)"', m.group(6)),
            "mood": re.findall('"([^"]+)"', m.group(7)),
            "len": m.group(8), "sty": m.group(9), "dem": int(m.group(10)),
            "soft": bool(m.group(11)), "why": un(m.group(12)),
            "src": m.group(13)})
    assert out, "no records parsed out of books.js"
    return out


def test_every_record_parses(shelf):
    """The regex above is strict, so a count mismatch means a record has a shape
    the site's own reader may also choke on."""
    raw = (ROOT / "books.js").read_text(encoding="utf-8").count('{t:"')
    assert len(shelf) == raw, f"parsed {len(shelf)} of {raw} records"


def test_no_description_trails_off(shelf):
    """190-character truncation left 270 of 817 ending mid-clause."""
    bad = [b["t"] for b in shelf if b["why"].rstrip().endswith("...")]
    assert not bad, f"{len(bad)} trail off, e.g. {bad[:4]}"


def test_every_book_is_sourced(shelf):
    """Hand-written lines were removed from the shelf, not left uncredited."""
    assert all(b["src"].startswith("https://en.wikipedia.org/wiki/") for b in shelf)


def test_no_description_is_publication_trivia(shelf):
    bad = [b["t"] for b in shelf
           if any(j in b["why"].lower() for j in F.JUNK)]
    assert not bad, f"{len(bad)} carry publication trivia, e.g. {bad[:4]}"


def test_no_description_opens_on_a_dangling_reference(shelf):
    bad = [b["t"] for b in shelf if F.DANGLING.match(b["why"])]
    assert not bad, f"{len(bad)} open on a dangling reference, e.g. {bad[:4]}"


def test_facets_are_in_vocabulary(shelf):
    tags = set(re.findall('"([^"]+)"', re.search(
        r"var TAGS = \[([^\]]*)\]",
        (ROOT / "index.html").read_text(encoding="utf-8")).group(1)))
    sets = set(re.findall('"([^"]+)"', re.search(
        r"var SETS = \[([^\]]*)\]",
        (ROOT / "index.html").read_text(encoding="utf-8")).group(1)))
    for b in shelf:
        assert b["f"] in ("fic", "non"), b["t"]
        assert b["len"] in ("s", "m", "l"), b["t"]
        assert b["sty"] in ("plain", "rich", "funny"), b["t"]
        assert 1 <= b["dem"] <= 3, b["t"]
        assert b["mood"], b["t"]
        assert set(b["mood"]) <= {"absorb", "learn", "unsettle", "laugh"}, b["t"]
        assert set(b["tags"]) <= tags, (b["t"], b["tags"])
        assert set(b["set"]) <= sets, (b["t"], b["set"])


def test_no_duplicate_titles(shelf):
    seen: dict[str, str] = {}
    dupes = []
    for b in shelf:
        k = re.sub(r"[^a-z0-9]", "", b["t"].lower())
        if k in seen:
            dupes.append(b["t"])
        seen[k] = b["t"]
    assert not dupes, f"duplicated: {dupes[:5]}"


def test_no_two_books_share_a_source(shelf):
    """Same-author drift put The Old Ways on Underland's article and Steve Jobs
    on The Innovators'. Two books citing one page means at least one is wrong."""
    by_src: dict[str, list[str]] = {}
    for b in shelf:
        by_src.setdefault(b["src"], []).append(b["t"])
    shared = {k: v for k, v in by_src.items() if len(v) > 1}
    assert not shared, f"shared sources: {list(shared.items())[:3]}"


def test_the_shelf_is_not_one_prize(shelf):
    """A cap per prize exists so the Edgar's 215 crime titles cannot set the
    shelf's character. No single subject should own more than half of it."""
    tally: dict[str, int] = {}
    for b in shelf:
        for t in b["tags"]:
            tally[t] = tally.get(t, 0) + 1
    worst, n = max(tally.items(), key=lambda x: x[1])
    assert n < len(shelf) * 0.55, f"{worst} covers {n} of {len(shelf)}"


# ----------------------------------------------------------- pure functions ----

def test_usable_rejects_what_shipped_once():
    assert R.usable("A father and his young son journey on foot across a "
                    "post-apocalyptic, ash-covered United States.")
    assert not R.usable("")
    assert not R.usable("Short.")
    assert not R.usable("It won the 2005 Pulitzer Prize for Fiction and more besides.")
    assert not R.usable("These figures are drawn from the years after the war "
                        "and the decades that followed them.")
    assert not R.usable("A line that ends in an ellipsis because it was cut at "
                        "one hundred and ninety characters...")
    assert not R.usable("lower case openings come from list items and tables of "
                        "contents rather than prose")


def test_sentence_split_survives_initials_and_abbreviations():
    got = F.split_sentences(
        "Disgrace is a 1999 novel by South African author J. M. Coetzee. "
        "It won the Booker Prize. Dr. Smith agreed with him. The end.")
    assert got[0].endswith("J. M. Coetzee."), got[0]
    assert len(got) == 4, got


def test_word_boundary_matching():
    """'war' inside 'awards' tagged 207 books as war books."""
    assert not H.hit("war", "stonewall book awards")
    assert H.hit("war", "world war ii")
    assert not H.hit("art", "departments")
    assert H.hit("art", "art history")
    assert not H.hit("sport", "transport")


def test_place_gazetteer_does_not_confuse_continents():
    assert S.regions(["Indiana"]) == ["america"]
    assert S.regions(["India"]) == ["asia"]
    assert "britain" in S.regions(["Great Britain", "Putney"])
    assert S.regions([]) == []


def test_useful_never_truncates():
    long_one = ("Greenblatt tells the story of how Poggio Bracciolini, a "
                "fifteenth-century papal emissary and obsessive book hunter, "
                "saved the last surviving copy of the Roman poet Lucretius's "
                "long philosophical work from the near-certain oblivion of a "
                "German monastery library where it had sat unread for centuries.")
    out = F.useful("The Swerve is a 2011 book by Stephen Greenblatt. " + long_one,
                   "The Swerve")
    assert not out.endswith("..."), out
    assert out in ("", long_one), out


def test_length_bands_match_the_spine_widths():
    """Spine width is drawn from len, so the bands and the widths have to agree."""
    import facet_books as FB
    assert FB.length(None) == "m"
    assert FB.length(120) == "s"
    assert FB.length(300) == "m"
    assert FB.length(700) == "l"


def test_settings_file_agrees_with_the_shelf(shelf):
    """Every setting written onto a book must have come from the lookup, not from
    a hand edit that the next --apply would silently undo."""
    p = HERE / "settings.json"
    if not p.exists():
        pytest.skip("settings.json not present")
    have = json.loads(p.read_text(encoding="utf-8"))
    for b in shelf:
        if b["set"] and b["t"] in have:
            assert set(b["set"]) == set(have[b["t"]]["set"]), b["t"]

# ------------------------------------------------- the two served artefacts ----

def test_served_files_are_in_step_with_books_js():
    """shelf.js and texts.js are GENERATED, and a stale one ships a shelf that
    disagrees with its own descriptions. This is the check that stops that."""
    import build_site_data as B
    shelf, texts = B.build()
    assert B.SHELF.read_text(encoding="utf-8") == shelf,         "shelf.js is stale - rerun tools/build_site_data.py"
    assert B.TEXTS.read_text(encoding="utf-8") == texts,         "texts.js is stale - rerun tools/build_site_data.py"


def test_the_blocking_file_carries_no_prose(shelf):
    """The whole point of the split: 427KB of descriptions must not be in the
    file that holds up first paint."""
    import build_site_data as B
    blocking = B.SHELF.read_text(encoding="utf-8")
    assert '"why"' not in blocking and "why:" not in blocking
    assert '"src"' not in blocking and "src:" not in blocking
    # ...and it must still carry everything the scoring needs.
    for f in ("t", "a", "y", "f", "tags", "mood", "len", "sty", "dem"):
        assert f'"{f}"' in blocking, f


def test_every_book_has_a_text(shelf):
    import build_site_data as B
    _, texts = B.build()
    # Split on the FIRST statement terminator, not the last: the file now ends
    # with the onTexts callback, and rindex(";") swallowed it into the JSON.
    body = texts.split("window.TEXTS = ", 1)[1].split(";\n", 1)[0]
    have = json.loads(body)
    missing = [b["t"] for b in shelf if b["t"] not in have]
    assert not missing, f"{len(missing)} books have no description entry"


def test_texts_calls_back():
    """The page renders before texts.js arrives, so the data file has to say when
    it landed. A load listener for this was nested inside another handler and
    never fired, and the description shipped blank."""
    import build_site_data as B
    assert B.TEXTS.read_text(encoding="utf-8").rstrip().endswith(
        "if (window.onTexts) window.onTexts();")
    assert "window.onTexts = function" in (ROOT / "index.html").read_text(
        encoding="utf-8")
