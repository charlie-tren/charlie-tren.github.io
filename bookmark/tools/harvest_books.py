"""Grow the shelf from verifiable lists rather than invention.

    python tools/harvest_books.py --collect     # candidates -> tools/candidates.json
    python tools/harvest_books.py --enrich      # year, length, subjects
    python tools/harvest_books.py --facet       # the shelf's own fields
    python tools/harvest_books.py --merge       # into books.js

WHY PRIZE CATEGORIES. A shelf of 331 hand-picked books cannot be tripled by
picking 700 more out of the air, and a bulk list scraped off a bookseller is
marketing copy with a ranking attached. Wikipedia's prize categories are clean,
machine-readable, spread across form and subject by construction, and every
member already HAS an article - which means the description pipeline that already
exists can describe it, and the provenance of why a book is on the shelf is a
fact rather than a taste claim.

WHAT IS DERIVED AND WHAT IS GUESSED, stated plainly because it changes what the
footer is allowed to say. Derived from data: title, author, first publication
year, page count (Open Library), subjects (Open Library, mapped onto the shelf's
sixteen tags), fiction or not (the prize's own category). Assigned by rule:
mood, prose and effort. Those three are taste, they are now partly mechanical,
and the footer says so.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CAND = HERE / "candidates.json"
UA = "bookmark-shelf/1.0 (https://charlietrenorden.com/bookmark/)"
API = "https://en.wikipedia.org/w/api.php"
OL = "https://openlibrary.org"

#: prize search term -> (is it fiction, tags the prize itself implies).
#: NOT category names. The real ones are spelled with an EN DASH -
#: "Category:Booker Prize-winning works" with a hyphen exists as a redirect and
#: returns zero members, which is how the first run of this file reported 0 across
#: all twenty-two categories and looked like an API problem. The names are
#: resolved by search now, and the resolver prints what it actually used.
PRIZES = {
    "Booker Prize": ("fic", ["literary"]),
    "Pulitzer Prize for Fiction": ("fic", ["literary"]),
    "Pulitzer Prize for General Nonfiction": ("non", ["ideas"]),
    "Pulitzer Prize for History": ("non", ["history"]),
    "Pulitzer Prize for Biography": ("non", ["memoir"]),
    "Hugo Award for Best Novel": ("fic", ["speculative"]),
    "Nebula Award for Best Novel": ("fic", ["speculative"]),
    "National Book Award for Fiction": ("fic", ["literary"]),
    "National Book Award for Nonfiction": ("non", ["ideas"]),
    "Women's Prize for Fiction": ("fic", ["literary"]),
    "Miles Franklin Award": ("fic", ["literary"]),
    "Costa Book Award": ("fic", ["literary"]),
    "Edgar Award": ("fic", ["crime"]),
    "James Tait Black Memorial Prize": ("fic", ["literary"]),
    "Whitbread Award": ("fic", ["literary"]),
    "Royal Society Prize for Science Books": ("non", ["science"]),
    "Wolfson History Prize": ("non", ["history"]),
    "Duff Cooper Prize": ("non", ["history"]),
    "Samuel Johnson Prize": ("non", ["ideas"]),
    "William Hill Sports Book of the Year": ("non", ["sport"]),
    "Wainwright Prize": ("non", ["nature"]),
    "Arthur C. Clarke Award": ("fic", ["speculative"]),
    "Orwell Prize": ("non", ["politics"]),
    "Bancroft Prize": ("non", ["history"]),
    "PEN/Faulkner Award": ("fic", ["literary"]),
}


def resolve_category(prize: str) -> str | None:
    """The category that actually has members, found rather than assumed."""
    u = (API + "?action=query&list=search&srnamespace=14&srlimit=8&format=json"
         "&srsearch=" + urllib.parse.quote(prize + " winning works"))
    try:
        hits = [h["title"][len("Category:"):] for h in get(u)["query"]["search"]]
    except Exception:                                              # noqa: BLE001
        return None
    # Prefer a "winning works" category over a "winners" one: the first holds the
    # BOOKS, the second holds the authors, and picking wrong fills the shelf with
    # biographies.
    hits.sort(key=lambda h: (0 if "winning works" in h.lower() else 1, len(h)))
    for h in hits:
        if "winners" in h.lower() and "winning works" not in h.lower():
            continue
        if members(h, probe=True):
            return h
    return None


#: Article titles that are never a book.
NOT_A_BOOK = re.compile(
    r"^(List of|Category:|Template:|Portal:)|"
    r"\((?:film|TV series|miniseries|play|musical|opera|album|band|award|prize)\)$",
    re.I)


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def members(cat: str, probe: bool = False) -> list[str]:
    out, cont = [], None
    while True:
        u = (API + "?action=query&list=categorymembers&cmtype=page&cmlimit=500"
             "&format=json&cmtitle=" + urllib.parse.quote("Category:" + cat))
        if cont:
            u += "&cmcontinue=" + urllib.parse.quote(cont)
        try:
            d = get(u)
        except Exception as exc:                                   # noqa: BLE001
            print(f"  ! {cat}: {type(exc).__name__}")
            return out
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        cont = d.get("continue", {}).get("cmcontinue")
        if probe or not cont:
            return out


def shelf_titles() -> set[str]:
    src = (ROOT / "books.js").read_text(encoding="utf-8")
    return {re.sub(r"[^a-z0-9]", "", m.lower())
            for m in re.findall('{t:"([^"]*)"', src)}


def collect() -> int:
    have = shelf_titles()
    out, unresolved = {}, []
    for prize, (form, tags) in PRIZES.items():
        cat = resolve_category(prize)
        if not cat:
            unresolved.append(prize)
            print(f"  {'--':>4}  {prize[:52]:54} no category found")
            continue
        ms = [m for m in members(cat) if not NOT_A_BOOK.search(m)]
        added = 0
        for m in ms:
            bare = re.sub(r"\s*\([^)]*\)$", "", m)
            key = re.sub(r"[^a-z0-9]", "", bare.lower())
            if key in have:
                continue
            rec = out.setdefault(m, {"page": m, "title": bare, "f": form,
                                     "tags": list(tags), "prizes": []})
            for t in tags:
                if t not in rec["tags"]:
                    rec["tags"].append(t)
            if prize not in rec["prizes"]:
                rec["prizes"].append(prize)
            added += 1
        print(f"  {len(ms):>4}  {cat[:52]:54} {added} new")
        time.sleep(0.1)
    CAND.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} candidates not already on the shelf -> {CAND.name}")
    if unresolved:
        print("no category for: " + ", ".join(unresolved))
    return 0



#: Per prize, so one long-running award cannot set the shelf's character. The
#: Edgar alone offered 215 crime titles against the Booker's 53, and taking
#: everything would have made a crime shelf with a literary section.
CAP = 55

#: Open Library subject strings -> the shelf's own sixteen tags. Deliberately
#: narrow: a tag that fires on everything is worse than a missing one, because the
#: subject question is a FILTER and a wrong tag puts a book in front of someone who
#: asked not to see it.
SUBJ = {
    "literary": ["literary", "fiction, literary"],
    "crime": ["detective", "mystery", "crime", "thriller", "espionage", "spy"],
    "speculative": ["science fiction", "fantasy", "dystop", "utopia", "space"],
    "history": ["history", "historiography", "civilization"],
    "war": ["war", "military", "world war", "holocaust", "vietnam", "civil war"],
    "politics": ["politic", "government", "presidents", "diplomacy", "election"],
    "markets": ["econom", "business", "finance", "money", "banking", "trade", "wall street"],
    "science": ["science", "physics", "biology", "evolution", "mathemat", "medicine",
                "astronom", "chemistry", "genetic"],
    "technology": ["technolog", "computer", "internet", "engineering", "invention"],
    "ideas": ["philosoph", "psycholog", "sociolog", "religion", "ethic", "essays"],
    "nature": ["natural history", "nature", "environment", "ecology", "animals",
               "birds", "climate", "wilderness"],
    "travel": ["travel", "voyages", "description and travel", "exploration"],
    "memoir": ["biography", "autobiograph", "memoir", "personal narrative", "diaries"],
    "family": ["family", "domestic fiction", "mothers", "fathers", "marriage",
               "childhood", "siblings"],
    "art": ["art", "music", "painting", "architecture", "photograph", "film", "theater"],
    "sport": ["sport", "baseball", "football", "cricket", "boxing", "cycling",
              "athletics", "olympic"],
}


def ol_search(title: str, author: str) -> dict:
    u = (OL + "/search.json?limit=1&fields=first_publish_year,number_of_pages_median,"
         "subject,author_name,title&q=" + urllib.parse.quote(f"{title} {author}".strip()))
    try:
        docs = get(u).get("docs") or []
        return docs[0] if docs else {}
    except Exception:                                              # noqa: BLE001
        return {}


def wiki_facts(page: str) -> dict:
    """Year and author out of the article's own short description and lead."""
    u = (API + "?action=query&prop=extracts|pageprops&exintro=1&explaintext=1"
         "&redirects=1&format=json&titles=" + urllib.parse.quote(page))
    try:
        pg = next(iter(get(u)["query"]["pages"].values()))
    except Exception:                                              # noqa: BLE001
        return {}
    ex = (pg.get("extract") or "")[:400]
    desc = (pg.get("pageprops") or {}).get("wikibase-shortdesc", "")
    # The short description is the reliable place for the year ("2009 novel by
    # Hilary Mantel"); the lead is the fallback and can carry a year that belongs
    # to something the book is ABOUT, so the description is tried first.
    YR = r"\b(1[6-9][0-9]{2}|20[0-2][0-9])\b"
    m = re.search(YR, desc) or re.search(YR, ex)
    year = int(m.group(1)) if m else None

    NAT = (r"American|British|Irish|Australian|Canadian|Scottish|English|Nigerian|"
           r"Indian|Japanese|South African|New Zealand|Welsh|Chinese|Russian")
    ROLE = r"novelist|writer|author|journalist|historian|poet|essayist|playwright"
    NAME = r"[A-Z][\w.'-]+(?: [A-Z][\w.'-]+){0,3}"
    a = (re.search(r"by (?:the )?(?:(?:" + NAT + r") )?(?:(?:" + ROLE + r") )?("
                   + NAME + r")", desc)
         or re.search(r"by (?:the )?(?:(?:" + NAT + r") )?(?:(?:" + ROLE + r") )?("
                      + NAME + r")", ex))
    return {"year": year, "author": a.group(1) if a else "", "desc": desc, "ex": ex}


