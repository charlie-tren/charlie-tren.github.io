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
browser user agent on 31/08/2026. An axis whose source has moved carries an
EMPTY url and the page prints its name without a link, because a dead link is
worse than no link: Gallagher's index has left its old Trinity address and no
candidate resolved.

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
    {"id": "education_spend", "domain": "education", "label": "Public education spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (1.8, 7.7),
     "source": "World Bank",
     "url": "https://data.worldbank.org/indicator/SE.XPD.TOTL.GD.ZS"},
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
     "source": "Gallagher, Election Indices",
     "url": ""},
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
    {"id": "redistribution", "domain": None, "label": "Redistribution",
     "unit": "Gini cut, market to disposable", "direction": "neither", "bounds": (0, 0.27),
     "source": "OECD Income Distribution Database",
     "url": "https://data-explorer.oecd.org/"},
]
