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
    "property-atlas": "https://charlietrenorden.com/property-atlas/",
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
    "bookmark": "https://charlietrenorden.com/bookmark/",
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
    # Was "#banksize", which is the question-bank line on the practice section - it
    # proved the bank had loaded and said nothing about the dial the card now frames.
    # #pl-done only carries a figure once the seeded store has been read.
    "cfa-companion": "#pl-done",
    # The match chips only exist once the shelf has been scored and a book chosen,
    # and unlike #title they are not in the markup beforehand.
    "bookmark": ".mchip",
    # Statecraft paints its thirteen domains from data.json after load, so the
    # shot lands on an empty column without this. WAS ".opt", which stopped
    # existing on 30/08/2026 when the option cards became sliders: the job would
    # have waited 30s, skipped, and failed the run. A range input is the thing
    # that only exists once the data has arrived.
    "statecraft": "#domains input[type=range]",
    # Property Atlas builds its table from data.json after load, so without this
    # the shot lands on an empty panel. A row is the first thing that only
    # exists once the data has arrived. (Named Absentee, then Foreign Property
    # Screener, before this - the comment had outlived two of them.)
    # Was "#rank rect" until 02/09/2026. The page was redesigned from an SVG
    # ranking chart to a table, so the selector waited 30s for an element that
    # no longer exists and failed the whole run - taking seven good thumbnails
    # with it. A READY selector is coupled to the page's markup; when a page is
    # redesigned, this is the second place to look.
    "property-atlas": "table tbody tr",
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
    # The home screen Charlie picked on 18/09/2026 is the progress dial, and progress is
    # per-visitor - a cold browser draws empty rings. Seed a plausible history and let
    # the page compute the figures from it, so the card shows the real arithmetic.
    #
    # Dates are resolved HERE, at shoot time, from day offsets. Baking absolute dates in
    # would leave the calendar strip drifting out of its own window within a week and
    # the rings quietly emptying, with nothing failing.
    "cfa-companion": """() => {
        const S = {"attempts": [{"q": "q0000", "t": "ethics", "ok": true, "ms": 63851, "at": 0, "m": "free", "ago": 10}, {"q": "q0001", "t": "fsa", "ok": false, "ms": 68496, "at": 0, "m": "free", "ago": 13}, {"q": "q0002", "t": "equity", "ok": true, "ms": 67566, "at": 0, "m": "free", "ago": 5}, {"q": "q0003", "t": "fi", "ok": true, "ms": 57938, "at": 0, "m": "free", "ago": 54}, {"q": "q0004", "t": "pm", "ok": true, "ms": 64390, "at": 0, "m": "free", "ago": 16}, {"q": "q0005", "t": "alts", "ok": false, "ms": 59941, "at": 0, "m": "free", "ago": 8}, {"q": "q0006", "t": "quant", "ok": true, "ms": 21497, "at": 0, "m": "free", "ago": 6}, {"q": "q0007", "t": "econ", "ok": true, "ms": 75148, "at": 0, "m": "free", "ago": 18}, {"q": "q0008", "t": "corporate", "ok": true, "ms": 56321, "at": 0, "m": "free", "ago": 40}, {"q": "q0009", "t": "deriv", "ok": true, "ms": 57518, "at": 0, "m": "free", "ago": 24}, {"q": "q0010", "t": "ethics", "ok": true, "ms": 43857, "at": 0, "m": "free", "ago": 13}, {"q": "q0011", "t": "fsa", "ok": true, "ms": 48092, "at": 0, "m": "free", "ago": 9}, {"q": "q0012", "t": "equity", "ok": true, "ms": 39976, "at": 0, "m": "free", "ago": 69}, {"q": "q0013", "t": "fi", "ok": true, "ms": 40849, "at": 0, "m": "free", "ago": 41}, {"q": "q0014", "t": "pm", "ok": true, "ms": 63758, "at": 0, "m": "free", "ago": 32}, {"q": "q0015", "t": "alts", "ok": false, "ms": 45863, "at": 0, "m": "free", "ago": 32}, {"q": "q0016", "t": "quant", "ok": true, "ms": 46917, "at": 0, "m": "free", "ago": 44}, {"q": "q0017", "t": "econ", "ok": false, "ms": 67558, "at": 0, "m": "free", "ago": 37}, {"q": "q0018", "t": "corporate", "ok": true, "ms": 67025, "at": 0, "m": "free", "ago": 22}, {"q": "q0019", "t": "deriv", "ok": false, "ms": 59443, "at": 0, "m": "free", "ago": 20}, {"q": "q0020", "t": "ethics", "ok": false, "ms": 20440, "at": 0, "m": "free", "ago": 10}, {"q": "q0021", "t": "fsa", "ok": false, "ms": 68914, "at": 0, "m": "free", "ago": 41}, {"q": "q0022", "t": "equity", "ok": true, "ms": 42342, "at": 0, "m": "free", "ago": 59}, {"q": "q0023", "t": "fi", "ok": true, "ms": 65260, "at": 0, "m": "free", "ago": 12}, {"q": "q0024", "t": "pm", "ok": false, "ms": 31592, "at": 0, "m": "free", "ago": 8}, {"q": "q0025", "t": "alts", "ok": false, "ms": 55350, "at": 0, "m": "free", "ago": 40}, {"q": "q0026", "t": "quant", "ok": true, "ms": 77983, "at": 0, "m": "free", "ago": 37}, {"q": "q0027", "t": "econ", "ok": false, "ms": 50872, "at": 0, "m": "free", "ago": 45}, {"q": "q0028", "t": "corporate", "ok": true, "ms": 43752, "at": 0, "m": "free", "ago": 15}, {"q": "q0029", "t": "deriv", "ok": true, "ms": 54024, "at": 0, "m": "free", "ago": 28}, {"q": "q0030", "t": "ethics", "ok": true, "ms": 59261, "at": 0, "m": "free", "ago": 51}, {"q": "q0031", "t": "fsa", "ok": false, "ms": 59668, "at": 0, "m": "free", "ago": 64}, {"q": "q0032", "t": "equity", "ok": true, "ms": 35214, "at": 0, "m": "free", "ago": 18}, {"q": "q0033", "t": "fi", "ok": false, "ms": 57548, "at": 0, "m": "free", "ago": 36}, {"q": "q0034", "t": "pm", "ok": true, "ms": 73136, "at": 0, "m": "free", "ago": 49}, {"q": "q0035", "t": "alts", "ok": false, "ms": 50198, "at": 0, "m": "free", "ago": 20}, {"q": "q0036", "t": "quant", "ok": true, "ms": 63927, "at": 0, "m": "free", "ago": 2}, {"q": "q0037", "t": "econ", "ok": true, "ms": 68701, "at": 0, "m": "free", "ago": 24}, {"q": "q0038", "t": "corporate", "ok": true, "ms": 66583, "at": 0, "m": "free", "ago": 48}, {"q": "q0039", "t": "deriv", "ok": false, "ms": 52375, "at": 0, "m": "free", "ago": 41}, {"q": "q0040", "t": "ethics", "ok": false, "ms": 45844, "at": 0, "m": "free", "ago": 7}, {"q": "q0041", "t": "fsa", "ok": true, "ms": 36310, "at": 0, "m": "free", "ago": 51}, {"q": "q0042", "t": "equity", "ok": true, "ms": 39375, "at": 0, "m": "free", "ago": 52}, {"q": "q0043", "t": "fi", "ok": true, "ms": 61904, "at": 0, "m": "free", "ago": 9}, {"q": "q0044", "t": "pm", "ok": false, "ms": 45708, "at": 0, "m": "free", "ago": 7}, {"q": "q0045", "t": "alts", "ok": true, "ms": 54462, "at": 0, "m": "free", "ago": 20}, {"q": "q0046", "t": "quant", "ok": true, "ms": 70325, "at": 0, "m": "free", "ago": 10}, {"q": "q0047", "t": "econ", "ok": false, "ms": 45911, "at": 0, "m": "free", "ago": 49}, {"q": "q0048", "t": "corporate", "ok": true, "ms": 51816, "at": 0, "m": "free", "ago": 47}, {"q": "q0049", "t": "deriv", "ok": true, "ms": 64932, "at": 0, "m": "free", "ago": 15}, {"q": "q0050", "t": "ethics", "ok": true, "ms": 67667, "at": 0, "m": "free", "ago": 62}, {"q": "q0051", "t": "fsa", "ok": true, "ms": 51320, "at": 0, "m": "free", "ago": 19}, {"q": "q0052", "t": "equity", "ok": true, "ms": 45963, "at": 0, "m": "free", "ago": 21}, {"q": "q0053", "t": "fi", "ok": true, "ms": 61172, "at": 0, "m": "free", "ago": 27}, {"q": "q0054", "t": "pm", "ok": false, "ms": 44240, "at": 0, "m": "free", "ago": 70}, {"q": "q0055", "t": "alts", "ok": false, "ms": 50607, "at": 0, "m": "free", "ago": 68}, {"q": "q0056", "t": "quant", "ok": true, "ms": 48188, "at": 0, "m": "free", "ago": 34}, {"q": "q0057", "t": "econ", "ok": true, "ms": 47216, "at": 0, "m": "free", "ago": 22}, {"q": "q0058", "t": "corporate", "ok": true, "ms": 54974, "at": 0, "m": "free", "ago": 65}, {"q": "q0059", "t": "deriv", "ok": true, "ms": 69230, "at": 0, "m": "free", "ago": 29}, {"q": "q0060", "t": "ethics", "ok": true, "ms": 57637, "at": 0, "m": "free", "ago": 25}, {"q": "q0061", "t": "fsa", "ok": false, "ms": 29088, "at": 0, "m": "free", "ago": 52}, {"q": "q0062", "t": "equity", "ok": true, "ms": 54461, "at": 0, "m": "free", "ago": 46}, {"q": "q0063", "t": "fi", "ok": false, "ms": 68725, "at": 0, "m": "free", "ago": 4}, {"q": "q0064", "t": "pm", "ok": true, "ms": 42954, "at": 0, "m": "free", "ago": 45}, {"q": "q0065", "t": "alts", "ok": true, "ms": 53594, "at": 0, "m": "free", "ago": 45}, {"q": "q0066", "t": "quant", "ok": false, "ms": 45482, "at": 0, "m": "free", "ago": 30}, {"q": "q0067", "t": "econ", "ok": true, "ms": 59426, "at": 0, "m": "free", "ago": 44}, {"q": "q0068", "t": "corporate", "ok": true, "ms": 30617, "at": 0, "m": "free", "ago": 1}, {"q": "q0069", "t": "deriv", "ok": true, "ms": 30866, "at": 0, "m": "free", "ago": 45}, {"q": "q0070", "t": "ethics", "ok": true, "ms": 69729, "at": 0, "m": "free", "ago": 50}, {"q": "q0071", "t": "fsa", "ok": false, "ms": 62451, "at": 0, "m": "free", "ago": 26}, {"q": "q0072", "t": "equity", "ok": true, "ms": 62724, "at": 0, "m": "free", "ago": 43}, {"q": "q0073", "t": "fi", "ok": true, "ms": 74251, "at": 0, "m": "free", "ago": 51}, {"q": "q0074", "t": "pm", "ok": true, "ms": 51753, "at": 0, "m": "free", "ago": 21}, {"q": "q0075", "t": "alts", "ok": true, "ms": 46107, "at": 0, "m": "free", "ago": 17}, {"q": "q0076", "t": "quant", "ok": true, "ms": 38815, "at": 0, "m": "free", "ago": 19}, {"q": "q0077", "t": "econ", "ok": true, "ms": 43537, "at": 0, "m": "free", "ago": 61}, {"q": "q0078", "t": "corporate", "ok": true, "ms": 41583, "at": 0, "m": "free", "ago": 17}, {"q": "q0079", "t": "deriv", "ok": true, "ms": 66260, "at": 0, "m": "free", "ago": 14}, {"q": "q0080", "t": "ethics", "ok": true, "ms": 65652, "at": 0, "m": "free", "ago": 25}, {"q": "q0081", "t": "fsa", "ok": false, "ms": 45951, "at": 0, "m": "free", "ago": 28}, {"q": "q0082", "t": "equity", "ok": true, "ms": 55826, "at": 0, "m": "free", "ago": 42}, {"q": "q0083", "t": "fi", "ok": true, "ms": 68061, "at": 0, "m": "free", "ago": 54}, {"q": "q0084", "t": "pm", "ok": false, "ms": 73314, "at": 0, "m": "free", "ago": 59}, {"q": "q0085", "t": "alts", "ok": false, "ms": 60579, "at": 0, "m": "free", "ago": 67}, {"q": "q0086", "t": "quant", "ok": true, "ms": 66363, "at": 0, "m": "free", "ago": 69}, {"q": "q0087", "t": "econ", "ok": true, "ms": 43833, "at": 0, "m": "free", "ago": 66}, {"q": "q0088", "t": "corporate", "ok": true, "ms": 43718, "at": 0, "m": "free", "ago": 1}, {"q": "q0089", "t": "deriv", "ok": false, "ms": 55271, "at": 0, "m": "free", "ago": 20}, {"q": "q0090", "t": "ethics", "ok": true, "ms": 29809, "at": 0, "m": "free", "ago": 8}, {"q": "q0091", "t": "fsa", "ok": true, "ms": 55730, "at": 0, "m": "free", "ago": 67}, {"q": "q0092", "t": "equity", "ok": true, "ms": 27911, "at": 0, "m": "free", "ago": 8}, {"q": "q0093", "t": "fi", "ok": true, "ms": 54661, "at": 0, "m": "free", "ago": 36}, {"q": "q0094", "t": "pm", "ok": true, "ms": 64552, "at": 0, "m": "free", "ago": 4}, {"q": "q0095", "t": "alts", "ok": false, "ms": 60850, "at": 0, "m": "free", "ago": 9}, {"q": "q0096", "t": "quant", "ok": true, "ms": 39366, "at": 0, "m": "free", "ago": 66}, {"q": "q0097", "t": "econ", "ok": true, "ms": 41206, "at": 0, "m": "free", "ago": 36}, {"q": "q0098", "t": "corporate", "ok": true, "ms": 36383, "at": 0, "m": "free", "ago": 32}, {"q": "q0099", "t": "deriv", "ok": false, "ms": 48685, "at": 0, "m": "free", "ago": 34}, {"q": "q0100", "t": "ethics", "ok": false, "ms": 59361, "at": 0, "m": "free", "ago": 58}, {"q": "q0101", "t": "fsa", "ok": true, "ms": 46121, "at": 0, "m": "free", "ago": 16}, {"q": "q0102", "t": "equity", "ok": true, "ms": 43589, "at": 0, "m": "free", "ago": 55}, {"q": "q0103", "t": "fi", "ok": true, "ms": 71111, "at": 0, "m": "free", "ago": 39}, {"q": "q0104", "t": "pm", "ok": true, "ms": 58470, "at": 0, "m": "free", "ago": 47}, {"q": "q0105", "t": "alts", "ok": true, "ms": 47111, "at": 0, "m": "free", "ago": 18}, {"q": "q0106", "t": "quant", "ok": false, "ms": 58563, "at": 0, "m": "free", "ago": 51}, {"q": "q0107", "t": "econ", "ok": false, "ms": 85932, "at": 0, "m": "free", "ago": 21}, {"q": "q0108", "t": "corporate", "ok": false, "ms": 56114, "at": 0, "m": "free", "ago": 56}, {"q": "q0109", "t": "deriv", "ok": false, "ms": 44781, "at": 0, "m": "free", "ago": 52}, {"q": "q0110", "t": "ethics", "ok": true, "ms": 56099, "at": 0, "m": "free", "ago": 47}, {"q": "q0111", "t": "fsa", "ok": true, "ms": 63555, "at": 0, "m": "free", "ago": 59}, {"q": "q0112", "t": "equity", "ok": true, "ms": 64483, "at": 0, "m": "free", "ago": 38}, {"q": "q0113", "t": "fi", "ok": true, "ms": 53424, "at": 0, "m": "free", "ago": 9}, {"q": "q0114", "t": "pm", "ok": true, "ms": 60793, "at": 0, "m": "free", "ago": 14}, {"q": "q0115", "t": "alts", "ok": true, "ms": 47060, "at": 0, "m": "free", "ago": 35}, {"q": "q0116", "t": "quant", "ok": true, "ms": 54014, "at": 0, "m": "free", "ago": 17}, {"q": "q0117", "t": "econ", "ok": false, "ms": 41066, "at": 0, "m": "free", "ago": 34}, {"q": "q0118", "t": "corporate", "ok": true, "ms": 35606, "at": 0, "m": "free", "ago": 64}, {"q": "q0119", "t": "deriv", "ok": false, "ms": 48162, "at": 0, "m": "free", "ago": 12}, {"q": "q0120", "t": "ethics", "ok": true, "ms": 54731, "at": 0, "m": "free", "ago": 10}, {"q": "q0121", "t": "fsa", "ok": true, "ms": 43518, "at": 0, "m": "free", "ago": 3}, {"q": "q0122", "t": "equity", "ok": true, "ms": 53866, "at": 0, "m": "free", "ago": 29}, {"q": "q0123", "t": "fi", "ok": true, "ms": 46450, "at": 0, "m": "free", "ago": 16}, {"q": "q0124", "t": "pm", "ok": true, "ms": 42559, "at": 0, "m": "free", "ago": 35}, {"q": "q0125", "t": "alts", "ok": false, "ms": 67052, "at": 0, "m": "free", "ago": 6}, {"q": "q0126", "t": "quant", "ok": true, "ms": 52489, "at": 0, "m": "free", "ago": 21}, {"q": "q0127", "t": "econ", "ok": true, "ms": 58723, "at": 0, "m": "free", "ago": 24}, {"q": "q0128", "t": "corporate", "ok": true, "ms": 47464, "at": 0, "m": "free", "ago": 27}, {"q": "q0129", "t": "deriv", "ok": true, "ms": 63048, "at": 0, "m": "free", "ago": 65}, {"q": "q0130", "t": "ethics", "ok": true, "ms": 48751, "at": 0, "m": "free", "ago": 33}, {"q": "q0131", "t": "fsa", "ok": true, "ms": 77052, "at": 0, "m": "free", "ago": 3}, {"q": "q0132", "t": "equity", "ok": true, "ms": 43388, "at": 0, "m": "free", "ago": 61}, {"q": "q0133", "t": "fi", "ok": true, "ms": 49139, "at": 0, "m": "free", "ago": 58}, {"q": "q0134", "t": "pm", "ok": true, "ms": 58250, "at": 0, "m": "free", "ago": 64}, {"q": "q0135", "t": "alts", "ok": true, "ms": 38480, "at": 0, "m": "free", "ago": 51}, {"q": "q0136", "t": "quant", "ok": false, "ms": 48538, "at": 0, "m": "free", "ago": 30}, {"q": "q0137", "t": "econ", "ok": true, "ms": 61110, "at": 0, "m": "free", "ago": 18}, {"q": "q0138", "t": "corporate", "ok": true, "ms": 49306, "at": 0, "m": "free", "ago": 17}, {"q": "q0139", "t": "deriv", "ok": true, "ms": 55829, "at": 0, "m": "free", "ago": 33}, {"q": "q0140", "t": "ethics", "ok": true, "ms": 71469, "at": 0, "m": "free", "ago": 49}, {"q": "q0141", "t": "fsa", "ok": false, "ms": 59064, "at": 0, "m": "free", "ago": 37}, {"q": "q0142", "t": "equity", "ok": true, "ms": 50498, "at": 0, "m": "free", "ago": 24}, {"q": "q0143", "t": "fi", "ok": true, "ms": 48013, "at": 0, "m": "free", "ago": 58}, {"q": "q0144", "t": "pm", "ok": true, "ms": 43781, "at": 0, "m": "free", "ago": 42}, {"q": "q0145", "t": "alts", "ok": true, "ms": 61424, "at": 0, "m": "free", "ago": 40}, {"q": "q0146", "t": "quant", "ok": true, "ms": 57174, "at": 0, "m": "free", "ago": 11}, {"q": "q0147", "t": "econ", "ok": true, "ms": 63547, "at": 0, "m": "free", "ago": 65}, {"q": "q0148", "t": "corporate", "ok": true, "ms": 52277, "at": 0, "m": "free", "ago": 12}, {"q": "q0149", "t": "deriv", "ok": true, "ms": 76224, "at": 0, "m": "free", "ago": 12}, {"q": "q0150", "t": "ethics", "ok": true, "ms": 40020, "at": 0, "m": "free", "ago": 39}, {"q": "q0151", "t": "fsa", "ok": true, "ms": 44731, "at": 0, "m": "free", "ago": 30}, {"q": "q0152", "t": "equity", "ok": true, "ms": 78461, "at": 0, "m": "free", "ago": 20}, {"q": "q0153", "t": "fi", "ok": false, "ms": 44785, "at": 0, "m": "free", "ago": 50}, {"q": "q0154", "t": "pm", "ok": true, "ms": 49005, "at": 0, "m": "free", "ago": 37}, {"q": "q0155", "t": "alts", "ok": false, "ms": 35930, "at": 0, "m": "free", "ago": 19}, {"q": "q0156", "t": "quant", "ok": true, "ms": 67080, "at": 0, "m": "free", "ago": 55}, {"q": "q0157", "t": "econ", "ok": false, "ms": 26606, "at": 0, "m": "free", "ago": 65}, {"q": "q0158", "t": "corporate", "ok": true, "ms": 35596, "at": 0, "m": "free", "ago": 3}, {"q": "q0159", "t": "deriv", "ok": false, "ms": 49533, "at": 0, "m": "free", "ago": 30}, {"q": "q0160", "t": "ethics", "ok": true, "ms": 71248, "at": 0, "m": "free", "ago": 14}, {"q": "q0161", "t": "fsa", "ok": true, "ms": 57182, "at": 0, "m": "free", "ago": 58}, {"q": "q0162", "t": "equity", "ok": true, "ms": 38355, "at": 0, "m": "free", "ago": 32}, {"q": "q0163", "t": "fi", "ok": true, "ms": 37872, "at": 0, "m": "free", "ago": 1}, {"q": "q0164", "t": "pm", "ok": true, "ms": 81403, "at": 0, "m": "free", "ago": 69}, {"q": "q0165", "t": "alts", "ok": true, "ms": 65861, "at": 0, "m": "free", "ago": 68}, {"q": "q0166", "t": "quant", "ok": true, "ms": 51115, "at": 0, "m": "free", "ago": 10}, {"q": "q0167", "t": "econ", "ok": false, "ms": 41363, "at": 0, "m": "free", "ago": 31}, {"q": "q0168", "t": "corporate", "ok": true, "ms": 58379, "at": 0, "m": "free", "ago": 59}, {"q": "q0169", "t": "deriv", "ok": true, "ms": 74070, "at": 0, "m": "free", "ago": 49}, {"q": "q0170", "t": "ethics", "ok": true, "ms": 61747, "at": 0, "m": "free", "ago": 6}, {"q": "q0171", "t": "fsa", "ok": true, "ms": 45854, "at": 0, "m": "free", "ago": 26}, {"q": "q0172", "t": "equity", "ok": true, "ms": 58438, "at": 0, "m": "free", "ago": 39}, {"q": "q0173", "t": "fi", "ok": false, "ms": 60566, "at": 0, "m": "free", "ago": 18}, {"q": "q0174", "t": "pm", "ok": true, "ms": 62282, "at": 0, "m": "free", "ago": 13}, {"q": "q0175", "t": "alts", "ok": false, "ms": 56120, "at": 0, "m": "free", "ago": 63}, {"q": "q0176", "t": "quant", "ok": true, "ms": 36433, "at": 0, "m": "free", "ago": 60}, {"q": "q0177", "t": "econ", "ok": false, "ms": 50376, "at": 0, "m": "free", "ago": 26}, {"q": "q0178", "t": "corporate", "ok": true, "ms": 65594, "at": 0, "m": "free", "ago": 38}, {"q": "q0179", "t": "deriv", "ok": true, "ms": 60138, "at": 0, "m": "free", "ago": 65}, {"q": "q0180", "t": "ethics", "ok": false, "ms": 41479, "at": 0, "m": "free", "ago": 27}, {"q": "q0181", "t": "fsa", "ok": false, "ms": 55458, "at": 0, "m": "free", "ago": 27}, {"q": "q0182", "t": "equity", "ok": true, "ms": 71587, "at": 0, "m": "free", "ago": 34}, {"q": "q0183", "t": "fi", "ok": false, "ms": 64483, "at": 0, "m": "free", "ago": 17}, {"q": "q0184", "t": "pm", "ok": true, "ms": 44326, "at": 0, "m": "free", "ago": 15}, {"q": "q0185", "t": "alts", "ok": false, "ms": 43654, "at": 0, "m": "free", "ago": 30}, {"q": "q0186", "t": "quant", "ok": true, "ms": 61980, "at": 0, "m": "free", "ago": 21}, {"q": "q0187", "t": "econ", "ok": true, "ms": 42162, "at": 0, "m": "free", "ago": 63}, {"q": "q0188", "t": "corporate", "ok": true, "ms": 33303, "at": 0, "m": "free", "ago": 54}, {"q": "q0189", "t": "deriv", "ok": true, "ms": 64634, "at": 0, "m": "free", "ago": 41}, {"q": "q0190", "t": "ethics", "ok": true, "ms": 45935, "at": 0, "m": "free", "ago": 44}, {"q": "q0191", "t": "fsa", "ok": false, "ms": 62817, "at": 0, "m": "free", "ago": 16}, {"q": "q0192", "t": "equity", "ok": false, "ms": 52718, "at": 0, "m": "free", "ago": 38}, {"q": "q0193", "t": "fi", "ok": true, "ms": 54026, "at": 0, "m": "free", "ago": 9}, {"q": "q0194", "t": "pm", "ok": true, "ms": 70673, "at": 0, "m": "free", "ago": 47}, {"q": "q0195", "t": "alts", "ok": false, "ms": 51858, "at": 0, "m": "free", "ago": 36}, {"q": "q0196", "t": "quant", "ok": false, "ms": 51127, "at": 0, "m": "free", "ago": 37}, {"q": "q0197", "t": "econ", "ok": true, "ms": 56473, "at": 0, "m": "free", "ago": 20}, {"q": "q0198", "t": "corporate", "ok": true, "ms": 50347, "at": 0, "m": "free", "ago": 25}, {"q": "q0199", "t": "deriv", "ok": false, "ms": 68663, "at": 0, "m": "free", "ago": 55}, {"q": "q0200", "t": "ethics", "ok": false, "ms": 59502, "at": 0, "m": "free", "ago": 27}, {"q": "q0201", "t": "fsa", "ok": false, "ms": 33713, "at": 0, "m": "free", "ago": 7}, {"q": "q0202", "t": "equity", "ok": false, "ms": 35612, "at": 0, "m": "free", "ago": 18}, {"q": "q0203", "t": "fi", "ok": false, "ms": 62272, "at": 0, "m": "free", "ago": 37}, {"q": "q0204", "t": "pm", "ok": true, "ms": 67052, "at": 0, "m": "free", "ago": 22}, {"q": "q0205", "t": "alts", "ok": true, "ms": 42698, "at": 0, "m": "free", "ago": 44}, {"q": "q0206", "t": "quant", "ok": true, "ms": 51172, "at": 0, "m": "free", "ago": 34}, {"q": "q0207", "t": "econ", "ok": true, "ms": 74923, "at": 0, "m": "free", "ago": 31}, {"q": "q0208", "t": "corporate", "ok": true, "ms": 38878, "at": 0, "m": "free", "ago": 22}, {"q": "q0209", "t": "deriv", "ok": false, "ms": 47058, "at": 0, "m": "free", "ago": 10}, {"q": "q0210", "t": "ethics", "ok": true, "ms": 65631, "at": 0, "m": "free", "ago": 29}, {"q": "q0211", "t": "fsa", "ok": true, "ms": 42855, "at": 0, "m": "free", "ago": 43}, {"q": "q0212", "t": "equity", "ok": false, "ms": 44699, "at": 0, "m": "free", "ago": 25}, {"q": "q0213", "t": "fi", "ok": true, "ms": 54374, "at": 0, "m": "free", "ago": 23}, {"q": "q0214", "t": "pm", "ok": true, "ms": 60700, "at": 0, "m": "free", "ago": 34}, {"q": "q0215", "t": "alts", "ok": false, "ms": 57605, "at": 0, "m": "free", "ago": 26}, {"q": "q0216", "t": "quant", "ok": false, "ms": 51968, "at": 0, "m": "free", "ago": 53}, {"q": "q0217", "t": "econ", "ok": false, "ms": 37554, "at": 0, "m": "free", "ago": 27}, {"q": "q0218", "t": "corporate", "ok": true, "ms": 49362, "at": 0, "m": "free", "ago": 36}, {"q": "q0219", "t": "deriv", "ok": true, "ms": 56261, "at": 0, "m": "free", "ago": 47}, {"q": "q0220", "t": "ethics", "ok": true, "ms": 32272, "at": 0, "m": "free", "ago": 28}, {"q": "q0221", "t": "fsa", "ok": true, "ms": 51579, "at": 0, "m": "free", "ago": 32}, {"q": "q0222", "t": "equity", "ok": true, "ms": 42934, "at": 0, "m": "free", "ago": 40}, {"q": "q0223", "t": "fi", "ok": false, "ms": 40191, "at": 0, "m": "free", "ago": 3}, {"q": "q0224", "t": "pm", "ok": true, "ms": 30798, "at": 0, "m": "free", "ago": 61}, {"q": "q0225", "t": "alts", "ok": false, "ms": 62769, "at": 0, "m": "free", "ago": 63}, {"q": "q0226", "t": "quant", "ok": true, "ms": 27136, "at": 0, "m": "free", "ago": 68}, {"q": "q0227", "t": "econ", "ok": false, "ms": 72171, "at": 0, "m": "free", "ago": 58}, {"q": "q0228", "t": "corporate", "ok": true, "ms": 58277, "at": 0, "m": "free", "ago": 67}, {"q": "q0229", "t": "deriv", "ok": false, "ms": 57130, "at": 0, "m": "free", "ago": 14}, {"q": "q0230", "t": "ethics", "ok": false, "ms": 48429, "at": 0, "m": "free", "ago": 59}, {"q": "q0231", "t": "fsa", "ok": true, "ms": 32104, "at": 0, "m": "free", "ago": 6}, {"q": "q0232", "t": "equity", "ok": true, "ms": 64797, "at": 0, "m": "free", "ago": 5}, {"q": "q0233", "t": "fi", "ok": false, "ms": 64903, "at": 0, "m": "free", "ago": 39}, {"q": "q0234", "t": "pm", "ok": false, "ms": 39977, "at": 0, "m": "free", "ago": 56}, {"q": "q0235", "t": "alts", "ok": false, "ms": 39753, "at": 0, "m": "free", "ago": 15}, {"q": "q0236", "t": "quant", "ok": true, "ms": 41557, "at": 0, "m": "free", "ago": 25}, {"q": "q0237", "t": "econ", "ok": true, "ms": 83900, "at": 0, "m": "free", "ago": 29}, {"q": "q0238", "t": "corporate", "ok": true, "ms": 69385, "at": 0, "m": "free", "ago": 59}, {"q": "q0239", "t": "deriv", "ok": true, "ms": 52125, "at": 0, "m": "free", "ago": 41}], "hours": {"0": 2.677, "1": 1.394, "2": 3.211, "3": 1.694, "5": 1.618, "6": 1.257, "7": 2.511, "9": 1.74, "10": 1.781, "11": 1.515, "12": 1.458, "13": 1.983, "14": 2.247, "15": 1.476, "16": 1.451, "17": 3.893, "18": 2.139, "19": 2.819, "20": 2.485, "21": 2.636, "22": 2.164, "24": 2.203, "25": 2.967, "26": 1.132, "27": 1.755, "28": 2.45, "29": 3.159, "30": 2.235, "31": 1.761, "33": 2.424, "34": 2.395, "35": 1.887, "36": 1.078, "37": 3.164, "38": 2.863, "39": 2.276, "40": 2.267, "41": 2.713, "43": 2.517, "47": 0.737, "48": 1.971, "49": 0.4, "50": 3.069, "51": 1.709, "52": 1.739, "54": 2.587, "55": 0.723, "57": 0.571, "58": 3.912, "59": 1.468, "60": 1.156, "61": 2.398, "62": 2.425, "63": 0.761, "64": 1.443, "65": 1.555, "66": 2.065, "67": 1.682, "68": 2.005}};
        const DAY = 86400000, now = Date.now();
        const iso = (d) => new Date(now - d * DAY).toISOString().slice(0, 10);
        const days = {};
        for (const [d, h] of Object.entries(S.hours)) {
            days[iso(Number(d))] = { seed: Math.round(h * 3600) };
        }
        const attempts = S.attempts.map((a) => ({
            q: a.q, t: a.t, ok: a.ok, ms: a.ms, m: a.m, at: now - a.ago * DAY,
        }));
        try {
            localStorage.setItem("cfa-companion.v1", JSON.stringify({
                attempts, sr: {}, device: "seed",
                plan: { exam: iso(-60), target: 300 },
                time: { days },
            }));
        } catch (e) {}
        location.reload();
    }""",
    # A second pass AFTER the reload, because the seed above reloads the page and
    # anything set before it is gone. `.planfoot` is a sync-status line and a Settings
    # chip: controls that say nothing on a card, and they were sitting in the middle of
    # the frame between the dial and the figures.
    "cfa-companion-after": """() => {
        const foot = document.querySelector('.planfoot');
        if (foot) foot.style.display = 'none';
    }""",
    # #filters-panel is ~300px of sliders and three "Any" dropdowns sitting between
    # the masthead and the map. The ANCHOR below claimed to show "the map with the
    # masthead above it" and could not: at 0.22 the frame started mid-filters, so the
    # card opened on a strip of half-cut controls and the page's name never got in
    # shot. Taking the panel out of shot puts the masthead directly above the map,
    # which is what the frame was always meant to be. The page is unaffected - this
    # runs in the shooter's browser only.
    "property-atlas": """() => {
        document.getElementById('filters-panel').style.display = 'none';
        // THE ATLANTIC CROP, Charlie's pick 18/09/2026. The map is 2.45:1 and the card
        // is 1.60:1, so no crop keeping every continent can fill it - and at the ~330px
        // the card renders at, the whole world is 135px tall and a country is two
        // pixels. Trimming the empty southern ocean, the obvious fix, came out barely
        // distinguishable from the original at that size.
        //
        // 150 40 750 400 holds the Americas, Europe and Africa: 22 of the 34 markets
        // with their labels readable. The height attribute has to go with it, or the
        // content letterboxes inside the old box and nothing visibly changes.
        const map = document.getElementById('map');
        if (map) {
            map.removeAttribute('height');
            map.setAttribute('viewBox', '150 40 750 400');
            map.setAttribute('preserveAspectRatio', 'xMidYMid meet');
            map.style.width = '100%';
            map.style.height = 'auto';
            map.style.display = 'block';
        }
    }""",
}

