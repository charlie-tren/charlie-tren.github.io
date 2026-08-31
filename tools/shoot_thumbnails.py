"""Re-shoot the project card thumbnails from the live sites.

    python tools/shoot_thumbnails.py daily      # the two that change every day
    python tools/shoot_thumbnails.py weekly     # all of them
    python tools/shoot_thumbnails.py one-story  # just one

Every site is shot from its live URL rather than a local build, so this works
the same on a laptop and in Actions with no dev server.

Three things this handles that a naive screenshot does not:

1. **Dead margin.** These sites centre their content in a max-width column and
   most open with a chunk of space above the masthead, so a plain 1280x800 shot is
   largely background - One Story was 49% empty either side plus 80px above. The
   crop is driven by the real content bounding box, measured in the page: the union
   of every visible text node, image, control and SVG, clipped to the viewport.
   An earlier version looked for flat-coloured edge columns instead, which missed
   Lexicon entirely because one full-width element defeated the test.
2. **The interesting bit is below the fold** on some pages. `ANCHOR` frames on a
   named element - Consensus Drift's masthead and filter dropdowns made for a
   thumbnail with no chart in it - and `context_above` keeps some of the page
   chrome in shot so the card still reads as a website rather than a bare graph.
3. **Churn.** A re-shoot of an unchanged page still produces different bytes, so
   a weekly job would commit noise forever. Anything under MIN_DIFF against the
   current file is left alone.

Run it from Actions, not from a laptop. Linux and Windows hint fonts differently,
so a local shot of an UNCHANGED page reads as a ~27-point difference against a
CI-shot one and vice versa - alternating between the two would commit a new
thumbnail every run. Use `gh workflow run "Refresh card thumbnails"` for a manual
refresh; keep local runs for developing this script.

The exception is Thinkerings, which Substack will not serve to a datacentre IP -
see READY below. That one card is shot from a laptop on purpose.
"""

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

SITES = {
    "one-story": "https://one-story.charlietrenorden.com/",
    "the-aftertimes": "https://aftertimes.charlietrenorden.com/",
    "photocopy": "https://charlietrenorden.com/photocopy/",
    "consensus-drift": "https://charlietrenorden.com/consensus-drift/",
    "lindy-effect": "https://charlietrenorden.com/lindy-effect/",
    "foreign-property-screener": "https://charlietrenorden.com/foreign-property-screener/",
    "crowdwise": "https://crowdwise.charlietrenorden.com/",
    "dcf-studio": "https://dcf.charlietrenorden.com/GOOGL",
    # a country page, not the picker - the landing page is three pills and a
    # half-empty card, which made for a thumbnail showing none of the product
    "chronoscape": "https://charlietrenorden.com/chronoscape/iceland/",
    # /archive rather than the root: Substack puts a subscribe interstitial over
    # the home page, and DISMISS only clears it once the post list is what loads
    "thinkerings": "https://thinkerings.substack.com/archive",
    "lexicon": "https://charlietrenorden.com/lexicon/",
    "beyond-small-talk": "https://charlietrenorden.com/beyond-small-talk/",
    "woop-woop": "https://charlietrenorden.com/woop-woop/",
    "shortfall": "https://charlietrenorden.com/shortfall/",
    "pendulum": "https://charlietrenorden.com/pendulum/",
    "cfa-companion": "https://charlietrenorden.com/cfa-companion/",
    "ghostwriters": "https://charlietrenorden.com/ghostwriters/",
    "statecraft": "https://charlietrenorden.com/statecraft/",
    # ?demo=1, not the lobby. The landing screen is a name field and a button,
    # which shows none of the game - the same fault the chronoscape entry above
    # exists to avoid. The demo renders a worked round through the page's own
    # render path, so the card cannot show something the game does not do.
    "worst-case-scenario": "https://charlietrenorden.com/worst-case-scenario/?demo=1",
}

# One Story, The Aftertimes and Photocopy republish every day, so their
# thumbnails are stale within 24 hours. Everything else only moves when its
# code does.
DAILY = ["one-story", "the-aftertimes", "photocopy"]

# A modal or interstitial in the way. Clicked, then given a moment to clear.
DISMISS = {
    "thinkerings": "text=No thanks",     # Substack's subscribe interstitial
}

