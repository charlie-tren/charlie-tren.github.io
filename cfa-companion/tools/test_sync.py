"""Drive the real sync service with two separate browser profiles.

    python tools/test_sync.py

Kept out of test_app.py because it talks to the live Worker at
cfa-sync.charlietrenorden.com. Each run uses a fresh random key, so it starts from
an empty state and leaves one small row behind.

What it has to prove, and what a mock could not: that a second device picks up the
first device's work, that work flows back the other way, and that syncing
repeatedly neither duplicates answers nor inflates hours. The merge is the risky
part, because both devices can push.
"""

import functools
import http.server
import pathlib
import secrets
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = 8750

results = []


def check(name, got, want=None):
    ok = got == want if want is not None else bool(got)
    results.append((name, ok))
    print(("PASS  " if ok else "FAIL  ") + f"{name}: {got}"
          + ("" if want is None else f"  (want {want})"))


def answer(page, n, choice=0):
    page.click("[data-mode='free']")
    page.click("#f-start")
    for _ in range(n):
        page.wait_for_selector("#t-choices .choice")
        page.click(f"#t-choices .choice >> nth={choice}")
        page.click("#t-next")


def main() -> int:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{PORT}/"
    key = "t" + secrets.token_hex(12)
    print(f"key for this run: {key}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch()

        laptop = browser.new_context().new_page()
        laptop.goto(url, wait_until="networkidle")
        laptop.fill("#pl-key", key)
        laptop.click("#pl-keysave")
        laptop.wait_for_timeout(2500)
        check("the key is accepted", laptop.inner_text("#pl-sync").startswith("synced"), True)
        laptop.fill("#pl-exam", "2027-02-20")
        laptop.dispatch_event("#pl-exam", "change")
        answer(laptop, 3)
        laptop.evaluate("() => window.CFA_COMPANION.sync()")
        laptop.wait_for_timeout(3000)
        check("laptop pushed three answers",
              laptop.evaluate("() => window.CFA_COMPANION.peek().attempts"), 3)

        phone = browser.new_context().new_page()
        phone.goto(url, wait_until="networkidle")
        check("phone starts empty",
              phone.evaluate("() => window.CFA_COMPANION.peek().attempts"), 0)
        phone.fill("#pl-key", key)
        phone.click("#pl-keysave")
        phone.wait_for_timeout(3500)
        check("phone pulled the answers",
              phone.evaluate("() => window.CFA_COMPANION.peek().attempts"), 3)
        check("phone pulled the exam date too",
              phone.inner_text("#pl-days") == laptop.inner_text("#pl-days"), True)

        answer(phone, 2, choice=1)
        phone.evaluate("() => window.CFA_COMPANION.sync()")
        phone.wait_for_timeout(3000)
        laptop.evaluate("() => window.CFA_COMPANION.sync()")
        laptop.wait_for_timeout(3000)
        check("work flows back the other way",
              laptop.evaluate("() => window.CFA_COMPANION.peek().attempts"), 5)

        for _ in range(2):
            laptop.evaluate("() => window.CFA_COMPANION.sync()")
            laptop.wait_for_timeout(2200)
        check("repeated syncs do not duplicate answers",
              laptop.evaluate("() => window.CFA_COMPANION.peek().attempts"), 5)
        check("repeated syncs do not inflate hours",
              laptop.evaluate("() => window.CFA_COMPANION.clock().sec") < 900, True)

        # A wrong key must see nothing, since the key is the whole boundary.
        stranger = browser.new_context().new_page()
        stranger.goto(url, wait_until="networkidle")
        stranger.fill("#pl-key", "z" + secrets.token_hex(12))
        stranger.click("#pl-keysave")
        stranger.wait_for_timeout(3000)
        check("a different key sees nothing",
              stranger.evaluate("() => window.CFA_COMPANION.peek().attempts"), 0)

        browser.close()
    httpd.shutdown()

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
