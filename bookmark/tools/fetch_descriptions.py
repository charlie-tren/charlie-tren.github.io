"""Replace the hand-written one-liners on the shelf with sourced ones.

    python tools/fetch_descriptions.py            # writes tools/descriptions.json
    python tools/fetch_descriptions.py --apply    # then rewrites books.js

WHY WIKIPEDIA AND NOT A BOOKSELLER. A publisher blurb is marketing copy and it is
copyright; scraping 331 of them would be both. Wikipedia's lead sentence is
factual, is CC BY-SA, and can be attributed - which is why every book that takes
one also stores the page URL, and the page credits it. Anything that cannot be
matched keeps the line it has and is listed at the end for a hand pass.

MATCHING IS THE HARD PART, not fetching. "The Road" and "Chronicles: Volume One"
both resolve to something on a plain title search, and it is the wrong thing. A
candidate is only accepted if the extract or the title names the author, or the
page is explicitly typed as a book - otherwise it is reported as unmatched rather
than quietly writing a description of a film.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books.js"
OUT = Path(__file__).resolve().parent / "descriptions.json"

UA = "bookmark-shelf/1.0 (https://charlietrenorden.com/bookmark/)"
API = "https://en.wikipedia.org/w/api.php"
REST = "https://en.wikipedia.org/api/rest_v1/page/summary/"
MAXLEN = 190


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


B = chr(92)   # heredocs eat backslashes; the pattern is built rather than typed


def shelf() -> list[dict]:
    """Read the records out of books.js without running it."""
    src = BOOKS.read_text(encoding="utf-8")
    body = src[src.index("window.SHELF = [") + len("window.SHELF = ["):]
    body = body[:body.rindex("]")]
    out = []
    pat = (B + '{t:"((?:[^"' + B + B + ']|' + B + B + '.)*)",a:"((?:[^"' + B + B + ']|' + B + B + '.)*)",y:(-?' + B + 'd+)')
    for m in re.finditer(pat, body):
        out.append({"t": m.group(1).replace(B + '"', '"'),
                    "a": m.group(2).replace(B + '"', '"'),
                    "y": int(m.group(3))})
    return out


def surname(a: str) -> str:
    return a.split(" and ")[0].strip().split()[-1]


def search(title: str, author: str) -> list[str]:
    """Titles worth trying, most specific first."""
    qs = [f'"{title}" {author} book', f"{title} {surname(author)} novel", f"{title} book"]
    seen, out = set(), []
    for q in qs:
        u = (API + "?action=query&list=search&format=json&srlimit=5&srsearch="
             + urllib.parse.quote(q))
        try:
            hits = get(u)["query"]["search"]
        except Exception:                                          # noqa: BLE001
            continue
        for h in hits:
            if h["title"] not in seen:
                seen.add(h["title"]); out.append(h["title"])
        if out:
            break
    return out[:6]


def norm(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()


#: A sentence that carries what the book IS ABOUT.
GOOD = ("tells the story", "follows", "set in", "recounts", "explores", "chronicles",
        "describes", "centres on", "centers on", "depicts", "traces", "concerns",
        "narrat", "protagonist", "argues", "examines", "account of", "story of",
        "history of", "portrait of", "is about", "charts", "documents", "the plot",
        "revolves", "takes place", "investigat", "the narrator")
#: Publication history, prizes and sales. All true, none of them a description -
#: and the lead paragraph of a well-known book is largely made of them.
JUNK = ("prize", "award", "shortlist", "longlist", "bestseller", "best-seller",
        "published by", "publisher", "first published", "printing", "adapted",
        "adaptation", "film", "translat", "edition", "sold", "copies", "serialis",
        "serializ", "reprint", "won the", "nominated", "acclaim", "reception",
        "ranked", "listed")


def useful(text: str, title: str, cap: int = MAXLEN) -> str:
    """Pick the sentence that says what the book is ABOUT.

    Two traps, both hit on the first pass. The lead sentence is the catalogue card
    - "The Road is a 2006 post-apocalyptic novel by American writer Cormac
    McCarthy" - which only restates the byline printed two lines above it. And the
    sentence after it is usually publication history, so blindly taking the second
    gave Gilead "It won the 2005 Pulitzer Prize" and Blood Meridian "McCarthy's
    fifth book, it was published by Random House". Score instead of counting.
    """
    parts = [p.strip() for p in
             re.split(r"(?<=[.!?])" + B + r"s+(?=[A-Z" + chr(8220) + "])", text.strip())
             if len(p.strip()) > 30]
    if not parts:
        return text.strip()[:cap]

    def sc(i, p):
        low = p.lower()
        s = sum(3 for g in GOOD if g in low) - sum(2 for j in JUNK if j in low)
        if re.match(r"^.{0,90}?" + B + r"b(?:is|was)" + B + r"s+(?:a|an|the)" + B + r"b", p):
            s -= 4                      # the catalogue card
        s -= i * 0.4                    # earlier is better, all else equal
        if len(p) < 60:
            s -= 2
        return s

    best = max(range(len(parts)), key=lambda i: sc(i, parts[i]))
    out = parts[best]
    if len(out) < 85 and best + 1 < len(parts):
        out = out + " " + parts[best + 1]
    if len(out) > cap:
        out = out[:cap].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return out


def intro(page: str) -> str:
    """The whole lead section, not the 2-4 sentence REST summary. Scoring needs
    something to choose between."""
    u = (API + "?action=query&prop=extracts&exintro=1&explaintext=1&redirects=1"
         "&format=json&titles=" + urllib.parse.quote(page))
    try:
        pgs = get(u)["query"]["pages"]
        return next(iter(pgs.values())).get("extract", "") or ""
    except Exception:                                              # noqa: BLE001
        return ""


BAD = ("may refer to", "disambiguation")
#: Page descriptions that mean the article is about a PERSON, not their book.
WHO = ("writer", "novelist", "author", "journalist", "historian", "poet",
       "essayist", "biographer", "economist", "philosopher", "playwright")


def describe(b: dict) -> dict | None:
    nt, na = norm(b["t"]), norm(surname(b["a"]))
    pages = search(b["t"], b["a"])
    # An exact title match is worth trying before anything the search ranked above
    # it: the search API happily puts the AUTHOR's page first for a famous name.
    pages.sort(key=lambda p: 0 if norm(p).startswith(nt) else 1)
    for page in pages:
        try:
            s = get(REST + urllib.parse.quote(page.replace(" ", "_")))
        except Exception:                                          # noqa: BLE001
            continue
        if s.get("type") == "disambiguation":
            continue
        ex = (s.get("extract") or "").strip()
        if not ex or any(x in ex[:80].lower() for x in BAD):
            continue
        desc = (s.get("description") or "").lower()

        # REJECT THE AUTHOR'S OWN PAGE. The first gate here asked only whether the
        # extract named the author, which every biography does - so Stoner took
        # "John Edward Williams was an American author" and The Remains of the Day
        # took Kazuo Ishiguro. Both read fine until you know the book.
        if norm(b["a"]) in norm(page) or any(w in desc for w in WHO):
            continue
        # The page must be ABOUT this book: its title says so, or the lead does,
        # or Wikidata types it as one.
        titled = norm(page).startswith(nt) or nt in norm(ex[:170])
        typed = any(w in desc for w in ("novel", "book", "memoir", "essay", "poem",
                                        "non-fiction", "nonfiction", "short story"))
        if not (titled or typed):
            continue
        if na not in norm(ex) and na not in norm(page) and not typed:
            continue
        full = intro(page) or ex
        return {"t": b["t"], "why": useful(full, b["t"]),
                "src": s["content_urls"]["desktop"]["page"], "page": page,
                "gate": "titled" if titled else "typed"}
    return None


def main(argv: list[str]) -> int:
    books = shelf()
    print(f"{len(books)} books on the shelf")
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [b for b in books if b["t"] not in have]
    print(f"{len(have)} already fetched, {len(todo)} to go")
    for i, b in enumerate(todo, 1):
        try:
            r = describe(b)
        except Exception as exc:                                   # noqa: BLE001
            r = None
            print(f"  ! {b['t']}: {type(exc).__name__}")
        have[b["t"]] = r
        if i % 20 == 0 or i == len(todo):
            OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
            got = sum(1 for v in have.values() if v)
            print(f"  {i}/{len(todo)}  matched {got}/{len(have)}")
        time.sleep(0.12)
    OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
    miss = [t for t, v in have.items() if not v]
    print(f"\nmatched {len(have) - len(miss)}/{len(have)}; {len(miss)} unmatched")
    for t in miss[:40]:
        print("   -", t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