# "The real page has arrived" - waited for before the shot, and a skip if it never
# comes. Substack serves Actions' datacentre IP a Cloudflare bot check that a
# residential run never sees, and the fixed waits below expired while the challenge
# was still spinning: the card committed on 17/08/2026 was a screenshot of
# "Performing security verification". A managed challenge clears itself in a few
# seconds, so waiting on real content rides it out instead of racing it.
READY = {
    "thinkerings": "a[href*='/p/']",     # post links in the archive list
    # Pendulum draws its charts from a megabyte of JSON after load. Without this
    # the shot lands on the loading state, which is a card showing nothing.
    "pendulum": "#area polygon",
    # The mode list is static markup, and the topic pickers live inside panels
    # that start hidden, so waiting on those waits forever. The bank count is the
    # first VISIBLE thing that only exists after the questions have loaded.
    "cfa-companion": "#banksize",
    # Statecraft paints its thirteen domains from data.json after load, so the
    # shot lands on an empty column without this. WAS ".opt", which stopped
    # existing on 30/08/2026 when the option cards became sliders: the job would
    # have waited 30s, skipped, and failed the run. A range input is the thing
    # that only exists once the data has arrived.
    "statecraft": "#domains input[type=range]",
    # Absentee ranks thirty-four countries from data.json after load, so without
    # this the shot lands on an empty panel. A bar is the first thing that only
    # exists once the data has arrived.
    "foreign-property-screener": "#rank rect",
}
READY_TIMEOUT = 30000

# Sites that are ALLOWED to skip without failing the run. Thinkerings is the only
# one: Substack serves Actions' datacentre IP a bot challenge that a laptop never
# sees, so CI cannot shoot it at all and its card is refreshed by hand. Everything
# NOT listed here is expected to shoot, and a skip is a failure - see the exit at
# the end of main(). That distinction is the point: printing a skip and exiting 0
# is how Thinkerings itself served a ten-day-old thumbnail with nobody noticing.
MAY_SKIP = ["thinkerings"]

# THINKERINGS IS EXPECTED TO SKIP IN ACTIONS. A real user agent was not enough -
# the challenge is keyed on the datacentre IP, and a CI run still sat on it for the
# full 30s on 17/08/2026. The same run from a laptop loads the archive first time.
# So this is the one card that has to be re-shot locally:
#
#     python tools/shoot_thumbnails.py thinkerings   # then commit assets/thinkerings.webp
#
# The usual objection to a local shot - Linux and Windows hinting alternating on
# every run - does not apply while CI cannot shoot it at all: CI skips, so nothing
# overwrites it. If Substack ever stops challenging, expect one churn commit as it
# flips back to a CI-hinted shot, and then quiet again.
# The attempt is left in rather than hard-skipped in CI so that can happen by itself.

# Nothing here should ever appear on one of these sites, so a page containing one is
# a challenge, an error or an outage - not a thumbnail. Checked for every site: the
# Substack card went stale silently for ten days because a bad shot still overwrote
# a good file, and only an eyeball caught it. Keeping the old image is always better.
JUNK = [
    "performing security verification",
    "checking your browser",
    "verify you are human",
    "enable javascript and cookies",
    "attention required",
    "502 bad gateway",
    "503 service temporarily unavailable",
    "504 gateway time-out",
    "site can't be reached",
]

# Playwright's default UA advertises HeadlessChrome, which is a large part of why a
# datacentre IP gets challenged at all. Cheaper than fighting the challenge after it
# has already been served.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

# Some pages put more above the fold than fits a 16:10 frame at the width of
# their content column, so the crop lopped the bottom off. Zooming the page out
# fits more in without widening the frame back into the dead margin.
#
# ZOOMING CANNOT FIX THIS. It shrinks width and height by the same factor, so the
# content's aspect ratio is unchanged and a too-tall page stays too tall - three
# hand-picked zoom values for Lexicon all still clipped, and so did a solved one.
# What actually fits tall content into a 16:10 frame is a WIDER frame: include some
# of the side margin back, up to height x 16/10. These pages get a wider viewport
# so there is margin available to spend.
FIT = ["lexicon", "chronoscape"]
VIEW_FIT = {"width": 1800, "height": 1150}
MAX_WIDEN = 1.22        # how much side margin the frame may spend before the type gets too small

