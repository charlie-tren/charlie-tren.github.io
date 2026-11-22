"""Share card for Portfolio Outlook: the mark and name over the page's own Range of Outcomes chart, faded (the Bitcoin
Power Law Forecast card's pattern). Draws 1200x630 at 2x natively; writes og-card.png and og-card-source.html (noindex).

    python portfolio-outlook/make_card.py [base_url]   # default http://localhost:8782
"""
import os
import sys

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8782"
BG, INK, SOFT = "#0f1319", "#e6e9ee", "#8a94a3"
MARK = open(os.path.join(HERE, "favicon.svg"), encoding="utf-8").read().replace("<svg ", '<svg class="mark" ')

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1100, "height": 900})
    pg.add_init_script("localStorage.setItem('theme','dark'); localStorage.setItem('er.pf','Index Mix')")
    pg.goto(BASE + "/portfolio-outlook/?nostats=1")
    pg.wait_for_selector("#c1 svg g.r")
    chart = pg.evaluate("document.querySelector('#c1 svg').outerHTML")
    css = pg.evaluate("getComputedStyle(document.documentElement).cssText")
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"><style>
    *{{box-sizing:border-box}} html,body{{margin:0}} body{{width:1200px;height:630px;overflow:hidden;background:{BG};color:{INK};
    font-family:ui-sans-serif,system-ui,"Segoe UI",sans-serif;position:relative;
    --accent:#82a8ca;--band:#5a82a8;--ink:{INK};--soft:{SOFT};--rule:#262d38;--axis:#3a4352;--own:#f0a24e;--bg:{BG};--fill:transparent}}
    .chart{{width:100%;height:auto;display:block}} .chart text{{font:400 12px ui-sans-serif,system-ui,sans-serif;fill:{SOFT}}}
    .chart text.lab{{fill:{INK};font-size:14px}}
    .mark{{width:80px;height:80px}} h1{{margin:0;font-weight:600;letter-spacing:-.025em;font-size:76px;line-height:1.02}}</style></head><body>
    <div style="position:absolute;left:340px;right:30px;top:50%;transform:translateY(-50%) scale(1.15);transform-origin:right center;opacity:.6">{chart}</div>
    <div style="position:absolute;inset:0;background:linear-gradient(90deg,{BG} 36%,transparent 78%)"></div>
    <div style="position:absolute;left:170px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:24px">{MARK}
    <h1>Portfolio<br>Outlook</h1></div></body></html>"""
    src = os.path.join(HERE, "og-card-source.html")
    open(src, "w", encoding="utf-8").write(html)
    card = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=2)
    card.goto("file:///" + src.replace("\\", "/"))
    card.wait_for_timeout(200)
    card.screenshot(path=os.path.join(HERE, "og-card.png"))
    b.close()
print("og-card.png written")
