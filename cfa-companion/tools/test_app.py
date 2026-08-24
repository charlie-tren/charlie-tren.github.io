"""End to end checks against a locally served copy of the page.

    python tools/test_app.py            run the checks
    python tools/test_app.py --shots    also write screenshots to tools/shots/

Every check prints PASS or FAIL and the run exits 1 if any failed.
"""

import functools
import http.server
import pathlib
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "tools" / "shots"
PORT = 8731

results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    print(("PASS  " if condition else "FAIL  ") + name + (f"   {detail}" if detail else ""))


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> int:
    shots = "--shots" in sys.argv
    if shots:
        SHOTS.mkdir(parents=True, exist_ok=True)
    httpd = serve()
    url = f"http://127.0.0.1:{PORT}/"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        # --- the study plan ----------------------------------------------------
        # Seed a known state and check the arithmetic, rather than trusting it.
        import datetime
        exam = (datetime.date.today() + datetime.timedelta(days=60)).isoformat()
        stamp = datetime.date.today().isoformat()
        page.goto(url, wait_until="networkidle")
        page.evaluate("""(a) => {
            const s = JSON.parse(localStorage.getItem('cfa-companion.v1') || '{}');
            s.attempts = s.attempts || []; s.sr = s.sr || {};
            s.device = "seed";
            s.time = { days: { "2026-01-01": { seed: 38.5*3600 },
                               [a.stamp]: { seed: 1.5*3600 } } };
            s.plan = { exam: a.exam, target: 300, extraMin: 0 };
            localStorage.setItem('cfa-companion.v1', JSON.stringify(s));
        }""", {"exam": exam, "stamp": stamp})
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(400)
        check("days to go counts correctly", page.inner_text("#pl-days") == "60",
              page.inner_text("#pl-days"))
        check("hours logged read back", page.inner_text("#pl-done") == "40h 0m",
              page.inner_text("#pl-done"))
        # 300 - 40 = 260 over 60 days.
        check("hours a day needed is right", page.inner_text("#pl-need") == "4.3",
              page.inner_text("#pl-need"))
        check("today is shown separately", page.inner_text("#pl-today") == "1h 30m",
              page.inner_text("#pl-today"))
        page.fill("#pl-extra", "10")
        page.click("#pl-addbtn")
        page.wait_for_timeout(200)
        check("off-site hours count toward the total",
              page.inner_text("#pl-done") == "50h 0m", page.inner_text("#pl-done"))
        check("off-site hours reduce the daily requirement",
              page.inner_text("#pl-need") == "4.2", page.inner_text("#pl-need"))
        check("the bar tracks the target",
              page.evaluate("() => document.getElementById('pl-bar').style.width")
              .startswith("16.6"),
              page.evaluate("() => document.getElementById('pl-bar').style.width"))

        # The clock must actually advance, and must stop when left untouched.
        before = page.evaluate("() => window.CFA_COMPANION.clock()")
        page.wait_for_timeout(11000)
        after = page.evaluate("() => window.CFA_COMPANION.clock()")
        check("the clock advances while the page is in use",
              after["sec"] >= before["sec"] + 5,
              f"{before['sec']} then {after['sec']}")
        page.evaluate("() => window.CFA_COMPANION.goIdle()")
        page.wait_for_timeout(500)
        check("the clock reports itself paused when untouched",
              page.evaluate("() => window.CFA_COMPANION.clock().counting") is False)
        idle_a = page.evaluate("() => window.CFA_COMPANION.clock().sec")
        page.wait_for_timeout(11000)
        idle_b = page.evaluate("() => window.CFA_COMPANION.clock().sec")
        check("an untouched page logs no time", idle_b == idle_a,
              f"{idle_a} then {idle_b}")
        check("the paused state is visible to the reader",
              "paused" in (page.get_attribute("#pl-today", "class") or ""),
              page.get_attribute("#pl-today", "class"))

        page.evaluate("() => localStorage.removeItem('cfa-companion.v1')")

        # --- a transient failure must heal itself ------------------------------
        # A load caught mid-deploy fails for a second or two. One silent retry
        # turns that into a non-event, so the reader never sees a panel.
        first = {"n": 0}

        def once(route):
            first["n"] += 1
            route.abort() if first["n"] == 1 else route.continue_()

        # bank.js has to be blocked too, or there is nothing to fail: with it
        # present the page makes no requests at all. This exercises the fallback.
        page.route("**/bank.js", lambda r: r.abort())
        page.route("**/data/*.json", once)
        page.goto(url, wait_until="load")
        page.wait_for_selector("#banksize:not(:empty)", timeout=15000)
        check("a transient load failure heals itself", page.locator("#modes").is_visible())
        check("a transient failure shows the reader nothing",
              page.locator("#loaderr").is_hidden())
        page.unroute("**/data/*.json")
        errors.clear()

        # --- what happens when the bank cannot be read -------------------------
        # A blocked fetch must say so and offer a way back, not leave a dead page.
        blocked = {"on": True}
        page.route("**/data/*.json",
                   lambda route: route.abort() if blocked["on"] else route.continue_())
        # bank.js stays blocked throughout this block, so the fetch path is used.
        page.goto(url, wait_until="load")
        page.wait_for_selector("#loaderr:not([hidden])")
        msg = page.inner_text("#loaderr")
        check("a failed load explains itself", "did not load" in msg, msg[:60])
        check("a failed load offers a retry",
              page.locator("#loaderr button").is_visible())
        check("a failed load hides the modes it cannot run",
              page.locator("#modes").is_hidden())
        blocked["on"] = False
        page.click("#loaderr button")
        page.wait_for_selector("#banksize:not(:empty)", timeout=15000)
        check("the retry recovers", page.locator("#modes").is_visible())
        check("the retry does not duplicate the topic pickers",
              page.evaluate("() => document.querySelectorAll('#b-topics .grid').length") == 1,
              str(page.evaluate("() => document.querySelectorAll('#b-topics .grid').length")))
        page.unroute("**/data/*.json")
        page.unroute("**/bank.js")
        errors.clear()      # the aborted requests above were deliberate

        page.goto(url, wait_until="networkidle")

        # --- the bank loads and the home screen sets itself up ------------------
        total = page.evaluate("() => document.querySelectorAll('#f-topics label').length")
        check("topic pickers built", total == 11, f"{total} labels, expected 11")
        check("no console errors on load", not errors, "; ".join(errors[:3]))

        bank_total = page.evaluate(
            "() => Array.from(document.querySelectorAll('#f-topics .n'))"
            ".slice(1).reduce((a, e) => a + Number(e.textContent), 0)"
        )
        check("bank counts render", bank_total > 0, f"{bank_total} questions")
        # Also the thumbnail job's readiness signal, so it has to be VISIBLE.
        size = page.inner_text("#banksize")
        check("the bank size is stated and visible",
              page.locator("#banksize").is_visible() and str(bank_total) in size, size)

        # A 30-question bank cannot supply a 180-question mock, and the button
        # must say so rather than starting a short one.
        mock_disabled = page.evaluate("() => document.querySelector(\"[data-mode='mock']\").disabled")
        mock_copy = page.inner_text("[data-mode='mock'] span")
        if bank_total < 180:
            check("mock disabled while the bank is thin", mock_disabled)
            check("mock copy names the shortfall", str(bank_total) in mock_copy, mock_copy)
        else:
            check("mock enabled with a full bank", not mock_disabled)

        # --- practice mode: feedback is immediate -------------------------------
        page.click("[data-mode='free']")
        page.click("#f-start")
        page.wait_for_selector("#t-choices .choice")
        check("practice hides the clock", page.locator("#t-clock").is_hidden())
        check("practice hides the flag", page.locator("#t-flag").is_hidden())
        check("feedback hidden before answering", page.locator("#t-feedback").is_hidden())

        page.click("#t-choices .choice >> nth=0")
        page.wait_for_selector("#t-feedback:visible")
        check("feedback appears on answering", page.locator("#t-feedback").is_visible())
        cls = page.get_attribute("#t-feedback", "class")
        check("feedback is marked right or wrong", "ok" in cls or "no" in cls, cls)
        check("solution is shown", len(page.inner_text("#t-feedback")) > 60)
        marked = page.evaluate("() => document.querySelectorAll('.choice.right').length")
        check("the correct choice is marked", marked == 1, f"{marked} marked")
        disabled = page.evaluate("() => document.querySelectorAll('.choice[disabled]').length")
        check("choices lock after answering", disabled == 3, f"{disabled} locked")

        after_one = page.evaluate("() => window.CFA_COMPANION.peek().attempts")
        check("the attempt was recorded", after_one == 1, f"{after_one} attempts")

        page.click("#t-next")
        page.wait_for_selector("#t-feedback", state="hidden")
        check("feedback clears on the next question", page.locator("#t-feedback").is_hidden())

        # Answer two more, then end and read the report.
        page.click("#t-choices .choice >> nth=1")
        page.click("#t-next")
        page.click("#t-choices .choice >> nth=2")
        page.on("dialog", lambda d: d.accept())
        page.click("#t-end")
        page.wait_for_selector("#report:not([hidden])")
        check("report renders", page.locator("#report").is_visible())
        what = page.text_content("#r-what")
        check("the report says what was sat", what == "Free run, 3 questions", what)
        counts = page.evaluate("() => Array.from(document.querySelectorAll('#r-topic .nq')).map(e => e.textContent)")
        check("each topic bar carries its question count", len(counts) >= 1 and all(counts), str(counts))
        bars = page.evaluate("() => document.querySelectorAll('#r-topic .bar').length")
        check("report draws topic bars", bars >= 1, f"{bars} bars")
        lines = page.evaluate("() => document.querySelectorAll('#r-topic .bar:first-child .refline').length")
        check("topic bars carry both reference lines", lines == 2, f"{lines} lines")
        hard = page.evaluate(
            "() => document.querySelector('#r-topic .bar:first-child .refline.hard').style.left"
        )
        check("the 70% line sits at 70%", hard == "70%", hard)
        pace = page.evaluate("() => document.querySelectorAll('#r-pace .bar').length")
        check("pace chart draws", pace >= 1, f"{pace} bars")
        reviewed = page.evaluate("() => document.querySelectorAll('#r-review .rq').length")
        check("only delivered questions are reviewable", reviewed == 3, f"{reviewed} rows, expected 3")

        # The wrong filter must actually hide rows, not just restyle them.
        wrong_total = page.evaluate("() => document.querySelectorAll(\"#r-review .rq[data-wrong='1']\").length")
        page.click("[data-rfilter='wrong']")
        visible = page.evaluate("() => Array.from(document.querySelectorAll('#r-review .rq')).filter(r => !r.hidden).length")
        check("the wrong filter hides the rest", visible == wrong_total, f"{visible} shown, {wrong_total} wrong")
        page.click("[data-rfilter='all']")

        if shots:
            page.screenshot(path=str(SHOTS / "report-desktop.png"), full_page=True)

        page.click("#r-done")
        page.wait_for_selector("#home:not([hidden])")
        check("progress strip appears once there is history", page.locator("#progress").is_visible())
        check("history charts appear", page.locator("#history").is_visible())
        answered = page.inner_text("#p-answered")
        check("answered count is right", answered == "3", answered)

        # --- history survives a reload -----------------------------------------
        page.reload(wait_until="networkidle")
        check("history survives a reload", page.inner_text("#p-answered") == "3",
              page.inner_text("#p-answered"))

        # --- mistakes and review modes gate on having something to show ---------
        mistakes_enabled = page.evaluate("() => !document.querySelector(\"[data-mode='mistakes']\").disabled")
        wrong_stored = page.evaluate(
            "() => { const s = JSON.parse(localStorage.getItem('cfa-companion.v1'));"
            " const last = {}; s.attempts.forEach(a => last[a.q] = a.ok);"
            " return Object.values(last).filter(v => v === false).length; }"
        )
        check("mistakes mode matches the stored wrong answers",
              mistakes_enabled == (wrong_stored > 0), f"{wrong_stored} wrong, enabled={mistakes_enabled}")
        review_enabled = page.evaluate("() => !document.querySelector(\"[data-mode='review']\").disabled")
        check("nothing is due for review on the same day", not review_enabled)

        # --- strict mode --------------------------------------------------------
        page.click("[data-mode='custom']")
        page.check("#b-strict")
        page.check("#b-timed")
        page.fill("#b-count", "6")
        page.click("#builder button[type=submit]")
        page.wait_for_selector("#t-choices .choice")

        check("strict shows the clock", page.locator("#t-clock").is_visible())
        check("strict shows the flag", page.locator("#t-flag").is_visible())
        check("strict shows the overview", page.locator("#t-overview").is_visible())
        check("strict shows strike-out buttons",
              page.evaluate("() => document.querySelectorAll('.strike').length") == 3)
        clock = page.inner_text("#t-clock")
        check("the clock is counting a 9 minute section", clock.startswith("0:0"), clock)

        page.click("#t-choices .choice >> nth=0")
        check("strict gives no feedback", page.locator("#t-feedback").is_hidden())
        check("strict marks nothing right or wrong",
              page.evaluate("() => document.querySelectorAll('.choice.right, .choice.wrong').length") == 0)
        check("strict shows the pick",
              page.evaluate("() => document.querySelectorAll('.choice.picked').length") == 1)
        check("strict records nothing yet",
              page.evaluate("() => window.CFA_COMPANION.peek().attempts") == 3)

        # An answer can be changed under exam conditions.
        page.click("#t-choices .choice >> nth=2")
        picked = page.evaluate(
            "() => Array.from(document.querySelectorAll('.choice')).findIndex(c => c.classList.contains('picked'))"
        )
        check("strict lets an answer be changed", picked == 2, f"picked index {picked}")

        page.click(".strike >> nth=0")
        check("strike-out marks a choice",
              page.evaluate("() => document.querySelectorAll('.choice.struck').length") == 1)

        page.click("#t-flag")
        check("flag button reflects state", page.inner_text("#t-flag") == "Flagged")

        page.click("#t-overview")
        page.wait_for_selector("#t-ovpanel:not([hidden])")
        cells = page.evaluate("() => document.querySelectorAll('#ov-grid button').length")
        check("overview lists the whole section", cells == 6, f"{cells} cells")
        done = page.evaluate("() => document.querySelectorAll('#ov-grid button.done').length")
        check("overview marks the attempted one", done == 1, f"{done} done")
        page.click("[data-filter='flagged']")
        flagged_cells = page.evaluate("() => document.querySelectorAll('#ov-grid button').length")
        check("the flagged filter narrows to one", flagged_cells == 1, f"{flagged_cells} cells")
        page.click("[data-filter='unattempted']")
        un = page.evaluate("() => document.querySelectorAll('#ov-grid button').length")
        check("the unattempted filter shows five", un == 5, f"{un} cells")
        page.click("#ov-close")

        # Highlighting must survive moving away and coming back.
        page.evaluate(
            "() => { const stem = document.getElementById('t-stem');"
            " const r = document.createRange();"
            " r.setStart(stem.firstChild, 0); r.setEnd(stem.firstChild, 12);"
            " const s = window.getSelection(); s.removeAllRanges(); s.addRange(r); }"
        )
        page.click("#t-hl")
        check("highlighting wraps the selection",
              page.evaluate("() => document.querySelectorAll('#t-stem mark').length") == 1)
        page.click("#t-next")
        page.click("#t-prev")
        check("the highlight survives navigation",
              page.evaluate("() => document.querySelectorAll('#t-stem mark').length") == 1)

        # Fill the rest wrongly and check the section commits all at once.
        page.evaluate("() => window.CFA_COMPANION.fill(false)")
        page.wait_for_selector("#report:not([hidden])")
        pct = page.inner_text("#r-pct")
        check("a wholly wrong section scores 0%", pct == "0%", pct)
        check("the section commits every answer at the end",
              page.evaluate("() => window.CFA_COMPANION.peek().attempts") == 9,
              str(page.evaluate("() => window.CFA_COMPANION.peek().attempts")))
        band = page.evaluate("() => document.querySelector('#r-topic .fill').className")
        check("a zero score is banded red", "b-bad" in band, band)

        page.click("#r-done")

        # --- weighting ----------------------------------------------------------
        # A weighted pick must not simply take the first n: ethics carries the
        # largest target, so it should be the most represented topic in a big set.
        spread = page.evaluate(
            "() => { const b = document.querySelector(\"[data-mode='custom']\"); return true; }"
        )
        page.click("[data-mode='custom']")
        page.fill("#b-count", "20")
        page.uncheck("#b-strict")
        page.uncheck("#b-timed")
        page.click("#builder button[type=submit]")
        page.wait_for_selector("#t-choices .choice")
        topics = page.evaluate("() => window.CFA_COMPANION.peek().topics")
        counts = {t: topics.count(t) for t in set(topics)}
        check("a weighted set spans topics", len(counts) >= 5, str(counts))
        check("ethics is the most represented topic",
              counts.get("ethics", 0) == max(counts.values()), str(counts))
        page.click("#t-end")
        page.wait_for_selector("#report:not([hidden])")
        page.click("#r-done")

        # --- the full mock, which only exists once the bank reaches 180 ---------
        page.evaluate("() => localStorage.removeItem('cfa-companion.v1')")
        page.reload(wait_until="networkidle")
        page.click("[data-mode='mock']")
        page.wait_for_selector("#t-choices .choice")
        peek = page.evaluate("() => window.CFA_COMPANION.peek()")
        check("the mock draws 180 questions", peek["length"] == 180, str(peek["length"]))
        check("the mock opens in session 1", peek["session"] == 0)
        check("the mock is strict", peek["strict"] is True)
        pos = page.inner_text("#t-pos")
        check("the mock counts within the session, not the whole paper",
              "1 OF 90" in pos.upper() and "SESSION 1 OF 2" in pos.upper(), pos)
        clock = page.inner_text("#t-clock")
        check("the session clock starts at 2h15", clock.startswith("2:1"), clock)

        # A weighted 180 must reproduce the exam's own split exactly, since the
        # bank was authored to those targets.
        topics = page.evaluate("() => window.CFA_COMPANION.peek().topics")
        counts = {t: topics.count(t) for t in set(topics)}
        targets = page.evaluate(
            "() => fetch('data/index.json').then(r => r.json())"
            ".then(d => Object.fromEntries(d.topics.map(t => [t.key, t.target])))"
        )
        check("the mock matches the exam topic weights exactly", counts == targets,
              f"got {counts}")

        page.evaluate("() => window.CFA_COMPANION.fill(true)")
        page.wait_for_selector("#break:not([hidden])")
        check("session 1 ends at the break screen", page.locator("#break").is_visible())
        check("the break reports the session count",
              page.inner_text("#br-count") == "90 of 90", page.inner_text("#br-count"))
        check("session 1 is recorded at the break",
              page.evaluate("() => window.CFA_COMPANION.peek().attempts") == 90,
              str(page.evaluate("() => window.CFA_COMPANION.peek().attempts")))

        page.click("#br-go")
        page.wait_for_selector("#t-choices .choice")
        peek = page.evaluate("() => window.CFA_COMPANION.peek()")
        check("session 2 starts at question 91", peek["idx"] == 90, str(peek["idx"]))
        check("session 2 is flagged as the second session", peek["session"] == 1)
        page.evaluate("() => window.CFA_COMPANION.fill(true)")
        page.wait_for_selector("#report:not([hidden])")
        check("an all-correct mock scores 100%", page.inner_text("#r-pct") == "100%",
              page.inner_text("#r-pct"))
        check("the mock report covers the whole paper",
              page.evaluate("() => document.querySelectorAll('#r-review .rq').length") == 180,
              str(page.evaluate("() => document.querySelectorAll('#r-review .rq').length")))
        check("all ten topics appear in the mock report",
              page.evaluate("() => document.querySelectorAll('#r-topic .bar').length") == 10,
              str(page.evaluate("() => document.querySelectorAll('#r-topic .bar').length")))
        check("both sessions are recorded",
              page.evaluate("() => window.CFA_COMPANION.peek().attempts") == 180,
              str(page.evaluate("() => window.CFA_COMPANION.peek().attempts")))
        page.click("#r-done")
        page.wait_for_selector("#home:not([hidden])")
        # A perfect mock leaves every topic at 100%, so naming one of them the
        # weakest would invent a weakness the answers do not show.
        check("no weakest topic is named when every topic is level",
              page.inner_text("#p-weak") == "all level", page.inner_text("#p-weak"))

        check("still no console errors", not errors, "; ".join(errors[:3]))

        if shots:
            page.screenshot(path=str(SHOTS / "home-desktop.png"), full_page=True)
            mob = browser.new_page(viewport={"width": 390, "height": 844})
            mob.goto(url, wait_until="networkidle")
            mob.screenshot(path=str(SHOTS / "home-mobile.png"), full_page=True)
            mob.click("[data-mode='free']")
            mob.click("#f-start")
            mob.wait_for_selector("#t-choices .choice")
            mob.screenshot(path=str(SHOTS / "question-mobile.png"), full_page=True)
            dark = browser.new_page(viewport={"width": 1100, "height": 900}, color_scheme="dark")
            dark.goto(url, wait_until="networkidle")
            dark.click("[data-mode='free']")
            dark.click("#f-start")
            dark.wait_for_selector("#t-choices .choice")
            dark.click("#t-choices .choice >> nth=0")
            dark.screenshot(path=str(SHOTS / "question-dark.png"), full_page=True)

        # Every block sits in the same column. A margin shorthand on the footer
        # once reset .wrap's auto side margins and pushed it flush left, which no
        # DOM assertion elsewhere would have noticed.
        page.set_viewport_size({"width": 1100, "height": 900})
        lefts = page.evaluate(
            "() => ['header.wrap', 'main.wrap', 'footer.wrap']"
            ".map(s => Math.round(document.querySelector(s).getBoundingClientRect().left))"
        )
        check("header, main and footer share one column", len(set(lefts)) == 1, str(lefts))

        # The page must never scroll sideways.
        for w in (390, 768, 1100):
            page.set_viewport_size({"width": w, "height": 800})
            over = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")
            check(f"no horizontal scroll at {w}px", not over)

        browser.close()

    httpd.shutdown()

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    if failed:
        for name, _, detail in failed:
            print(f"  FAILED  {name}   {detail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