# JS run after load, before the shot. A page that shows something at random should
# not leave its card to chance - Beyond Small Talk drew "What's the highest you've
# ever been?", which is not the line to lead a public site with.
PREPARE = {
    # Set the text, then restore the page's own class contract: "q" plus a len-*
    # bucket that drives the type size. Setting only the bucket dropped the base
    # class and the question rendered at body size.
    "beyond-small-talk": """() => {
        const q = document.getElementById('q');
        q.textContent = 'What are you pretending not to know?';
        q.className = 'q len-s';
    }""",
    # The landing screen is a menu, which tells a viewer nothing about the
    # product. Drive it into a question with its worked solution showing, which is
    # the thing worth advertising. The click handlers are synchronous, so this runs
    # in one pass.
    "cfa-companion": """() => {
        document.querySelector("[data-mode='free']").click();
        document.getElementById('f-start').click();
        document.querySelector('#t-choices .choice').click();
    }""",
}

# Sites that look better - or are designed - dark. Playwright emulates light by
# default, so a site that keys off prefers-color-scheme renders in its light theme
# unless told otherwise.
SCHEME = {
    "cfa-companion": "dark",
    "beyond-small-talk": "dark",
    # Same family as Beyond Small Talk: a room you open on a phone in a dark pub.
    "worst-case-scenario": "dark",
    "woop-woop": "dark",
    "pendulum": "dark",
    # Both verified 19/08/2026 to key off prefers-color-scheme with no stored choice:
    # photocopy body goes rgb(250,249,247) -> rgb(19,18,17), shortfall also flips its
    # data-theme attribute light -> dark. So emulation alone is enough; neither needs
    # a PREPARE step to set a localStorage key.
    "photocopy": "dark",
    "shortfall": "dark",
    # Statecraft follows prefers-color-scheme with nothing stored, same as the two
    # above, so emulation alone flips it and no PREPARE step is needed.
    "statecraft": "dark",
}

# Pages whose top is a masthead rather than the product: frame on an element
# instead. `context_above` is the share of the frame height spent on whatever sits
# above that element, so the card shows a website with a chart in it rather than a
# chart on its own.
ANCHOR = {
    "consensus-drift": {"selector": "svg", "context_above": 0.30},
    # The top of the page is a wordmark and six sliders. Shot unanchored on
    # 31/08/2026 the card was 590px of controls and three bars, which reads as a
    # settings screen rather than as a ranking of thirty-four countries. Framed
    # on the chart, with enough above it to keep the title and a row of the
    # controls in, so the card still shows a website with a chart in it.
    # 0.18 landed mid-hint and left an orphan "HELP." across the top of the card.
    "foreign-property-screener": {"selector": "#rank-panel", "context_above": 0.10},
    # The top of the page is the hero and a scatter that is currently just a sorted
    # curve. The cards, with real company names and per-flag scores, are the product.
    #
    # Charlie asked for the dot plot on the card (25/08/2026). That is #quadPanel,
    # the Cross-Plot - score against short interest, one dot per company. NOT
    # #stripPanel: "Distributions" draws density curves now, not the strip of dots
    # it did when this file was first written.
    "shortfall": {"selector": "#quadPanel", "context_above": 0.10},
    # The top of the page is a wordmark, a country picker and three meters. The
    # product is the choosing: option cards with a policy, who already does it,
    # and what it costs. The first shot, 30/08/2026, reached only the "Tax and
    # Redistribution" heading before the frame ran out, which is the same
    # masthead-and-dropdowns card this ANCHOR table exists to prevent.
    # Framed on the first domain with enough context above to keep the meters in,
    # since the meters are what make the options read as choices with a price.
    # Re-aimed 30/08/2026 at the chart, which is now the best thing on the page:
    # NO ANCHOR FOR STATECRAFT. It had one aimed at .chart, from when the chart
    # was a full-width opener. On 31/08/2026 the chart moved into a 26rem sticky
    # rail beside the sliders, and framing on it produced a card that was the
    # top-left corner of a radar and nothing else. The top of the page is now
    # the right frame on its own: wordmark, country picker, the fingerprint in
    # the rail and the first two policies, which is the whole product.
    #
    # The lesson is not about this site: an ANCHOR names an element and says
    # nothing about how big that element is, so a layout change can turn a good
    # frame into a crop with no test failing. Look at the card after any layout
    # change on an anchored site.
}

