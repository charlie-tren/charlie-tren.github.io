"""Render mobile-layout options for the Position Record, at phone width.

    python position-record/tools/mobile_options.py     # writes tools/mobile_options.png

Drawn from the real positions.json and the last cached prices, so the widths and
the rounding are the ones that will actually ship - a mock with round numbers
hides the overflow and the precision faults this is meant to expose.

ROUND 2, 11/09/2026. Round 1 offered card / pinned-table / scroll-hint and Charlie
took the card: "A is my favourite but it still looks shit". It was a seven-row
label-value form, 340px per position, every field the same weight, so nothing read
first and three positions ran to a metre of scrolling. These four keep one card per
position and vary the INFORMATION DESIGN instead:

The move they share is to stop printing Entry, Stop, Target and To-target as four
separate numbers. A position is a point between its stop and its target, and R is
already the unit of this page - stop is -1R by construction and the target is a
fixed R - so one track in R-space carries all four, works the same for a long and a
short with no inversion, and leaves only the genuine metadata as text.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "mobile_options.png"


def rows() -> list[dict]:
    data = json.loads((ROOT / "positions.json").read_text(encoding="utf-8"))
    px = json.loads((ROOT / "prices.json").read_text(encoding="utf-8"))
    out = []
    for p in data["open"]:
        price = px[p["symbol"]]["price"]
        sign = 1 if p["direction"] == "Long" else -1
        risk = abs(p["entry"] - p["stop"])
        r = (price - p["entry"]) * sign / risk
        reward = (p["target"] - p["entry"]) * sign / risk
        dp = int(p["dp"])
        ccy = p["ccy"]
        gap = " " if ccy[-1:].isalpha() else ""
        d, m, y = p["entry_date"].split("-")[::-1]

        def money(v, dp=dp):
            return f"{ccy}{gap}{v:,.{dp}f}"

        out.append({
            "name": p["name"], "kind": p["kind"], "dir": p["direction"],
            "opened": f"{d}/{m}/{y[2:]}",
            "entry": money(p["entry"]), "stop": money(p["stop"]),
            "target": money(p["target"]), "now": money(price),
            "carry": f"{p['carry_pct']:+.2f}%",
            "r": r, "r_s": f"{r:+.2f}", "reward": reward,
            "totarget": f"{reward - r:.2f}R",
            # Where the current price sits on a track running stop (-1R) to target.
            "pct_now": (r + 1) / (reward + 1) * 100,
            "pct_entry": 1 / (reward + 1) * 100,
        })
    return sorted(out, key=lambda x: x["name"])


def rail(p, *, ticks=True):
    cls = "up" if p["r"] >= 0 else "dn"
    lo, hi = sorted((p["pct_entry"], p["pct_now"]))
    marks = ""
    if ticks:
        marks = (f'<span class="tk" style="left:{p["pct_entry"]:.2f}%"></span>')
    return (
        f'<div class="rail">'
        f'  <div class="track"></div>'
        f'  <div class="fill {cls}" style="left:{lo:.2f}%;width:{hi - lo:.2f}%"></div>'
        f'  {marks}'
        f'  <span class="dot {cls}" style="left:{p["pct_now"]:.2f}%"></span>'
        f'</div>'
        f'<div class="ends"><span>{p["stop"]}<i>stop</i></span>'
        f'<span class="ra">{p["target"]}<i>target</i></span></div>')


# --- A1 -----------------------------------------------------------------------
def a1(rs):
    out = []
    for p in rs:
        out.append(
            f'<div class="c1">'
            f'<div class="hd"><span class="nm">{p["name"]}</span>'
            f'<span class="big {"up" if p["r"] >= 0 else "dn"}">{p["r_s"]}<i>R</i></span></div>'
            f'{rail(p)}'
            f'<div class="meta">{p["dir"]} &middot; {p["kind"]} &middot; {p["opened"]}'
            f' &middot; carry {p["carry"]}</div>'
            f'<button class="thesis">Thesis</button>'
            f'</div>')
    return f'<div class="set">{"".join(out)}</div>'


# --- A2 -----------------------------------------------------------------------
def a2(rs):
    out = []
    for p in rs:
        stats = "".join(
            f'<div><b>{v}</b><i>{k}</i></div>'
            for k, v in (("entry", p["entry"]), ("now", p["now"]),
                         ("carry", p["carry"]), ("to target", p["totarget"])))
        out.append(
            f'<div class="c2">'
            f'<div class="hd"><span class="nm">{p["name"]}</span>'
            f'<span class="big {"up" if p["r"] >= 0 else "dn"}">{p["r_s"]}<i>R</i></span></div>'
            f'<div class="sub2">{p["dir"]} &middot; {p["kind"]} &middot; {p["opened"]}</div>'
            f'<div class="strip">{stats}</div>'
            f'<button class="thesis">Thesis</button>'
            f'</div>')
    return f'<div class="set">{"".join(out)}</div>'


# --- A3 -----------------------------------------------------------------------
def a3(rs):
    out = []
    for p in rs:
        out.append(
            f'<div class="c3">'
            f'<div class="hd"><div><span class="nm">{p["name"]}</span>'
            f'<span class="sub3">{p["dir"]} &middot; {p["kind"]} &middot; {p["opened"]}</span></div>'
            f'<span class="big {"up" if p["r"] >= 0 else "dn"}">{p["r_s"]}<i>R</i></span></div>'
            f'{rail(p, ticks=False)}'
            f'<button class="thesis">Thesis</button>'
            f'</div>')
    return f'<div class="set">{"".join(out)}</div>'


# --- A4 -----------------------------------------------------------------------
def a4(rs):
    out = []
    for p in rs:
        cls = "up" if p["r"] >= 0 else "dn"
        out.append(
            f'<div class="c4">'
            f'<div class="hd4">'
            f'  <span class="nm">{p["name"]}</span>'
            f'  <span class="chip {p["dir"].lower()}">{p["dir"]}</span>'
            f'  <span class="big {cls}">{p["r_s"]}<i>R</i></span>'
            f'</div>'
            f'{rail(p)}'
            f'<dl class="pairs">'
            f'<dt>Entry</dt><dd>{p["entry"]}</dd>'
            f'<dt>Now</dt><dd>{p["now"]}</dd>'
            f'<dt>Carry</dt><dd>{p["carry"]}</dd>'
            f'<dt>To target</dt><dd>{p["totarget"]}</dd>'
            f'</dl>'
            f'<button class="thesis">Thesis</button>'
            f'</div>')
    return f'<div class="set">{"".join(out)}</div>'


PAGE = """<!doctype html><meta charset="utf-8"><style>
:root { --bg:#0f1319; --raised:#171c24; --ink:#e6e9ee; --soft:#8a94a3;
        --faint:#5d6675; --rule:#262d38; --accent:#82a8ca; --pos:#6ea67f; --neg:#c2705c;
        --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
        --sans:ui-sans-serif,system-ui,sans-serif; }
