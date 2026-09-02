"""The fourteen axes the reveal plots.

One axis per domain, so that no domain is unmeasured and no axis is decoration,
plus redistribution, which no single domain owns and which is the summary figure
most readers recognise.

`bounds` are the plotting range for the track, not the theoretical range of the
measure, and they are DERIVED FROM THE DATA rather than rounded to a nice number.

Re-derived 30/08/2026 by derive_bounds.py, over everything that occupies each
axis: forty-five countries' measured cells, all 69 effective option values, and
the tax slider's own ends, padded by about 6% and snapped outward to the axis's
own precision. Run that script and paste the result; do not hand-edit a bound.

THIRTEEN OF THE FOURTEEN MOVED when twenty-five measured-only countries were
added the same day, because the new rows hold most of the new extremes. The four
that widened materially are the ones to know about: grid_carbon 0-600 to 0-740,
because Saudi Arabia at 692 and Kuwait at 635 sit above the old ceiling;
pension_spend 2.5-14.5 to 2-17, because Greece at 16.2 and Italy at 16.1 do;
family_spend 0.4-3.6 to 0.4-4, because Iceland reads 3.8; tax_take 10-60 to
8.5-58, where the ceiling is now set by the tax SLIDER at 55 rather than by any
country, since chart.js plots the raw rate on that spoke. Seven narrowed, which
recovers travel rather than losing it.

An earlier derivation on 30/08/2026 fixed four axes that were wasting half their
range on space nothing reaches: health_public was 0 to 100 for data spanning 33.1
to 86.1, education_spend 0 to 10 for 2.2 to 7.3, pension_spend 0 to 18 for 3.4 to
13.4, family_spend 0 to 5 for 0.6 to 3.3. That is not cosmetic: the fingerprint
scales every spoke by these, so education could travel only 11% of its ring
across its entire option range and the graphic sat still while the visitor
changed policy. check_travel.py is what keeps that from creeping back.

`url` is the page the figures were actually read from, checked with a real
browser user agent on 31/08/2026.

GALLAGHER IS THE AWKWARD ONE and its link points at the Internet Archive
deliberately. Michael Gallagher's Election Indices has left its old Trinity
address: every candidate path 404s, including the two the values were originally
read through. The Wayback availability API confirms the PDF is archived, so the
link is the archive's HISTORY for that file rather than one snapshot, because
the only snapshot it holds is from 2023 and these figures are the 16 June 2025
edition. Linking the 2023 copy would point a reader at different numbers from
the ones on the page. The edition is named in the source text instead.

Direct fetches of web.archive.org returned 429 while checking this, which is
rate limiting rather than absence: the availability API answered 200 for the
same URL in the same minute.

`direction` says which way is better ONLY for the purpose of never colouring a
track by it. It exists so the page can state the direction in words next to the
number, because a bare comparative like "higher" tells the reader nothing about
what is being measured.
"""

