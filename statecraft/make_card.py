"""Renders statecraft/og-card.png, the 1200x630 share card.

WHY THIS EXISTS AT ALL. index.html declares twitter:card as
summary_large_image and points og:image at og-card.png. That pair is worse
than no card tags: the tag tells X and Slack to reserve a large image slot,
and with nothing to put in it they render the slot empty, so every share of
the site looks like a broken page.

TWO RULES SHAPE WHAT IS DRAWN, and both are the kind of thing that is easy to
get wrong in a way nobody notices until the link is already out.

1. DARK, FROM THE PAGE'S OWN TOKENS. Every image asset on this estate is dark.
   A light rectangle dropped into a dark chat thread reads as a page from
   somewhere else, which is the opposite of what a share card is for. The
   palette below is lifted from the dark block of style.css rather than picked
   to look nice here, so restyling the page and not restyling the card shows up
   as a diff instead of as drift.

2. IT SHOWS THE DEFAULT VIEW. The page opens on a country guessed from the
   visitor's timezone with that country's own settings and nothing changed
   yet, so political capital and public patience are both at zero of 250 and
   only the money meter has anything in it. The card shows exactly that. A card
   showing three full meters would be advertising a state of the page that
   nobody arrives at, and the reader who clicks would go looking for it.

The meter figures are COMPUTED FROM data.json rather than typed in, using the
same arithmetic as budget.js, so they cannot quietly go stale when a cost
changes. The country is data.json's own fallback, which is what a visitor
outside the twenty mapped timezones actually lands on.
"""

import json
import re
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
DATA = HERE / "data.json"
OUT = HERE / "og-card.png"
SCRATCH = HERE / "_card_scratch.html"

WIDTH, HEIGHT = 1200, 630

# READ OUT OF style.css, NOT COPIED FROM IT.
#
# These were a hand-copied block with the comment "update both or neither"
# above them, and of course they drifted: the card kept the old blue accent and
# the old serif stack through a palette change and a font change, so every share
# of the page advertised a design the site no longer had. That is invisible from
# the site itself, exactly like a broken share card, and it is the same fault as
# the stale thumbnail on the same day.
#
# The file already parses the tax constants out of budget.js rather than keeping
# a second copy. This is the same move for colour and type. If a token is ever
# renamed the assertion below fails loudly rather than the card quietly reverting
# to whatever the fallback was.

STYLE = HERE / "style.css"

# Compiled once, and as a RAW string: written inline through a shell heredoc a
# backslash-s arrives as a literal escape.
PROP = re.compile(r"--([a-z0-9-]+):\s*([^;]+);")


def dark_tokens():
    """Every custom property from the :root[data-theme="dark"] block."""
    css = STYLE.read_text(encoding="utf-8")
    start = css.index(':root[data-theme="dark"] {')
    block = css[start:css.index("}", start)]
    found = dict(PROP.findall(block))
    missing = [k for k in ("bg", "panel", "ink", "soft", "faint", "rule",
                           "track", "accent", "font-title", "font-body")
               if k not in found]
    if missing:
        raise SystemExit(f"style.css dark block has no {', '.join(missing)}; "
                         f"the share card cannot be built from it")
    return {k: v.strip() for k, v in found.items()}


_T = dark_tokens()
BG, PANEL, INK = _T["bg"], _T["panel"], _T["ink"]
SOFT, FAINT, RULE, TRACK = _T["soft"], _T["faint"], _T["rule"], _T["track"]
ACCENT = _T["accent"]

# The page uses one family for both now, but the card keeps two names so its
# layout code does not have to change if that ever splits again.
SERIF = _T["font-title"]
SANS = _T["font-body"]

# Kept identical to og:description in index.html.
DESCRIPTION = ("Design a country one policy at a time, "
               "and find out which real one you built.")

REFORM_POOL = 250


def tax_curve():
    """The tax curve constants, READ OUT OF budget.js rather than copied here.

    budget.js is the one named place they live. A second copy in this file could
    be retuned in one place and left stale in the other, and the only symptom
    would be a share card quoting a capacity the page does not agree with. The
    regex is asserted, so a rename fails loudly here instead of silently
    reverting the card to whatever was hard-coded.
    """
    src = (HERE / "budget.js").read_text(encoding="utf-8")
    m = re.search(r"export const TAX = Object\.freeze\(\{\s*MIN:\s*([\d.]+),\s*"
                  r"MAX:\s*([\d.]+),\s*KINK:\s*([\d.]+),\s*LEAK:\s*([\d.]+)\s*\}\);", src)
    assert m, "could not read the TAX constants out of budget.js"
    lo, hi, kink, leak = (float(g) for g in m.groups())
    return lo, hi, kink, leak


def realised_revenue(rate):
    """What a headline take of `rate` actually collects. Mirrors budget.js."""
    lo, hi, kink, leak = tax_curve()
    r = min(hi, max(lo, rate))
    return r - leak * max(0.0, r - kink) ** 2