* { box-sizing:border-box; }
body { margin:0; background:#05070a; color:var(--ink); font:13px/1.4 var(--sans); }
h1 { font:400 22px var(--serif); margin:20px 22px 4px; }
p.l { margin:0 22px 18px; color:var(--soft); }
.sheet { display:flex; gap:20px; padding:0 22px 26px; align-items:flex-start; }
.col { width:375px; flex:0 0 375px; }
.cap { font:600 11px var(--sans); letter-spacing:.1em; text-transform:uppercase;
       color:var(--accent); margin:0 0 4px; }
.sub { color:var(--faint); font-size:11.5px; margin:0 0 10px; min-height:44px; }
.phone { width:375px; background:var(--bg); border:1px solid var(--rule);
         border-radius:14px; overflow:hidden; padding:6px 0 14px; }
.set { padding:0 18px; }
.nm { font:400 1.02rem/1.2 var(--serif); }
.up { color:var(--pos); } .dn { color:var(--neg); }
.thesis { appearance:none; background:none; border:0; padding:0; cursor:pointer;
          color:var(--accent); font:600 11.5px var(--sans); letter-spacing:.05em; }
.thesis::after { content:"\\25BE"; padding-left:.35rem; }

.hd { display:flex; justify-content:space-between; align-items:baseline; gap:10px; }
.big { font:500 20px/1 var(--sans); font-variant-numeric:tabular-nums;
       letter-spacing:-.01em; white-space:nowrap; }
.big i { font:600 9.5px var(--sans); font-style:normal; letter-spacing:.12em;
         color:var(--faint); padding-left:.22rem; vertical-align:.42em; }

/* the track: stop at the left edge, target at the right, entry a tick between */
.rail { position:relative; height:3px; margin:13px 0 0; }
.track { position:absolute; inset:0; background:var(--rule); border-radius:2px; }
.fill { position:absolute; top:0; height:3px; border-radius:2px; opacity:.55; }
.fill.up { background:var(--pos); } .fill.dn { background:var(--neg); }
.tk { position:absolute; top:-3px; width:1px; height:9px; background:var(--faint); }
.dot { position:absolute; top:-3.5px; width:10px; height:10px; margin-left:-5px;
       border-radius:50%; border:2px solid var(--bg); }
.dot.up { background:var(--pos); } .dot.dn { background:var(--neg); }
.ends { display:flex; justify-content:space-between; margin-top:7px;
        font:400 11.5px var(--sans); color:var(--soft);
        font-variant-numeric:tabular-nums; }
.ends i { display:block; font:600 9px var(--sans); font-style:normal;
          letter-spacing:.12em; text-transform:uppercase; color:var(--faint);
          margin-top:2px; }
.ends .ra { text-align:right; }

.c1, .c2, .c3, .c4 { border-bottom:1px solid var(--rule); padding:14px 0 14px; }
.c1 .meta, .sub2 { font:400 11.5px var(--sans); color:var(--faint); }
.c1 .meta { margin:11px 0 11px; }
.c1 .thesis, .c3 .thesis, .c4 .thesis { display:inline-block; }

.sub2 { margin:5px 0 0; }
.strip { display:grid; grid-template-columns:repeat(4,1fr); gap:0; margin:12px 0 12px;
         border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); }
