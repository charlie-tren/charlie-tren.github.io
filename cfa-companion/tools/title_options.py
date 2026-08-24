"""Try heading faces on the HOME screen, which is where the display type actually
shows: the wordmark, the four big figures, and the section headings.

    python tools/title_options.py

The body face stays Inter, which is settled. Each panel is the real page with
--font-title overridden and a seeded plan, so the figures are real numbers in a
real layout rather than a mock-up of one. Writes tools/shots/title-options-*.png.
"""

import datetime
import functools
import http.server
import pathlib
import socketserver
import threading

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "tools" / "shots"
PORT = 8754
CLIP_H = 660

SYSTEM_SERIF = ('"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif')

# (label, family for --font-title, google family name or None for a system stack)
OPTIONS = [
    ("25  Fraunces, live now", "'Fraunces', serif", "Fraunces"),
    ("26  Instrument Serif", "'Instrument Serif', serif", "Instrument Serif"),
    ("27  DM Serif Display", "'DM Serif Display', serif", "DM Serif Display"),
    ("28  Playfair Display", "'Playfair Display', serif", "Playfair Display"),
    ("29  Newsreader", "'Newsreader', serif", "Newsreader"),
    ("30  Source Serif 4", "'Source Serif 4', serif", "Source Serif 4"),
    ("31  Literata", "'Literata', serif", "Literata"),
    ("32  Spectral", "'Spectral', serif", "Spectral"),
    ("33  Libre Baskerville", "'Libre Baskerville', serif", "Libre Baskerville"),
    ("34  Petrona", "'Petrona', serif", "Petrona"),
    ("35  Bitter", "'Bitter', serif", "Bitter"),
    ("36  Crimson Pro", "'Crimson Pro', serif", "Crimson Pro"),
    ("37  Space Grotesk, a sans", "'Space Grotesk', sans-serif", "Space Grotesk"),
    ("38  Archivo, a sans", "'Archivo', sans-serif", "Archivo"),
    ("39  Inter, so headings are just heavier body", "'Inter', sans-serif", "Inter"),
    ("40  The system serif, no webfont", SYSTEM_SERIF, None),
]


def seed(page):
    stamp = datetime.date.today().isoformat()
    exam = (datetime.date.today() + datetime.timedelta(days=87)).isoformat()
    page.evaluate("""(a) => {
        localStorage.setItem('cfa-companion.v1', JSON.stringify({
          attempts: [], sr: {}, device: 'demo',
          plan: { exam: a.exam, target: 300, extraMin: 0, at: 1 },
          time: { days: { '2026-08-01': { demo: 41.5*3600 }, [a.stamp]: { demo: 1.2*3600 } } }
        }));
    }""", {"exam": exam, "stamp": stamp})


def shoot(page, label, family, google):
    if google:
        page.add_style_tag(url="https://fonts.googleapis.com/css2?family="
                               + google.replace(" ", "+")
                               + ":ital,wght@0,400;0,600;1,400&display=swap")
    page.add_style_tag(content=f":root {{ --font-title: {family} !important; }}")
    page.evaluate("""(text) => {
        const b = document.createElement('div');
        b.textContent = text;
        b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99;padding:7px 14px;'
          + 'background:#1f5f74;color:#fff;font:600 12px/1.3 system-ui,sans-serif;'
          + 'letter-spacing:.09em;text-transform:uppercase';
        document.body.prepend(b);
        document.querySelector('header.wrap').style.paddingTop = '2.6rem';
    }""", label)
    page.wait_for_timeout(2200)
    return page.screenshot(clip={"x": 0, "y": 0, "width": 1000, "height": CLIP_H})


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{PORT}/"

    tiles = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for label, family, google in OPTIONS:
            page = b.new_page(viewport={"width": 1000, "height": CLIP_H},
                              device_scale_factor=2)
            page.goto(url, wait_until="networkidle")
            seed(page)
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(500)
            tiles.append(shoot(page, label, family, google))
            page.close()
            print("shot", label)
        b.close()
    httpd.shutdown()

    ims = [Image.open(__import__("io").BytesIO(t)) for t in tiles]
    w, h = ims[0].size
    pad = 20
    per_sheet = 4
    for n in range(0, len(ims), per_sheet):
        group = ims[n:n + per_sheet]
        sheet = Image.new("RGB", (w * 2 + pad * 3, h * 2 + pad * 3), "#d9d5cc")
        for i, im in enumerate(group):
            x = pad + (i % 2) * (w + pad)
            y = pad + (i // 2) * (h + pad)
            sheet.paste(im.convert("RGB"), (x, y))
        out = SHOTS / f"title-options-{n // per_sheet + 1}.png"
        sheet.save(out)
        print("wrote", out.name)


if __name__ == "__main__":
    main()
