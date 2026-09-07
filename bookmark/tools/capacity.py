"""How many questions can a shelf of this size actually support?

    python tools/capacity.py

The question "should we ask more to make it more bespoke" has a measurable
answer, and it is not the same answer at 331 books as at 950. What binds is not
the NUMBER of questions but which kind: form and subject are hard FILTERS and
divide the shelf, everything else is scored and merely reorders it. So the test
is the size of the shortlist in the narrowest answer a real person would give.
"""
from __future__ import annotations

import json
import re
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
B = chr(92)


def shelf() -> list[dict]:
    src = (ROOT / "books.js").read_text(encoding="utf-8")
    body = src[src.index("window.SHELF = ["):]
    pat = (B + '{t:"((?:[^"' + B + B + ']|' + B + B + '.)*)",a:"((?:[^"' + B + B
           + ']|' + B + B + '.)*)",y:(-?' + B + 'd+),f:"(' + B + 'w+)",tags:'
           + B + '[([^' + B + ']]*)' + B + '],mood:' + B + '[([^' + B + ']]*)'
           + B + '],len:"(' + B + 'w)",sty:"(' + B + 'w+)",dem:(' + B + 'd)')
    out = []
    for m in re.finditer(pat, body):
        out.append({"t": m.group(1), "y": int(m.group(3)), "f": m.group(4),
                    "tags": re.findall('"([^"]+)"', m.group(5)),
                    "mood": re.findall('"([^"]+)"', m.group(6)),
                    "len": m.group(7), "sty": m.group(8), "dem": int(m.group(9)),
                    "soft": 0})
    return out


def pending() -> list[dict]:
    p = HERE / "new_books.json"
    if not p.exists():
        return []
    return [dict(r, soft=1) for r in json.loads(p.read_text(encoding="utf-8"))]


TAGS = ["literary", "crime", "speculative", "history", "war", "politics",
        "markets", "science", "technology", "ideas", "nature", "travel",
        "memoir", "family", "art", "sport"]
LENORD = {"s": 0, "m": 1, "l": 2}


def era(b):
    return "contemporary" if b["y"] >= 2005 else ("modern" if b["y"] >= 1945 else "older")


def eligible(books, st):
    out = []
    for b in books:
        if st["form"] != "any" and b["f"] != st["form"]:
            continue
        if st["tags"] and not any(t in b["tags"] for t in st["tags"]):
            continue
        out.append(b)
    return out


def score(b, st):
    s = 0.0
    soft = 0.5 if b.get("soft") else 1.0
    hits = sum(1 for m in st["mood"] if m in b["mood"])
    s += hits * 3
    if not hits:
        s -= 3 * soft
    if st["len"] != "any":
        s += 3 if b["len"] == st["len"] else (
            -1.5 if abs(LENORD[b["len"]] - LENORD[st["len"]]) == 1 else -4)
    if st["era"] != "any":
        s += 3 if era(b) == st["era"] else -3
    if st["sty"] != "any":
        s += 3 if b["sty"] == st["sty"] else -1 * soft
    s -= abs(b["dem"] - st["dem"]) * 1.6 * soft
    s += sum(2.5 for t in st["tags"] if t in b["tags"])
    return s


def shortlist(books, st):
    pool = eligible(books, st)
    if not pool:
        return []
    ranked = sorted(((score(b, st), i, b) for i, b in enumerate(pool)),
                    key=lambda x: (-x[0], x[1]))
    best = ranked[0][0]
    band = [r for r in ranked if r[0] >= best - 6]
    if len(band) < 6:
        band = ranked[:6]
    return [r[2] for r in band[:30]]


def sweep(books, label):
    """Every answer a real person might give, one subject at a time plus a
    two-subject case, and the resulting shortlist size."""
    sizes = []
    empties = 0
    for form, ln, er, sty, dem, tag in product(
            ["any", "fic", "non"], ["any", "s", "m", "l"],
            ["any", "contemporary", "modern", "older"],
            ["any", "plain", "rich", "funny"], [1, 2, 3],
            [[]] + [[t] for t in TAGS]):
        st = {"mood": ["absorb"], "form": form, "len": ln, "era": er,
              "sty": sty, "dem": dem, "tags": tag}
        n = len(shortlist(books, st))
        sizes.append(n)
        if n == 0:
            empties += 1
    sizes.sort()
    n = len(sizes)
    print(f"{label}: {len(books)} books over {n} answer combinations")
    print(f"   shortlist size   p1 {sizes[n//100]}   p5 {sizes[n//20]}   "
          f"median {sizes[n//2]}   p95 {sizes[19*n//20]}")
    print(f"   empty shelves    {empties} ({100*empties/n:.1f}%)")
    print(f"   under 10 books   {sum(1 for x in sizes if x < 10)} "
          f"({100*sum(1 for x in sizes if x < 10)/n:.1f}%)")
    return sizes


if __name__ == "__main__":
    now = shelf()
    print(f"read {len(now)} books off the shelf\n")
    sweep(now, "TODAY")
    print()
    grown = now + pending()
    if len(grown) > len(now):
        sweep(grown, "GROWN")
