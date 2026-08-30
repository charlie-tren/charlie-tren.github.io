"""The fourteen axes the reveal plots.

One axis per domain, so that no domain is unmeasured and no axis is decoration,
plus redistribution, which no single domain owns and which is the summary figure
most readers recognise.

`bounds` are the plotting range for the track, not the theoretical range of the
measure, and they are DERIVED FROM THE DATA rather than rounded to a nice number.

Re-derived 30/08/2026 over everything that occupies each axis, which is the
twenty countries' measured cells plus all 69 option values, padded by about 6%.
Four were wasting half their range on space nothing reaches: health_public was
0 to 100 for data spanning 33.1 to 86.1, education_spend 0 to 10 for 2.2 to 7.3,
pension_spend 0 to 18 for 3.4 to 13.4, family_spend 0 to 5 for 0.6 to 3.3. That
is not cosmetic: the fingerprint scales every spoke by these, so education could
travel only 11% of its ring across its entire option range and the graphic sat
still while the visitor changed policy.

`direction` says which way is better ONLY for the purpose of never colouring a
track by it. It exists so the page can state the direction in words next to the
number, because a bare comparative like "higher" tells the reader nothing about
what is being measured.
"""

AXES = [
    {"id": "tax_take", "domain": "tax", "label": "Tax take",
     "unit": "% of GDP", "direction": "neither", "bounds": (10, 60),
     "source": "OECD Revenue Statistics / IMF"},
    {"id": "health_public", "domain": "healthcare", "label": "Public share of health spend",
     "unit": "%", "direction": "neither", "bounds": (28, 92),
     "source": "WHO Global Health Expenditure Database"},
    {"id": "education_spend", "domain": "education", "label": "Public education spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (1.8, 7.8),
     "source": "World Bank"},
    {"id": "social_housing", "domain": "housing", "label": "Social housing",
     "unit": "% of stock", "direction": "neither", "bounds": (0, 38),
     "source": "OECD Affordable Housing Database"},
    {"id": "pension_spend", "domain": "retirement", "label": "Public pension spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (2.5, 14.5),
     "source": "OECD Pensions at a Glance"},
    {"id": "grid_carbon", "domain": "energy", "label": "Grid carbon",
     "unit": "g/kWh", "direction": "lower", "bounds": (0, 600),
     "source": "Ember / Our World in Data"},
    {"id": "expression", "domain": "speech", "label": "Freedom of expression",
     "unit": "index, 0 to 1", "direction": "higher", "bounds": (0, 1),
     "source": "V-Dem freedom of expression index"},
    {"id": "disproportionality", "domain": "voting", "label": "Electoral disproportionality",
     "unit": "Gallagher index", "direction": "lower", "bounds": (0, 30),
     "source": "Gallagher, Election Indices"},
    {"id": "bargaining", "domain": "work", "label": "Collective bargaining coverage",
     "unit": "%", "direction": "neither", "bounds": (0, 100),
     "source": "OECD/AIAS ICTWSS"},
    {"id": "military_burden", "domain": "defence", "label": "Military burden",
     "unit": "% of GDP", "direction": "neither", "bounds": (0, 10),
     "source": "SIPRI Military Expenditure Database"},
    {"id": "foreign_born", "domain": "immigration", "label": "Foreign-born share",
     "unit": "%", "direction": "neither", "bounds": (0, 90),
     "source": "UN DESA International Migrant Stock"},
    {"id": "incarceration", "domain": "justice", "label": "Incarceration",
     "unit": "per 100,000", "direction": "neither", "bounds": (0, 600),
     "source": "World Prison Brief"},
    {"id": "family_spend", "domain": "family", "label": "Family benefit spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (0.4, 3.6),
     "source": "OECD Social Expenditure Database"},
    {"id": "redistribution", "domain": None, "label": "Redistribution",
     "unit": "Gini cut, market to disposable", "direction": "neither", "bounds": (0, 0.30),
     "source": "OECD Income Distribution Database"},
]
