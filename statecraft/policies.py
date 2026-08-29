"""The thirteen domains and their options.

Most options are something a real country actually does, and carry the country
tags to prove it. That constraint is what stops the menu being one-sided: the
original spec's list was almost entirely interventionist, which would have
collapsed every visitor onto Denmark and killed the reveal.

A SMALL MINORITY carry an empty `countries` list on purpose, and the empty list
is a deliberate claim rather than a missing field: nobody does this. Universal
basic income, absolute freedom of speech, banning private combustion cars and an
age cap on representatives are all things a visitor should be able to choose and
no country has. The reveal says so in as many words, and `test_the_menu_stays_
grounded` holds the untagged share down so the page cannot drift into a wishlist.

COSTS ARE SUBJECTIVE AND THE PAGE SAYS SO. They are published in full in the
method section, as on DCF Studio and One Story, so a reader who disagrees can
see exactly what they disagree with.

  financial  % of GDP. Only on non-tax options. Drawn down from the revenue the
             tax choice raises.
  political  points out of 100. Institutional capital: constitutional change,
             entrenched interests, electoral risk.
  social     points out of 100. Cohesion and personal-freedom cost, and the
             friction the policy creates.

`axis` is the value this option implies on its domain's axis, in that axis's own
unit. An option may also contribute to `redistribution`, which is summed across
the tax, work and family choices.
"""

