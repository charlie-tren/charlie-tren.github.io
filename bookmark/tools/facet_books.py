"""Turn enriched candidates into shelf records, and say which fields are guesses.

    python tools/facet_books.py --facet    # candidates.json -> tools/new_books.json
    python tools/facet_books.py --merge    # append them to books.js

WHAT IS KNOWN AND WHAT IS INFERRED. This distinction is the whole point of the
file, because the footer is only allowed to claim what is true.

  KNOWN, from data:
    t, a   title and author            Wikipedia article + Open Library
    y      first publication year      Wikipedia short description, then OL
    f      fiction or not              the prize's own category
    len    short / middling / long     Open Library median page count
    tags   subject                     OL subjects, mapped onto the sixteen
    why    the description             the existing Wikipedia pipeline

  INFERRED BY RULE, and flagged `soft:1`:
    mood   what it does to you
    sty    prose
    dem    how much work

Those last three are taste. A rule from subject and era gets them roughly right
and cannot get them exactly right, so every record carries `soft:1` and the
scoring halves the penalty for missing on a soft facet. A hand-set facet is a
claim; a soft one is a prior, and they should not weigh the same.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CAND = HERE / "candidates.json"
NEW = HERE / "new_books.json"
BOOKS = ROOT / "books.js"

#: Page count -> the shelf's three length bands, matching how the existing 331
#: were banded (spine width is drawn from this, so the bands have to agree or the
#: shelf stops meaning anything).
def length(pages: int | None) -> str:
    if not pages:
        return "m"
    return "s" if pages < 260 else ("m" if pages <= 450 else "l")


#: subject -> mood. A book takes every mood its subjects imply, which is why the
#: field is a list on the shelf too.
MOOD = {
    "absorb": ["crime", "speculative", "literary", "family", "sport", "travel"],
    "learn": ["history", "science", "technology", "markets", "ideas", "politics",
              "nature", "art"],
    "unsettle": ["war", "politics", "crime"],
}

#: subject -> prose. Only two rules, because a third would be invention: the
#: older literary canon reads slow, reported nonfiction and genre read fast.
RICH = ("literary", "art", "ideas")
PLAIN = ("crime", "sport", "markets", "technology", "travel", "war")

#: subject -> effort.
HARD = ("ideas", "science", "history", "politics")
EASY = ("crime", "sport", "family", "travel")


def facet_one(v: dict) -> dict | None:
    if not v.get("year") or not v.get("author"):
        return None
    tags = [t for t in v["tags"]][:6]
    if not tags:
        return None

    moods = [m for m, ts in MOOD.items() if any(t in tags for t in ts)]
    if not moods:
        moods = ["absorb" if v["f"] == "fic" else "learn"]

    sty = "plain"
    if any(t in tags for t in RICH) and v["year"] < 1990:
        sty = "rich"
    elif any(t in tags for t in RICH) and v["f"] == "fic":
        sty = "rich"
    elif any(t in tags for t in PLAIN):
        sty = "plain"

    dem = 2
    if any(t in tags for t in HARD):
        dem = 3
    if any(t in tags for t in EASY) and not any(t in tags for t in HARD):
        dem = 1
    if v["year"] < 1900:
        dem = min(3, dem + 1)

    return {"t": v["title"], "a": v["author"], "y": int(v["year"]), "f": v["f"],
            "tags": tags, "mood": moods[:3], "len": length(v.get("pages")),
            "sty": sty, "dem": dem, "soft": 1,
            "why": "", "page": v["page"],
            "prizes": v.get("prizes", [])}


def existing() -> set[str]:
    src = BOOKS.read_text(encoding="utf-8")
    return {re.sub(r"[^a-z0-9]", "", m.lower())
            for m in re.findall('{t:"([^"]*)"', src)}


def facet() -> int:
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    have = existing()
    out, skipped = [], {"no year or author": 0, "no subject": 0, "already on": 0}
    seen = set()
    for v in cand.values():
        key = re.sub(r"[^a-z0-9]", "", v["title"].lower())
        if key in have or key in seen:
            skipped["already on"] += 1
            continue
        rec = facet_one(v)
        if rec is None:
            skipped["no year or author" if not (v.get("year") and v.get("author"))
                    else "no subject"] += 1
            continue
        seen.add(key)
        out.append(rec)
    out.sort(key=lambda r: (r["a"], r["t"]))
    NEW.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} new shelf records -> {NEW.name}")
    for k, n in skipped.items():
        print(f"   skipped, {k}: {n}")
    tally: dict[str, int] = {}
    for r in out:
        for t in r["tags"]:
            tally[t] = tally.get(t, 0) + 1
    print("   subjects: " + ", ".join(f"{k} {v}" for k, v in
                                      sorted(tally.items(), key=lambda x: -x[1])))
    lens: dict[str, int] = {}
    for r in out:
        lens[r["len"]] = lens.get(r["len"], 0) + 1
    print(f"   lengths: {lens}    fiction: "
          f"{sum(1 for r in out if r['f'] == 'fic')}/{len(out)}")
    return 0


def describe() -> int:
    """Descriptions for the new records, using the page we already know.

    No matching risk here at all, which is the one nice thing about arriving via a
    prize category: the article is the reason the book is a candidate, so there is
    no search step to get wrong. Every gate the other pipeline needed - is this
    the page I asked for, is its title the book's title, is it a film adaptation -
    exists only because that one starts from a title and has to find the article.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    sys.path.insert(0, str(HERE))
    import fetch_descriptions as F
    import redescribe as R

    recs = json.loads(NEW.read_text(encoding="utf-8"))
    todo = [r for r in recs if not r.get("why")]
    print(f"{len(todo)} of {len(recs)} need a description", flush=True)

    def one(r):
        try:
            w = F.best_description(r["page"], r["t"])
        except Exception as exc:                                   # noqa: BLE001
            return r, "", type(exc).__name__
        # Same refusal as everywhere else, and it lives in ONE function now:
        # three copies of this test had already drifted apart on the ellipsis.
        return r, (w if R.usable(w) else ""), None

    #: Four, not eight. Wikipedia returns 429 above that and the throttle in
    #: fetch_descriptions.get is what keeps this inside the limit.
    errs = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(one, r) for r in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            r, w, err = fut.result()
            if err:
                errs += 1
            r["why"] = w
            # PERCENT-ENCODED. A page title can contain a double quote -
            # Sue Grafton's '"B" Is for Burglar' does - and an unencoded one
            # closed the JS string in books.js 1400 records in.
            r["src"] = ("https://en.wikipedia.org/wiki/"
                        + urllib.parse.quote(r["page"].replace(" ", "_"),
                                             safe="_(),'!$&+;=@~*-."))
            if i % 50 == 0 or i == len(todo):
                NEW.write_text(json.dumps(recs, indent=1, ensure_ascii=False),
                               encoding="utf-8")
                print(f"  {i}/{len(todo)}  described "
                      f"{sum(1 for x in recs if x.get('why'))}", flush=True)
    NEW.write_text(json.dumps(recs, indent=1, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for r in recs if r.get("why"))
    print(f"{ok}/{len(recs)} have a usable description; the rest are dropped")
    # A run where a tenth of the calls THREW is a rate-limit or an outage, not a
    # shelf of books without summaries, and saying so is the difference between
    # rerunning it and shipping 400 silent refusals.
    print(f"requests that failed outright: {errs}"
          + ("   <-- rerun, this is not a real result" if errs > len(todo) / 20 else ""))
    return 0


def esc(x: str) -> str:
    return x.replace("\\", "\\\\").replace('"', '\\"')


def existing_sources() -> set:
    return set(re.findall(r'src:"([^"]*)"', BOOKS.read_text(encoding="utf-8")))


def merge() -> int:
    recs = json.loads(NEW.read_text(encoding="utf-8"))
    recs = [r for r in recs if r.get("why")]
    # DEDUPE ON THE SOURCE PAGE, NOT THE TITLE. A normalised-title key treats
    # "Bad Blood" and "Bad Blood: Secrets and Lies in a Silicon Valley Startup"
    # as different books, and six pairs of the same book reached the shelf that
    # way - each pair citing one Wikipedia article between them. The article IS
    # the identity; the title is just how it was written down that time.
    have_src = existing_sources()
    seen = set()
    kept = []
    for r in recs:
        src = r.get("src", "")
        if src and (src in have_src or src in seen):
            continue
        seen.add(src)
        kept.append(r)
    if len(kept) != len(recs):
        print(f"skipped {len(recs) - len(kept)} already on the shelf under "
              f"another title")
    recs = kept
    if not recs:
        print("Nothing has a description yet - run the description fetch first.")
        return 1
    src = BOOKS.read_text(encoding="utf-8")
    at = src.rindex("]")
    # The record before the insertion point may or may not carry a trailing
    # comma - the purge pass strips it - and appending without checking produced
    # a books.js that failed to parse with "Unexpected token '{'" 500 records in.
    if src[:at].rstrip().endswith("}"):
        cut = src[:at].rstrip()
        src = cut + "," + src[at:]
        at = len(cut) + 1
    lines = []
    for r in recs:
        lines.append(
            '{t:"%s",a:"%s",y:%d,f:"%s",tags:[%s],mood:[%s],len:"%s",sty:"%s",'
            'dem:%d,soft:1,why:"%s",src:"%s"},' % (
                esc(r["t"]), esc(r["a"]), r["y"], r["f"],
                ",".join('"%s"' % t for t in r["tags"]),
                ",".join('"%s"' % m for m in r["mood"]),
                r["len"], r["sty"], r["dem"], esc(r["why"]), esc(r["src"])))
    body = ("\n\n/* ---- Added from prize lists. Title, author, year, length and\n"
            "   subject are read from Wikipedia and Open Library; mood, prose and\n"
            "   effort are inferred by rule and carry soft:1, which halves the\n"
            "   scoring penalty for missing on them. See tools/facet_books.py. */\n"
            + "\n".join(lines).rstrip(","))
    src = src[:at] + body + "\n" + src[at:]
    BOOKS.write_text(src, encoding="utf-8")
    print(f"merged {len(recs)} books; shelf is now {src.count(chr(123) + 't:')}")
    return 0


def main(argv: list[str]) -> int:
    if "--facet" in argv:
        return facet()
    if "--describe" in argv:
        return describe()
    if "--merge" in argv:
        return merge()
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