def enrich() -> int:
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    # apply the cap, keeping the books that several prizes agree on
    by_prize: dict[str, list] = {}
    for k, v in cand.items():
        by_prize.setdefault(v["prizes"][0], []).append(k)
    keep = set()
    for prize, ks in by_prize.items():
        ks.sort(key=lambda k: -len(cand[k]["prizes"]))
        keep.update(ks[:CAP])
    cand = {k: v for k, v in cand.items() if k in keep}
    print(f"{len(cand)} after a cap of {CAP} per prize")

def enrich_one(v: dict) -> dict:
    w = wiki_facts(v["page"])
    v["author"] = w.get("author") or ""
    v["year"] = w.get("year")
    o = ol_search(v["title"], v["author"])
    if not v["author"] and o.get("author_name"):
        v["author"] = o["author_name"][0]
    if not v["year"] and o.get("first_publish_year"):
        v["year"] = o["first_publish_year"]
    v["pages"] = o.get("number_of_pages_median")
    # DROP OPEN LIBRARY'S MACHINE TAGS. Its subject list mixes real subjects with
    # rows like "award:national_book_critics_circle_award=fiction" and "stonewall
    # book awards", and a bare substring test on "war" matches the word AWARD. That
    # one needle tagged 207 books as war books, including Hotel du Lac.
    subs = [x.lower() for x in (o.get("subject") or [])
            if ":" not in x and "=" not in x][:140]
    v["subs"] = subs
    v["tags"] = list(dict.fromkeys(v.get("prize_tags") or v["tags"]))
    for tag, needles in SUBJ.items():
        if tag in v["tags"]:
            continue
        if any(any(hit(n, s) for s in subs) for n in needles):
            v["tags"].append(tag)
    return v


