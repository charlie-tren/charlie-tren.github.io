"""Re-derive every description on the shelf, in place.

    python tools/redescribe.py            # -> tools/redescribed.json
    python tools/redescribe.py --apply    # write them into books.js

Runs when the SELECTION rules change rather than when the data does. The books
each already carry the Wikipedia page their line came from, in `src`, so there is
no matching step here at all - only re-running the sentence scorer over the same
articles. That is what makes a rule change cheap: the expensive half of the
pipeline is finding the right article, and it is already done.

Why it exists: descriptions were cut at 190 characters with an ellipsis, which
left a third of the shelf trailing off mid-clause. Removing the cut changed which
sentence wins for every book, not just the ones that were cut.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BOOKS = ROOT / "books.js"
OUT = HERE / "redescribed.json"
WORKERS = 4   # Wikipedia 429s above this; see fetch_descriptions.get

sys.path.insert(0, str(HERE))
import fetch_descriptions as F                                     # noqa: E402


def shelf() -> list[dict]:
    src = BOOKS.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'\{t:"((?:[^"\\]|\\.)*)".*?src:"([^"]*)"', src):
        page = urllib.parse.unquote(m.group(2).rsplit("/", 1)[-1]).replace("_", " ")
        out.append({"t": m.group(1).replace('\\"', '"'), "page": page})
    return out


def usable(w: str) -> bool:
    """Same refusal as the fetch pipeline, in one place."""
    if not w or len(w) < 55:
        return False
    if chr(10) in w or not w[:1].isupper():
        return False
    if w.endswith("..."):
        return False
    if F.DANGLING.match(w):
        return False
    return not any(j in w.lower() for j in F.JUNK)


def one(b: dict) -> dict:
    try:
        w = F.best_description(b["page"], b["t"])
    except Exception as exc:                                       # noqa: BLE001
        # Distinguished from an empty result on purpose. Swallowing a 429 into the
        # same bucket as "this article has no summary" is what produced 433 false
        # refusals in one run.
        return {"t": b["t"], "why": "", "err": type(exc).__name__}
    return {"t": b["t"], "why": w if usable(w) else ""}


def collect() -> int:
    books = shelf()
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [b for b in books if b["t"] not in have]
    print(f"{len(books)} on the shelf, {len(todo)} to re-derive", flush=True)
    errs = [0]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = [pool.submit(one, b) for b in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            if r.get("err"):
                errs[0] += 1
            have[r["t"]] = r["why"]
            if i % 100 == 0 or i == len(todo):
                OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False),
                               encoding="utf-8")
                print(f"  {i}/{len(todo)}  usable {sum(1 for v in have.values() if v)}",
                      flush=True)
    OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for v in have.values() if v)
    trail = sum(1 for v in have.values() if v.endswith("..."))
    print(f"\n{ok}/{len(have)} usable, {len(have) - ok} kept their existing line")
    print(f"still trailing off: {trail}")
    print(f"requests that failed outright: {errs[0]}"
          + ("   <-- rerun, this is not a real result" if errs[0] > len(todo) / 20 else ""))
    return 0


def apply() -> int:
    have = json.loads(OUT.read_text(encoding="utf-8"))
    src = BOOKS.read_text(encoding="utf-8")
    done = 0

    def sub(m):
        nonlocal done
        title = m.group(1).replace('\\"', '"')
        new = have.get(title)
        if not new:
            return m.group(0)
        done += 1
        return (m.group(0)[:m.start(2) - m.start(0)]
                + new.replace("\\", "\\\\").replace('"', '\\"')
                + m.group(0)[m.end(2) - m.start(0):])

    src = re.sub(r'\{t:"((?:[^"\\]|\\.)*)".*?why:"((?:[^"\\]|\\.)*)"', sub, src)
    BOOKS.write_text(src, encoding="utf-8")
    print(f"rewrote {done} descriptions")
    return 0


if __name__ == "__main__":
    raise SystemExit(apply() if "--apply" in sys.argv[1:] else collect())