AXES = [
    {"id": "tax_take", "domain": "tax", "label": "Tax take",
     "unit": "% of GDP", "direction": "neither", "bounds": (8.5, 58),
     "source": "OECD Revenue Statistics / IMF",
     "url": "https://www.oecd.org/en/data/datasets/global-revenue-statistics-database.html"},
    {"id": "health_public", "domain": "healthcare", "label": "Public share of health spend",
     "unit": "%", "direction": "neither", "bounds": (29, 92),
     "source": "WHO Global Health Expenditure Database",
     "url": "https://data.who.int/indicators"},
    # REPLACED education_spend ON 02/09/2026, and the reason is that the old axis
    # measured the wrong thing. Public education spend across all levels as a
    # share of GDP is the size of the school system; every option in the
    # education domain is about who pays for university. The five option medians
    # sat between 4.30 and 5.20 on a track 5.9 wide, so the spoke travelled 15%,
    # the thinnest of the thirteen and exactly on check_travel.py's floor, and
    # it put "Free through university" BELOW "Free at school, deferred fees
    # after". This measures the quantity the labels describe. The options
    # separate by 47.66 points and the spoke travels 60%.
    #
    # THE SERIES IS THE AFTER-TRANSFERS COLUMN, which is why the United Kingdom
    # reads 21.76 and looks at a glance like a fault. A government loan the
    # student repays to the university is counted as private money, so a
    # deferred-fee system books the whole bill to the household with the state
    # acting as lender rather than payer. The same OECD table's initial-funds
    # column reads the UK at 44.05. Adopting this column is an editorial choice
    # about whether a student loan is the state paying or the student paying, and
    # the method section on the page states which convention is in use.
    #
    # It costs ten cells: 36 of 45 against the old axis's 44. Switzerland is the
    # real loss and its row says why it cannot be filled.
    #
    # (17, 96) from derive_bounds.py on 02/09/2026, run after the cells and the
    # option values were swapped, on step 1 as for health_public. The occupants
    # run 21.76 (UK) to 91.17 (NO), a span of 69.41, padded 6% and snapped
    # outward. No other axis moved on the same run.
    {"id": "tertiary_public", "domain": "education",
     "label": "Public share of university funding",
     "unit": "%", "direction": "neither", "bounds": (17, 96),
     # `source` is printed in the axes table on the page, beside thirteen others
     # that read "OECD Social Expenditure Database" and the like. It carried the
     # SDMX key as well, which put EXP_SOURCE S13, EDUCATION_LEV ISCED11_5T8 and
     # UNIT_MEASURE PT_EXP in front of a reader who wants to know where the
     # number came from. The key is how the number is FETCHED and belongs in
     # fetch_indicators.py and in this comment, which is where it now is:
     #   EXP_SOURCE=S13, EDUCATION_LEV=ISCED11_5T8, UNIT_MEASURE=PT_EXP,
     #   EXP_DESTINATION=INST_EDU, EXPENDITURE_TYPE=DIR_EXP
     "source": "OECD Education at a Glance, UOE finance collection",
     "url": "https://data-explorer.oecd.org/vis?df[ds]=DisseminateFinalDMZ&df[id]=DSD_EAG_UOE_FIN%40DF_UOE_FIN_SOURCE_GV_PR_NDOM&df[ag]=OECD.EDU.IMEP"},
    {"id": "social_housing", "domain": "housing", "label": "Social housing",
     "unit": "% of stock", "direction": "neither", "bounds": (0, 36.5),
     "source": "OECD Affordable Housing Database",
     "url": "https://www.oecd.org/en/data/datasets/oecd-affordable-housing-database.html"},
    {"id": "pension_spend", "domain": "retirement", "label": "Public pension spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (2, 17),
     "source": "OECD Pensions at a Glance",
     "url": "https://data-explorer.oecd.org/"},
    {"id": "grid_carbon", "domain": "energy", "label": "Grid carbon",
     "unit": "g/kWh", "direction": "lower", "bounds": (0, 740),
     "source": "Ember / Our World in Data",
     "url": "https://ourworldindata.org/grapher/carbon-intensity-electricity"},
    {"id": "expression", "domain": "speech", "label": "Freedom of expression",
     "unit": "index, 0 to 1", "direction": "higher", "bounds": (0, 1),
     "source": "V-Dem freedom of expression index",
     "url": "https://ourworldindata.org/grapher/freedom-of-expression-index"},
    {"id": "disproportionality", "domain": "voting", "label": "Electoral disproportionality",
     "unit": "Gallagher index", "direction": "lower", "bounds": (0, 25.5),
     "source": "Gallagher, Election Indices, 16 June 2025, via the Internet Archive",
     "url": "https://web.archive.org/web/*/tcd.ie/Political_Science/people/michael_gallagher/ElSystems/Docts/ElectionIndices.pdf"},
    {"id": "bargaining", "domain": "work", "label": "Collective bargaining coverage",
     "unit": "%", "direction": "neither", "bounds": (5, 100),
     "source": "OECD/AIAS ICTWSS",
     "url": "https://data-explorer.oecd.org/"},
    {"id": "military_burden", "domain": "defence", "label": "Military burden",
     "unit": "% of GDP", "direction": "neither", "bounds": (0, 9.5),
     "source": "SIPRI Military Expenditure Database",
     "url": "https://data.worldbank.org/indicator/MS.MIL.XPND.GD.ZS"},
    {"id": "foreign_born", "domain": "immigration", "label": "Foreign-born share",
     "unit": "%", "direction": "neither", "bounds": (0, 82),
     "source": "UN DESA International Migrant Stock",
     "url": "https://data.worldbank.org/indicator/SM.POP.TOTL.ZS"},
    {"id": "incarceration", "domain": "justice", "label": "Incarceration",
     "unit": "per 100,000", "direction": "neither", "bounds": (0, 580),
     "source": "World Prison Brief",
     "url": "https://www.prisonstudies.org/world-prison-brief-data"},
    {"id": "family_spend", "domain": "family", "label": "Family benefit spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (0.4, 4),
     "source": "OECD Social Expenditure Database",
     "url": "https://data-explorer.oecd.org/"},
    # THE ONLY SUMMED AXIS. `summed` says the visitor's value is the sum of
    # several domains' contributions rather than one domain's option value, and
    # it is declared here because three separate places used to hold their own
    # copy of that fact: match.js, test_data.py and derive_bounds.py. Two of the
    # three agreed. derive_bounds.py did not, and derived this axis's bounds from
    # a population of single contributions when what gets plotted is the sum of
    # three, which is how a ceiling of 0.27 came to sit under a plotted 0.44.
    {"id": "redistribution", "domain": None, "label": "Redistribution",
     "summed": True,
     # (0, 0.31) from derive_bounds.py on 02/09/2026, once occupants() started
     # enumerating the sum instead of the parts. The ceiling is the most
     # redistributive design the menu can build (tax_departure + wo_ubi +
     # fa_universal, 0.2918), which sits above every real country: Finland tops
     # the measured cells at 0.246. That is correct. The menu contains policies
     # no country runs, so a visitor can build past the top of the world.
     "unit": "Gini cut, market to disposable", "direction": "neither", "bounds": (0, 0.31),
     "source": "OECD Income Distribution Database",
     "url": "https://data-explorer.oecd.org/"},
]
