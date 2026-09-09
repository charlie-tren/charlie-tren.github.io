"""Run: python -m pytest crosscheck/test_build.py

The parsers get the most attention here, because both read a file another repository
publishes and neither controls its shape. A silent parse change is the failure this
page is most exposed to: it would still produce a page, just a wrong one.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402


SHORTFALL_JS = 'window.SHORTFALL = ' + json.dumps({
    "disclosed": [{"ticker": "TRAP", "name": "Disclosed Only", "sector": "X",
                   "market": "M", "composite": 99.0, "applicable": 6}],
    "names": [
        {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Technology",
         "market": "United States (NYSE & Nasdaq)", "composite": 100.0, "applicable": 6},
        {"ticker": "KO", "name": "Coca-Cola", "sector": "Consumer Defensive",
         "market": "United States (NYSE & Nasdaq)", "composite": 12.0, "applicable": 5},
        {"ticker": "SOLO", "name": "Not In Drift", "sector": "X",
         "market": "M", "composite": 50.0, "applicable": 4},
    ],
}) + ';\n'

DRIFT_HTML = (
    '<html><body><script id="rows" type="application/json">'
    + json.dumps([
        {"ticker": "AMD", "name": "AMD", "sector": "Technology", "market": "US",
         "gap": 15.8, "bandkey": "behind", "mcap": 800.0, "analysts": 52},
        {"ticker": "KO", "name": "Coca-Cola", "sector": "Consumer Defensive",
         "market": "US", "gap": -17.6, "bandkey": "ahead", "mcap": 380.0, "analysts": 27},
    ])
    + "</script></body></html>"
)


class TestParsers:
    def test_reads_the_full_names_list_not_the_disclosed_subset(self):
        # `disclosed` is 17 companies carrying an event and `names` is all 640. Both
        # parse, both are lists of the same shape, and reaching for the wrong one builds
        # a plausible-looking page with 3% of the data in it.
        names = build.parse_shortfall(SHORTFALL_JS)
        assert [n["ticker"] for n in names] == ["AMD", "KO", "SOLO"]
        assert "TRAP" not in {n["ticker"] for n in names}

    def test_survives_the_trailing_semicolon_and_the_assignment(self):
        assert len(build.parse_shortfall(SHORTFALL_JS)) == 3

    def test_reads_the_inlined_rows_block(self):
        assert [d["ticker"] for d in build.parse_drift(DRIFT_HTML)] == ["AMD", "KO"]

    def test_raises_rather_than_returning_nothing_when_the_block_is_gone(self):
        # An empty list here would join to zero rows and publish an empty page, which
        # reads as "no companies qualify" rather than as a broken build.
        with pytest.raises(ValueError):
            build.parse_drift("<html><body>redesigned</body></html>")


class TestJoin:
    def test_keeps_only_companies_present_in_both(self):
        rows = build.join(build.parse_shortfall(SHORTFALL_JS), build.parse_drift(DRIFT_HTML))
        assert [r["ticker"] for r in rows] == ["AMD", "KO"]

    def test_carries_the_strain_score_across_rather_than_recomputing_it(self):
        rows = build.join(build.parse_shortfall(SHORTFALL_JS), build.parse_drift(DRIFT_HTML))
        assert rows[0]["strain"] == 100.0
        assert rows[0]["applicable"] == 6

    def test_orders_by_the_three_measures_combined_rather_than_by_strain_alone(self):
        # Sorted by Shortfall's score alone until 10/09/2026, which quietly made one of
        # the three columns the page's default opinion - the opposite of what a
        # cross-tab is for.
        rows = build.join(build.parse_shortfall(SHORTFALL_JS), build.parse_drift(DRIFT_HTML))
        assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))
        assert [r["score"] for r in rows] == sorted(
            [r["score"] for r in rows], reverse=True
        )


class TestReading:
    def test_uses_consensus_drifts_own_ten_point_bands(self):
        # Not a new cut. Drawing these bands anywhere else would give the estate two
        # answers to one question.
        assert build.reading(15.8) == "behind"
        assert build.reading(-17.6) == "ahead"
        assert build.reading(0.0) == "inline"

    def test_the_boundaries_land_the_way_the_source_site_lands_them(self):
        # Measured against the live data 09/09/2026: behind runs 10.1 to 89.8, inline
        # -10.0 to 9.9, ahead -211.1 to -10.1. So the band edges are inclusive.
        assert build.reading(10.0) == "behind"
        assert build.reading(9.9) == "inline"
        assert build.reading(-10.0) == "ahead"
        assert build.reading(-9.9) == "inline"

    def test_positive_gap_means_the_price_is_behind_not_ahead(self):
        # The one thing a reader could get exactly backwards, so it is pinned.
        assert build.reading(50.0) == "behind"
        assert build.reading(-50.0) == "ahead"


class TestGuard:
    def test_refuses_to_write_when_a_source_has_collapsed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(build, "COUNTS", tmp_path / "counts.json")
        build.check_universes(640, 1216, 609)
        with pytest.raises(SystemExit) as e:
            build.check_universes(40, 1216, 38)
        assert "REFUSING TO WRITE" in str(e.value)

    def test_allows_ordinary_drift_in_coverage(self, tmp_path, monkeypatch):
        # These universes move by tens every week as estimate history thins out. A guard
        # that fires on that gets turned off, and then it is not there for the real one.
        monkeypatch.setattr(build, "COUNTS", tmp_path / "counts.json")
        build.check_universes(640, 1216, 609)
        build.check_universes(620, 1150, 570)

    def test_a_first_run_has_nothing_to_compare_against_and_proceeds(self, tmp_path, monkeypatch):
        monkeypatch.setattr(build, "COUNTS", tmp_path / "counts.json")
        build.check_universes(640, 1216, 609)

    def test_records_the_counts_so_the_next_run_has_a_baseline(self, tmp_path, monkeypatch):
        counts = tmp_path / "counts.json"
        monkeypatch.setattr(build, "COUNTS", counts)
        build.check_universes(640, 1216, 609)
        assert json.loads(counts.read_text())["joined"] == 609

    def test_a_collapse_in_the_JOIN_alone_is_caught(self, tmp_path, monkeypatch):
        # Both sources can publish fully and still stop agreeing on the key. That is the
        # failure neither site can see from its own side.
        monkeypatch.setattr(build, "COUNTS", tmp_path / "counts.json")
        build.check_universes(640, 1216, 609)
        with pytest.raises(SystemExit):
            build.check_universes(640, 1216, 12)


class TestCorners:
    def test_counts_the_four_situations_against_the_top_quartile_of_strain(self):
        rows = [
            {"strain": 100, "reading": "behind"},
            {"strain": 90, "reading": "ahead"},
            {"strain": 50, "reading": "behind"},
            {"strain": 10, "reading": "ahead"},
        ]
        c = build.corners(rows)
        assert c["strained_behind"] + c["strained_ahead"] + c["clean_behind"] + c["clean_ahead"] == 4

    def test_does_not_divide_by_zero_on_a_short_list(self):
        assert build.corners([{"strain": 5, "reading": "inline"}])["cut"] == 5


DCF_JSON = json.dumps({
    "site": "DCF Studio",
    "as_of": "2026-09-09",
    "published": 4,
    "ratios": {"AMD": 0.30, "KO": 0.61, "MSFT": 1.20, "SOLO": 2.40},
})


class TestDcfBands:
    """DCF Studio's model runs systematically below market prices - median 0.61x
    across the 506 it can value - so the page shows where a company SITS in that
    distribution and never the implied price. A number that is uniformly 0.6x is a
    perfectly good ordering and a bad valuation, and only one of those can be printed
    honestly."""

    def test_reads_the_published_ratios(self):
        assert build.parse_dcf(DCF_JSON)["AMD"] == 0.30

    def test_cuts_the_distribution_into_thirds(self):
        lo, hi = build.dcf_cuts([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        assert lo < hi
        bands = [build.dcf_band(r, (lo, hi)) for r in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]]
        assert bands.count("dearer") == 2
        assert bands.count("middle") == 2
        assert bands.count("cheaper") == 2

    def test_a_higher_ratio_is_cheaper_not_dearer(self):
        # The one thing a reader could have exactly backwards. A high ratio means the
        # model puts the shares above the market price.
        cuts = build.dcf_cuts([0.2, 0.5, 1.0, 2.0])
        assert build.dcf_band(2.0, cuts) == "cheaper"
        assert build.dcf_band(0.2, cuts) == "dearer"

    def test_a_company_with_no_reading_gets_none_rather_than_a_middle_band(self):
        # 103 of the 609 are dropped as implausible. Landing them in the middle band
        # would state a finding the model explicitly refused to make.
        rows = build.join(
            build.parse_shortfall(SHORTFALL_JS), build.parse_drift(DRIFT_HTML),
            {"AMD": 0.30},
        )
        by = {r["ticker"]: r for r in rows}
        assert by["AMD"]["dcf"] == 0.30
        assert by["KO"]["dcf"] is None
        assert by["KO"]["dcfband"] is None

    def test_the_column_is_absent_entirely_when_dcf_is_unreachable(self):
        # Degrade to LESS, never to a column of blanks. A blank column reads as "the
        # model had no opinion on any of these", which is a claim; no column reads as
        # what it is.
        rows = build.join(
            build.parse_shortfall(SHORTFALL_JS), build.parse_drift(DRIFT_HTML), None,
        )
        assert all(r["dcf"] is None for r in rows)
        assert build.has_dcf(rows) is False

    def test_says_it_has_dcf_when_enough_rows_carry_one(self):
        rows = build.join(
            build.parse_shortfall(SHORTFALL_JS), build.parse_drift(DRIFT_HTML),
            {"AMD": 0.30, "KO": 0.61},
        )
        assert build.has_dcf(rows) is True

    def test_a_handful_of_readings_is_not_a_column(self):
        # One company in 609 with a reading is a curiosity, not a ranked column, and
        # ranking two names against each other says nothing at all.
        many = [{"dcf": None} for _ in range(600)] + [{"dcf": 0.5}, {"dcf": 0.6}]
        assert build.has_dcf(many) is False

    def test_survives_a_file_that_lost_its_ratios(self):
        assert build.parse_dcf('{"site": "DCF Studio"}') == {}


class TestCombinedRank:
    """One ordering across three measures that do not share a scale.

    Shortfall is 0-100 where high is bad, the gap is percentage points either side of
    zero, and DCF is a ratio with a median near 0.61. Averaging those raw would let the
    gap, which has by far the widest numeric range, decide everything. Each is turned
    into its own percentile first, so each contributes equally by construction.

    ORIENTED SO HIGHER IS MORE ATTRACTIVE, on all three: unstrained accounts, price
    behind analyst estimates, and a model value above the market price. That makes one
    coherent axis - at the top the three agree the shares look cheap and the numbers
    look clean, at the bottom they agree on the opposite.
    """

    def rows(self):
        return [
            # strain, gap, dcf
            {"ticker": "BEST", "strain": 0, "gap": 40.0, "dcf": 2.0},
            {"ticker": "MID", "strain": 50, "gap": 0.0, "dcf": 0.6},
            {"ticker": "WORST", "strain": 100, "gap": -40.0, "dcf": 0.2},
        ]

    def test_puts_the_name_all_three_agree_on_at_the_top(self):
        ranked = build.rank_rows(self.rows())
        assert [r["ticker"] for r in ranked] == ["BEST", "MID", "WORST"]
        assert ranked[0]["rank"] == 1
        assert ranked[-1]["rank"] == 3

    def test_low_strain_is_attractive_not_high(self):
        # Shortfall's own scale runs the other way: 100 is the MOST strained. Carrying
        # it through unflipped would put the worst accounts at the top of the page.
        a = build.rank_rows([
            {"ticker": "CLEAN", "strain": 5, "gap": 0.0, "dcf": 0.6},
            {"ticker": "STRAINED", "strain": 95, "gap": 0.0, "dcf": 0.6},
        ])
        assert a[0]["ticker"] == "CLEAN"

    def test_a_positive_gap_is_attractive_because_the_price_is_behind(self):
        a = build.rank_rows([
            {"ticker": "BEHIND", "strain": 50, "gap": 40.0, "dcf": 0.6},
            {"ticker": "AHEAD", "strain": 50, "gap": -40.0, "dcf": 0.6},
        ])
        assert a[0]["ticker"] == "BEHIND"

    def test_a_higher_dcf_ratio_is_attractive(self):
        a = build.rank_rows([
            {"ticker": "CHEAP", "strain": 50, "gap": 0.0, "dcf": 2.0},
            {"ticker": "DEAR", "strain": 50, "gap": 0.0, "dcf": 0.2},
        ])
        assert a[0]["ticker"] == "CHEAP"

    def test_a_missing_dcf_averages_the_two_that_are_there(self):
        # 103 of the 609 have no DCF reading. Scoring a missing component as zero would
        # push every one of them to the bottom of the page for having no opinion, which
        # is a ranking of data coverage rather than of companies.
        a = build.rank_rows([
            {"ticker": "NODCF", "strain": 0, "gap": 40.0, "dcf": None},
            {"ticker": "HASDCF", "strain": 100, "gap": -40.0, "dcf": 0.2},
        ])
        assert a[0]["ticker"] == "NODCF"

    def test_the_widest_raw_range_does_not_dominate(self):
        # The gap spans about 270 points and strain spans 100, so on raw numbers the gap
        # would outvote everything. On percentiles a name that is last on two measures
        # cannot be first overall on the strength of one.
        a = build.rank_rows([
            {"ticker": "ONEGOOD", "strain": 100, "gap": 200.0, "dcf": 0.1},
            {"ticker": "TWOGOOD", "strain": 0, "gap": -5.0, "dcf": 2.0},
        ])
        assert a[0]["ticker"] == "TWOGOOD"

    def test_every_row_gets_a_distinct_rank_from_one_upward(self):
        ranked = build.rank_rows(self.rows())
        assert sorted(r["rank"] for r in ranked) == [1, 2, 3]

    def test_handles_a_single_row_without_dividing_by_zero(self):
        assert build.rank_rows([{"ticker": "ONE", "strain": 50, "gap": 1.0, "dcf": 0.5}])[0]["rank"] == 1

    def test_one_extreme_outlier_does_not_flatten_the_rest(self):
        # The live gap runs from -211.1 to +56.7. Under min-max scaling that single
        # bottom name compresses everything else into the top of the range and the
        # measure stops separating the companies anyone is actually comparing.
        # On rank position the pack keeps its spread whatever the extremes do.
        pack = [{"ticker": f"T{i}", "strain": 50, "gap": float(i), "dcf": 0.6}
                for i in range(10)]
        without = build.rank_rows([dict(r) for r in pack])
        with_outlier = build.rank_rows(
            [dict(r) for r in pack] + [{"ticker": "CRASH", "strain": 50, "gap": -211.0, "dcf": 0.6}]
        )
        order_a = [r["ticker"] for r in without]
        order_b = [r["ticker"] for r in with_outlier if r["ticker"] != "CRASH"]
        assert order_a == order_b
        # And the pack still spans a wide range of scores rather than bunching.
        scores = [r["score"] for r in with_outlier if r["ticker"] != "CRASH"]
        assert max(scores) - min(scores) > 0.25

    def test_ties_share_a_position_rather_than_being_ordered_by_accident(self):
        a = build.rank_rows([
            {"ticker": "A", "strain": 50, "gap": 5.0, "dcf": 0.6},
            {"ticker": "B", "strain": 50, "gap": 5.0, "dcf": 0.6},
        ])
        assert a[0]["score"] == a[1]["score"]