# Sites that look better - or are designed - dark. Playwright emulates light by
# default, so a site that keys off prefers-color-scheme renders in its light theme
# unless told otherwise.
SCHEME = {
    "cfa-companion": "dark",
    # Bookmark has no light mode at all: a wall of cloth spines on a pale ground
    # reads as swatches. The emulation is set anyway so the shot cannot drift.
    "bookmark": "dark",
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
    # The dial, with the masthead above it - consistent with every other card, and the
    # element Charlie picked stays the first thing you see. 0.34 reaches the wordmark and
    # the tagline; more than that and the frame runs past the panel into the sliced stat
    # row underneath.
    "cfa-companion": {"selector": "#plan", "context_above": 0.27},
    "consensus-drift": {"selector": "svg", "context_above": 0.30},
    # The top of the page is a wordmark and six sliders. Shot unanchored on
    # 31/08/2026 the card was 590px of controls and three bars, which reads as a
    # settings screen rather than as a ranking of thirty-four countries. Framed
    # on the chart, with enough above it to keep the title and a row of the
    # controls in, so the card still shows a website with a chart in it.
    # 0.18 landed mid-hint and left an orphan "HELP." across the top of the card.
    # The MAP, not the table. Anchored on the table the card sliced its own last
    # column, because a nine-column table is wider than 16:10 will hold and the
    # crop has to cut somewhere. A world map is legible at card size and a
    # truncated table is not, so the card shows the map with the masthead above
    # it. (Before that it was "#rank-panel", an element deleted two redesigns
    # earlier - ANCHOR is coupled to the markup exactly like READY is.)
    # 0.22 was set when the filter panel was still in shot and it framed on the
    # panel's bottom edge, not the masthead. With the panel hidden in PREPARE this
    # reaches the wordmark and the tagline and stops.
    "property-atlas": {"selector": "#map-panel", "context_above": 0.30},
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


def changed_enough(new, dest, force=False):
    """False if the new shot is visually the same as what is already committed.

    `force` bypasses the guard, and it exists because THE GUARD CANNOT SEE A
    COLOUR-ONLY CHANGE. On 31/08/2026 Statecraft's entire palette was
    regenerated, every hue on the page replaced, and this scored the difference
    at 1.36 against a MIN_DIFF of 2.0 and kept the old card. The layout was
    identical, so nearly every pixel was unchanged and the new colours lived in
    thin borders and small text. The card then advertised a design the site no
    longer had, and only an eyeball caught it, which is how the Substack card
    went stale for ten days.

    Lowering MIN_DIFF globally would put the weekly sweep back to committing
    noise, which is the thing it exists to stop, so the override is scoped to
    intent instead. See main().
    """
    if force:
        return True, None
    if not dest.exists():
        return True, None
    old = Image.open(dest).convert("RGB")
    if old.size != new.size:
        return True, None
    diff = ImageStat.Stat(ImageChops.difference(old, new)).mean
    return max(diff) >= MIN_DIFF, max(diff)


def main():
    skipped = []
    force = False
    arg = (sys.argv[1] if len(sys.argv) > 1 else "weekly").lower()
    if arg == "daily":
        slugs = DAILY
    elif arg in ("weekly", "all"):
        slugs = list(SITES)
    elif arg in SITES:
        slugs = [arg]
        # NAMING ONE SITE IS A DELIBERATE ACT, so it overrides the churn guard.
        # That guard exists to stop the weekly sweep committing noise across
        # twenty pages nobody touched. Someone asking for one specific card has
        # a reason, and the likeliest reason is a change too small in pixels for
        # the guard to see, which is exactly the case that produced it.
        force = True
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
                # A PREPARE step may NAVIGATE - cfa-companion's seeds localStorage and
                # reloads, because the page reads its store once at boot. READY was
                # waited on before PREPARE ran, so after a reload the frame would be
                # shot against a half-built page. Re-settle, then re-wait READY.
                # Harmless for every other slug: nothing to load, so both return at once.
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:                    # noqa: BLE001
                    pass
                if slug in READY:
                    try:
                        page.wait_for_selector(READY[slug], timeout=READY_TIMEOUT)
                    except Exception:                # noqa: BLE001
                        skipped.append(slug) or print(
                            f"{slug:<18} SKIPPED - {READY[slug]!r} never came back after "
                            f"PREPARE; keeping the old thumbnail")
                        continue
                    page.wait_for_timeout(700)       # the dial animates its rings in

            # A step that has to run AFTER a navigating PREPARE, for chrome that only
            # exists once the page has rebuilt itself.
            if slug + "-after" in PREPARE:
                page.evaluate(PREPARE[slug + "-after"])
                page.wait_for_timeout(250)

            im = framed(page, slug, tmp / f"{slug}.png", scale)
            if im.width > TARGET_W:
                im = im.resize((TARGET_W, round(im.height * TARGET_W / im.width)),
                               Image.LANCZOS)

            dest = OUT / f"{slug}.webp"
            ok, diff = changed_enough(im, dest, force)
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
