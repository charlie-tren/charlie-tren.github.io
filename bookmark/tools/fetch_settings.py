"""Where each book is set, from Open Library's own `place` field.

    python tools/fetch_settings.py             # -> tools/settings.json
    python tools/fetch_settings.py --apply     # add set:[...] to books.js

Open Library indexes a `place` list per work, which is a cataloguer's answer to
exactly this question and is far better than anything guessable from the subject
list: Wolf Hall returns Great Britain / England / Putney / Westminster, Things
Fall Apart returns Umuofia / Nigeria / Mbanta. Those are mapped onto eight broad
regions, because eight is the most a reader will scan and a country-level answer
would be an empty shelf on most of them.

A book with no place stays UNPLACED and carries no setting. That is not a gap to
be filled with a guess - roughly a third of the shelf is genuinely unplaceable
(invented worlds, essays, ideas) and saying so is the honest answer. The question
is scored rather than filtered, so an unplaced book is never penalised for it.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BOOKS = ROOT / "books.js"
NEW = HERE / "new_books.json"
OUT = HERE / "settings.json"
UA = "bookmark-shelf/1.0 (https://charlietrenorden.com/bookmark/)"
OL = "https://openlibrary.org"
WORKERS = 8

#: place name -> region. Matched on whole words against each place string, so
#: "Ireland" does not fire on "Northern Ireland"... it does, and should: both are
#: the same region here. What the word boundary stops is "India" inside
#: "Indiana", which is two different continents.
GAZ = {
    "britain": ["england", "scotland", "wales", "britain", "great britain",
                "united kingdom", "ireland", "london", "edinburgh", "dublin",
                "yorkshire", "cornwall", "oxford", "cambridge", "glasgow",
                "manchester", "liverpool", "belfast", "hebrides", "isle of"],
    "america": ["united states", "america", "new york", "california", "chicago",
                "boston", "washington", "texas", "mississippi", "louisiana",
                "maine", "montana", "alaska", "canada", "ontario", "quebec",
                "toronto", "los angeles", "san francisco", "philadelphia",
                "detroit", "appalachia", "new england", "brooklyn", "harlem",
                "seattle", "vermont", "iowa", "nebraska", "kansas", "ohio",
                "virginia", "carolina", "georgia", "florida", "alabama",
                "tennessee", "kentucky", "missouri", "oklahoma", "arizona",
                "nevada", "utah", "colorado", "wyoming", "dakota", "michigan",
                "wisconsin", "minnesota", "illinois", "indiana", "maryland",
                "new jersey", "pennsylvania", "connecticut", "massachusetts"],
    "europe": ["france", "germany", "italy", "spain", "portugal", "greece",
               "russia", "soviet union", "poland", "netherlands", "holland",
               "belgium", "austria", "hungary", "czech", "sweden", "norway",
               "denmark", "finland", "iceland", "switzerland", "yugoslavia",
               "serbia", "croatia", "romania", "bulgaria", "ukraine", "paris",
               "berlin", "rome", "madrid", "vienna", "prague", "moscow",
               "amsterdam", "venice", "naples", "sicily", "lisbon", "athens",
               "warsaw", "budapest", "istanbul", "europe", "balkans"],
    "asia": ["china", "japan", "india", "korea", "vietnam", "thailand",
             "indonesia", "malaysia", "philippines", "pakistan", "bangladesh",
             "sri lanka", "nepal", "burma", "myanmar", "cambodia", "laos",
             "singapore", "taiwan", "hong kong", "tokyo", "beijing", "shanghai",
             "delhi", "bombay", "mumbai", "calcutta", "kolkata", "seoul",
             "saigon", "asia", "siberia", "mongolia", "tibet", "afghanistan"],
    "africa": ["nigeria", "kenya", "south africa", "egypt", "ethiopia", "ghana",
               "sudan", "somalia", "zimbabwe", "rhodesia", "congo", "uganda",
               "tanzania", "zambia", "mozambique", "angola", "senegal", "mali",
               "morocco", "algeria", "tunisia", "libya", "sierra leone",
               "rwanda", "botswana", "namibia", "cameroon", "lagos", "nairobi",
               "cairo", "johannesburg", "cape town", "africa", "sahara"],
    "latam": ["mexico", "brazil", "argentina", "chile", "peru", "colombia",
              "cuba", "venezuela", "bolivia", "ecuador", "uruguay", "paraguay",
              "guatemala", "nicaragua", "honduras", "panama", "haiti",
              "dominican republic", "jamaica", "trinidad", "caribbean",
              "puerto rico", "barbados", "antigua", "mexico city", "rio de janeiro",
              "buenos aires", "havana", "lima", "bogota", "patagonia",
              "amazon", "andes", "west indies", "latin america"],
    "oceania": ["australia", "new zealand", "tasmania", "sydney", "melbourne",
                "queensland", "victoria", "new south wales", "western australia",
                "south australia", "northern territory", "auckland",
                "papua new guinea", "fiji", "samoa", "tahiti", "polynesia",
                "outback", "pacific islands"],
    "mideast": ["israel", "palestine", "lebanon", "syria", "iraq", "iran",
                "turkey", "saudi arabia", "jordan", "yemen", "kuwait",
                "jerusalem", "beirut", "baghdad", "tehran", "damascus",
                "middle east", "persia", "arabia", "united arab emirates"],
}


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def regions(places: list[str]) -> list[str]:
    """Whole-word matching. The substring version of this is the mistake that
    tagged 207 books as war books because "awards" contains "war"."""
    low = [p.lower() for p in places]
    out = []
    for region, names in GAZ.items():
        for n in names:
            if any(re.search(r"\b" + re.escape(n) + r"\b", p) for p in low):
                out.append(region)
                break
    return out


def look(title: str, author: str) -> list[str]:
    u = (OL + "/search.json?limit=1&fields=place&q="
         + urllib.parse.quote(f"{title} {author}".strip()))
    try:
        docs = get(u).get("docs") or []
    except Exception:                                              # noqa: BLE001
        return []
    return (docs[0].get("place") if docs else None) or []


def shelf() -> list[tuple[str, str]]:
    src = BOOKS.read_text(encoding="utf-8")
    return [(m.group(1), m.group(2)) for m in
            re.finditer(r'\{t:"((?:[^"\\]|\\.)*)",a:"((?:[^"\\]|\\.)*)"', src)]


def collect() -> int:
    pairs = shelf()
    if NEW.exists():
        pairs += [(r["t"], r["a"]) for r in
                  json.loads(NEW.read_text(encoding="utf-8"))]
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [(t, a) for t, a in pairs if t not in have]
    print(f"{len(pairs)} books, {len(todo)} to look up", flush=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(look, t, a): t for t, a in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            t = futs[fut]
            try:
                places = fut.result()
            except Exception:                                      # noqa: BLE001
                places = []
            have[t] = {"places": places[:10], "set": regions(places)}
            if i % 100 == 0 or i == len(todo):
                OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False),
                               encoding="utf-8")
                placed = sum(1 for v in have.values() if v["set"])
                print(f"  {i}/{len(todo)}  placed {placed}", flush=True)
    OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
    tally: dict[str, int] = {}
    for v in have.values():
        for r in v["set"]:
            tally[r] = tally.get(r, 0) + 1
    placed = sum(1 for v in have.values() if v["set"])
    print(f"\n{placed}/{len(have)} placed, {len(have) - placed} unplaceable")
    print("   " + ", ".join(f"{k} {n}" for k, n in
                            sorted(tally.items(), key=lambda x: -x[1])))
    return 0


def apply() -> int:
    have = json.loads(OUT.read_text(encoding="utf-8"))
    src = BOOKS.read_text(encoding="utf-8")
    done = 0

    def sub(m):
        nonlocal done
        title = m.group(1).replace('\\"', '"')
        rec = have.get(title)
        if not rec or not rec["set"] or ",set:[" in m.group(0):
            return m.group(0)
        done += 1
        return (m.group(0) + ',set:['
                + ",".join('"%s"' % r for r in rec["set"]) + "]")

    src = re.sub(r'\{t:"((?:[^"\\]|\\.)*)",a:"(?:[^"\\]|\\.)*",y:-?\d+', sub, src)
    BOOKS.write_text(src, encoding="utf-8")
    print(f"added a setting to {done} books on the shelf")
    return 0


def main(argv: list[str]) -> int:
    if "--apply" in argv:
        return apply()
    return collect()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
