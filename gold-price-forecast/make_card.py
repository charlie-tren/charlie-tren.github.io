"""Share card and raster icons for Gold Price Forecast, in the Bitcoin Forecast card's design (name over the page's own
chart, faded). Lifts the live chart SVG from the page served locally, draws 1200x630 at 2x natively, and writes
og-card.png, og-card-source.html (noindex), favicon-48.png, favicon-192.png and apple-touch-icon.png from favicon.svg.

    python gold-price-forecast/make_card.py [base_url]   # default http://localhost:8781
"""
import os, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8781'
BG, INK, SOFT = '#0f1319', '#e6e9ee', '#8a94a3'
SVG = open(os.path.join(HERE, 'favicon.svg')).read()
COIN = SVG.replace('<svg ', '<svg class="coin" ')

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, px in (('favicon-48.png', 48), ('favicon-192.png', 192), ('apple-touch-icon.png', 180)):
        ic = b.new_page(viewport={'width': px, 'height': px})
        ic.set_content(f'<html><body style="margin:0;background:transparent">{SVG.replace("<svg ", f"<svg width={px} height={px} ")}</body></html>')
        ic.screenshot(path=os.path.join(HERE, name), omit_background=name != 'apple-touch-icon.png')
    pg = b.new_page(viewport={'width': 1100, 'height': 900})
    pg.add_init_script("localStorage.setItem('theme','dark')")
    pg.goto(BASE + '/gold-price-forecast/?nostats=1'); pg.wait_for_selector('#chart path')
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
    <h1>Gold<br>Price<br>Forecast</h1></div></body></html>'''
    src = os.path.join(HERE, 'og-card-source.html'); open(src, 'w', encoding='utf-8').write(html)
    card = b.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=2)
    card.goto('file:///' + src.replace('\\', '/')); card.wait_for_timeout(200)
    card.screenshot(path=os.path.join(HERE, 'og-card.png'))
    b.close()
print('og-card.png and icons written')
