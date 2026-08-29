"""The fourteen axes the reveal plots.

One axis per domain, so that no domain is unmeasured and no axis is decoration,
plus redistribution, which no single domain owns and which is the summary figure
most readers recognise.

`bounds` are the plotting range for the track, not the theoretical range of the
measure. They are set wide enough to hold every country in the set with headroom
and are re-derived from the data by a test, never rounded to a nice number.

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
     "unit": "%", "direction": "neither", "bounds": (0, 100),
     "source": "WHO Global Health Expenditure Database"},
    {"id": "education_spend", "domain": "education", "label": "Public education spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (0, 10),
     "source": "World Bank"},
    {"id": "social_housing", "domain": "housing", "label": "Social housing",
     "unit": "% of stock", "direction": "neither", "bounds": (0, 90),
     "source": "OECD Affordable Housing Database"},
    {"id": "pension_spend", "domain": "retirement", "label": "Public pension spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (0, 18),
     "source": "OECD Pensions at a Glance"},
    {"id": "grid_carbon", "domain": "energy", "label": "Grid carbon",
     "unit": "g/kWh", "direction": "lower", "bounds": (0, 700),
     "source": "Ember / Our World in Data"},
    {"id": "expression", "domain": "speech", "label": "Freedom of expression",
     "unit": "index, 0 to 1", "direction": "higher", "bounds": (0, 1),
     "source": "V-Dem freedom of expression index"},
    {"id": "disproportionality", "domain": "voting", "label": "Electoral disproportionality",
     "unit": "Gallagher index", "direction": "lower", "bounds": (0, 25),
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
     "unit": "per 100,000", "direction": "neither", "bounds": (0, 700),
     "source": "World Prison Brief"},
    {"id": "family_spend", "domain": "family", "label": "Family benefit spend",
     "unit": "% of GDP", "direction": "neither", "bounds": (0, 5),
     "source": "OECD Social Expenditure Database"},
    {"id": "redistribution", "domain": None, "label": "Redistribution",
     "unit": "Gini cut, market to disposable", "direction": "neither", "bounds": (0, 0.30),
     "source": "OECD Income Distribution Database"},
]