.strip div { padding:8px 6px 7px; border-left:1px solid var(--rule); }
.strip div:first-child { border-left:0; padding-left:0; }
.strip b { display:block; font:400 12.5px var(--sans); color:var(--ink);
           font-variant-numeric:tabular-nums; }
.strip i { display:block; font:600 9px var(--sans); font-style:normal;
           letter-spacing:.1em; text-transform:uppercase; color:var(--faint);
           margin-top:3px; }

.sub3 { display:block; font:400 11.5px var(--sans); color:var(--faint); margin-top:4px; }
.c3 .thesis { margin-top:13px; }

.hd4 { display:flex; align-items:baseline; gap:9px; }
.hd4 .big { margin-left:auto; }
.chip { font:500 10px/1 var(--sans); letter-spacing:.05em; color:var(--soft);
        border:1px solid var(--rule); border-radius:3px; padding:3px 5px; }
.pairs { display:grid; grid-template-columns:auto 1fr auto 1fr; gap:7px 10px;
         margin:13px 0 12px; align-items:baseline; }
.pairs dt { font:600 9px/1.6 var(--sans); letter-spacing:.1em; text-transform:uppercase;
            color:var(--faint); white-space:nowrap; }
.pairs dd { margin:0; font:400 12.5px/1.15 var(--sans); color:var(--soft);
            font-variant-numeric:tabular-nums; white-space:nowrap; }
</style>
<h1>One card per position: four ways</h1>
<p class="l">Same three positions. Entry, stop, target and to-target become one track in R-space, because stop is -1R by construction and that works for a long and a short without inverting anything.</p>
<div class="sheet">
  <div class="col"><p class="cap">A1 &middot; Rail, meta on one line</p>
    <p class="sub">R large at the right, the track underneath with its two ends labelled, then everything else as a single faint line.</p>
    <div class="phone">__A1__</div></div>
  <div class="col"><p class="cap">A2 &middot; No track, ruled number strip</p>
    <p class="sub">Keeps the figures as figures, four across between hairlines, so it stays a record rather than a chart.</p>
    <div class="phone">__A2__</div></div>
  <div class="col"><p class="cap">A3 &middot; Quietest</p>
    <p class="sub">Name and meta stacked at the left, R at the right, one track. Four items per position and nothing else.</p>
    <div class="phone">__A3__</div></div>
  <div class="col"><p class="cap">A4 &middot; Rail plus the numbers</p>
    <p class="sub">The track for shape and the four numbers underneath for the detail. The fullest, and the tallest.</p>
    <div class="phone">__A4__</div></div>
</div>"""


def main() -> int:
    rs = rows()
    assert len(rs) >= 3, f"expected the live book, got {len(rs)}"
    # The track is only honest if the current price really sits between the ends.
    for p in rs:
        assert 0 <= p["pct_now"] <= 100, f"{p['name']} plots off its own track"
        assert p["reward"] > 0, f"{p['name']} has a target behind its entry"

    html = PAGE
    for tag, block in (("__A1__", a1(rs)), ("__A2__", a2(rs)),
                       ("__A3__", a3(rs)), ("__A4__", a4(rs))):
        assert tag in html, f"{tag} placeholder missing from PAGE"
        html = html.replace(tag, block)
    tmp = HERE / "_mobile_options.html"
    tmp.write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1660, "height": 900}, device_scale_factor=2)
        pg.goto(tmp.resolve().as_uri())
        pg.wait_for_timeout(400)
        phones = pg.evaluate("() => document.querySelectorAll('.phone').length")
        # NOTHING MAY OVERFLOW. The whole point of the card is that a phone never
        # scrolls sideways, so measure it rather than trusting the eye.
        over = pg.evaluate("""() => [].map.call(document.querySelectorAll('.phone'),
            function (n) { return n.scrollWidth - n.clientWidth; })""")
        # And each treatment must be a different height, or two of them are the same
        # design wearing different labels.
        tall = pg.evaluate("""() => [].map.call(document.querySelectorAll('.set'),
            function (n) { return Math.round(n.getBoundingClientRect().height); })""")
        pg.screenshot(path=str(OUT), full_page=True)
        b.close()
    tmp.unlink()
    assert phones == 4, f"{phones} phones rendered, expected 4"
    assert all(o == 0 for o in over), f"a card layout overflowed its phone: {over}"
    assert len(set(tall)) >= 3, f"treatments are too alike in height: {tall}"
    print(f"4 options -> {OUT.name}; overflow {over}; heights {tall} px for 3 positions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