DOMAINS = [
    {
        "id": "tax",
        "name": "Tax and Redistribution",
        "axis": "tax_take",
        "options": [
            {"id": "tax_minimal", "label": "Minimal state",
             "detail": "No income tax. Revenue from resources and consumption.",
             "countries": ["AE"], "revenue": 16.0, "political": 25, "social": 20,
             "axis": {"tax_take": 16.0, "redistribution": 0.01}},
            # EE verified 2026-08-29: still a genuine flat rate, 22% for 2026. The
            # legislated rise to 24% was reversed in December 2025, and the
            # income-dependent "tax hump" in the basic exemption was abolished from
            # 2026, so it is flatter now than it was.
            # https://www.ey.com/en_ee/insights/tax/significant-tax-changes-in-estonia-in-2025-2026
            {"id": "tax_flat", "label": "Flat income tax",
             "detail": "One rate on all income, few deductions.",
             "countries": ["EE"], "revenue": 33.0, "political": 30, "social": 15,
             "axis": {"tax_take": 33.0, "redistribution": 0.08}},
            {"id": "tax_anglo", "label": "Moderate progressive",
             "detail": "Progressive rates, a middling take, broad exemptions.",
             "countries": ["US", "AU", "NZ", "CA", "JP", "KR", "CH", "IL", "CL", "SG"],
             "revenue": 34.0, "political": 10, "social": 8,
             "axis": {"tax_take": 34.0, "redistribution": 0.11}},
            {"id": "tax_continental", "label": "High, funded by payroll",
             "detail": "Heavy social contributions on wages alongside income tax.",
             "countries": ["DE", "FR", "NL", "UK"], "revenue": 43.0, "political": 25, "social": 20,
             "axis": {"tax_take": 43.0, "redistribution": 0.18}},
            {"id": "tax_nordic", "label": "Nordic take",
             "detail": "High broad-based income tax and a high VAT.",
             "countries": ["DK", "SE", "NO", "FI"], "revenue": 46.0, "political": 40, "social": 30,
             "axis": {"tax_take": 46.0, "redistribution": 0.24}},
            # Untagged on purpose. Exit taxes on unrealised gains are real, in
            # Norway and the US among others, but no country runs one as a headline
            # revenue regime that pays for immigration, so there is nothing to tag
            # it to and the reveal says "which no country does". Cut once during
            # Task 2 for failing a test that required a tag; the TEST was the thing
            # that was wrong, since four more untagged options land in Tasks 3 and 4
            # and they are the aspirational half of the menu.
            {"id": "tax_departure", "label": "Nordic take plus a departure tax",
             "detail": "As above, and residents pay to leave, subsidising arrivals.",
             "countries": [], "revenue": 47.0, "political": 60, "social": 55,
             "axis": {"tax_take": 47.0, "redistribution": 0.25}},
        ],
    },
    {
        "id": "healthcare",
        "name": "Healthcare",
        "axis": "health_public",
        "options": [
            {"id": "hc_private", "label": "Private, employer-led",
             "detail": "Insurance through work, a safety net for the old and poor.",
             "countries": ["US"], "financial": 8.5, "political": 15, "social": 30,
             "axis": {"health_public": 50.0}},
            {"id": "hc_savings", "label": "Compulsory medical savings",
             "detail": "Everyone saves into their own account and is charged at the point of use.",
             "countries": ["SG"], "financial": 2.5, "political": 55, "social": 35,
             "axis": {"health_public": 45.0}},
            {"id": "hc_insurance", "label": "Mandatory insurance, regulated market",
             "detail": "Everyone must buy cover; insurers may not refuse anyone.",
             "countries": ["NL", "CH", "DE", "FR", "JP", "KR", "IL", "CL"],
             "financial": 7.5, "political": 30, "social": 15,
             "axis": {"health_public": 78.0}},
            {"id": "hc_mixed", "label": "Public with a private tier",
             "detail": "Universal public cover, and you may pay to go faster.",
             "countries": ["AU", "NZ", "CA", "DK", "SE", "NO", "FI", "EE", "AE"],
             "financial": 7.0, "political": 20, "social": 10,
             "axis": {"health_public": 80.0}},
            # UK label and detail corrected 2026-08-29. The original read "Fully
            # public, no private tier" and "Paying to skip the queue is not
            # available", which is plainly false: PHIN reports UK private
            # admissions running at record levels, split roughly 70% insurer-funded
            # and 30% self-pay in Q2 2025. The tag survives, the wording did not.
            # https://www.phin.org.uk/news/phin-private-market-update-september-2025-uk
            # The axis value was 95.0, which no source supports. ONS UK Health
            # Accounts put the government share of UK healthcare spending at 81.3%
            # in 2024, so it is set to that.
            # https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/healthcaresystem/bulletins/ukhealthaccounts/2024and2025
            {"id": "hc_public", "label": "Tax-funded national service",
             "detail": "One service for everyone, free at the point of use and paid for out of "
                       "general taxation. A private sector exists alongside it, unsubsidised.",
             "countries": ["UK"], "financial": 9.0, "political": 45, "social": 25,
             "axis": {"health_public": 81.3}},
        ],
    },
    {
        "id": "education",
        "name": "Education",
        "axis": "education_spend",
        "options": [
            {"id": "ed_market", "label": "Fees at every level past school",
             "detail": "Universities set their own prices. Loans, not grants.",
             "countries": ["US", "KR", "JP", "CL", "SG"],
             "financial": 4.2, "political": 10, "social": 25,
             "axis": {"education_spend": 4.2}},
            {"id": "ed_deferred", "label": "Free at school, deferred fees after",
             "detail": "Tertiary costs are paid back through the tax system once you earn.",
             "countries": ["AU", "NZ", "UK"], "financial": 4.8, "political": 20, "social": 12,
             "axis": {"education_spend": 4.8}},
            {"id": "ed_vocational", "label": "Free, with an early vocational track",
             "detail": "Free through university, and most students stream into apprenticeships.",
             "countries": ["DE", "CH", "NL", "AE"], "financial": 5.0, "political": 35, "social": 20,
             "axis": {"education_spend": 5.0}},
            {"id": "ed_free", "label": "Free through university",
             "detail": "No tuition at any level, and a maintenance grant while studying.",
             "countries": ["DK", "SE", "NO", "FI", "EE", "FR", "IL"],
             "financial": 6.3, "political": 35, "social": 10,
             "axis": {"education_spend": 6.3}},
            {"id": "ed_free_selective", "label": "Free, and selective from twelve",
             "detail": "No tuition, and an exam at twelve decides which school you attend.",
             "countries": ["CA"], "financial": 5.4, "political": 45, "social": 40,
             "axis": {"education_spend": 5.4}},
        ],
    },
    {
        "id": "housing",
        "name": "Housing",
        "axis": "social_housing",
        "options": [
            {"id": "ho_market", "label": "Private market, no state role",
             "detail": "Housing is built and owned privately. The state zones and nothing else.",
             "countries": ["US", "AU", "NZ", "CA", "EE", "CL", "IL", "AE"],
             "financial": 0.3, "political": 5, "social": 30,
             "axis": {"social_housing": 4.0}},
            {"id": "ho_subsidy", "label": "Private market with rent support",
             "detail": "Cash help with rent rather than housing built by the state.",
             "countries": ["UK", "DE", "JP", "KR", "CH", "NO", "FI"],
             "financial": 1.2, "political": 15, "social": 15,
             "axis": {"social_housing": 12.0}},
            {"id": "ho_cooperative", "label": "Co-operative and non-profit rental",
             "detail": "A large regulated rental sector run by non-profits, alongside a private market.",
             "countries": ["DK", "SE", "FR"], "financial": 1.6, "political": 35, "social": 15,
             "axis": {"social_housing": 22.0}},
            # NL verified 2026-08-29 and the figure cut. OECD PH4.2 groups the
            # Netherlands with Austria and Denmark at "over 20% of the total housing
            # stock", and names the Netherlands as one of the three countries whose
            # sector shrank by more than 2 percentage points over the decade. The
            # Dutch government's own figure is 29%. The axis read 34.0 and the detail
            # said "a third of the stock"; both are now 29%.
            # https://www.oecd.org/content/dam/oecd/en/data/datasets/affordable-housing-database/ph4-2-social-rental-housing-stock.pdf
            # https://www.government.nl/topics/housing/rented-housing
            {"id": "ho_social", "label": "Large social rental sector",
             "detail": "Non-profit housing associations own close to 29% of the stock "
                       "and let it below market rent.",
             "countries": ["NL"], "financial": 2.0, "political": 45, "social": 20,
             "axis": {"social_housing": 29.0}},
            # SG verified 2026-08-29: about 78% of the resident population lives in
            # HDB flats, and roughly nine in ten of those households own their flat
            # on a 99-year lease. Tag and figure both survive.
            # https://www.statista.com/statistics/966747/population-living-in-public-housing-singapore/
            {"id": "ho_singapore", "label": "State-built flats, sold to residents",
             "detail": "The state builds most housing and sells it on long leases. Most people own.",
             "countries": ["SG"], "financial": 2.4, "political": 70, "social": 35,
             "axis": {"social_housing": 78.0}},
        ],
    },
    {
        "id": "retirement",
        "name": "Retirement",
        "axis": "pension_spend",
        "options": [
            # CL amended 2026-08-29. Law 21.735, in force from August 2025, turns
            # Chile into a formally mixed system: the compulsory individual AFP
            # account stays and remains the main pillar, but a new employer
            # contribution rising to 8.5% by 2033 is split between the account and a
            # collective Autonomous Pension Protection Fund, on top of the flat PGU
            # floor. The detail now says "mostly" rather than claiming it is purely
            # individual accounts.
            # https://www.dlapiper.com/en/insights/publications/2025/08/chile-mixed-pension-and-social-security-system
            {"id": "re_private", "label": "Private accounts, mandatory",
             "detail": "Retirement is funded mostly out of your own compulsory fund. "
                       "The state pension is a floor only.",
             "countries": ["CL", "SG", "AE"], "financial": 3.0, "political": 55, "social": 30,
             "axis": {"pension_spend": 3.0}},
            {"id": "re_super", "label": "Means-tested pension plus mandatory saving",
             "detail": "A state pension for those who need it, and compulsory employer contributions.",
             "countries": ["AU", "NZ", "NL", "CH", "EE"],
             "financial": 5.0, "political": 40, "social": 15,
             "axis": {"pension_spend": 5.0}},
            {"id": "re_flat", "label": "Flat state pension, saving voluntary",
             "detail": "The same modest pension for everyone. Private saving is encouraged, not required.",
             "countries": ["UK", "CA", "IL", "US"], "financial": 6.5, "political": 15, "social": 12,
             "axis": {"pension_spend": 6.5}},
            {"id": "re_earnings", "label": "Earnings-related state pension",
             "detail": "What the state pays you depends on what you earned.",
             "countries": ["DK", "SE", "NO", "FI", "DE", "JP", "KR"],
             "financial": 9.0, "political": 25, "social": 10,
             "axis": {"pension_spend": 9.0}},
            {"id": "re_generous", "label": "Generous earnings-related, early retirement",
             "detail": "A high replacement rate and a low pension age.",
             "countries": ["FR"], "financial": 14.0, "political": 45, "social": 15,
             "axis": {"pension_spend": 14.0}},
        ],
    },
]
