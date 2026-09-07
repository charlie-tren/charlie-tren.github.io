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


def tight(x: str) -> str:
    """Normalised with the spaces out too, for title containment. Wikipedia
    punctuates numbers and we do not: "Debt: The First 5000 Years" and "Debt: The
    First 5,000 Years" are the same book, and a space-separated comparison called
    them different and threw away a correct match."""
    return re.sub(r"[^a-z0-9]+", "", x.lower())


#: Abbreviations that end in a full stop and are followed by a capital, which a
#: naive split treats as a sentence boundary.
ABBR = ("Mr", "Mrs", "Ms", "Dr", "Prof", "St", "Rev", "Jr", "Sr", "vs", "No", "Vol")


def split_sentences(text: str) -> list[str]:
    """Split on a full stop only where one really ends a sentence.

    An INITIAL is the case that bites: "Disgrace is a 1999 novel by South African
    author J. M. Coetzee" splits after the J, and the description shipped as
    "...by South African author J." A single capital letter before the stop is
    never a sentence end. Done by splitting naively and STITCHING BACK, because
    Python's lookbehind must be fixed width and the guard is not.
    """
    raw = re.split("(?<=[.!?])" + B + "s+(?=[A-Z" + chr(8220) + "])", text.strip())
    out = []
    for part in raw:
        tail = part.rstrip()[:-1].split()[-1] if part.rstrip()[:-1].split() else ""
        if out and (len(prev_tail(out[-1])) == 1 or prev_tail(out[-1]) in ABBR):
            out[-1] = out[-1] + " " + part
        else:
            out.append(part)
        del tail
    return [p.strip() for p in out if p.strip()]


def prev_tail(part: str) -> str:
    """The last word of a fragment, without its trailing stop."""
    body = part.rstrip().rstrip(".!?")
    toks = body.split()
    return toks[-1] if toks else ""



#: Sections that actually say what the book is about. Ordered by how reliably
#: they do it.
SUMMARY_SECTIONS = ("plot", "plot summary", "synopsis", "summary", "story",
                    "overview", "contents", "content", "argument", "arguments",
                    "themes", "theme", "subject", "background and content")


def sections(page: str) -> dict[str, str]:
    """The whole article as plaintext, split on its own headings.

    THE LEAD IS NOT ENOUGH FOR NONFICTION. Wikipedia's opening paragraph on a
    business or science book is largely bibliographic - who wrote it, who
    published it, what it won - so scoring only the lead pushed dozens of entries
    onto the catalogue card: "Antifragile: Things That Gain From Disorder is a book
    by Nassim Nicholas Taleb published on...". What the book argues is in the
    Summary or Contents section, one heading down.
    """
    u = (API + "?action=query&prop=extracts&explaintext=1&redirects=1"
         "&format=json&titles=" + urllib.parse.quote(page))
    try:
        pgs = get(u)["query"]["pages"]
        txt = next(iter(pgs.values())).get("extract", "") or ""
    except Exception:                                              # noqa: BLE001
        return {}
    out, name, buf = {}, "", []
    for line in txt.split(chr(10)):
        m = re.match(r"^==+ *(.+?) *==+$", line.strip())
        if m:
            out[name.lower()] = chr(10).join(buf).strip()
            name, buf = m.group(1), []
        else:
            buf.append(line)
    out[name.lower()] = chr(10).join(buf).strip()
    return out


def best_description(page: str, title: str) -> str:
    """Try the summary sections, then the lead, then the catalogue card."""
    sec = sections(page)
    for want in SUMMARY_SECTIONS:
        body = sec.get(want, "")
        if len(body) > 120:
            cand = useful(body, title, allow_card=False)
            if cand:
                return cand
    lead = sec.get("", "")
    if lead:
        cand = useful(lead, title, allow_card=False)
        if cand:
            return cand
    # Last resort before the byline restatement: any other section at all. Some
    # articles put the whole of what the book says under a heading nobody would
    # guess - "Structure", "The three cities", "Method".
    for name, body in sec.items():
        if name in SUMMARY_SECTIONS or name == "" or len(body) < 160:
            continue
        if any(x in name for x in ("reception", "publication", "adapt", "legacy",
                                   "award", "edition", "reference", "further",
                                   "external", "see also", "bibliograph", "note")):
            continue
        cand = useful(body, title, allow_card=False)
        if cand:
            return cand
    return useful(lead, title) if lead else ""

