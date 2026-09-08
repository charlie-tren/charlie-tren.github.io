"""Harvest books from a prize's own ARTICLE, for the prizes with no category.

    python tools/harvest_lists.py            # adds to tools/candidates.json
    python tools/harvest_lists.py --dry-run  # count them and stop

28 of the 63 prizes in harvest_books.py have no "winning works" category on
Wikipedia, and they are disproportionately the NON-FICTION ones: Baillie
Gifford, Wolfson, the Royal Society, the FT business book, Wainwright, both
travel prizes. That is the whole reason the shelf came out 79% fiction.

HOW, without parsing tables. A prize article links every winner and shortlistee
it names, so the harvest is: take the article's outgoing links, ask Wikidata for
each one's short description in batches of fifty, and keep the ones whose
description says they are a BOOK. Those descriptions are also the cleanest
metadata on the site - "2003 book by Bill Bryson" carries the type, the year and
the author in one string - so nothing has to be inferred from a table's column
order, which is where a table parser would spend all its effort and still be
brittle.

WHAT THIS INCLUDES. Shortlistees as well as winners, because a prize article
names both and the distinction is not recoverable from the links alone. For a
shelf of recommendations that is the right trade: a Baillie Gifford shortlisting
is not a weaker book, it is a book that lost to another good one.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harvest_books as H                                          # noqa: E402

CAND = HERE / "candidates.json"
API = H.API

#: article title -> (form, tags the prize implies). All non-fiction: the fiction
#: prizes that also failed to resolve are left out on purpose, because the shelf
#: is already 79% fiction and adding more would widen the gap this file exists
#: to close.
ARTICLES = {
    "Baillie Gifford Prize": ("non", ["ideas"]),
    "Wolfson History Prize": ("non", ["history"]),
    "Cundill History Prize": ("non", ["history"]),
    "Duff Cooper Prize": ("non", ["history"]),
    "Francis Parkman Prize": ("non", ["history"]),
    "Hessell-Tiltman Prize": ("non", ["history"]),
    "Elizabeth Longford Prize": ("non", ["history", "memoir"]),
    "Royal Society Science Book Prize": ("non", ["science"]),
    "PEN/E. O. Wilson Literary Science Writing Award": ("non", ["science"]),
    "Financial Times Business Book of the Year Award": ("non", ["markets"]),
    "Orwell Prize": ("non", ["politics"]),
    "Wainwright Prize": ("non", ["nature"]),
    "Boardman Tasker Prize for Mountain Literature": ("non", ["nature", "travel"]),
    "Thomas Cook Travel Book Award": ("non", ["travel"]),
    "Dolman Best Travel Book Award": ("non", ["travel"]),
    "William Hill Sports Book of the Year": ("non", ["sport"]),
    "Cricket Society and MCC Book of the Year": ("non", ["sport"]),
    "Anisfield-Wolf Book Award": ("non", ["ideas", "politics"]),
    "Los Angeles Times Book Prize": ("non", ["ideas"]),
    "Pulitzer Prize for Biography or Autobiography": ("non", ["memoir"]),
    "National Book Critics Circle Award": ("non", ["ideas"]),
    "Lionel Gelber Prize": ("non", ["politics"]),
    "Arthur Ross Book Award": ("non", ["politics", "history"]),
    "Hillman Prize": ("non", ["politics"]),
    "Ondaatje Prize": ("non", ["travel"]),
    "Rathbones Folio Prize": ("non", ["ideas"]),
    "PEN/John Kenneth Galbraith Award": ("non", ["ideas"]),
}

#: A description that means "this page is a BOOK". Wikidata writes these to a
#: house pattern - an optional year, up to two qualifiers, then the noun.
IS_BOOK = re.compile(
    r"^(?:\d{4}\s+)?(?:[\w-]+\s+){0,2}"
    r"(book|memoir|autobiography|biography|essay collection|monograph|"
    r"history|treatise|study|travelogue)\b", re.I)

#: ...and one that means it is a PERSON, which the noun test alone lets through:
#: "British non-fiction author and books journalist" starts with a nationality,
#: carries no year, and a bare "contains the word book" test kept it.
#:
#: The life-dates branch deliberately does NOT name the dash. Wikipedia writes
#: "(1933-1973)" with an en dash, a literal one is banned in this estate's
#: source, and the Write tool converts the escape back into a literal - so the
#: test is "a year in brackets followed by anything that is not a digit or a
#: closing bracket", which catches every separator without naming one.
IS_PERSON = re.compile(
    r"\b(novelist|author|writer|journalist|historian|academic|professor"
    r"|critic|broadcaster|poet|publisher|politician|economist|scientist)\b"
    r"|\((?:born|b\.)\s*\d{4}|\(\d{4}[^\d)]", re.I)

YEAR = re.compile(r"\b(1[6-9][0-9]{2}|20[0-2][0-9])\b")
BY = re.compile(r"\bby\s+([A-Z][\w.'-]+(?:\s+[A-Z][\w.'-]+){0,3})")


def links(article: str) -> list[str]:
    out: list[str] = []
    cont = None
    while True:
        u = (API + "?action=query&prop=links&plnamespace=0&pllimit=500"
             "&redirects=1&format=json&titles=" + urllib.parse.quote(article))
        if cont:
            u += "&plcontinue=" + urllib.parse.quote(cont)
        try:
            d = H.get(u)
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ! {article}: {type(exc).__name__}")
            return out
        for p in d.get("query", {}).get("pages", {}).values():
            out += [x["title"] for x in p.get("links", [])]
        cont = d.get("continue", {}).get("plcontinue")
        if not cont:
            return out


def shortdescs(titles: list[str]) -> dict[str, str]:
    """Fifty at a time, which is the API cap for a titles= list."""
    out: dict[str, str] = {}
    for i in range(0, len(titles), 50):
        u = (API + "?action=query&prop=pageprops&ppprop=wikibase-shortdesc"
             "&redirects=1&format=json&titles="
             + urllib.parse.quote("|".join(titles[i:i + 50])))
        try:
            d = H.get(u)
        except Exception:                                          # noqa: BLE001
            continue
        for p in d.get("query", {}).get("pages", {}).values():
            sd = (p.get("pageprops") or {}).get("wikibase-shortdesc", "")
            if sd:
                out[p["title"]] = sd
    return out


def is_a_book(desc: str) -> bool:
    return bool(IS_BOOK.match(desc)) and not IS_PERSON.search(desc)


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    cand = json.loads(CAND.read_text(encoding="utf-8")) if CAND.exists() else {}
    have = H.shelf_titles()
    added = 0

    for article, (form, tags) in ARTICLES.items():
        ls = [t for t in links(article) if not H.NOT_A_BOOK.search(t)]
        books = {t: d for t, d in shortdescs(ls).items() if is_a_book(d)}
        new = 0
        for title, desc in books.items():
            bare = re.sub(r"\s*\([^)]*\)$", "", title)
            if re.sub(r"[^a-z0-9]", "", bare.lower()) in have:
                continue
            rec = cand.get(title)
            if rec is None:
                rec = cand[title] = {
                    "page": title, "title": bare, "f": form,
                    "tags": list(tags), "prize_tags": list(tags),
                    "prizes": [], "desc": desc}
                # Taken straight off the short description where it is there,
                # which saves --enrich a Wikipedia round trip per book.
                y, a = YEAR.search(desc), BY.search(desc)
                if y:
                    rec["year"] = int(y.group(1))
                if a:
                    rec["author"] = a.group(1)
                new += 1
                added += 1
            for t in tags:
                if t not in rec["tags"]:
                    rec["tags"].append(t)
                if t not in rec.setdefault("prize_tags", []):
                    rec["prize_tags"].append(t)
            if article not in rec["prizes"]:
                rec["prizes"].append(article)
        print(f"  {len(ls):>4} links  {len(books):>3} books  {new:>3} new   {article}",
              flush=True)

    if dry:
        print(f"{added} new candidates (dry run, nothing written)")
        return 0
    CAND.write_text(json.dumps(cand, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{added} added; candidates.json now holds {len(cand)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
