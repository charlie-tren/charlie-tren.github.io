"""Contact sheet of display faces for Bookmark, rendered at the sizes actually used.

    python tools/font_options.py

Three specimens per face, because a face can pass one and fail another:
  - the wordmark at 38px, where a display serif either has character or does not;
  - a book title at 37px, the same weight the page uses;
  - a SPINE at 13px vertical, which is the hardest test on this site and the one
    that kills candidates - a face with fine hairlines turns to mush there.

Trap this file exists to avoid: the stacks contain double quotes, so the style
attribute MUST be single-quoted. A previous contact sheet on this estate rendered
one font ten times because the first inner quote closed the attribute.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "font_options_2.png"

# name, Google Fonts family (None = no request), CSS stack
FACES = [
    ("Spectral (current)", "Spectral:wght@400;500;600", "'Spectral',Georgia,serif", "where we are"),
    ("IM Fell English", "IM+Fell+English:ital@0;1", "'IM Fell English',Georgia,serif", "antiquarian"),
    ("IM Fell DW Pica", "IM+Fell+DW+Pica:ital@0;1", "'IM Fell DW Pica',Georgia,serif", "antiquarian"),
    ("Almendra", "Almendra:wght@400;700", "'Almendra',Georgia,serif", "antiquarian"),
    ("Bodoni Moda", "Bodoni+Moda:opsz,wght@6..96,400;6..96,600", "'Bodoni Moda',Georgia,serif", "didone"),
    ("Prata", "Prata", "'Prata',Georgia,serif", "didone"),
    ("Abril Fatface", "Abril+Fatface", "'Abril Fatface',Georgia,serif", "didone, heavy"),
    ("Young Serif", "Young+Serif", "'Young Serif',Georgia,serif", "wedge"),
    ("Eczar", "Eczar:wght@400;600", "'Eczar',Georgia,serif", "wedge"),
    ("Vollkorn", "Vollkorn:wght@400;600", "'Vollkorn',Georgia,serif", "old-style, chunky"),
    ("Alegreya", "Alegreya:wght@400;600", "'Alegreya',Georgia,serif", "old-style, calligraphic"),
    ("Petrona", "Petrona:wght@400;600", "'Petrona',Georgia,serif", "quirky text"),
    ("DM Serif Display", "DM+Serif+Display", "'DM Serif Display',Georgia,serif", "editorial display"),
    ("Yeseva One", "Yeseva+One", "'Yeseva One',Georgia,serif", "art nouveau"),
    ("Cinzel", "Cinzel:wght@400;600", "'Cinzel',Georgia,serif", "roman caps"),
    ("Marcellus", "Marcellus", "'Marcellus',Georgia,serif", "roman caps, softer"),
    ("Rokkitt", "Rokkitt:wght@400;600", "'Rokkitt',Georgia,serif", "slab"),
    ("Bree Serif", "Bree+Serif", "'Bree Serif',Georgia,serif", "slab, friendly"),
    ("Grenze", "Grenze:wght@400;600", "'Grenze',Georgia,serif", "condensed, gothic-ish"),
    ("Syne", "Syne:wght@400;700", "'Syne',sans-serif", "sans, odd"),
]

FAMS = "&".join("family=" + f[1] for f in FACES if f[1])

ROWS = "".join(
    # THE ATTRIBUTE QUOTE MUST NOT BE THE QUOTE THE STACK USES. These stacks
    # quote family names with ' , so the attribute is " . Getting this backwards
    # renders every row in the SAME face and looks like a font-loading problem.
    f"""<div class="row">
          <div class="nm">{i+1}. {name}<span class="reg">{FACES[i][3]}</span></div>
          <div class="spec" style="--f: {stack}">
            <div class="brand">Bookmark<span class="dot">.</span></div>
            <div class="title">Say Nothing</div>
            <div class="sp"><span class="t">The Remains of the Day</span></div>
            <div class="sp"><span class="t">Piranesi</span></div>
          </div>
        </div>"""
    for i, (name, _, stack, _reg) in enumerate(FACES))

HTML = f"""<!doctype html><meta charset=utf-8>
<link rel=preconnect href=https://fonts.googleapis.com>
<link rel=preconnect href=https://fonts.gstatic.com crossorigin>
<link href='https://fonts.googleapis.com/css2?{FAMS}&family=Hanken+Grotesk:wght@400;600&display=block' rel=stylesheet>
<style>
  body{{margin:0;background:#1a1916;color:#efe9dc;font:14px 'Hanken Grotesk',sans-serif;padding:26px 30px}}
  .row{{display:grid;grid-template-columns:200px 1fr;gap:26px;align-items:center;
        padding:18px 0;border-top:1px solid #33302a}}
  .row:first-child{{border-top:none}}
  .nm{{color:#9a9384;font-size:13px;letter-spacing:.04em}}
  .reg{{display:block;color:#6f695d;font-size:11px;margin-top:3px}}
  .spec{{display:flex;align-items:flex-end;gap:38px}}
  .brand{{display:inline-block;font-family:var(--f);font-size:38px;font-weight:600;letter-spacing:-.025em;line-height:1}}
  .dot{{color:#d9a441}}
  .title{{display:inline-block;font-family:var(--f);font-size:37px;font-weight:500;letter-spacing:-.02em;line-height:1.05}}
  .sp{{width:34px;height:150px;border-radius:3px 3px 0 0;flex:0 0 auto;position:relative;
       background:repeating-linear-gradient(90deg,rgba(255,255,255,.035) 0 1px,transparent 1px 4px),
         linear-gradient(90deg,rgba(0,0,0,.42) 0 3px,rgba(255,255,255,.10) 4px 7px,
           transparent 20%,transparent 78%,rgba(0,0,0,.34) 100%),#44405e;
       display:flex;align-items:center;justify-content:center;overflow:hidden;
       box-shadow:inset 0 2px 0 rgba(255,255,255,.13)}}
  .sp .t{{writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;color:#f6f1e4;
          font-family:var(--f);font-size:13px;letter-spacing:.02em}}
</style>{ROWS}"""


def main() -> None:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1180, "height": 800}, device_scale_factor=2)
        pg.set_content(HTML, wait_until="networkidle")
        pg.wait_for_timeout(1800)
        # PROVE the faces differ before shipping the sheet. Ten identical rows is
        # the failure mode this check exists for, and it looked fine in code.
        # Measure an INLINE element: a block div's width is the column's, not the
        # text's, and the first version of this check compared fifteen container
        # widths and "failed" on fonts that were loading perfectly well.
        widths = pg.eval_on_selector_all(
            ".brand", "e=>e.map(x=>Math.round(x.getBoundingClientRect().width))")
        print("wordmark widths:", widths)
        # Calibrated to the failure it guards, which is TOTAL collapse - every
        # row in one face. Two faces happening to set "Bookmark." to the same
        # pixel is ordinary, and a stricter bound failed a perfectly good sheet.
        if len(set(widths)) < max(3, len(widths) // 2):
            raise SystemExit(f"faces are not resolving separately: {widths}")
        pg.screenshot(path=str(OUT), full_page=True)
        b.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
