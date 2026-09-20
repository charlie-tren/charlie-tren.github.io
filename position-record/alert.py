"""Open a GitHub issue when a watched pair goes through its trigger.

Run after build.py in the daily workflow: python position-record/alert.py

WHY AN ISSUE: the page can show a trigger being hit, but nobody is looking at the
page at 22:00 UTC. An issue assigned to Charlie is emailed to him by GitHub, needs
no mail provider and no secret beyond the job's own token, and is a record of when
the trigger fired that sits next to the code. The estate's one mail path (Brevo)
was put under account review in August 2026 and is not a channel to lean on.

ONE ISSUE PER PAIR WHILE ARMED. A pair that stays through its trigger for a week
is one event, not seven emails: an open issue with the pair's title means "already
told". When the reading comes back inside the trigger the issue is closed with the
reading that closed it, so the next crossing opens a fresh one.

Reads the same files the page is built from: positions.json for the trigger and
prices.json for the cached reading build.py just wrote. No second fetch, so the
alert and the page can never disagree.
"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "positions.json"
PRICES = HERE / "prices.json"
ASSIGNEE = "charlie-tren"
LABEL = "watch-trigger"


def armed(w, reading):
    """True when the reading is through the trigger, on the trigger's own side."""
    v = reading["value"]
    return v <= w["trigger_pct"] if w["trigger_pct"] < 0 else v >= w["trigger_pct"]


def title(w):
    return f"Watching: {w['name']} is through its trigger"


def body(w, reading):
    side = f"long {w['long']['name']}, short {w['short']['name']}"
    return (f"{w['name']} read {reading['value']:+.1f}% against its one-year mean on "
            f"{reading['asof']}, through the {w['trigger_pct']:+.0f}% trigger.\n\n"
            f"The setup on the page is {side}, hard exit after {w['exit_days']} days.\n\n"
            f"https://charlietrenorden.com/position-record/\n\n"
            f"Opened by the daily position-record run. It closes itself when the "
            f"reading comes back inside the trigger.")


def decide(watching, cache, open_titles):
    """What to do for each pair: ('open', w, reading), ('close', w, reading) or
    nothing. Pure, so it is testable without a token."""
    acts = []
    for w in watching:
        reading = cache.get(f"watch:{w['long']['symbol']}/{w['short']['symbol']}")
        if not reading:
            continue
        told = title(w) in open_titles
        if armed(w, reading) and not told:
            acts.append(("open", w, reading))
        elif not armed(w, reading) and told:
            acts.append(("close", w, reading))
    return acts


def gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def open_issues():
    out = gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number,title")
    return {i["title"]: i["number"] for i in json.loads(out or "[]")}


def main(argv):
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    cache = json.loads(PRICES.read_text(encoding="utf-8"))
    watching = data.get("watching") or []
    if "--test" in argv:
        # A real issue, assigned and then closed, so the email path is proven end to
        # end rather than assumed. The title says what it is.
        num = gh("issue", "create", "--title", "Watching: alert test",
                 "--body", "Test of the trigger alert. Closed by the same run.",
                 "--label", LABEL, "--assignee", ASSIGNEE).strip().rsplit("/", 1)[-1]
        gh("issue", "close", num, "--comment", "Test complete.")
        print(f"  test issue #{num} opened and closed")
        return
    try:
        current = open_issues()
    except subprocess.CalledProcessError as exc:
        # The label does not exist until the first issue carries it; gh treats an
        # unknown label as an error rather than an empty list.
        if "not found" in (exc.stderr or "").lower():
            current = {}
        else:
            raise
    acts = decide(watching, cache, set(current))
    if not acts:
        print(f"  {len(watching)} watched, nothing to tell")
        return
    for kind, w, reading in acts:
        if kind == "open":
            gh("issue", "create", "--title", title(w), "--body", body(w, reading),
               "--label", LABEL, "--assignee", ASSIGNEE)
            print(f"  opened: {title(w)} ({reading['value']:+.1f}%)")
        else:
            gh("issue", "close", str(current[title(w)]),
               "--comment", f"Back inside the trigger: {reading['value']:+.1f}% on {reading['asof']}.")
            print(f"  closed: {title(w)} ({reading['value']:+.1f}%)")


if __name__ == "__main__":
    main(sys.argv[1:])
