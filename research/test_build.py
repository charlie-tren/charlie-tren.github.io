"""Tests for the research page builder.

    python -m pytest research -q

This is the only code on the hub that can be SILENTLY wrong. It divides a live quote
by the price printed in a report and publishes the result as a percentage return next
to a Buy or a Hold, so a wrong answer there still looks like an answer, and it is the
first row a sceptical reader checks.

fetch() is replaced in every test rather than mocked at the yfinance layer: its only
job is to fill the cache, and everything worth asserting - the return, the guard, the
fallback - happens in main() off that cache.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

REAL = Path(__file__).resolve().parent


def load_build(tmp, reports, prices=None):
    """Import build.py with every path pointed at a temp directory."""
    spec = importlib.util.spec_from_file_location(f"rbuild_{tmp.name}", REAL / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    shutil.copy(REAL / "template.html.j2", tmp / "template.html.j2")
    (tmp / "reports.json").write_text(json.dumps({"reports": reports}), encoding="utf-8")
    if prices is not None:
        (tmp / "prices.json").write_text(json.dumps(prices), encoding="utf-8")

    mod.HERE = tmp
    mod.REPORTS = tmp / "reports.json"
    mod.PRICES = tmp / "prices.json"
    mod.TEMPLATE = tmp / "template.html.j2"
    mod.OUT = tmp / "index.html"
    return mod


def report(**kw):
    base = {"symbol": "ARB.AX", "name": "ARB Corporation", "date": "2026-08-23",
            "call": "Buy", "call_price": 79.09, "currency": "$", "file": "arb.pdf"}
    base.update(kw)
    return base


# ------------------------------------------------------------------ the return

def test_return_is_the_move_since_the_call(tmp_path):
    b = load_build(tmp_path, [report()])
    b.fetch = lambda syms, cache: (cache.update(
        {"ARB.AX": {"price": 84.36, "asof": "2026-08-26"}}) or (list(syms), []))
    b.main()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # The template formats with %+.1f, so the sign is explicit and a rise rendering as
    # a fall is caught here rather than by eye.
    assert "+6.7%" in html, "84.36 against a call at 79.09 is +6.7%"
    # On the rendered span, not a bare substring: "dn" also appears in the stylesheet,
    # so `"dn" not in html` can never be true and would read as a passing check.
    assert 'class="since up"' in html and 'class="since dn"' not in html


def test_a_fall_is_negative(tmp_path):
    b = load_build(tmp_path, [report()])
    b.fetch = lambda syms, cache: (cache.update(
        {"ARB.AX": {"price": 58.73, "asof": "2026-08-26"}}) or (list(syms), []))
    b.main()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "-25.7%" in html, "58.73 against a call at 79.09 is -25.7%"
    assert 'class="since dn"' in html


# -------------------------------------------------------------------- the guard

def test_no_price_at_all_refuses_to_write(tmp_path):
    """A blank return next to an investment call reads as flat, which is a lie. The
    build must exit non-zero and leave the published page byte-identical."""
    b = load_build(tmp_path, [report()])
    (tmp_path / "index.html").write_text("ORIGINAL", encoding="utf-8")
    b.fetch = lambda syms, cache: ([], [])          # total failure, empty cache
    with pytest.raises(SystemExit) as e:
        b.main()
    assert e.value.code != 0 and e.value.code is not None
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == "ORIGINAL"


def test_one_failed_name_falls_back_to_its_cached_quote(tmp_path):
    """A single flaky symbol must not blank its row or fail the run - that is what
    prices.json is for. The page says when the price was taken."""
    b = load_build(tmp_path, [report()], prices={"ARB.AX": {"price": 80.00, "asof": "2026-08-20"}})
    b.fetch = lambda syms, cache: ([], list(syms))  # fetch failed, cache untouched
    b.main()
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "80.00" in html and "2026-08-20" in html


# --------------------------------------------------------------------- the tone

@pytest.mark.parametrize("call,expected", [
    ("Buy", "pos"), ("Accumulate", "pos"), ("Overweight", "pos"), ("Add on weakness", "pos-soft"),
    ("Sell", "neg"), ("Reduce", "neg"), ("Avoid", "neg"), ("Underweight", "neg"),
    ("Modest buy", "pos-soft"), ("Weak buy", "pos-soft"), ("Tentative buy", "pos-soft"),
    ("Hold", "neutral"), (None, "none"), ("", "none"),
])
def test_tone_maps_every_rating_it_claims_to(tmp_path, call, expected):
    """Ratings not yet used must colour themselves, which is the whole reason tone() reads
    the call TEXT rather than a per-row field. A hedged call must not shout as loudly as
    an outright one."""
    b = load_build(tmp_path, [])
    assert b.tone(call) == expected


def test_an_explicit_tone_in_the_data_wins(tmp_path):
    b = load_build(tmp_path, [report(call="Buy", tone="neutral")])
    b.fetch = lambda syms, cache: (cache.update(
        {"ARB.AX": {"price": 79.09, "asof": "2026-08-26"}}) or (list(syms), []))
    b.main()
    assert 'neutral' in (tmp_path / "index.html").read_text(encoding="utf-8")
