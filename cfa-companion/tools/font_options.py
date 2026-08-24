"""Render the question screen in several type pairings and shoot a contact sheet.

    python tools/font_options.py

Writes tools/shots/font-options.png. Each panel shows the roles that actually
matter: the section heading, the stem, the three choices, and the small caps
label above a worked solution.
"""

import pathlib

from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).resolve().parent / "shots" / "font-options.png"

SYSTEM_SERIF = ('"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, '
                '"Times New Roman", serif')
SYSTEM_SANS = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
               '"Helvetica Neue", Arial, sans-serif')

# (label, heading face, body face)
OPTIONS = [
    ("1  Now: system serif and system sans", SYSTEM_SERIF, SYSTEM_SANS),
    ("2  Spectral and Hanken Grotesk, both already on the site",
     "'Spectral', serif", "'Hanken Grotesk', sans-serif"),
    ("3  Spectral throughout", "'Spectral', serif", "'Spectral', serif"),
    ("4  Source Serif 4 and IBM Plex Sans",
     "'Source Serif 4', serif", "'IBM Plex Sans', sans-serif"),
    ("5  Newsreader and Inter", "'Newsreader', serif", "'Inter', sans-serif"),
    ("6  Literata and Public Sans", "'Literata', serif", "'Public Sans', sans-serif"),
    ("7  IBM Plex Serif throughout", "'IBM Plex Serif', serif", "'IBM Plex Serif', serif"),
    ("8  EB Garamond and Hanken Grotesk",
     "'EB Garamond', serif", "'Hanken Grotesk', sans-serif"),
    ("9  System serif and Hanken Grotesk", SYSTEM_SERIF, "'Hanken Grotesk', sans-serif"),
    ("10  Fraunces and Inter", "'Fraunces', serif", "'Inter', sans-serif"),
]

FONTS = ("family=Spectral:wght@400;600&family=Hanken+Grotesk:wght@400;600"
         "&family=Source+Serif+4:wght@400;600&family=IBM+Plex+Sans:wght@400;600"
         "&family=Newsreader:wght@400;600&family=Inter:wght@400;600"
         "&family=Literata:wght@400;600&family=Public+Sans:wght@400;600"
         "&family=IBM+Plex+Serif:wght@400;600&family=EB+Garamond:wght@400;600"
         "&family=Fraunces:wght@400;600")

STEM = ("A company incurs an expenditure that it may either capitalise or expense as "
        "incurred. Compared with expensing it, capitalising the expenditure will most "
        "likely result in:")
CHOICES = [
    "lower cash flow from operations in the year of the expenditure.",
    "higher cash flow from operations in the year of the expenditure.",
    "higher total cash flow in the year of the expenditure.",
]


def panel(i, label, heading, body):
    letters = "ABC"
    choices = "".join(
        f'<div class="choice{" picked" if n == 1 else ""}">'
        f'<span class="letter">{letters[n]}</span><span>{c}</span></div>'
        for n, c in enumerate(CHOICES)
    )
    return f"""
    <section class="panel" style="--fh:{heading}; --fb:{body}">
      <p class="label">{label}</p>
      <h2>Practice</h2>
      <p class="stem">{STEM}</p>
      {choices}
      <p class="ref">CAPITALISING AGAINST EXPENSING</p>
      <p class="sol">The cash paid is the same either way, but classification differs.
      Capitalising records the payment as an investing outflow, so operating cash flow
      is higher.</p>
    </section>"""


HTML = f"""<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{FONTS}&display=swap">
<style>
  body {{ margin: 0; background: #efece5; padding: 26px;
          display: grid; grid-template-columns: repeat(2, 700px); gap: 26px; }}
  .panel {{ background: #fbfaf7; border: 1px solid #e2ded4; border-radius: 10px;
            padding: 22px 26px 24px; color: #1b1a17; }}
  .label {{ margin: 0 0 14px; font: 600 12px/1.3 {SYSTEM_SANS}; letter-spacing: .09em;
            text-transform: uppercase; color: #a09a8c; }}
  h2 {{ margin: 0 0 12px; font: 600 17.6px/1.3 var(--fh); letter-spacing: .01em; }}
  .stem {{ margin: 0 0 18px; font: 400 17px/1.62 var(--fb); }}
  .choice {{ display: flex; gap: 11px; align-items: baseline; padding: 11px 14px;
             margin-bottom: 7px; background: #fff; border: 1px solid #e2ded4;
             border-radius: 8px; font: 400 16px/1.5 var(--fb); }}
  .choice.picked {{ border-color: #1f5f74; box-shadow: inset 0 0 0 1px #1f5f74; }}
  .letter {{ width: 1.1em; font-weight: 600; color: #8a8579; }}
  .choice.picked .letter {{ color: #1f5f74; }}
  .ref {{ margin: 18px 0 8px; font: 400 12px/1.3 var(--fb); letter-spacing: .07em;
          text-transform: uppercase; color: #8a8579; }}
  .sol {{ margin: 0; font: 400 15.7px/1.55 var(--fb); }}
</style>
{"".join(panel(i, *o) for i, o in enumerate(OPTIONS))}
"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1478, "height": 1000},
                        device_scale_factor=2)
        pg.set_content(HTML)
        pg.wait_for_timeout(2500)          # let the webfonts arrive
        pg.screenshot(path=str(OUT), full_page=True)
        b.close()
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