#: A sentence lifted out of a paragraph can open on a reference to something that
#: is no longer there. "Through these figures, it offers a history of the
#: Troubles" is a good sentence about Say Nothing and a bad first line, because
#: the figures were named in the sentence before it.
DANGLING = re.compile(
    r"^(?:Through these|These|Those|Both|Another|The former|The latter|Here|Such|"
    r"Instead|However|Meanwhile|Nevertheless|Moreover|Additionally|In addition|"
    r"Thereafter|Subsequently|Afterwards)" + B + r"b")

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
        "ranked", "listed", "nobel", "sequel", "prequel", "well received",
        "critics", "accolade", "best-selling", "bestselling", "review",
        "his first book", "her first book", "'s sixth book", "'s fifth book",
        "audiobook", "narrated by", "released on", "hardcover", "paperback",
        "imprint", "isbn", "novelette", "plot points", "the novel expands")


def useful(text: str, title: str, cap: int = MAXLEN, allow_card: bool = True) -> str:
    """Pick the sentence that says what the book is ABOUT.

    Two traps, both hit on the first pass. The lead sentence is the catalogue card
    - "The Road is a 2006 post-apocalyptic novel by American writer Cormac
    McCarthy" - which only restates the byline printed two lines above it. And the
    sentence after it is usually publication history, so blindly taking the second
    gave Gilead "It won the 2005 Pulitzer Prize" and Blood Meridian "McCarthy's
    fifth book, it was published by Random House". Score instead of counting.
    """
    parts = [p.strip() for p in split_sentences(text) if len(p.strip()) > 30]
    # A "sentence" spanning a line break is a list item, a table row or a
    # contents entry, not prose. Born to Run took half a paragraph about a Grand
    # Prix questionnaire that way, and Stories of Your Life took its own table of
    # contents, complete with award notes in brackets.
    parts = [p for p in parts
             if chr(10) not in p and p[:1].isupper()
             and "originally published in" not in p.lower()
             and not DANGLING.match(p)]
    if not parts:
        # Everything was filtered out as non-prose. Returning the raw text here
        # is how a table of contents shipped as a book description.
        return "" if not allow_card else ""

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
    # WHERE EVERYTHING SCORES BADLY, TAKE THE CARD. Some articles have no plot
    # summary in the lead at all, and the alternative is shipping "An audiobook,
    # read by Matthew Waterson, was also released in June 2019" as the reason to
    # read a book. The byline restatement is dull; that is worse.
    if sc(best, parts[best]) < 0:
        # allow_card=False means "I have another section to try" - return nothing
        # rather than the byline restatement, and let the caller move on.
        if not allow_card:
            return ""
        best = 0
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
#: A parenthetical that says the page is about something ADAPTED FROM the book,
#: or about the whole property. "Dune" contains "Dune (franchise)" and "Crime and
#: Punishment" contains "Crime and Punishment (play)", so plain title containment
#: waves both through - and the franchise page describes a media franchise while
#: the play page describes a stage adaptation.
NOT_THE_BOOK = ("(franchise)", "(film)", "(film series)", "(tv series)", "(miniseries)",
                "(play)", "(musical)", "(opera)", "(album)", "(song)", "(band)",
                "(video game)", "(series)", "(character)", "(disambiguation)",
                "(magazine)", "(newspaper)", "(company)")
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
        # THE PAGE'S TITLE MUST BE THE BOOK'S TITLE. Accepting a page that was
        # merely typed as a book let same-author drift straight through: The Old
        # Ways took Underland, Steve Jobs took The Innovators, The Hidden Life of
        # Trees took The Overstory. All three are books, all three name an author,
        # and all three are the wrong book. This check used to live in a separate
        # validate pass, which meant every re-fetch put the bad matches back for
        # the validator to remove again.
        if tight(b["t"]) not in tight(page):
            continue
        if any(q in page.lower() for q in NOT_THE_BOOK):
            continue
        typed = any(w in desc for w in ("novel", "book", "memoir", "essay", "poem",
                                        "non-fiction", "nonfiction", "short story"))
        titled = True
        if na not in norm(ex) and na not in norm(page) and not typed:
            continue
        return {"t": b["t"], "why": best_description(page, b["t"]) or useful(ex, b["t"]),
                "src": s["content_urls"]["desktop"]["page"], "page": page,
                "gate": "titled" if titled else "typed"}
    return None