VIEW = {"width": 1280, "height": 800}
SCALE = 2                # shoot at 2x so cropping costs no sharpness
TARGET_W = 1400          # cards render ~600px wide, so this covers retina
QUALITY = 84
MARGIN_FRAC = 0.04       # breathing room either side of the content column
MIN_DIFF = 2.0           # mean channel difference below this counts as no change


# Measured in the page rather than guessed from pixels: the union of every
# visible text node, image, control and SVG, clipped to the viewport. That is the
# real content box, so cropping to it removes both the max-width side gutters and
# the dead space above a masthead in one step.
CONTENT_BOX_JS = """() => {
  const vw = innerWidth, vh = innerHeight;
  let x0 = vw, y0 = vh, x1 = 0, y1 = 0, n = 0;
  document.querySelectorAll('*').forEach(e => {
    const tag = e.tagName;
    if (tag === 'SCRIPT' || tag === 'STYLE') return;
    const hasText = [...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim());
    const isVisual = ['IMG', 'SVG', 'CANVAS', 'INPUT', 'SELECT', 'BUTTON'].includes(tag);
    if (!hasText && !isVisual) return;
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    if (r.bottom < 0 || r.top > vh || r.right < 0 || r.left > vw) return;
    x0 = Math.min(x0, Math.max(0, r.left));
    y0 = Math.min(y0, Math.max(0, r.top));
    x1 = Math.max(x1, Math.min(vw, r.right));
    y1 = Math.max(y1, Math.min(vh, r.bottom));
    n++;
  });
  return n ? {x0, y0, x1, y1} : null;
}"""


# Like CONTENT_BOX_JS but the bottom is NOT clipped to the viewport - the whole
# point is to find content that falls below the fold. Capped at scrollHeight,
# because an inner scrolling list reports element bottoms far past the page:
# Chronoscape's event list measured 6374px against a 1060px document.
FIT_BOX_JS = """() => {
  const vw = innerWidth;
  let x0 = vw, x1 = 0, bottom = 0;
  document.querySelectorAll('*').forEach(e => {
    const tag = e.tagName;
    if (tag === 'SCRIPT' || tag === 'STYLE') return;
    const hasText = [...e.childNodes].some(c => c.nodeType === 3 && c.textContent.trim());
    const isVisual = ['IMG', 'SVG', 'CANVAS', 'INPUT', 'SELECT', 'BUTTON'].includes(tag);
    if (!hasText && !isVisual) return;
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    if (r.right < 0 || r.left > vw) return;
    x0 = Math.min(x0, Math.max(0, r.left));
    x1 = Math.max(x1, Math.min(vw, r.right));
    bottom = Math.max(bottom, r.bottom);
  });
  return {width: x1 - x0, height: Math.min(bottom, document.documentElement.scrollHeight)};
}"""


def content_height(page):
    """How far the content really reaches, ignoring the fold."""
    box = page.evaluate(FIT_BOX_JS)
    return (box or {}).get("height") or 0


def crop_16x10(im, x0, y0, w, h_avail, scale=SCALE):
    """Crop a 16:10 frame of width w starting at (x0, y0), in CSS pixels."""
    h = min(w * 10 / 16, h_avail)
    return im.crop(tuple(round(v * scale) for v in (x0, y0, x0 + w, y0 + h)))


