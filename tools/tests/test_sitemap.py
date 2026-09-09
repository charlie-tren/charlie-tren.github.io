"""The sitemap must describe what the domain actually serves.

09/09/2026. Search Console reported 115 pages "Discovered - currently not
indexed". Not an error: sitemap.xml was hand-maintained, listed ten URLs, and
Ghostwriters had grown to 135 pages that appeared in no sitemap anywhere. Google
found them by following links, had no priority signal, and deprioritised the lot.

Hand-maintenance could never have held - Ghostwriters gains an essay every day.
"""
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SITEMAP = ROOT / "sitemap.xml"
BUILDER = ROOT / "tools" / "build_sitemap.py"


def _locs() -> list[str]:
    return re.findall(r"<loc>([^<]+)</loc>", SITEMAP.read_text(encoding="utf-8"))


def test_the_sitemap_is_up_to_date():
    """The check the daily job runs. If this fails, someone added a page and did
    not regenerate - which is the exact failure that hid 135 pages."""
    r = subprocess.run([sys.executable, str(BUILDER), "--check"],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr or r.stdout


def test_no_noindex_page_is_submitted():
    """Submitting a noindex page is how you earn 'Excluded by noindex tag' in the
    index report - the sitemap contradicting the page. The redirect stubs
    (/crowdwise/, /one-story/, /the-aftertimes/ ...) all carry noindex."""
    offenders = []
    for loc in _locs():
        rel = loc.replace("https://charlietrenorden.com/", "")
        for cand in (ROOT / rel, ROOT / rel / "index.html"):
            if cand.is_file():
                if "noindex" in cand.read_text(encoding="utf-8", errors="replace"):
                    offenders.append(rel)
                break
    assert not offenders, f"sitemap lists noindex pages: {offenders}"


def test_the_ghostwriters_corpus_is_listed():
    """The 115. Every essay is a real page with its own title and content, and
    every one of them was missing."""
    essays = list((ROOT / "ghostwriters" / "e").glob("*.html"))
    assert essays, "no ghostwriters essays found - has the layout moved?"
    listed = {l for l in _locs() if "/ghostwriters/e/" in l}
    assert len(listed) == len(essays), (
        f"{len(essays)} essays on disk, {len(listed)} in the sitemap")


def test_paths_hosted_in_OTHER_repos_are_still_listed():
    """A generator that walks only this repo drops these silently. It did exactly
    that on its first run, deleting four URLs the hand-written file had carried
    for months: they are served from this domain but live in their own
    repositories, so nothing on disk here proves they exist."""
    locs = set(_locs())
    for p in ("shortfall", "consensus-drift", "lindy-effect", "woop-woop", "photocopy"):
        assert f"https://charlietrenorden.com/{p}/" in locs, f"/{p}/ is missing"


def test_nothing_that_is_not_a_page_is_submitted():
    """Render sources, design mockups and the Search Console verification file are
    files that happen to end in .html. None of them is a page."""
    bad = [l for l in _locs()
           if "/assets/" in l or re.search(r"/(designs\d*|icons\d*)\.html$", l)
           or "google1" in l]
    assert not bad, f"non-pages in the sitemap: {bad}"