def rescue(b: dict) -> dict | None:
    """Second pass for the ones the search could not surface.

    Ask Wikipedia for the exact title and nothing else, and require the AUTHOR's
    surname in the result. Strict on purpose: the shelf's "The Outsiders" is
    Thorndike on capital allocation, and "The Outsiders (book)" resolves happily
    to S. E. Hinton's novel, which is typed as a book, reads as a book, and is the
    wrong book. Most of what is left here has no article of its own - Deep Work,
    Ordinary Men and The Living Mountain all redirect to their author - and those
    should stay unmatched rather than take a biography.
    """
    try:
        s = get(REST + urllib.parse.quote(b["t"].replace(" ", "_")))
    except Exception:                                              # noqa: BLE001
        return None
    if s.get("type") != "standard":
        return None
    # A REDIRECT IS A DIFFERENT PAGE. Wikipedia answers "Deep Work" with Cal
    # Newport's biography, whose extract of course names Newport, so an
    # author-name blocklist let it through - "American computer scientist" is not
    # in it and never would have been. The general check is that the page it
    # handed back is the page that was asked for.
    if norm(s["titles"]["normalized"]) != norm(b["t"]):
        return None
    if norm(s["titles"]["normalized"]) == norm(b["a"]):
        return None
    ex = (s.get("extract") or "").strip()
    na = norm(surname(b["a"]))
    if not ex or na not in norm(ex):
        return None
    if any(w in (s.get("description") or "").lower() for w in WHO):
        return None
    return {"t": b["t"], "why": useful(intro(s["titles"]["canonical"]) or ex, b["t"]),
            "src": s["content_urls"]["desktop"]["page"],
            "page": s["titles"]["normalized"], "gate": "exact"}


def validate() -> int:
    """Post-hoc check that each description is about the book it is filed under.

    THE FAILURE THIS CATCHES is same-author drift: The Old Ways took Underland,
    Steve Jobs took The Innovators, and The Hidden Life of Trees took The
    Overstory. Every one passed the fetch-time gate because the page IS a book and
    DOES name an author. The rule that separates them is simply that the page's
    title has to be the book's title.
    """
    have = json.loads(OUT.read_text(encoding="utf-8"))
    books = {b["t"]: b for b in shelf()}
    dropped = []
    for t, v in list(have.items()):
        if not v:
            continue
        if tight(t) not in tight(v["page"]):
            dropped.append((t, v["page"]))
            have[t] = None
    # A page used twice means at most one of them can be right; the title decides.
    seen = {}
    for t, v in list(have.items()):
        if not v:
            continue
        other = seen.get(v["page"])
        if other:
            keep = t if norm(v["page"]).startswith(norm(t)) else other
            drop = other if keep == t else t
            dropped.append((drop, v["page"] + " (duplicate)"))
            have[drop] = None
            seen[v["page"]] = keep
        else:
            seen[v["page"]] = t
    OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"dropped {len(dropped)} that were about a different book:")
    for t, pg in dropped:
        print(f"   {t}  ->  {pg}")
    print(f"{sum(1 for v in have.values() if v)}/{len(have)} still matched")
    return 0


