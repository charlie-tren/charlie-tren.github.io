"""Renders the share cards for the hub projects: a 1200x630 layout drawn natively
at 2x (2400x1260, never supersampled), content inside an 880px centred safe column
because every client centre-crops the card. The HTML source is kept beside the PNG.

    python tools/make_cards.py                # all of them
    python tools/make_cards.py lexicon        # one

WHY THIS EXISTS. On 10/09/2026 a sweep of all twenty-five properties found CFA
Companion declaring `twitter:card=summary_large_image` with no `og:image` - the
pairing that renders BROKEN rather than plain, because the platform reserves the
image slot and paints it empty. That is the same fault the-aftertimes/card.py and
statecraft/make_card.py were each written to fix, found a third time, which is
why this one is spec-driven instead of a third copy. Lexicon, Property Atlas and
Woop Woop had no card tags at all - honest, but a link with no preview reads as
dead next to carded ones. tools/test_estate_head.mjs now fails on the broken
pairing so a fourth instance cannot go unnoticed.

THREE RULES, two inherited and one new.

1. PALETTE AND COPY ARE PARSED FROM THE SITE, never typed here. statecraft's card
   kept an old accent and an old font stack through two redesigns because those
   were hand-copied; a rename now fails loudly in `tokens()` instead. The lede is
   read from the page's own og:description so the image and the text beside it
   cannot drift apart.

2. THE CARD MATCHES WHAT A VISITOR ACTUALLY SEES. statecraft/make_card.py states
   the estate rule as "every image asset here is dark", and reads its dark block.
   That rule was written from a set of dark sites; it does not survive contact
   with Lexicon, whose whole design is warm paper, or Property Atlas, which pins
   `color-scheme: light` and says in its own CSS that an OS setting is not a
   request for this page. A dark card for either would advertise a design the
   site does not have, which is the fault rule 1 exists to prevent. So the rule
   here is mechanical: use the block the CSS treats as its base `:root`, unless
   the document pins one on <html data-theme>, and then use that. Woop Woop pins
   dark and gets a dark card; these three are light and get light ones.

3. THE TITLE IS DRAWN, unlike the-aftertimes' card. Its docstring is right that
   painting a headline duplicates the `og:title` a platform renders beside the
   image - but that card's subject is artwork filling the frame. These three have
   no artwork, so a card with no type is an empty rectangle. Statecraft and DCF
   Studio both draw their wordmark for the same reason.
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
WIDTH, HEIGHT = 1200, 630

#: One entry per card. `tokens` maps this file's roles onto whatever the site
#: calls them - the estate has --fg, --ink and --paper all meaning the same
#: thing, and normalising here keeps the renderer free of per-site branches.
SITES = {
    "cfa-companion": {
        "name": "CFA Companion",
        "css": "cfa-companion/style.css",
        "copy": ("cfa-companion/index.html", "og:description"),
        "tokens": {"bg": "bg", "panel": "panel", "ink": "ink", "dim": "ink-2",
                   "faint": "ink-3", "rule": "rule", "accent": "accent"},
        "fonts": "Newsreader:wght@400;600&family=Inter:wght@400;500",
        "title_font": "Newsreader, Georgia, serif",
        "body_font": "Inter, system-ui, sans-serif",
        "eyebrow": "Level I practice",
        "assert_face": '600 16px Newsreader',
    },
    "lexicon": {
        "name": "Lexicon",
        "css": "lexicon/index.html",
        "copy": ("lexicon/index.html", "og:description"),
        "tokens": {"bg": "paper", "panel": "card", "ink": "ink", "dim": "ink-soft",
                   "faint": "ink-soft", "rule": "line", "accent": "oxblood"},
        "fonts": "Spectral:wght@400;500;600&family=Hanken+Grotesk:wght@400;500;600",
        "title_font": "Spectral, Georgia, serif",
        "body_font": "'Hanken Grotesk', system-ui, sans-serif",
        "eyebrow": "Spaced repetition",
        "assert_face": '600 16px Spectral',
    },
    "property-atlas": {
        "name": "Property Atlas",
        "css": "property-atlas/style.css",
        "copy": ("property-atlas/index.html", "og:description"),
        "tokens": {"bg": "bg", "panel": "panel", "ink": "ink", "dim": "ink-soft",
                   "faint": "ink-faint", "rule": "rule", "accent": "accent"},
        "fonts": "Gloock&family=Inter:wght@400;500",
        "title_font": "Gloock, Georgia, serif",
        "body_font": "Inter, system-ui, sans-serif",
        "eyebrow": "Thirty-four markets",
        "assert_face": '400 16px Gloock',
    },
    # From here down: a mark instead of an eyebrow, and no webfont where the
    # site sets itself in a system stack.
    "crosscheck": {
        "name": "Crosscheck",
        "css": "crosscheck/template.html.j2",
        "copy": ("crosscheck/template.html.j2", "og:description"),
        "tokens": {"bg": "bg", "panel": "raised", "ink": "ink", "dim": "soft",
                   "faint": "faint", "rule": "rule", "accent": "accent"},
        "title_font": '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif',
        "body_font": "ui-sans-serif, system-ui, sans-serif",
        "mark": "crosscheck/favicon.svg",
    },
    "beyond-small-talk": {
        "name": "Beyond Small Talk",
        "css": "assets/room.css",
        "copy": ("beyond-small-talk/index.html", "og:description"),
        "tokens": {"bg": "bg", "panel": "raised", "ink": "ink", "dim": "soft",
                   "faint": "faint", "rule": "rule", "accent": "accent"},
        "title_font": '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif',
        "body_font": "ui-sans-serif, system-ui, sans-serif",
        "mark": "assets/room/favicon.svg",
    },
    "split-the-room": {
        "name": "Split the Room",
        "css": "assets/room.css",
        "copy": ("split-the-room/index.html", "og:description"),
        "tokens": {"bg": "bg", "panel": "raised", "ink": "ink", "dim": "soft",
                   "faint": "faint", "rule": "rule", "accent": "accent"},
        "title_font": '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif',
        "body_font": "ui-sans-serif, system-ui, sans-serif",
        "mark": "assets/room/favicon.svg",
    },
    "spectrum": {
        "name": "Spectrum",
        "css": "assets/room.css",
        "copy": ("spectrum/index.html", "og:description"),
        "tokens": {"bg": "bg", "panel": "raised", "ink": "ink", "dim": "soft",
                   "faint": "faint", "rule": "rule", "accent": "accent"},
        "title_font": '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif',
        "body_font": "ui-sans-serif, system-ui, sans-serif",
        "mark": "assets/room/favicon.svg",
    },
    "bookmark": {
        "name": "Bookmark",
        "css": "bookmark/index.html",
        "copy": ("bookmark/index.html", "og:description"),
        "tokens": {"bg": "paper", "panel": "paper2", "ink": "ink", "dim": "ink-soft",
                   "faint": "ink-soft", "rule": "line", "accent": "accent"},
        "fonts": "Young+Serif&family=Hanken+Grotesk:wght@400;500",
        "title_font": "'Young Serif', Georgia, serif",
        "body_font": "'Hanken Grotesk', system-ui, sans-serif",
        "mark": "bookmark/favicon.svg",
        "assert_face": "400 16px 'Young Serif'",
    },
}
SAFE = 160   # side margin: 1200 - 2 * 160 = 880, which survives a 1.4:1 centre crop

PROP = re.compile(r"--([a-z0-9-]+):\s*([^;]+);")


def tokens(spec):
    """The site's base palette, parsed from its own stylesheet.

    Deliberately the FIRST `:root` block: for every site here that is the base
    the page ships with, and a later `[data-theme]` or media block is an
    override a visitor has to ask for. See rule 2.
    """
    css = (ROOT / spec["css"]).read_text(encoding="utf-8")
    start = css.index(":root")
    block = css[start:css.index("}", start)]
    found = {k: v.strip() for k, v in PROP.findall(block)}
    out = {}
    for role, name in spec["tokens"].items():
        if name not in found:
            raise SystemExit(f"{spec['css']} :root has no --{name} (wanted for "
                             f"'{role}'); the card cannot be built from it")
        out[role] = found[name]
    return out


def lede(spec):
    """The sentence the page already shows a sharer, read out of its own head."""
    path, which = spec["copy"]
    html = (ROOT / path).read_text(encoding="utf-8")
    pat = (r'<meta\s+property="og:description"\s+content="([^"]+)"' if which == "og:description"
           else r'<meta\s+name="description"\s+content="([^"]+)"')
    m = re.search(pat, html)
    if not m:
        raise SystemExit(f"{path} has no {which}; the card would have to invent "
                         f"its own wording, which is the drift this avoids")
    return m.group(1)


def page_html(spec, t, text):
    fonts = (f"""<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={spec['fonts']}&display=swap">"""
             if spec.get("fonts") else "")
    if spec.get("mark"):
        svg = (ROOT / spec["mark"]).read_text(encoding="utf-8").strip()
        top = f'<div class="mark">{svg}</div>'
    else:
        top = f'<p class="eyebrow">{spec["eyebrow"]}</p>'
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="robots" content="noindex">
{fonts}
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {WIDTH}px; height: {HEIGHT}px; }}
  body {{
    background: {t['bg']};
    color: {t['ink']};
    font-family: {spec['body_font']};
    padding: 76px {SAFE}px 68px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
  }}
  .eyebrow {{
    font-size: 19px;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {t['accent']};
  }}
  h1 {{
    margin-top: 20px;
    font-family: {spec['title_font']};
    font-size: 96px;
    font-weight: 400;
    letter-spacing: -0.02em;
    line-height: 1.02;
  }}
  .lede {{
    margin-top: 28px;
    margin-bottom: 92px;
    max-width: {WIDTH - 2 * SAFE}px;
    color: {t['dim']};
    font-size: 30px;
    line-height: 1.38;
  }}
  .foot {{
    position: absolute;
    left: {SAFE}px;
    right: {SAFE}px;
    bottom: 68px;
    padding-top: 28px;
    border-top: 1px solid {t['rule']};
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    font-size: 20px;
    color: {t['faint']};
  }}
  .foot .dom {{ color: {t['dim']}; }}
  .mark svg {{ display: block; width: 84px; height: 84px; }}