def framed(page, slug, raw, scale=SCALE):
    """Return the cropped 16:10 image for one site."""
    if slug in ANCHOR:
        cfg = ANCHOR[slug]
        # Playwright's own `clip` cannot reach below the fold - a tall element
        # came back silently truncated - so scroll, shoot the viewport, and crop
        # with PIL.
        el = page.locator(cfg["selector"]).first
        box = el.bounding_box()                  # viewport-relative, pre-scroll

        # Frame geometry first, because where to scroll depends on the frame height.
        pad = box["width"] * MARGIN_FRAC
        x0 = max(0, box["x"] - pad)
        x1 = min(VIEW["width"], box["x"] + box["width"] + pad)
        w = x1 - x0
        h = min(w * 10 / 16, VIEW["height"])

        # Put the element's TOP `context_above` of the way down the frame.
        # `scroll_into_view_if_needed` cannot do this for an element TALLER than the
        # viewport - it stops as soon as the element merely overlaps, which for
        # Shortfall's 3998px card list scrolled 1600px PAST the top of the list. The
        # frame then started mid-row with no page chrome in it at all, so the card
        # read as a bare table rather than a website.
        top = box["y"] + page.evaluate("() => scrollY")
        page.evaluate("y => scrollTo(0, y)",
                      max(0, top - h * cfg.get("context_above", 0)))
        page.wait_for_timeout(600)
        box = el.bounding_box()                  # re-measure after the scroll
        page.screenshot(path=str(raw))
        im = Image.open(raw).convert("RGB")
        # Start the frame above the element so the card keeps some page chrome.
        y0 = max(0, min(box["y"] - h * cfg.get("context_above", 0),
                        VIEW["height"] - h))
        return crop_16x10(im, x0, y0, w, VIEW["height"] - y0, scale)

    page.screenshot(path=str(raw))
    im = Image.open(raw).convert("RGB")
    box = page.evaluate(CONTENT_BOX_JS)
    if not box:
        return crop_16x10(im, 0, 0, VIEW["width"], VIEW["height"], scale)

    view = VIEW_FIT if slug in FIT else VIEW
    pad = (box["x1"] - box["x0"]) * MARGIN_FRAC
    x0 = max(0, box["x0"] - pad)
    x1 = min(view["width"], box["x1"] + pad)

    if slug in FIT:
        # Widen the frame until the content's real height fits inside it, spending
        # the side margin rather than shrinking the page. Centred on the content so
        # the extra space is taken evenly from both sides.
        #
        # Capped: widening all the way makes the content small in the card - Lexicon
        # went from clipped to unreadably zoomed out at full widening. Past the cap,
        # accept that the last few pixels of the page fall outside the frame.
        need = min((content_height(page) - box["y0"]) * 16 / 10,
                   (x1 - x0) * MAX_WIDEN)
        if need > x1 - x0:
            mid = (x0 + x1) / 2
            half = min(need, view["width"]) / 2
            x0 = max(0, min(mid - half, view["width"] - min(need, view["width"])))
            x1 = min(view["width"], x0 + min(need, view["width"]))

    # Only a little of the top margin is kept - it is nearly always dead space.
    y0 = max(0, box["y0"] - pad / 2)
    return crop_16x10(im, x0, y0, x1 - x0, view["height"] - y0, scale)


def changed_enough(new, dest):
    """False if the new shot is visually the same as what is already committed."""
    if not dest.exists():
        return True, None
    old = Image.open(dest).convert("RGB")
    if old.size != new.size:
        return True, None
    diff = ImageStat.Stat(ImageChops.difference(old, new)).mean
    return max(diff) >= MIN_DIFF, max(diff)


