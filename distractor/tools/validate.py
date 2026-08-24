"""Check the question bank against the schema and the exam's own stem conventions.

Run from the distractor directory:  python tools/validate.py
Exits 1 on any error. Warnings do not fail the build.
"""

import json
import pathlib
import re
import sys

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

QUALIFIERS = [
    "most likely", "least likely", "best described", "most appropriate",
    "most accurate", "least appropriate", "least accurate", "closest to",
    "most directly", "most consistent",
]

# Forms the Level I exam does not use. Each is a regex against the lower-cased stem.
BANNED = {
    r"\bexcept\b": "the exam does not use 'except'",
    r"all of the above": "the exam does not offer 'all of the above'",
    r"\ba and b\b": "the exam does not offer combination answers",
    r"\bnone of the above\b": "the exam does not offer 'none of the above'",
    r"which of the following is (true|false)": "the exam does not use true or false",
}

LONG_DASHES = (chr(0x2014), chr(0x2013))

errors: list[str] = []
warnings: list[str] = []


def main() -> int:
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    seen_ids: dict[str, str] = {}
    counts = {}

    for topic in index["topics"]:
        key = topic["key"]
        path = DATA / f"{key}.json"
        if not path.exists():
            errors.append(f"{key}: no data file")
            continue
        try:
            questions = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{key}.json: invalid JSON, {exc}")
            continue

        counts[key] = len(questions)
        for q in questions:
            check(q, key, seen_ids)

    total = sum(counts.values())
    target = sum(t["target"] for t in index["topics"])

    print(f"{'topic':<12}{'have':>6}{'target':>8}")
    for topic in index["topics"]:
        key = topic["key"]
        have = counts.get(key, 0)
        gap = "" if have >= topic["target"] else f"  need {topic['target'] - have} more"
        print(f"{key:<12}{have:>6}{topic['target']:>8}{gap}")
    print(f"{'TOTAL':<12}{total:>6}{target:>8}")

    for w in warnings:
        print(f"warning  {w}")
    for e in errors:
        print(f"ERROR    {e}")

    if errors:
        print(f"\n{len(errors)} error(s).")
        return 1
    print(f"\nNo errors. {len(warnings)} warning(s). {total} of {target} questions written.")
    return 0


def check(q, key, seen_ids) -> None:
    qid = q.get("id", "<missing id>")
    where = f"{key}/{qid}"

    for field in ("id", "ref", "stem", "choices", "answer", "solution", "distractors"):
        if field not in q:
            errors.append(f"{where}: missing '{field}'")
            return

    if qid in seen_ids:
        errors.append(f"{where}: duplicate id, already used in {seen_ids[qid]}")
    seen_ids[qid] = key

    if len(q["choices"]) != 3:
        errors.append(f"{where}: {len(q['choices'])} choices, the exam always has 3")
    if not isinstance(q["answer"], int) or not 0 <= q["answer"] < len(q["choices"]):
        errors.append(f"{where}: answer {q['answer']!r} is not a valid choice index")
        return
    if len(q["distractors"]) != len(q["choices"]):
        errors.append(f"{where}: distractors must align with choices")
    else:
        blanks = [i for i, d in enumerate(q["distractors"]) if not d.strip()]
        if blanks != [q["answer"]]:
            errors.append(
                f"{where}: the blank distractor must be the answer. "
                f"answer={q['answer']}, blanks={blanks}"
            )
    if not q["solution"].strip():
        errors.append(f"{where}: empty solution")
    if len(set(c.strip().lower() for c in q["choices"])) != 3:
        errors.append(f"{where}: two choices are identical")

    stem = q["stem"].lower()
    for pattern, why in BANNED.items():
        if re.search(pattern, stem):
            errors.append(f"{where}: {why}")
    if not any(qual in stem for qual in QUALIFIERS):
        warnings.append(f"{where}: stem carries no qualifier")
    if not q["stem"].rstrip().endswith(":") and "?" not in q["stem"]:
        warnings.append(f"{where}: stem is neither a question nor a lead-in ending in a colon")

    for text in [q["stem"], q["solution"], *q["choices"], *q["distractors"]]:
        if any(d in text for d in LONG_DASHES):
            errors.append(f"{where}: contains an em or en dash")


if __name__ == "__main__":
    sys.exit(main())