def default_budgets(data):
    """The three budgets for the opening view: the fallback country, unchanged.

    Mirrors budgets() in budget.js. Political and social are charged only on
    domains changed away from the starting country, and on load nothing has
    been changed, so both are zero by construction rather than by assumption.

    Capacity is what the country's own tax rate realises, plus its non-tax
    revenue, floored at what it already spends.
    """
    code = data["fallback"]
    country = next(c for c in data["countries"] if c["code"] == code)
    choices = country["choices"]

    rate = 0.0
    spend = 0.0
    for domain in data["domains"]:
        chosen = next(o for o in domain["options"] if o["id"] == choices[domain["id"]])
        if isinstance(chosen.get("rate"), (int, float)):
            rate = chosen["rate"]
        if isinstance(chosen.get("financial"), (int, float)):
            spend += chosen["financial"]

    # ITS OWN MEASURED TAX TAKE, matching startingRate() in budget.js. The option
    # rate is one hand-set number standing for every country that runs it, and
    # this was a third copy of that rule which had drifted back to it: the card
    # showed Australia raising 33.8% of GDP when the page shows 29.5.
    measured = (country.get("indicators") or {}).get("tax_take")
    if measured and isinstance(measured.get("value"), (int, float)):
        rate = measured["value"]

    capacity = max(realised_revenue(rate) + country.get("nonTaxRevenue", 0.0), spend)
    capacity, spend = round(capacity, 1), round(spend, 1)
    return code, [
        ("Budget", f"{spend:.1f} of {capacity:.1f}% of GDP",
         spend / capacity if capacity else 0),
        ("Political capital", f"0 of {REFORM_POOL}", 0.0),
        ("Public patience", f"0 of {REFORM_POOL}", 0.0),
    ]


def meter_html(name, figure, fraction):
    pct = max(0.0, min(1.0, fraction)) * 100
    return f"""
      <div class="meter">
        <span class="m-name">{name}</span>
        <span class="m-fig">{figure}</span>
        <span class="m-track"><span class="m-fill" style="width:{pct:.4f}%"></span></span>
      </div>"""


def page_html(meters):
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<!-- The font the page actually uses. Without this the card inherits the token's
     fallback stack and renders in whatever the shooting machine has, which is
     how it came out in a generic sans while the site was in Archivo. The
     renderer waits on document.fonts before shooting. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&display=swap">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {WIDTH}px; height: {HEIGHT}px; }}
  body {{
    background: {BG};
    color: {INK};
    font-family: {SANS};
    padding: 76px 84px 72px;
    display: flex;
    flex-direction: column;
  }}
  h1 {{
    font-family: {SERIF};
    font-weight: 400;
    font-size: 92px;
    letter-spacing: -0.015em;
    line-height: 1;
    color: {INK};
  }}
  .lede {{
    margin-top: 26px;
    max-width: 830px;
    color: {SOFT};
    font-size: 32px;
    line-height: 1.4;
  }}
  .meters {{
    margin-top: auto;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0 44px;
    padding: 30px 38px 34px;
    border: 1px solid {RULE};
    border-radius: 18px;
    background: {PANEL};
  }}
  .meter {{ display: flex; flex-direction: column; min-width: 0; }}
  .m-name {{ color: {SOFT}; font-size: 21px; }}
  .m-fig {{
    margin: 6px 0 16px;
    color: {INK};
    font-size: 27px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}
  .m-track {{
    margin-top: auto;
    height: 10px;
    border-radius: 999px;
    background: {TRACK};
    overflow: hidden;
  }}
  .m-fill {{ display: block; height: 100%; border-radius: 999px; background: {ACCENT}; }}
  .foot {{ margin-top: 26px; color: {FAINT}; font-size: 20px; letter-spacing: 0.01em; }}
</style></head>
<body>
  <h1>Statecraft</h1>
  <p class="lede">{DESCRIPTION}</p>
  <div class="meters">{''.join(meter_html(*m) for m in meters)}
  </div>
  <p class="foot">charlietrenorden.com/statecraft</p>
</body></html>"""


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed: pip install playwright && "
              "playwright install chromium", file=sys.stderr)
        return 1

    data = json.loads(DATA.read_text(encoding="utf-8"))
    code, meters = default_budgets(data)
    SCRATCH.write_text(page_html(meters), encoding="utf-8")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=1,
            )
            page.goto(SCRATCH.as_uri())
            # WAIT FOR THE WEBFONT, and fail rather than ship a card in the
            # fallback stack: unlike the thumbnail job, this runs by hand and a
            # wrong card would be committed without anyone seeing it render.
            #
            # ASK FOR THE FACES, do not just wait on the status. document.fonts
            # .status reads "loaded" while a face nothing has demanded yet has
            # not been fetched, so waiting on it alone passed instantly and then
            # the check below failed. load() requests them and resolves when they
            # are there.
            page.evaluate("""() => Promise.all([
                document.fonts.load('700 16px Archivo'),
                document.fonts.load('600 16px Archivo'),
                document.fonts.load('400 16px Archivo'),
            ])""")
            page.wait_for_function("() => document.fonts.status === 'loaded'",
                                   timeout=15000)
            if not page.evaluate("() => document.fonts.check('700 16px Archivo')"):
                raise SystemExit("Archivo did not load; refusing to write a card "
                                 "in the fallback face")
            page.screenshot(path=str(OUT))
            browser.close()
    finally:
        SCRATCH.unlink(missing_ok=True)

    size = OUT.stat().st_size
    print(f"wrote {OUT}")
    print(f"  {WIDTH}x{HEIGHT}, {size:,} bytes ({size / 1024:.1f} KiB)")
    print(f"  opening view: {code}, nothing changed")
    for name, figure, _ in meters:
        print(f"    {name:<18} {figure}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
