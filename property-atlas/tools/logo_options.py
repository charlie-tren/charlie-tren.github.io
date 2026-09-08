"""Render mark options for the Property Atlas masthead, at the sizes they are used.

    python tools/logo_options.py     # writes tools/logo_options.png

Every option is drawn on the same 64x74 viewBox as the shipped `.mark`, so the one
Charlie picks drops into index.html with no refitting. Each row shows it at 40px
beside the wordmark (the masthead), then at 20px and 16px (a favicon, a tab), on
the paper and on the dark ground - a mark chosen at 96px on white turns to mush in
a tab, which is already on file for this estate.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "logo_options.png"

# (name, one-line intent, svg body on a 0 0 64 74 viewBox)
#   .i fills ink   .a fills accent   .s strokes ink   .as strokes accent
#   .h fills the paper, i.e. a hole
MARKS: list[tuple[str, str, str]] = [
    ("Pin, as shipped", "the current mark, for comparison",
     '<path class="i" d="M32 6C42 6 50 14 50 24c0 13-18 34-18 34S14 37 14 24C14 14 22 6 32 6Z"/>'
     '<circle class="h" cx="32" cy="23" r="7"/>'),

    ("Parallels", "a pin whose hole is a globe",
     '<path class="i" d="M32 6C42 6 50 14 50 24c0 13-18 34-18 34S14 37 14 24C14 14 22 6 32 6Z"/>'
     '<circle class="h" cx="32" cy="23" r="9.5"/>'
     '<path class="as" fill="none" stroke-width="1.7" d="M22.5 23h19M25 18h14M25 28h14M32 13.5v19"/>'),

    ("Two pins", "one filled, one outline: the market and the outsider",
     '<path class="i" d="M24 8C33 8 40 15 40 24c0 12-16 30-16 30S8 36 8 24C8 15 15 8 24 8Z"/>'
     '<circle class="h" cx="24" cy="23" r="6"/>'
     '<path class="as" fill="none" stroke-width="3.4" d="M46 24c6 0 10 4.5 10 10.5 0 8-10 19-10 19S36 42.5 36 34.5C36 28.5 40 24 46 24Z"/>'),

    ("Keyhole", "what a foreigner may unlock",
     '<path class="i" d="M32 6C42 6 50 14 50 24c0 13-18 34-18 34S14 37 14 24C14 14 22 6 32 6Z"/>'
     '<path class="h" d="M32 13a7.5 7.5 0 0 1 3.2 14.3l2.3 8.7H26.5l2.3-8.7A7.5 7.5 0 0 1 32 13Z"/>'),

    ("Roof and needle", "a house under a compass point",
     '<path class="a" d="M32 3l10 15H22Z"/>'
     '<path class="i" d="M32 24 55 43v25H9V43Z"/>'
     '<rect class="h" x="26" y="49" width="12" height="19"/>'),

    ("Crosshair", "a coordinate, which is all a market is here",
     '<circle class="s" fill="none" stroke-width="4.5" cx="32" cy="34" r="19"/>'
     '<path class="i" d="M29.7 4h4.6v17h-4.6zM29.7 47h4.6v17h-4.6zM2 31.7h17v4.6H2zM45 31.7h17v4.6H45z"/>'
     '<circle class="a" cx="32" cy="34" r="6.5"/>'),

    ("Window, one lit", "thirty-four markets, one you are looking at",
     '<rect class="i" x="7" y="9" width="50" height="50" rx="3"/>'
     '<path class="h" d="M12 14h17v17H12zM35 36h17v17H35zM12 36h17v17H12z"/>'
     '<rect class="a" x="35" y="14" width="17" height="17"/>'),

    ("Floor plates", "a stack of slabs in perspective",
     '<path class="i" d="M32 6 58 18 32 30 6 18Z"/>'
     '<path class="a" d="M32 25 58 37 32 49 6 37Z"/>'
     '<path class="i" d="M32 44 58 56 32 68 6 56Z" opacity=".42"/>'),

    ("Globe, one dot", "the whole world, one holding",
     '<circle class="s" fill="none" stroke-width="4" cx="32" cy="34" r="26"/>'
     '<path class="s" fill="none" stroke-width="2.4" d="M6 34h52M32 8c9.5 10 9.5 42 0 52M32 8c-9.5 10-9.5 42 0 52"/>'
     '<circle class="a" cx="45" cy="21" r="7.5"/>'),

    ("Deed corner", "a title document with the corner turned",
     '<path class="i" d="M11 5h29l13 13v51H11Z"/>'
     '<path class="a" d="M40 5l13 13H40Z"/>'
     '<path class="h" d="M18 30h28v3.5H18zM18 41h28v3.5H18zM18 52h17v3.5H18z"/>'),

    ("Key and parallel", "a key whose head is a latitude line",
     '<circle class="s" fill="none" stroke-width="5.5" cx="22" cy="22" r="14"/>'
     '<path class="as" fill="none" stroke-width="2.6" d="M9 22h26"/>'
     '<path class="i" d="M30 32 57 59v9h-9L21 41Z"/>'),

    ("Stamp", "a passport stamp with a roof in it",
     '<circle class="s" fill="none" stroke-width="3.6" cx="32" cy="34" r="26" stroke-dasharray="5.5 4"/>'
     '<path class="i" d="M32 17 51 33v17H13V33Z"/>'
     '<rect class="a" x="27" y="38" width="10" height="12"/>'),

    ("Gate ajar", "open to foreigners, with conditions",
     '<path class="i" d="M7 15h6v48H7zM51 15h6v48h-6z"/>'
     '<path class="i" d="M13 20h15v4.5H13zM13 33h15v4.5H13zM13 46h15v4.5H13z"/>'
     '<path class="a" d="M36 21l15-5v46l-15-5Z"/>'),

    ("Yield steps", "what it pays, market by market",
     '<path class="i" d="M7 52h13v16H7zM26 38h13v30H26z"/>'
     '<path class="a" d="M45 18h13v50H45z"/>'
     '<path class="as" fill="none" stroke-width="3.2" d="M9 40 32 24 55 6"/>'),

    ("Sign post", "for sale, seen from the road",
     '<path class="i" d="M27.5 20h4.5v48h-4.5z"/>'
     '<path class="a" d="M32 6h26v22H32z"/>'
     '<path class="h" d="M37 13h16v3.5H37zM37 20h10v3.5H37z"/>'
     '<path class="i" d="M5 6h24v6.5H5z"/>'),

    ("Pin as A", "the A of Atlas, standing as a pin",
     '<path class="i" d="M32 5 55 63h-9.5L32 26 18.5 63H9Z"/>'
     '<path class="a" d="M21 43h22v6.5H21z"/>'),

    ("Contour", "a market as a height on a map",
     '<path class="as" fill="none" stroke-width="2.8" d="M5 59c9-15 19-15 27 0s18 15 27 0"/>'
     '<path class="s" fill="none" stroke-width="2.8" d="M10 44c7.5-13.5 14.5-13.5 22 0s14.5 13.5 22 0"/>'
     '<path class="s" fill="none" stroke-width="2.8" d="M15.5 29c6-11.5 10.5-11.5 16.5 0s10.5 11.5 16.5 0"/>'
     '<circle class="a" cx="32" cy="15" r="6.5"/>'),

    ("Ledger rule", "a market is a row in a table",
     '<path class="i" d="M6 13h52v5.5H6zM6 28h30v5.5H6zM6 43h41v5.5H6zM6 58h22v5.5H6z"/>'
     '<circle class="a" cx="49" cy="30.5" r="7.5"/>'),
]

PAGE = """<!doctype html><meta charset="utf-8"><style>
:root { --ink:#0d2b45; --acc:#0d7680; --bg:#fff1e5; --rule:#f0dcc9;
        --font-title: Gloock, "Iowan Old Style", Palatino, Georgia, serif; }
