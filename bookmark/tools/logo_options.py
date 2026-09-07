"""Contact sheet of logo marks for Bookmark, at the sizes they get used.

    python tools/logo_options.py

Three rows per mark, and the 16px one decides it. A mark that reads at 44px and
turns to mush in a browser tab has failed, which is how the Pendulum cradle was
chosen. Every mark is a 24-unit viewBox, two colours only - currentColor for the
ink and the site accent for the one thing that should catch the eye.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "logo_options.png"
A = "#d9a441"

MARKS = [
    ("Ribbon", "the plain bookmark: a strip with a notched tail",
     f'<path d="M7 2h10v20l-5-4.6L7 22z" fill="{A}"/>'),

    ("Ribbon in a book", "a closed book with the ribbon still in it",
     f'<rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/>'
     f'<path d="M9.5 3h4v9l-2-1.9L9.5 12z" fill="{A}"/>'),

    ("Dog-ear", "the corner you turn down when there is no ribbon",
     f'<path d="M4 3h11l5 5v13H4z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
     f'<path d="M15 3l5 5h-5z" fill="{A}"/>'),

    ("Open book", "the obvious one, included so the others have a baseline",
     '<path d="M12 6.5C10 4.8 7.4 4.2 4 4.4v13.2c3.4-.2 6 .4 8 2.1 2-1.7 4.6-2.3 8-2.1V4.4c-3.4-.2-6 .4-8 2.1z"'
     ' fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
     f'<path d="M12 6.5v13.2" stroke="{A}" stroke-width="1.8"/>'),

    ("One pulled out", "a row of spines with this month's standing proud - the site's own idea",
     '<rect x="3" y="7" width="3.4" height="14" rx="1" fill="currentColor" opacity=".55"/>'
     '<rect x="7.4" y="9" width="3.4" height="12" rx="1" fill="currentColor" opacity=".55"/>'
     f'<rect x="11.8" y="3" width="3.8" height="18" rx="1" fill="{A}"/>'
     '<rect x="16.6" y="8" width="3.4" height="13" rx="1" fill="currentColor" opacity=".55"/>'),

    ("The gap", "the same idea inverted: the shelf, and the space where it went",
     '<rect x="2.5" y="6" width="3.2" height="15" rx="1" fill="currentColor" opacity=".6"/>'
     '<rect x="6.4" y="8" width="3.2" height="13" rx="1" fill="currentColor" opacity=".6"/>'
     f'<path d="M11 21V8" stroke="{A}" stroke-width="1.6" stroke-dasharray="2.2 2"/>'
     f'<path d="M15.5 21V7" stroke="{A}" stroke-width="1.6" stroke-dasharray="2.2 2"/>'
     '<rect x="17.9" y="5" width="3.2" height="16" rx="1" fill="currentColor" opacity=".6"/>'),

    ("Gilt spine", "one spine end-on, banded, matching the shelf on the page",
     '<rect x="7" y="2" width="10" height="20" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.8"/>'
     f'<path d="M8.6 6.5h6.8M8.6 8h6.8M8.6 16h6.8M8.6 17.5h6.8" stroke="{A}" stroke-width="1.3"/>'),

    ("Ribbon B", "the letter built out of the ribbon",
     '<path d="M6 3h6a4 4 0 0 1 0 8H6zM6 11h6.6a4 4 0 0 1 0 8H6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
     f'<path d="M6 3v18l-2.4-2.2L6 21z" fill="{A}"/>'),

    ("Index tab", "the tab that marks a place from the outside",
     '<rect x="3" y="3" width="14" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/>'
     f'<rect x="15" y="7" width="6" height="5" rx="1.4" fill="{A}"/>'),

    ("Stack", "books piled flat, one of them the accent",
     '<rect x="3" y="15.5" width="18" height="4" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.7"/>'
     f'<rect x="4.5" y="10" width="15" height="4" rx="1.4" fill="{A}"/>'
     '<rect x="3" y="4.5" width="18" height="4" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.7"/>'),

    ("Tilted spine", "one book leaning out of the row, mid-pull",
     '<rect x="3" y="6" width="3.4" height="15" rx="1" fill="currentColor" opacity=".55"/>'
     '<rect x="7.3" y="6" width="3.4" height="15" rx="1" fill="currentColor" opacity=".55"/>'
     f'<g transform="rotate(14 15 14)"><rect x="13.2" y="4" width="4" height="17" rx="1.2" fill="{A}"/></g>'),

    ("Page and rule", "a single page with the line you stopped on",
     '<path d="M5 2.5h14v19H5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
     '<path d="M8 7h8M8 10h8M8 16h8" stroke="currentColor" stroke-width="1.4" opacity=".5"/>'
     f'<path d="M8 13h8" stroke="{A}" stroke-width="2.2"/>'),
]

ROWS = "".join(
    f"""<div class="row">
      <div class="nm">{i+1}. {name}<span class="reg">{note}</span></div>
      <div class="specs">
        <span class="s16"><svg viewBox="0 0 24 24" width="16" height="16">{svg}</svg></span>
        <span class="s24"><svg viewBox="0 0 24 24" width="24" height="24">{svg}</svg></span>
        <span class="s44"><svg viewBox="0 0 24 24" width="44" height="44">{svg}</svg></span>
        <span class="lock"><svg viewBox="0 0 24 24" width="30" height="30">{svg}</svg><b>Bookmark<i>.</i></b></span>
      </div>
    </div>"""
    for i, (name, note, svg) in enumerate(MARKS))

HTML = f"""<!doctype html><meta charset=utf-8>
<link rel=preconnect href=https://fonts.gstatic.com crossorigin>
<link href='https://fonts.googleapis.com/css2?family=Spectral:wght@400;600&family=Hanken+Grotesk:wght@400;600&display=block' rel=stylesheet>
<style>
  body{{margin:0;background:#1a1916;color:#efe9dc;font:14px 'Hanken Grotesk',sans-serif;padding:24px 30px}}
  .row{{display:grid;grid-template-columns:230px 1fr;gap:24px;align-items:center;
        padding:16px 0;border-top:1px solid #33302a}}
  .row:first-child{{border-top:none}}
  .nm{{color:#9a9384;font-size:13px}}
  .reg{{display:block;color:#6f695d;font-size:11px;margin-top:3px;line-height:1.35}}
  .specs{{display:flex;align-items:center;gap:34px}}
  .specs span{{display:inline-flex;align-items:center;justify-content:center}}
  .s16,.s24,.s44{{color:#efe9dc}}
  .s16{{width:16px}}
  .lock{{gap:11px;padding-left:14px;border-left:1px solid #33302a}}
  .lock b{{font-family:'Spectral',serif;font-size:34px;font-weight:600;letter-spacing:-.025em}}
  .lock i{{color:#d9a441;font-style:normal}}
</style>{ROWS}"""


def main() -> None:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 800}, device_scale_factor=3)
        pg.set_content(HTML, wait_until="networkidle")
        pg.wait_for_timeout(1200)
        n = pg.eval_on_selector_all(".row svg", "e=>e.length")
        assert n == len(MARKS) * 4, f"expected {len(MARKS)*4} svgs, drew {n}"
        pg.screenshot(path=str(OUT), full_page=True)
        b.close()
    print("wrote", OUT, f"({len(MARKS)} marks)")


if __name__ == "__main__":
    main()
