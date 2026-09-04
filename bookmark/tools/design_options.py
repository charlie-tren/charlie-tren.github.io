"""Contact sheet of design directions for Book Club.

    python book-club/tools/design_options.py

Loads the REAL page from a local server and overrides CSS variables and a small
amount of layout per option, so what is judged is the actual page with its actual
type and copy, not a mock-up. Writes tools/design_options.png.
"""

import io
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
HUB = HERE.parent.parent
PORT = 8813
URL = f"http://localhost:{PORT}/book-club/?p=learn%7Cnon%7Cany%7Cany%7Cany%7C3%7Cmarkets"

SHOT_W, SHOT_H = 860, 620

OPTIONS = [
    ("1. Paper", """
     :root{--paper:#f4f0e6;--paper2:#ebe5d6;--card:#fbf8f1;--ink:#211f1a;--ink-soft:#6a6354;
           --line:#ddd4c0;--line2:#cfc4ad;--accent:#7a2e2e;--accent-soft:#f0e2df}
     """),
    ("2. Newsprint", """
     :root{--paper:#fdfdfb;--paper2:#f1f1ed;--card:#fdfdfb;--ink:#111;--ink-soft:#666;
           --line:#111;--line2:#c9c9c4;--accent:#c0392b;--accent-soft:#fbeae7}
     .pick{border-width:1px 0;border-radius:0;box-shadow:none;padding-left:0;padding-right:0}
     .title{font-size:42px;font-weight:600;letter-spacing:-.03em}
     .buy{border-radius:0}.alt{border-radius:0}.opt{border-radius:0}
     .mchip{border-radius:0;background:transparent}
     """),
    ("3. Reading lamp", """
     :root{--paper:#14171a;--paper2:#1c2126;--card:#1a1f24;--ink:#eee6d8;--ink-soft:#98a2ab;
           --line:#2b3238;--line2:#3a434b;--accent:#e0a458;--accent-soft:#2a2318}
     .pick{box-shadow:0 30px 60px -40px #000}
     """),
    ("4. Index card", """
     :root{--paper:#e8e4d9;--paper2:#dedad0;--card:#fdfcf7;--ink:#1e1c18;--ink-soft:#6f6a5e;
           --line:#c8c2b2;--line2:#b3ab98;--accent:#2f5d50;--accent-soft:#e2ece7}
     .pick{border-radius:2px;box-shadow:0 2px 0 #cfc8b6,0 14px 30px -22px rgba(0,0,0,.45)}
     .byline,.month,.mchip,.qlabel{font-family:'Courier New',monospace}
     .month{letter-spacing:.16em}
     .buy,.alt,.opt{border-radius:3px}
     """),
    ("5. Spine", """
     :root{--paper:#f6f4ef;--paper2:#eae6dd;--card:#ffffff;--ink:#1a1a1a;--ink-soft:#6b6b6b;
           --line:#e2ded4;--line2:#cfc9bc;--accent:#e8622c;--accent-soft:#fde9e0}
     .pick{border-radius:4px;border-left:10px solid var(--accent);padding-left:34px}
     .title{font-weight:600}
     .buy,.alt,.opt{border-radius:4px}
     """),
    ("6. Plain", """
     :root{--paper:#ffffff;--paper2:#f4f5f7;--card:#ffffff;--ink:#16181d;--ink-soft:#71767f;
           --line:#e6e8ec;--line2:#d5d9df;--accent:#2f5bd0;--accent-soft:#eaf0ff}
     .title,.why,.lede,.brand,h2.sec{font-family:'Hanken Grotesk',sans-serif}
     .title{font-weight:600;font-size:31px;letter-spacing:-.02em}
     .why{font-size:16px}
     .pick{border-radius:10px;box-shadow:none}
     """),
]


def main():
    srv = subprocess.Popen(
        ["python", "-m", "http.server", str(PORT), "--directory", str(HUB)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    shots = []
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            for name, css in OPTIONS:
                pg = b.new_page(viewport={"width": SHOT_W, "height": SHOT_H},
                                device_scale_factor=2)
                pg.goto(URL, wait_until="networkidle")
                pg.add_style_tag(content=css)
                pg.wait_for_timeout(350)
                shots.append((name, Image.open(io.BytesIO(pg.screenshot())).convert("RGB")))
                pg.close()
            b.close()
    finally:
        srv.terminate()

    cols, pad, label = 2, 26, 40
    w, h = shots[0][1].size
    sheet = Image.new("RGB", (cols * w + (cols + 1) * pad,
                              3 * (h + label) + 4 * pad), "#3a3a3a")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("segoeuib.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    for i, (name, im) in enumerate(shots):
        c, r = i % cols, i // cols
        x = pad + c * (w + pad)
        y = pad + r * (h + label + pad)
        d.text((x, y + 4), name, fill="#ffffff", font=font)
        sheet.paste(im, (x, y + label))
    out = HERE / "design_options.png"
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