def hit(needle: str, subject: str) -> bool:
    """Whole words, not substrings. "art" inside "departments", "sport" inside
    "transport" and "war" inside "awards" are all the same mistake."""
    return re.search(r"\b" + re.escape(needle), subject) is not None


#: Open Library's search endpoint takes 3 to 6 seconds a call, so sequentially
#: this stage ran for 40 minutes and printed nothing for the first twelve. The
#: work is entirely IO-bound and the two services are independent, so a small
#: pool turns it into minutes. Kept small on purpose - these are free public APIs
#: and there is no reason to lean on them.
WORKERS = 8


def enrich() -> int:
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    # apply the cap, keeping the books that several prizes agree on
    by_prize: dict[str, list] = {}
    for k, v in cand.items():
        by_prize.setdefault(v["prizes"][0], []).append(k)
    keep = set()
    for prize, ks in by_prize.items():
        ks.sort(key=lambda k: -len(cand[k]["prizes"]))
        keep.update(ks[:CAP])
    cand = {k: v for k, v in cand.items() if k in keep}
    print(f"{len(cand)} after a cap of {CAP} per prize", flush=True)

    todo = [k for k, v in cand.items() if "year" not in v]
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(enrich_one, cand[k]): k for k in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            k = futs[fut]
            try:
                cand[k] = fut.result()
            except Exception as exc:                               # noqa: BLE001
                cand[k]["year"] = None
                print(f"  ! {k}: {type(exc).__name__}", flush=True)
            if i % 50 == 0 or i == len(todo):
                CAND.write_text(json.dumps(cand, indent=1, ensure_ascii=False),
                                encoding="utf-8")
                done = sum(1 for x in cand.values() if x.get("year"))
                print(f"  {i}/{len(todo)}  with a year: {done}", flush=True)
    CAND.write_text(json.dumps(cand, indent=1, ensure_ascii=False), encoding="utf-8")
    ok = [v for v in cand.values() if v.get("year") and v.get("author")]
    print(f"{len(ok)}/{len(cand)} have both a year and an author")
    return 0


def main(argv: list[str]) -> int:
    if "--collect" in argv:
        return collect()
    if "--enrich" in argv:
        return enrich()
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