body { margin:0; background:var(--bg); color:var(--ink);
       font:13px/1.4 -apple-system, "Segoe UI", Roboto, sans-serif; }
table { border-collapse:collapse; width:100%%; }
td, th { padding:9px 12px; border-bottom:1px solid var(--rule); vertical-align:middle; }
th { font-size:10px; letter-spacing:.12em; text-transform:uppercase; color:#5c7186; text-align:left; }
.n { font-weight:650; width:118px; }
.why { color:#3d5b73; width:215px; font-size:12px; }
.dark { background:#000; }
.dark svg .i { fill:#e8e8e8; } .dark svg .s { stroke:#e8e8e8; }
.dark svg .a { fill:#ffa028; } .dark svg .as { stroke:#ffa028; }
.dark svg .h { fill:#000; }
svg .i { fill:var(--ink); } svg .s { stroke:var(--ink); }
svg .a { fill:var(--acc); } svg .as { stroke:var(--acc); }
svg .h { fill:var(--bg); }
.word { display:flex; align-items:center; gap:12px; font:400 40px/1 var(--font-title); white-space:nowrap; }
.m40 { width:35px; height:40px; } .m20 { width:17px; height:20px; } .m16 { width:14px; height:16px; }
h1 { font:400 26px var(--font-title); margin:18px 12px 6px; }
p.lede { margin:0 12px 14px; color:#3d5b73; }
</style>
<h1>Property Atlas: mark options</h1>
<p class="lede">Each at masthead size beside the wordmark, then at 20px and 16px, on the paper and on the dark ground.</p>
<table><tr><th>Option</th><th>Intent</th><th>Masthead, 40px</th><th>20</th><th>16</th><th class="dark">Dark: 40 / 20 / 16</th></tr>
%s</table>"""

ROW = """<tr>
<td class="n">%(i)d. %(name)s</td><td class="why">%(why)s</td>
<td><span class="word"><svg class="m40" viewBox="0 0 64 74">%(svg)s</svg>Property Atlas</span></td>
<td><svg class="m20" viewBox="0 0 64 74">%(svg)s</svg></td>
<td><svg class="m16" viewBox="0 0 64 74">%(svg)s</svg></td>
<td class="dark"><svg class="m40" viewBox="0 0 64 74">%(svg)s</svg>
  <svg class="m20" viewBox="0 0 64 74">%(svg)s</svg>
  <svg class="m16" viewBox="0 0 64 74">%(svg)s</svg></td></tr>"""


def main() -> int:
    # SELFTEST FIRST. A contact sheet whose options all render alike is the
    # failure mode on this estate: a quoting bug once printed fifteen font
    # options in one face, and only looking at the PNG caught it.
    assert len({s for _, _, s in MARKS}) == len(MARKS), "two options share their SVG"

    rows = "".join(ROW % {"i": i, "name": n, "why": w, "svg": s}
                   for i, (n, w, s) in enumerate(MARKS, 1))
    tmp = HERE / "_logo_options.html"
    tmp.write_text(PAGE % rows, encoding="utf-8")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1150, "height": 900}, device_scale_factor=2)
        pg.goto(tmp.resolve().as_uri())
        pg.wait_for_timeout(500)
        drawn = pg.evaluate("() => document.querySelectorAll('svg.m40').length")
        pg.screenshot(path=str(OUT), full_page=True)
        b.close()
    tmp.unlink()
    assert drawn == len(MARKS) * 2, f"{drawn} marks rendered, expected {len(MARKS) * 2}"
    print(f"{len(MARKS)} options -> {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
