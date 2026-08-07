"""Re-shoot the project card thumbnails from the live sites.

    python tools/shoot_thumbnails.py daily      # the two that change every day
    python tools/shoot_thumbnails.py weekly     # all of them
    python tools/shoot_thumbnails.py one-story  # just one

Every site is shot from its live URL rather than a local build, so this works
the same on a laptop and in Actions with no dev server.

Three things this handles that a naive screenshot does not:

1. **Side gutters.** Most of these sites centre their content in a max-width
   column, so a 1280-wide shot is mostly empty background - One Story was 49%
   dead space (657px of content in a 1280px frame). The shot is taken at 2x and
   cropped to the content column, so the text is legible at card size.
2. **The interesting bit is below the fold** on some pages. `FOCUS` shoots a
   named element instead of the top of the page - Consensus Drift's masthead and
   filter dropdowns made for a thumbnail with no chart in it.
3. **Churn.** A re-shoot of an unchanged page still produces different bytes, so
   a weekly job would commit noise forever. Anything under MIN_DIFF against the
   current file is left alone.

Run it from Actions, not from a laptop. Linux and Windows hint fonts differently,
so a local shot of an UNCHANGED page reads as a ~27-point difference against a
CI-shot one and vice versa - alternating between the two would commit a new
thumbnail every run. Use `gh workflow run "Refresh card thumbnails"` for a manual
refresh; keep local runs for developing this script.
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
    "consensus-drift": "https://charlietrenorden.com/consensus-drift/",
    "crowdwise": "https://crowdwise.charlietrenorden.com/",
    "dcf-studio": "https://dcf.charlietrenorden.com/GOOGL",
    # a country page, not the picker - the landing page is three pills and a
    # half-empty card, which made for a thumbnail showing none of the product
    "chronoscape": "https://chronoscape.charlietrenorden.com/iceland/",
    "thinkerings": "https://thinkerings.substack.com/",
    "lexicon": "https://charlietrenorden.com/lexicon/",
    "beyond-small-talk": "https://charlietrenorden.com/beyond-small-talk/",
}

# One Story and The Aftertimes republish every day, so their thumbnails are
# stale within 24 hours. Everything else only moves when its code does.
DAILY = ["one-story", "the-aftertimes"]

# Pages whose top is a masthead rather than the product. Shoot this element.
FOCUS = {
    "consensus-drift": "svg",       # the quadrant chart IS the product
}

VIEW = {"width": 1280, "height": 800}
SCALE = 2                # shoot at 2x so cropping costs no sharpness
TARGET_W = 1400          # cards render ~600px wide, so this covers retina
QUALITY = 84
MARGIN_FRAC = 0.04       # breathing room either side of the content column
MIN_DIFF = 2.0           # mean channel difference below this counts as no change


def gutters(im):
    """Columns at each edge that are a single flat colour top to bottom."""
    w, h = im.size
    px = im.load()

    def flat(x):
        c = px[x, 0]
        return all(px[x, y] == c for y in range(0, h, 5))

    left = 0
    while left < w // 2 and flat(left):
        left += 1
    right = w - 1
    while right > w // 2 and flat(right):
        right -= 1
    return left, right


def framed(page, slug, raw):
    """Return the cropped 16:10 image for one site."""
    if slug in FOCUS:
        # Playwright's own `clip` cannot reach below the fold - a tall element
        # came back silently truncated - so scroll it into view, shoot the
        # viewport, and crop with PIL.
        el = page.locator(FOCUS[slug]).first
        el.scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        box = el.bounding_box()                  # viewport-relative
        page.screenshot(path=str(raw))
        im = Image.open(raw).convert("RGB")

        pad = box["width"] * MARGIN_FRAC
        x0 = max(0, box["x"] - pad)
        x1 = min(VIEW["width"], box["x"] + box["width"] + pad)
        w = x1 - x0
        h = min(w * 10 / 16, VIEW["height"])
        y0 = max(0, min(box["y"] + box["height"] / 2 - h / 2, VIEW["height"] - h))
        return im.crop(tuple(round(v * SCALE) for v in (x0, y0, x0 + w, y0 + h)))

    page.screenshot(path=str(raw))
    im = Image.open(raw).convert("RGB")
    w, h = im.size
    left, right = gutters(im)
    pad = int((right - left + 1) * MARGIN_FRAC)
    x0 = max(0, left - pad)
    x1 = min(w, right + 1 + pad)
    return im.crop((x0, 0, x1, min(h, round((x1 - x0) * 10 / 16))))


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
        ctx = browser.new_context(viewport=VIEW, device_scale_factor=SCALE)
        page = ctx.new_page()
        for slug in slugs:
            try:
                page.goto(SITES[slug], wait_until="networkidle", timeout=60000)
            except Exception as exc:                # noqa: BLE001
                # One unreachable site must not cost the whole run. A stale
                # thumbnail is better than a half-updated set.
                print(f"{slug:<18} SKIPPED - {type(exc).__name__}: {exc}"[:140])
                continue
            page.wait_for_timeout(2500)             # client-drawn charts

            im = framed(page, slug, tmp / f"{slug}.png")
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
    if not wrote:
        return
    subprocess.run(["git", "diff", "--stat", "--", "assets"], cwd=ROOT, check=False)


if __name__ == "__main__":
    main()