</style></head>
<body>
  {top}
  <h1>{spec['name']}</h1>
  <p class="lede">{text}</p>
  <div class="foot"><span class="dom">charlietrenorden.com/{spec['slug']}</span><span>Charlie Trenorden</span></div>
</body></html>"""


def build(slug, page):
    spec = dict(SITES[slug], slug=slug)
    t = tokens(spec)
    text = lede(spec)
    source = ROOT / slug / "og-card-source.html"
    out = ROOT / slug / "og-card.png"
    source.write_text(page_html(spec, t, text), encoding="utf-8")
    page.goto(source.as_uri())
    if spec.get("assert_face"):
        # ASK FOR THE FACE, do not just wait on the status: document.fonts.status
        # reads "loaded" while a face nothing has demanded yet is unfetched, so
        # waiting on it alone passes instantly and the card ships in the fallback.
        page.evaluate("(f) => document.fonts.load(f)", spec["assert_face"])
        page.wait_for_function("() => document.fonts.status === 'loaded'", timeout=15000)
        if not page.evaluate("(f) => document.fonts.check(f)", spec["assert_face"]):
            raise SystemExit(f"{slug}: {spec['assert_face']} did not load; refusing "
                             f"to write a card in the fallback face")
    page.screenshot(path=str(out))
    size = out.stat().st_size
    # WhatsApp drops a thumbnail over about 300KB.
    assert size < 300 * 1024, f"{out}: {size / 1024:.0f} KiB, over the 300 KiB WhatsApp limit"
    print(f"  {slug}/og-card.png  {2 * WIDTH}x{2 * HEIGHT}, {size / 1024:.1f} KiB, "
          f"bg {t['bg']}, accent {t['accent']}")
    return out


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed: pip install playwright && "
              "playwright install chromium", file=sys.stderr)
        return 1
    wanted = argv or list(SITES)
    unknown = [s for s in wanted if s not in SITES]
    if unknown:
        print(f"unknown: {', '.join(unknown)}. known: {', '.join(SITES)}", file=sys.stderr)
        return 1
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT},
                                device_scale_factor=2)
        for slug in wanted:
            build(slug, page)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