def main():
    skipped = []
    arg = (sys.argv[1] if len(sys.argv) > 1 else "weekly").lower()
    if arg == "daily":
        slugs = DAILY
    elif arg in ("weekly", "all"):
        slugs = list(SITES)
    elif arg in SITES:
        slugs = [arg]
    else:
        sys.exit(f"unknown target {arg!r} - use daily, weekly, or one of: "
                 + ", ".join(SITES))

    tmp = ROOT / ".shots"
    tmp.mkdir(exist_ok=True)
    wrote = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # A context per site: zooming a page out shrinks its content box in CSS
        # pixels, so a fixed 2x shot of a zoomed page lands well under the width a
        # retina card needs. FIT sites get a higher device scale to cancel that.
        for slug in slugs:
            scale = SCALE
            ctx = browser.new_context(viewport=VIEW_FIT if slug in FIT else VIEW,
                                      device_scale_factor=scale,
                                      user_agent=UA)
            page = ctx.new_page()
            page.emulate_media(color_scheme=SCHEME.get(slug, "light"))
            try:
                page.goto(SITES[slug], wait_until="networkidle", timeout=60000)
            except Exception:                       # noqa: BLE001
                # networkidle never settles on a page that keeps chattering.
                # Substack's archive did exactly this on 17/08/2026 and skipped
                # for ten days, so its card went stale silently. Fall back to
                # "DOM is up" and let the fixed wait below cover the rendering.
                try:
                    page.goto(SITES[slug], wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(3500)
                except Exception as exc:            # noqa: BLE001
                    # One unreachable site must not cost the whole run. A stale
                    # thumbnail is better than a half-updated set.
                    skipped.append(slug) or print(f"{slug:<18} SKIPPED - {type(exc).__name__}: {exc}"[:140])
                    continue
            page.wait_for_timeout(2500)             # client-drawn charts

            # WEBFONTS, before the READY selector rather than after: a shot taken
            # while a Google font is still in flight renders the whole card in
            # the fallback stack, which is a silent visual defect of exactly the
            # kind READY exists to prevent. document.fonts.ready resolves once
            # every face the page asked for has loaded or failed, so this costs
            # nothing on the sites that use no webfont. Wrapped because a hung
            # font request must not take the whole run down: a card in the
            # fallback face still beats no card at all.
            try:
                page.wait_for_function("() => document.fonts.status === 'loaded'",
                                       timeout=8000)
            except Exception:                       # noqa: BLE001
                print(f"{slug:<18} webfonts had not settled in 8s; shooting anyway")

            if slug in READY:
                try:
                    page.wait_for_selector(READY[slug], timeout=READY_TIMEOUT)
                except Exception:                   # noqa: BLE001
                    skipped.append(slug) or print(f"{slug:<18} SKIPPED - {READY[slug]!r} never appeared "
                          f"in {READY_TIMEOUT // 1000}s; keeping the old thumbnail")
                    continue

            body = (page.inner_text("body")[:4000] or "").lower()
            hit = next((j for j in JUNK if j in body), None)
            if hit:
                skipped.append(slug) or print(f"{slug:<18} SKIPPED - page reads as a challenge or error "
                      f"({hit!r}); keeping the old thumbnail")
                continue

            if slug in DISMISS:
                try:
                    page.click(DISMISS[slug], timeout=4000)
                    page.wait_for_timeout(900)
                except Exception:                    # noqa: BLE001
                    pass                             # the modal may not have shown

            if slug in PREPARE:
                page.evaluate(PREPARE[slug])
                page.wait_for_timeout(300)

            im = framed(page, slug, tmp / f"{slug}.png", scale)
            if im.width > TARGET_W:
                im = im.resize((TARGET_W, round(im.height * TARGET_W / im.width)),
                               Image.LANCZOS)

            dest = OUT / f"{slug}.webp"
            ok, diff = changed_enough(im, dest)
            if not ok:
                print(f"{slug:<18} unchanged (diff {diff:.2f} < {MIN_DIFF})")
                continue
            im.save(dest, "WEBP", quality=QUALITY, method=6)
            wrote.append(dest.name)
            note = "new" if diff is None else f"diff {diff:.2f}"
            print(f"{slug:<18} {im.width}x{im.height}  "
                  f"{dest.stat().st_size // 1024}KB  ({note})")
        browser.close()

    for f in tmp.glob("*.png"):
        f.unlink()
    tmp.rmdir()

    print(f"\n{len(wrote)} thumbnail(s) updated"
          + (f": {', '.join(wrote)}" if wrote else " - nothing to commit"))
    # The workflow keys its commit step off this, so an unchanged run is a no-op
    # rather than a commit of identical-looking bytes.
    if wrote:
        subprocess.run(["git", "diff", "--stat", "--", "assets"], cwd=ROOT, check=False)

    # Anything written above is kept and still committed - a partial refresh beats
    # none - but an unexpected skip turns the run red so it is actually seen.
    # Deliberately NOT triggered by "unchanged": an unchanged page legitimately
    # writes nothing, which is why file age alone can never be the signal.
    unexpected = [x for x in skipped if x not in MAY_SKIP]
    if unexpected:
        sys.exit("FAILED: could not shoot " + ", ".join(unexpected)
                 + ". Anything else above was written and is safe to commit.")
    if skipped:
        print("skipped as expected: " + ", ".join(skipped))


if __name__ == "__main__":
    main()
