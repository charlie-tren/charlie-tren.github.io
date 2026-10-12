"""Rasterise favicon.svg into the icon files, with the right alpha for each target.

    python tools/make_icons.py                  # the hub's own mark, at the root
    python tools/make_icons.py crosscheck       # any folder holding a favicon.svg

Two targets that want OPPOSITE things, which is what went wrong before:

- **Browser tabs** (favicon.ico, favicon-192.png, favicon-48.png) want the corners
  TRANSPARENT, so the rounded tile reads as a tile. These were previously flattened
  onto white, which put four white dots in the corners of every dark tab bar - and
  because every page without its own icon falls back to /favicon.ico, that was the
  whole estate.
- **apple-touch-icon.png** wants NO transparency and NO rounding: iOS applies its
  own mask and paints anything transparent BLACK. So it is drawn full-bleed in the
  tile colour with square corners and let iOS round it.

Rasterised with Playwright rather than a native SVG library so this needs nothing
installed beyond what the thumbnail job already uses.
"""

import io
import re
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
# A sub-page needs no .ico: browsers only fetch one from the origin root, and a
# page that links its own PNG never falls back to it.
DIR = ROOT / sys.argv[1] if len(sys.argv) > 1 else ROOT
SVG = (DIR / "favicon.svg").read_text(encoding="utf-8")
TILE = re.search(r'<rect[^>]*fill="(#[0-9a-fA-F]{6})"', SVG).group(1)

# apple-touch: same glyph, full-bleed tile, square corners. The tile is the
# first rect, whatever its radius.
SVG_SQUARE = re.sub(r'(<rect[^>]*?)\srx="[^"]*"', r"\1", SVG, count=1)


def render(pw, svg: str, size: int, transparent: bool) -> Image.Image:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": size, "height": size})
    pg.set_content(
        f'<style>html,body{{margin:0;padding:0;background:transparent}}'
        f'svg{{display:block;width:{size}px;height:{size}px}}</style>{svg}'
    )
    png = pg.screenshot(omit_background=transparent)
    b.close()
    return Image.open(io.BytesIO(png)).convert("RGBA")


def main():
    with sync_playwright() as pw:
        big = render(pw, SVG, 192, True)
        big.save(DIR / "favicon-192.png")
        big.resize((48, 48), Image.LANCZOS).save(DIR / "favicon-48.png")
        if DIR == ROOT:
            # A real multi-size .ico: 16 is what a tab actually draws.
            big.save(ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)])

        touch = render(pw, SVG_SQUARE, 180, False)
        flat = Image.new("RGB", touch.size, TILE)
        flat.paste(touch, mask=touch.split()[3])
        flat.save(DIR / "apple-touch-icon.png")

    for f in ("favicon-192.png", "favicon-48.png", "favicon.ico", "apple-touch-icon.png"):
        if not (DIR / f).exists():
            continue
        im = Image.open(DIR / f)
        corner = im.convert("RGBA").getpixel((0, 0))
        tab = f != "apple-touch-icon.png"
        assert (corner[3] == 0) if tab else (im.mode == "RGB"), \
            f"{DIR / f}: wrong alpha for its target (mode {im.mode}, corner {corner})"
        print(f"{f:24} {im.size[0]}x{im.size[1]}  mode={im.mode}  corner={corner}")


if __name__ == "__main__":
    main()
