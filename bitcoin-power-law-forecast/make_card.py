"""Share card for Bitcoin Power Law Forecast: name over the page's own chart, faded (picked 21/11/2026, round 1 option 7).
Not built by tools/make_cards.py. Lifts the live chart SVG from the page served locally, draws 1200x630 at 2x natively,
and writes og-card.png plus og-card-source.html (noindex). Name sits inside the 160px safe column.

    python bitcoin-power-law-forecast/make_card.py [base_url]   # default http://localhost:8781
"""
import os, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8781'
BG, INK, SOFT = '#0f1319', '#e6e9ee', '#8a94a3'
COIN = open(os.path.join(HERE, 'favicon.svg')).read().replace('<svg ', '<svg class="coin" ')

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1100, 'height': 900})
    pg.add_init_script("localStorage.setItem('theme','dark')")
    pg.goto(BASE + '/bitcoin-power-law-forecast/?nostats=1'); pg.wait_for_selector('#chart path')
    pg.add_style_tag(content='#chart{height:400px!important}')
    pg.evaluate("dispatchEvent(new Event('resize'))"); pg.wait_for_timeout(400)
    chart = pg.evaluate("(() => { const e = document.getElementById('chart'); e.setAttribute('viewBox', '0 0 ' + e.clientWidth + ' ' + e.clientHeight); return e.outerHTML; })()")
    html = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"><style>
    *{{box-sizing:border-box}} html,body{{margin:0}} body{{width:1200px;height:630px;overflow:hidden;background:{BG};color:{INK};
    font-family:ui-sans-serif,system-ui,"Segoe UI",sans-serif;position:relative}}
    .chart{{width:100%;height:auto;display:block}} .chart text{{font:400 12px ui-sans-serif,system-ui,sans-serif;fill:{SOFT}}}
    .coin{{width:76px;height:76px}} h1{{margin:0;font-weight:600;letter-spacing:-.025em;font-size:72px;line-height:1.02}}</style></head><body>
    <div style="position:absolute;left:20px;right:30px;bottom:20px;opacity:.55">{chart}</div>
    <div style="position:absolute;inset:0;background:linear-gradient(90deg,{BG} 38%,transparent 80%)"></div>
    <div style="position:absolute;left:170px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:24px">{COIN}
    <h1>Bitcoin<br>Power Law<br>Forecast</h1></div></body></html>'''
    src = os.path.join(HERE, 'og-card-source.html'); open(src, 'w', encoding='utf-8').write(html)
    card = b.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=2)
    card.goto('file:///' + src.replace('\\', '/')); card.wait_for_timeout(200)
    card.screenshot(path=os.path.join(HERE, 'og-card.png'))
    b.close()
print('og-card.png written')