def cull() -> int:
    """Drop anything that is still not a description.

    A pipeline that DEGRADES on a bad source ships a table of contents as the
    reason to read a book. This one refuses instead: the shelf already has a
    hand-written line for every title, so an unmatched book loses nothing, and
    295 good lines plus 36 honest ones beats 331 where a dozen are junk.
    """
    have = json.loads(OUT.read_text(encoding="utf-8"))
    out = []
    for t, v in list(have.items()):
        if not v:
            continue
        w = v["why"]
        why_bad = None
        if chr(10) in w or not w[:1].isupper():
            why_bad = "not prose"
        elif any(j in w.lower() for j in JUNK):
            why_bad = "publication trivia"
        elif re.match("^" + re.escape(t) + ".{0,70}?" + B + "b(?:is|was) an? ", w):
            why_bad = "restates the byline"
        elif len(w) < 55:
            why_bad = "too short to say anything"
        if why_bad:
            out.append((t, why_bad)); have[t] = None
    OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"culled {len(out)}; they keep their hand-written line")
    for t, r in out:
        print(f"   {t[:34]:36} {r}")
    print(f"{sum(1 for v in have.values() if v)}/{len(have)} sourced")
    return 0


def esc(x: str) -> str:
    return x.replace(B, B + B).replace('"', B + '"')


def apply() -> int:
    """Rewrite books.js in place: swap each why: for the sourced line and add a
    src: link. Books with no match keep the line they have and carry no src, so
    the page can tell the two apart and credit only what it took."""
    have = json.loads(OUT.read_text(encoding="utf-8"))
    src = BOOKS.read_text(encoding="utf-8")
    done = kept = 0

    def sub(m):
        nonlocal done, kept
        title = m.group(1).replace(B + '"', '"')
        rec = have.get(title)
        if not rec:
            kept += 1
            return m.group(0)
        done += 1
        return (m.group(0)[:m.start(2) - m.start(0)] + esc(rec["why"])
                + '",src:"' + rec["src"] + m.group(0)[m.end(2) - m.start(0):])

    pat = (B + '{t:"((?:[^"' + B + B + ']|' + B + B + '.)*)".*?why:"((?:[^"'
           + B + B + ']|' + B + B + '.)*)"')
    src = re.sub(pat, sub, src, flags=re.S)
    BOOKS.write_text(src, encoding="utf-8")
    print(f"rewrote {done} descriptions, kept {kept} hand-written")
    return 0


def main(argv: list[str]) -> int:
    if "--apply" in argv:
        return apply()
    books = shelf()
    print(f"{len(books)} books on the shelf")
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    if "--cull" in argv:
        return cull()
    if "--validate" in argv:
        return validate()
    if "--rescore" in argv:
        # The junk list is a blocklist, so it leaks, and the leaks only show once
        # you read 311 of them. Rather than re-fetch the shelf, re-score the lead
        # section for the handful whose chosen sentence still trips it.
        only_junk = "--all" not in argv
        bad = [b for b in books if have.get(b["t"])
               and (not only_junk
                    or any(j in have[b["t"]]["why"].lower() for j in JUNK))]
        print(f"re-scoring {len(bad)}")
        for b in bad:
            rec = have[b["t"]]
            txt = intro(rec["page"])
            if not txt:
                continue
            new = best_description(rec["page"], b["t"]) or useful(txt, b["t"])
            if new != rec["why"]:
                print(f"  {b['t'][:26]:28} | {new[:92]}")
                rec["why"] = new
            time.sleep(0.12)
        OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
        return 0
    if "--rescue" in argv:
        left = [b for b in books if not have.get(b["t"])]
        print(f"retrying {len(left)} unmatched with an exact-title lookup")
        for b in left:
            r = rescue(b)
            if r:
                have[b["t"]] = r
                print(f"  + {b['t']}: {r['why'][:90]}")
            time.sleep(0.12)
        OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
        got = sum(1 for v in have.values() if v)
        print(f"now matched {got}/{len(have)}")
        return 0
    todo = [b for b in books if not have.get(b["t"])]
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
