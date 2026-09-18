"""Contrast and colour-separation floors for both themes, asserted against style.css.

WHY THIS FILE EXISTS. The dark theme was replaced on 18/09/2026 because its map read
as orange blobs on a void: the unshaded continents did not separate from the sea.
Nothing failed, because the palette was a block of hex in a stylesheet no test looked
at.

A NOTE ON THE MEASURE, because the first version of this file got it wrong. The
rejected theme's land and sea were #1a1a1a on #0a0a0a, which is a 1.1:1 contrast
ratio - a number that looks damning and is the wrong instrument. A contrast ratio is
scale-invariant, so it exaggerates differences at the dark end; in perceptually-uniform
terms that pair is a lightness step of dL* 6.5, which is LARGER than the light theme's
salmon-on-cream land and sea (dL* 5.3) that reads fine. So the ratio did not explain
the fault, and a ratio floor written from it failed the light theme, which is the
design Charlie likes.

What actually separated them: the light theme's land and sea differ in HUE as well
(dChroma 5.7), and the rejected theme's differed in lightness ALONE (dChroma 0.0, both
pure neutral greys). A small lightness step with no hue cue at the bottom of the range
is the fault. That is the rule asserted below, and it needs no threshold fitted to a
handful of examples.

Text floors are WCAG AA and apply to both themes. The map floors are about seeing a
filled region as a region, which is a different job from reading a glyph.
"""
import math
import pathlib
import re

import pytest

CSS = (pathlib.Path(__file__).parent / "style.css").read_text(encoding="utf-8")


def tokens(selector: str) -> dict[str, str]:
    """The hex custom properties inside one rule block."""
    block = CSS.split(selector)[1].split("}")[0]
    found = dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", block))
    assert found, f"no hex tokens found in {selector}"
    return found


LIGHT = tokens(":root {")
DARK = tokens(':root[data-theme="dark"]')


def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h: str) -> float:
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# (label, token, against, floor). Text floors are WCAG AA; the map floors are the
# lower bar a filled region needs to be seen as a region at all, which is a
# different job from reading a glyph.
PAIRS = [
    ("ink on panel", "ink", "panel", 4.5),
    ("ink on bg", "ink", "bg", 4.5),
    ("ink-soft on panel", "ink-soft", "panel", 4.5),
    # The 11px uppercase column headers are the tightest text on the page, and they
    # are ink-faint. #6b7f92 was tried in the light theme and failed at 3.93.
    ("ink-faint on panel", "ink-faint", "panel", 4.5),
    ("accent on panel", "accent", "panel", 3.0),
    ("under on panel", "under", "panel", 3.0),
    ("over on panel", "over", "panel", 3.0),
]

THEMES = [("light", LIGHT), ("dark", DARK)]


@pytest.mark.parametrize("theme,tok", THEMES)
@pytest.mark.parametrize("label,a,b,floor", PAIRS)
def test_contrast_floor(theme, tok, label, a, b, floor):
    got = contrast(tok[a], tok[b])
    assert got >= floor, (
        f"{theme}: {label} is {got:.2f}:1 ({tok[a]} on {tok[b]}), floor {floor}")


@pytest.mark.parametrize("theme,tok", THEMES)
def test_ramp_steps_are_distinguishable(theme, tok):
    """Six steps that a reader cannot tell apart is a one-step ramp with a legend."""
    steps = [tok[f"ramp{i}"] for i in range(1, 7)]
    for i in range(5):
        got = contrast(steps[i], steps[i + 1])
        assert got >= 1.15, (
            f"{theme}: ramp{i + 1} -> ramp{i + 2} is only {got:.2f}:1")


@pytest.mark.parametrize("theme,tok", THEMES)
def test_ramp_is_monotonic(theme, tok):
    """The ramp has to run one way. A ramp that dips mid-scale makes two different
    ease scores render as the same shade, which is worse than a flat map because it
    looks like a reading."""
    lums = [luminance(tok[f"ramp{i}"]) for i in range(1, 7)]
    assert lums == sorted(lums) or lums == sorted(lums, reverse=True), \
        f"{theme}: ramp luminance is not monotonic: {[round(x, 4) for x in lums]}"


def test_dark_redefines_every_light_token():
    """The dark block's own contract. A token left out falls through to a salmon
    value on a navy ground, and nothing would fail."""
    missing = sorted(set(LIGHT) - set(DARK))
    assert not missing, f"dark theme does not redefine: {missing}"


def _lab(h: str) -> tuple[float, float, float]:
    r, g, b = (_lin(int(h[i:i + 2], 16)) for i in (1, 3, 5))
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)  # noqa: E731
    fx, fy, fz = f(X), f(Y), f(Z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def chroma_distance(a: str, b: str) -> float:
    """Separation in the a*b* plane - hue and saturation, with lightness removed."""
    return math.dist(_lab(a)[1:], _lab(b)[1:])


# Pairs of large adjacent fills on the map. Each pair must carry a hue cue, not only a
# lightness step, because a lightness step alone is what the rejected theme had.
ADJACENT = [
    ("land vs sea", "map-land", "map-sea"),
    ("lowest shaded step vs unshaded land", "ramp1", "map-land"),
]


@pytest.mark.parametrize("theme,tok", THEMES)
@pytest.mark.parametrize("label,a,b", ADJACENT)
def test_adjacent_fills_are_not_separated_by_lightness_alone(theme, tok, label, a, b):
    got = chroma_distance(tok[a], tok[b])
    assert got >= 3.0, (
        f"{theme}: {label} differ by only dChroma {got:.2f} ({tok[a]} / {tok[b]}). "
        "Two large fills side by side need a hue cue, not just a lightness step.")


def test_the_checks_can_fail():
    """A check that cannot come out negative is decoration. The rejected amber theme's
    land and sea are kept here as the case that must fail."""
    assert chroma_distance("#1a1a1a", "#0a0a0a") < 3.0     # pure neutrals, no hue cue
    assert contrast("#6b7f92", "#fff8f0") < 4.5            # the light ink-faint that failed
