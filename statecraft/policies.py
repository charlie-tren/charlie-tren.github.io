"""The thirteen domains and their options.

Most options are something a real country actually does. That constraint is what
stops the menu being one-sided: the original spec's list was almost entirely
interventionist, which would have collapsed every visitor onto Denmark and killed
the reveal.

WHO HOLDS AN OPTION IS THE `choices` MATRIX IN countries.py, and it is the only
record of that. `build_data.holders` reads it, and everything downstream reads
holders: the derived axis medians, the reveal's "Also the policy in ...", the
slider caption in app.js and `yourCountries` in match.js.

There used to be a second answer. Every option carried a `countries` tag list,
hand-written, and four of those surfaces read it instead. It was written when the
matrix held twenty countries and never extended as the matrix reached forty-five,
so by 02/09/2026 it named 190 of the 585 matrix cells. Every tag in it was still
TRUE, which is why nothing ever failed and why the test guarding it passed every
day of that year: it could catch a wrong tag and never a missing one. The lists
were deleted rather than repaired, because a hand-maintained copy of the matrix
goes stale again the moment somebody codes a country and forgets.

FIVE OPTIONS ARE HELD BY NOBODY, on purpose. Universal basic income, absolute
freedom of speech, banning private combustion cars and an age cap on
representatives are all things a visitor should be able to choose and no country
has. The reveal says so in as many words, and `test_the_menu_stays_grounded`
holds that share down so the page cannot drift into a wishlist.

COSTS ARE SUBJECTIVE AND THE PAGE SAYS SO. They are published in full in the
method section, as on DCF Studio and One Story, so a reader who disagrees can
see exactly what they disagree with.

  financial  % of GDP. Only on non-tax options. Drawn down from the revenue the
             tax rate raises.
  rate       % of GDP. Only on tax options. The HEADLINE tax take that option
             represents, which is where the tax slider sits when it lands on
             that option. It is not the money the state gets: budget.js runs it
             through a concave realisation curve first, and adds the country's
             non-tax revenue. See the calibration block in budget.js.
  political  points out of 100. Institutional capital: constitutional change,
             entrenched interests, electoral risk.
  social     points out of 100. Cohesion and personal-freedom cost, and the
             friction the policy creates.

POLITICAL IS WHAT IT COSTS TO ENACT AND SOCIAL IS WHAT IT COSTS TO LIVE WITH,
and the two routinely move in OPPOSITE directions. That reading was applied
across the file on 2026-08-29 and it changed thirty-five numbers, each annotated
where it sits. Before it, political and social were near-perfectly correlated:
every domain priced its moderate consensus option lowest on both, which made the
three budgets one budget, turned each domain into a ladder, and left 73 of the
options strictly dominated. A visitor with a calculator would have picked the
same centrist package thirteen times and the reveal would have sorted almost
everyone onto the same handful of countries.

The correlation was an artefact of scoring familiarity rather than cost. Many
policies are hard to pass and pleasant to live under: a clean grid, a pension
that abolishes old-age poverty, near-universal home ownership. Many are easy to
pass and unpleasant to live under: doing nothing about pollution, restricting
speech, tough-on-crime sentencing. The do-nothing options were the worst of it,
priced as free on every budget when inaction has real costs that simply do not
appear on a ledger. `test_no_option_is_strictly_dominated` is the check that
holds this open, and it caps the count at six rather than zero because a genuine
outlier is allowed. Two remain, both on `en_car_free`, and the reason is in the
comment beside it.

`axis` is the value this option implies on its domain's axis, in that axis's own
unit. IT IS A FALLBACK: build_data.py overwrites the domain's own axis with the
median of the countries the matrix says hold the option, and the hand value
survives only where no holder has a measurement. It is still emitted, as
`axis_hand`. An option may also contribute to `redistribution`, which is summed
across the tax, work and family choices and stays a hand value throughout.
"""

DOMAINS = [
    {
        "id": "tax",
        "name": "Tax and Redistribution",
        "axis": "tax_take",
        "options": [
            # REVENUE AND TAX TAKE ARE DIFFERENT THINGS FOR A RESOURCE STATE.
            # This option carried a `revenue` of 16.0, which was a tax take; on
            # 2026-08-30 that was raised to 27.8, which is general government
            # revenue; and on the SAME DAY the field was split in two, which is
            # what it should have been from the start.
            #
            # A state's income is tax PLUS non-tax income, and one number cannot
            # be both. `rate` is now the headline TAX take only, back at 16.0,
            # and the 11.8 points of hydrocarbon and investment income that make
            # up the difference live on the UAE's own row in countries.py as
            # `nonTaxRevenue`, because they are a fact about the country a
            # visitor starts from and not about the tax policy they choose. A
            # visitor who moves the UAE to a Nordic tax rate keeps the oil.
            # Modelling it as tax meant they lost it, which was never right.
            #
            # The sourcing below is what fixes 27.8, and 27.8 less a 16.0 tax
            # take is where the 11.8 comes from.
            #
            # IMF general government revenue for the UAE is 27.8% of GDP in 2024.
            # https://www.imf.org/external/datamapper/rev@FPP/ARE
            # (machine-readable at /external/datamapper/api/v1/rev/ARE)
            # Checked 2026-08-30. Cross-checked twice, because the fault being
            # fixed here is a plausible number on the wrong basis and a second
            # plausible number would not have caught it:
            #   - the same dataset's expenditure series reads 21.4% for 2024, and
            #     27.8 less 21.4 is the 6.4% of GDP general government surplus the
            #     2025 Article IV states for 2024, so this is the series the
            #     Article IV reports from.
            #   - CBUAE's Quarterly Economic Review puts general government
            #     revenue at 26.9% of GDP in H1 2024. Different institution, same
            #     neighbourhood.
            # For contrast, the World Bank's GC.REV.XGRT.GD.ZS reads 3.0% for the
            # UAE in 2024 because it is FEDERAL government only, which is the same
            # wrong-basis trap tax_take itself was moved off.
            #
            # THE AXIS VALUE AND THE RATE NOW AGREE, at 16.0, and that is the
            # point of the split rather than a coincidence. The tax_take axis is
            # total TAX revenue as a share of GDP on an OECD Revenue Statistics
            # / IMF basis, and for the UAE that is genuinely low: 5% VAT since
            # 2018 and 9% corporate tax since 2023, against bounds of (10, 60).
            # The 11.8 points that used to sit in this field, and made the two
            # disagree, are non-tax revenue and are recorded as such. AE carries
            # no measured tax_take cell, so this hand value is what the page
            # plots.
            {"id": "tax_minimal", "label": "Minimal state",
             "detail": "No income tax. Revenue from resources and consumption.", "rate": 16.0, "political": 25, "social": 20,
             "axis": {"tax_take": 16.0, "redistribution": 0.01}},
            # EE verified 2026-08-29: still a genuine flat rate, 22% for 2026. The
            # legislated rise to 24% was reversed in December 2025, and the
            # income-dependent "tax hump" in the basic exemption was abolished from
            # 2026, so it is flatter now than it was.
            # https://www.ey.com/en_ee/insights/tax/significant-tax-changes-in-estonia-in-2025-2026
            {"id": "tax_flat", "label": "Flat income tax",
             "detail": "One rate on all income, few deductions.", "rate": 33.0, "political": 30, "social": 15,
             "axis": {"tax_take": 33.0, "redistribution": 0.08}},
            {"id": "tax_anglo", "label": "Moderate progressive",
             "detail": "Progressive rates, a middling take, broad exemptions.",
             "rate": 34.0, "political": 10, "social": 8,
             "axis": {"tax_take": 34.0, "redistribution": 0.11}},
            {"id": "tax_continental", "label": "High, funded by payroll",
             "detail": "Heavy social contributions on wages alongside income tax.", "rate": 43.0, "political": 25, "social": 20,
             "axis": {"tax_take": 43.0, "redistribution": 0.18}},
            {"id": "tax_nordic", "label": "Nordic take",
             "detail": "High broad-based income tax and a high VAT.", "rate": 46.0, "political": 40, "social": 30,
             "axis": {"tax_take": 46.0, "redistribution": 0.24}},
            # Untagged on purpose. Exit taxes on unrealised gains are real, in
            # Norway and the US among others, but no country runs one as a headline
            # revenue regime that pays for immigration, so there is nothing to tag
            # it to and the reveal says "which no country does". Cut once during
            # Task 2 for failing a test that required a tag; the TEST was the thing
            # that was wrong, since four more untagged options land in Tasks 3 and 4
            # and they are the aspirational half of the menu.
            {"id": "tax_departure", "label": "Nordic take plus a departure tax",
             "detail": "A high broad-based take, and residents pay to leave, subsidising arrivals.", "rate": 47.0, "political": 60, "social": 55,
             "axis": {"tax_take": 47.0, "redistribution": 0.25}},
        ],
    },
    {
        "id": "healthcare",
        "name": "Healthcare",
        "axis": "health_public",
        "options": [
            {"id": "hc_private", "label": "Private, employer-led",
             "detail": "Insurance through work, a safety net for the old and poor.", "financial": 8.5, "political": 15, "social": 30,
             "axis": {"health_public": 50.0}},
            {"id": "hc_savings", "label": "Compulsory medical savings",
             "detail": "Everyone saves into their own account and is charged at the point of use.", "financial": 2.5, "political": 55, "social": 35,
             "axis": {"health_public": 45.0}},
            {"id": "hc_insurance", "label": "Mandatory insurance, regulated market",
             "detail": "Everyone must buy cover; insurers may not refuse anyone.",
             "financial": 7.5, "political": 30, "social": 15,
             "axis": {"health_public": 78.0}},
            # WHAT SEPARATES THIS OPTION FROM hc_public, settled 02/09/2026. It used
            # to be nothing. Both options described a universal service, both sets of
            # holders had a private sector beside it, and the split between them had no
            # stated rule: the UK, Spain and Malta sat on hc_public while Denmark,
            # Sweden, Norway, Canada and six others ran the same kind of service and sat
            # here. The measurements agreed there was no difference, medians of 73.2 and
            # 77.15 on a track from 29 to 92.
            #
            # The rule is now whether the state SUPPORTS the private tier or merely
            # tolerates it. hc_mixed means the state pays people to hold duplicate
            # private cover or penalises them for going without: a premium rebate, tax
            # relief on premiums, a surcharge on non-holders, a mandate to buy, or an
            # explicit opt-out into a state-funded private scheme. hc_public means it
            # does none of those, and may restrict duplicate cover outright.
            #
            # Australia is the anchor here, with a rebate and the Medicare Levy
            # Surcharge running at once. Canada is the anchor for hc_public, where six
            # provinces prohibit duplicate insurance. Ten cells moved on the rule and
            # every one carries its mechanism in countries.py.
            #
            # Social raised from 10 on 2026-08-29. A universal service with a paid fast
            # lane sorts patients by what they can pay at the moment they are least able
            # to shop, and that resentment is a real cohesion cost. Pricing it as the
            # least divisive option here made it dominate every other healthcare choice
            # on all three budgets at once.
            #
            # THE COSTS WERE RE-EXAMINED 02/09/2026 UNDER THE NEW RULE AND KEPT. The
            # question was whether 7.0 / 20 / 22 still reads, now that the option means
            # a subsidised tier rather than merely a tolerated one. It reads better than
            # it did. Financial 7.0 against hc_public's 9.0 is the point of the policy:
            # a rebate costs money but buys the state out of some of the demand, and
            # every holder here spends less publicly than the UK does. Political 20
            # against 45 is right because subsidising insurance is the easy sell and
            # abolishing the private tier is the hard one. Social 22 against 12 is the
            # one carrying the most weight, and it is the honest direction: a state that
            # pays some people to jump the queue has chosen to sort patients by money,
            # where a state that merely permits it has only failed to stop it.
            {"id": "hc_mixed", "label": "Public with a subsidised private tier",
             "detail": "Universal public cover, and the state pays you to take private "
                       "insurance on top of it, or taxes you for going without.",
             "financial": 7.0, "political": 20, "social": 22,
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
            # Social cut from 25. One service everyone uses, with the rich and the poor in
            # the same queue, is the least socially divisive arrangement in the domain.
            # What it costs is money and political capital, not cohesion.
            # Detail rewritten 02/09/2026 to state the rule above rather than imply it.
            # "A private sector exists alongside it, unsubsidised" was already the right
            # test and was too quiet to code against: eleven holders now turn on that
            # clause, so it says what it means. "Free at the point of use" came out
            # because it was never the test and was false of several holders anyway.
            # The hand axis value below is not what the page plots, since build_data
            # derives every non-tax axis from the median of the holders, so the ONS
            # figure that set it now documents one country of eleven rather than the
            # option. Left as it stands rather than restated as a median that would go
            # stale the next time a cell moves.
            {"id": "hc_public", "label": "Tax-funded national service",
             "detail": "One service for everyone, paid for out of general taxation. A private "
                       "sector may exist beside it, but the state gives it nothing and may bar "
                       "it from duplicating public cover.", "financial": 9.0, "political": 45, "social": 12,
             "axis": {"health_public": 81.3}},
        ],
    },
    {
        "id": "education",
        "name": "Education",
        "axis": "tertiary_public",
        # THE FIVE HAND VALUES BELOW ARE ON A NEW SCALE from 02/09/2026. The axis
        # was education_spend, public education spend across all levels as a
        # share of GDP, and it is now tertiary_public, the general government
        # share of expenditure on tertiary institutions after transfers, in per
        # cent. The old values ran 4.2 to 6.3 and would read as almost no public
        # funding at all on a percentage-share track, so every one of them was
        # rewritten as a judgement of what share of the university bill that
        # option's government picks up.
        #
        # THEY ARE FALLBACKS AND NOTHING ELSE. build_data.py derives an option's
        # plotted value from the median of the countries that hold it, so a hand
        # value only reaches the page where no holder has a measurement. Of the
        # five, only ed_free_selective is in that position, because the Canada
        # recode left it with no holders at all.
        "options": [
            {"id": "ed_market", "label": "Fees at every level past school",
             "detail": "Universities set their own prices. Loans, not grants.",
             "financial": 4.2, "political": 10, "social": 25,
             # A fee market still leaves the state paying for research, capital
             # and a good deal of undergraduate teaching, so under half rather
             # than nothing. Holders measure 47.29.
             "axis": {"tertiary_public": 45.0}},
            # Social raised from 12. Deferred fees hand young adults a debt that follows
            # them for decades and shapes when they can buy a house or start a family.
            # That was priced at almost nothing.
            {"id": "ed_deferred", "label": "Free at school, deferred fees after",
             "detail": "Tertiary costs are paid back through the tax system once you earn.", "financial": 4.8, "political": 20, "social": 22,
             # THE LOWEST OF THE FIVE, which is not a mistake. On the
             # after-transfers convention a loan the state advances and the
             # student repays is the student's money, so a deferred-fee system
             # books more of the bill to households than an ordinary fee market
             # does. Holders measure 33.95.
             "axis": {"tertiary_public": 35.0}},
            {"id": "ed_vocational", "label": "Free, with an early vocational track",
             "detail": "Free through university, and most students stream into apprenticeships.", "financial": 5.0, "political": 35, "social": 20,
             # THE HIGHEST OF THE FIVE. Free tuition and a publicly funded
             # apprenticeship system beside it, with a smaller fee-paying
             # foreign intake than the free-tuition group carries. Holders
             # measure 81.61.
             "axis": {"tertiary_public": 82.0}},
            {"id": "ed_free", "label": "Free through university",
             "detail": "No tuition at any level, and a maintenance grant while studying.",
             "financial": 6.3, "political": 35, "social": 10,
             # No tuition means the state is close to the whole bill, short of
             # what private and international students pay in. Holders measure
             # 77.45, held down by Cyprus, Israel, Portugal and Ireland.
             "axis": {"tertiary_public": 80.0}},
            # Financial cut from 5.4. Free tuition behind a hard selection filter educates
            # far fewer people to the level that costs money, so it is genuinely the
            # cheapest of the five rather than the middle. Its price is the 45 political
            # and the 40 social of sorting children by examination.
            # EMPTIED BY THE CANADA RECODE OF 02/09/2026 AND KEPT ANYWAY. Canada
            # was its only holder and was moved to ed_market, because Canadian
            # universities charge about CAD 7,734 a year and nothing in Canada
            # selects at twelve. DO NOT DELETE THIS OPTION. The URL encodes an
            # education choice by its position in this list, so removing an
            # option renumbers every option after it and silently changes the
            # policy behind every shared link. It joins UBI, absolute free
            # speech, the car ban and the age cap as an option no country holds,
            # which the reveal already says in as many words.
            #
            # A LATER PASS SHOULD ASK WHETHER THE MENU NEEDS BOTH THIS AND
            # ed_vocational. "Free, and selective from twelve" and "Free, with an
            # early vocational track" are the same policy read two ways: the
            # countries that stream children early are exactly the countries that
            # sort them by examination, and all nine of them sit in ed_vocational.
            # Nothing in the file distinguishes the two beyond which sentence was
            # written first. Merging them is a menu change and a URL change at
            # once, so it is a decision rather than a tidy-up.
            {"id": "ed_free_selective", "label": "Free, and selective from twelve",
             "detail": "No tuition, and an exam at twelve decides which school you attend.", "financial": 4.0, "political": 45, "social": 40,
             # THE ONLY ONE OF THE FIVE THAT REACHES THE PAGE. Canada was the
             # sole holder and was recoded to ed_market on 02/09/2026, so this
             # option has no countries and no median, and this number is what
             # gets plotted. Free tuition behind a hard selection filter puts
             # the state on the whole teaching bill for a smaller cohort, so it
             # sits with the free options rather than between them and the fee
             # ones.
             "axis": {"tertiary_public": 80.0}},
        ],
    },
    {
        "id": "housing",
        "name": "Housing",
        "axis": "social_housing",
        "options": [
            {"id": "ho_market", "label": "Private market, no state role",
             "detail": "Housing is built and owned privately. The state zones and nothing else.",
             "financial": 0.3, "political": 5, "social": 30,
             "axis": {"social_housing": 4.0}},
            # Social raised from 15. Demand-side help is capitalised into prices, so it
            # lifts the price for everyone who does not qualify. That is the best
            # documented cost in the domain and it was not in the number.
            {"id": "ho_subsidy", "label": "Private market with rent support",
             "detail": "Cash help with rent rather than housing built by the state.",
             # SE moved here from ho_cooperative 2026-08-29. OECD PH4.2 excludes
             # Sweden from the social rental housing indicator outright, because
             # municipal housing company rents "are not set at below-market levels
             # and are thus not considered as social housing in this indicator".
             # Sveriges Allmannytta puts allmannyttan at just under 20% of the
             # stock, but it is let at market rent and is open to everyone, so it
             # is not a below-market non-profit sector. Sweden's redistributive
             # housing instrument is the cash allowance (bostadsbidrag, and
             # bostadstillagg for pensioners), which is exactly this option. Not
             # ho_market, because rents are regulated on the bruksvarde system and
             # a fifth of the stock is municipally owned.
             # https://www.oecd.org/content/dam/oecd/en/data/datasets/affordable-housing-database/ph4-2-social-rental-housing-stock.pdf
             # https://www.sverigesallmannytta.se/in-english/public-housing-in-sweden/
             "financial": 1.2, "political": 15, "social": 25,
             "axis": {"social_housing": 12.0}},
            {"id": "ho_cooperative", "label": "Co-operative and non-profit rental",
             "detail": "A large regulated rental sector run by non-profits, alongside a private market.", "financial": 1.6, "political": 35, "social": 15,
             "axis": {"social_housing": 22.0}},
            # NL verified 2026-08-29 and the figure cut. OECD PH4.2 groups the
            # Netherlands with Austria and Denmark at "over 20% of the total housing
            # stock", and names the Netherlands as one of the three countries whose
            # sector shrank by more than 2 percentage points over the decade. The
            # Dutch government's own figure is 29%. The axis read 34.0 and the detail
            # said "a third of the stock"; both are now 29%.
            # https://www.oecd.org/content/dam/oecd/en/data/datasets/affordable-housing-database/ph4-2-social-rental-housing-stock.pdf
            # https://www.government.nl/topics/housing/rented-housing
            # Social cut from 20. Dutch associations let to a broad income mix rather than
            # a residual poor, which is exactly what stops a large social sector becoming
            # an estate problem. The cost is the 45 political of building it.
            {"id": "ho_social", "label": "Large social rental sector",
             "detail": "Non-profit housing associations own close to 29% of the stock "
                       "and let it below market rent.", "financial": 2.0, "political": 45, "social": 12,
             "axis": {"social_housing": 29.0}},
            # SG verified 2026-08-29: about 78% of the resident population lives in
            # HDB flats, and roughly nine in ten of those households own their flat
            # on a 99-year lease. Tag and label both survive.
            # https://www.statista.com/statistics/966747/population-living-in-public-housing-singapore/
            #
            # THE AXIS VALUE WAS 78.0 AND IT WAS ON THE WRONG BASIS, corrected
            # 2026-08-29. 78 is the share of the resident population LIVING in HDB
            # housing. The social_housing axis measures social RENTAL stock as a
            # share of all dwellings, per OECD PH4.2, and its bounds are (0, 38),
            # so a marker at 78 would have been clamped to the far edge and read as
            # a fact. Same fault as the tax_take one already fixed, where the World
            # Bank series measured central government revenue while the options
            # were written on the OECD total-tax basis: the fix is to put both
            # sides on one basis.
            #
            # On the PH4.2 basis: HDB rental flats under management were 63,558 as
            # at 31 March 2025 (HDB Key Statistics 2024/2025, Residential
            # Properties, Rental Flats total), against 1,623,242 total residential
            # dwelling units as at end-June 2025 (SingStat via data.gov.sg,
            # Residential Dwellings). 63,558 / 1,623,242 = 3.9%.
            # https://www.hdb.gov.sg/-/media/hdb-pulse/reports/annual-reports-and-financial-statements/HDB_Key-Statistics-2025.pdf
            # https://data.gov.sg/datasets/d_6c58a523a05b55836f383fa2a68d332d/view
            #
            # THE CONSEQUENCE IS THE INTERESTING PART, not a defect: on this axis
            # the Singapore model correctly reads LOW, near Australia's 3.2%,
            # because its flats are sold rather than let. A country can house
            # almost everyone through the state and still hold almost no social
            # rental stock. That is the whole point of the policy.
            # Social cut from 35. A country where nearly everyone owns their home has the
            # least housing-driven inequality in the set. This model's cost is political,
            # and it is already priced at 70: compulsory land acquisition and a forced
            # savings scheme.
            {"id": "ho_singapore", "label": "State-built flats, sold to residents",
             "detail": "The state builds most housing and sells it on long leases. Most people own.", "financial": 2.4, "political": 70, "social": 10,
             "axis": {"social_housing": 3.9}},
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
             # AE removed 2026-08-29 and moved to re_generous. There are no
             # mandatory individual accounts in the UAE. GPSSA is a contributory
             # pay-as-you-go defined-benefit scheme.
             "financial": 3.0, "political": 55, "social": 30,
             "axis": {"pension_spend": 3.0}},
            {"id": "re_super", "label": "Means-tested pension plus mandatory saving",
             "detail": "A state pension for those who need it, and compulsory employer contributions.",
             "financial": 5.0, "political": 40, "social": 15,
             "axis": {"pension_spend": 5.0}},
            {"id": "re_flat", "label": "Flat state pension, saving voluntary",
             "detail": "The same modest pension for everyone. Private saving is encouraged, not required.", "financial": 6.5, "political": 15, "social": 12,
             "axis": {"pension_spend": 6.5}},
            {"id": "re_earnings", "label": "Earnings-related state pension",
             "detail": "What the state pays you depends on what you earned.",
             "financial": 9.0, "political": 25, "social": 10,
             "axis": {"pension_spend": 9.0}},
            # Social cut from 15. A pension generous enough to hold every retiree near the
            # working-age median abolishes old-age poverty, which is the lowest cohesion
            # cost in the domain. What it costs is the 14.0% of GDP and the political
            # capital to keep it there.
            {"id": "re_generous", "label": "Generous earnings-related, early retirement",
             "detail": "A high replacement rate and a low pension age.",
             # AE added 2026-08-29. GPSSA pays 60% of the last five years' average
             # contribution salary at 15 years of service, rising 2% a year to a
             # cap of 100% at 35 years, with a pension age of 60 and a resignation
             # pension from 50 after 20 years. A 100% ceiling and a pension at 60
             # is a higher replacement rate and a lower age than France, so this is
             # the tighter of the two earnings-related options.
             # https://www.gpssa.gov.ae/pages/en/help/faq/what-retirement-age-and-what-are-pension-entitlement-conditions-once-retired
             # https://u.ae/en/information-and-services/jobs/working-in-uae-government-sector/pensions-and-social-security-for-uae-citizens
             # CAVEAT the reveal must carry: GPSSA covers Emirati and GCC nationals
             # only, who are roughly an eighth of the residents. Everyone else gets
             # an end-of-service gratuity and no pension at all. None of the five
             # options describes that, so this cell describes the citizen system.
             "financial": 14.0, "political": 45, "social": 8,
             "axis": {"pension_spend": 14.0}},
        ],
    },
    {
        "id": "energy",
        "name": "Transport and Energy",
        "axis": "grid_carbon",
        "options": [
            # Social raised from 10. An unpriced fossil grid with roads as the transport
            # plan carries the domain's largest local health burden. Pricing pollution at
            # nothing made doing nothing cheaper than every alternative on all three
            # budgets, which is the worst incentive the page could hand a visitor.
            {"id": "en_fossil", "label": "Cheap fossil power, cars assumed",
             "detail": "No carbon price. Roads are the transport plan.", "financial": 0.4, "political": 5, "social": 40,
             "axis": {"grid_carbon": 480.0}},
            # NL, JP, SG and KR moved here 2026-08-29, three of them from en_hydro
            # and Korea from en_nuclear. All four price emissions and none of them
            # has the clean grid en_hydro claims: NL 253.6, KR 417.1, JP 477.3 and
            # SG 497.1 g/kWh against 28 to 58 for the four that stayed.
            #   NL  EU ETS plus a national CO2 levy on industry since 2021, a floor
            #       of EUR 87.90/t in 2025 against an EU ETS price of EUR 66.76.
            #       https://www.pwc.nl/en/insights-and-publications/tax-news/pwc-special-budget-day/taxplan-2021-co-2-levy.html
            #   SG  carbon tax since 2019, raised five-fold to S$25/t in 2024 and
            #       legislated to S$45/t for 2026 to 2027, covering the facilities
            #       responsible for about 80% of national emissions.
            #       https://www.nccs.gov.sg/singapores-climate-action/mitigation-efforts/carbontax/
            #   JP  a carbon tax since 2012, low at JPY 289/t, and the GX-ETS became
            #       mandatory for emitters above 100kt on 1 April 2026.
            #       https://icapcarbonaction.com/en/ets/japan-gx-ets
            #   KR  the K-ETS has priced emissions since 2015 and covered 77.75% of
            #       national greenhouse gases in 2023.
            #       https://icapcarbonaction.com/en/ets/korea-emissions-trading-system-k-ets
            # KNOWN WIDE, and reported by check_spread.py as such: this option names
            # an instrument and the axis measures an outcome, so a priced grid that
            # burns oil shale (EE 319) sits beside one that burns almost nothing
            # (NZ 93). Same shape as vo_fptp. Pricing carbon is not the same claim
            # as having decarbonised.
            {"id": "en_carbon_tax", "label": "Carbon tax, private cars kept",
             "detail": "Emissions are priced. People still drive.",
             "financial": 0.6, "political": 35, "social": 25,
             "axis": {"grid_carbon": 180.0}},
            # KR removed 2026-08-29. Nuclear is Korea's largest single source but
            # not most of its power: on provisional January to November 2025 figures
            # nuclear was 169.3 TWh (31.1%) against coal 157.9 TWh and LNG 148.5 TWh,
            # so fossil generation is about 56% between them. "Most power from
            # reactors" is only true of France, whose grid is 41.4 g/kWh against
            # Korea's 417.1.
            # https://ember-energy.org/latest-updates/fossil-fuels-fall-below-50-of-south-koreas-electricity-for-the-first-month-on-record/
            # Social cut from 30. A reactor fleet is the lowest-emitting firm supply in the
            # set and imposes no local air-quality burden at all. The friction is siting
            # and public fear, and that is already the 70 political.
            {"id": "en_nuclear", "label": "Nuclear baseload",
             "detail": "Most power from reactors the state builds and guarantees.", "financial": 2.2, "political": 70, "social": 20,
             "axis": {"grid_carbon": 60.0}},
            # JP, NL and SG removed 2026-08-29. This option makes two claims and
            # they were being treated as one: a clean grid AND a transport network
            # good enough to skip a car. All three had the second and none had the
            # first. Singapore's grid is overwhelmingly gas and Japan's has been
            # coal and gas heavy since Fukushima. The four that remain are 28.1 to
            # 57.5 g/kWh, which is what the option says.
            {"id": "en_hydro", "label": "Renewables and heavy public transport",
             "detail": "A clean grid, and a network good enough that a car is optional.",
             "financial": 2.4, "political": 45, "social": 20,
             "axis": {"grid_carbon": 45.0}},
            # Financial cut from 3.2. The option's own instruments, fuel excise, stamp duty
            # and an annual road fee, are revenue collected against the tram and rail
            # build, so the net draw on the budget is well below the gross cost of the
            # network. It is STILL dominated by the two cheapest energy options on all
            # three budgets, and that is left alone: it is the one thing in this domain
            # nobody does, and it is dearer than doing nothing in every currency the page
            # counts. See test_no_option_is_strictly_dominated.
            {"id": "en_car_free", "label": "Private combustion cars banned",
             "detail": "Trams and rail carry everyone. Fuel excise, stamp duty and an annual fee price the rest off the road.", "financial": 1.8, "political": 85, "social": 80,
             "axis": {"grid_carbon": 30.0}},
            # RELABELLED 02/09/2026. It read "Clean grid and a deposit-return
            # scheme", and its detail opened "A clean grid and good rail". Germany
            # is the only country coded to it and Germany's grid is 329.7 g/kWh,
            # which is the second dirtiest of the six options here and well above
            # en_carbon_tax at 217.4. So the page told a visitor who picked a clean
            # grid that their grid carbon was 330.
            #
            # The hand value of 55.0 is what hid it: it agreed with the label, and
            # nothing compared the label to the country. It is kept below, as every
            # hand value is, because the gap between 55 and 330 is the record of
            # the mistake.
            #
            # The label lost the limb that was false. The deposit-return scheme and
            # the rail are real and are what separates this from a carbon tax; the
            # clean grid was aspiration written as description.
            {"id": "en_deposit", "label": "Deposit returns and good rail, cars kept",
             "detail": "Dense rail, every container carries a refundable deposit, and cars are still allowed. The grid is still coming off coal.", "financial": 2.6, "political": 40, "social": 18,
             "axis": {"grid_carbon": 55.0}},
        ],
    },
    {
        "id": "speech",
        "name": "Speech and Information",
        "axis": "expression",
        "options": [
            {"id": "sp_absolute", "label": "Absolute freedom of speech",
             "detail": "No legal limit on what may be said, including hatred and defamation.", "financial": 0.0, "political": 60, "social": 65,
             "axis": {"expression": 0.97}},
            # Political cut from 25. A near-absolute protection is one constitutional
            # clause and, once written, needs no standing apparatus to enforce. What it
            # costs is living with what it permits, which is the 30 social.
            {"id": "sp_first_amendment", "label": "Near-absolute, narrow exceptions",
             "detail": "Speech is protected except for incitement and a short list of harms.", "financial": 0.1, "political": 14, "social": 30,
             "axis": {"expression": 0.93}},
            # KR and JP moved here from sp_order 2026-08-29. Both sit above several
            # countries already on this option on the measured axis, so putting them
            # a bucket below was a claim the data will not carry: KR 0.933 is level
            # with CA 0.933, and JP 0.847 is above UK 0.833 and IL 0.822.
            #   KR  no public-order speech regime of the Singaporean kind. What
            #       Korea has is criminal defamation (up to 2 years, 5 for false
            #       statements) and criminal insult (up to 1 year), which is a
            #       limit on speech attacking a person or group.
            #       https://futurefreespeech.org/south-korea/
            #   JP  the borderline case, and the weaker of the two fits, so the
            #       caveat is recorded rather than smoothed over. The 2016 Hate
            #       Speech Elimination Act condemns group-directed speech but sets
            #       no penalty, so the crime doing the work is the Penal Code
            #       insult offence, raised in 2022 from 30 days detention to up to
            #       a year, plus local ordinances such as Kawasaki's.
            #       https://www.loc.gov/item/global-legal-monitor/2016-08-31/japan-new-act-targets-hate-speech-against-persons-from-outside-japan/
            #       https://monolith.law/en/general-corporate/contempt-severe-punishment
            {"id": "sp_hate_limits", "label": "Free, with hate-speech limits",
             "detail": "Broad protection, and speech attacking a group is a crime.",
             "financial": 0.2, "political": 15, "social": 15,
             "axis": {"expression": 0.88}},
            # Singapore alone from 2026-08-29. It is the only one of the twenty with
            # a standing public-order speech regime, and at 0.40 it is 0.45 clear of
            # the next country in the set.
            # Political cut from 30. Public-order limits need no constitutional
            # entrenchment and no institution to defend them. A legislature can pass them
            # in a session, which is precisely why they spread. The cost is social.
            {"id": "sp_order", "label": "Limited where it threatens public order",
             "detail": "Speech that the state judges divisive or destabilising is restricted.", "financial": 0.2, "political": 12, "social": 45,
             "axis": {"expression": 0.62}},
            # Political cut from 45 and social raised from 70. State control of speech is
            # the cheapest thing in this domain to impose, because it removes the
            # institution that would resist it, and by a distance the most expensive to
            # live under. Pricing it as dear on both made it a choice nobody could reach.
            {"id": "sp_restricted", "label": "State-controlled",
             "detail": "Criticism of the state and its rulers is prosecuted.", "financial": 0.3, "political": 8, "social": 85,
             "axis": {"expression": 0.20}},
        ],
    },
    {
        "id": "voting",
        "name": "Voting and Representation",
        "axis": "disproportionality",
        "options": [
            {"id": "vo_none", "label": "No competitive national elections",
             "detail": "Rulers are not chosen at the ballot box.", "financial": 0.0, "political": 90, "social": 80,
             "axis": {"disproportionality": None}},
            # Social raised from 10. This option's own axis value is the evidence: the UK
            # sits at 23.64 on the Gallagher index, the highest in the set. A system that
            # regularly seats a government most people voted against carries a real
            # legitimacy cost, and it was priced as the least costly system here.
            {"id": "vo_fptp", "label": "First past the post, voluntary",
             "detail": "One member per seat, most votes wins, turnout is up to you.", "financial": 0.1, "political": 10, "social": 38,
             "axis": {"disproportionality": 14.0}},
            {"id": "vo_preferential", "label": "Preferential and compulsory",
             "detail": "You rank the candidates, and voting is a legal duty.", "financial": 0.2, "political": 40, "social": 25,
             "axis": {"disproportionality": 9.0}},
            {"id": "vo_proportional", "label": "Proportional, voluntary",
             "detail": "Seats match the national vote share. Coalitions are normal.",
             "financial": 0.2, "political": 45, "social": 15,
             "axis": {"disproportionality": 3.0}},
            # Social cut from 25. A law any citizen can put to a public vote is the hardest
            # in the set to call imposed. The cost is the political capital to build the
            # machinery and then live with it, which is the 70.
            {"id": "vo_direct", "label": "Proportional plus binding referendums",
             "detail": "Any law can be put to a public vote by petition.", "financial": 0.4, "political": 70, "social": 10,
             "axis": {"disproportionality": 2.5}},
            # Financial cut from 0.2. An age cap is a line in the electoral act. It is the
            # cheapest thing in this file to administer, and the whole cost is the 75
            # political of disqualifying people by birthdate.
            {"id": "vo_age_cap", "label": "Proportional, with an age cap on representatives",
             "detail": "Seats match the vote, and nobody may stand past a fixed age.", "financial": 0.05, "political": 75, "social": 35,
             "axis": {"disproportionality": 3.0}},
        ],
    },
    {
        "id": "work",
        "name": "Work and Welfare",
        "axis": "bargaining",
        "options": [
            {"id": "wo_at_will", "label": "At-will employment, thin welfare",
             "detail": "Easy to hire and fire. Unemployment help is short and conditional.", "financial": 0.8, "political": 10, "social": 30,
             "axis": {"bargaining": 12.0, "redistribution": 0.01}},
            # Social raised from 15. A wage floor with no collective voice leaves the pay
            # dispersion and the in-work poverty that the sector-bargaining countries do
            # not have. It was priced as the least frictional option in the domain.
            {"id": "wo_minimum", "label": "Statutory minimums, weak unions",
             "detail": "The law sets a wage floor and leave. Bargaining is mostly individual.",
             "financial": 1.4, "political": 20, "social": 26,
             "axis": {"bargaining": 28.0, "redistribution": 0.03}},
            {"id": "wo_bargaining", "label": "Sector-wide bargaining",
             "detail": "Unions and employers set pay across a whole industry, members or not.",
             # NO removed 2026-08-29: Norway sits on wo_transparency, which is sector
             # bargaining PLUS the skattelister, and is the more specific claim.
             "financial": 1.8, "political": 45, "social": 20,
             "axis": {"bargaining": 80.0, "redistribution": 0.06}},
            # Social cut from 20. Six weeks guaranteed and twelve public holidays is the
            # lowest-friction thing here to live under. Its cost is the money and the 55
            # political of legislating it over employers.
            {"id": "wo_mandated_leave", "label": "Sector bargaining, six weeks leave",
             "detail": "Industry-wide pay deals, and the law guarantees six weeks paid leave and twelve public holidays.", "financial": 2.2, "political": 55, "social": 12,
             "axis": {"bargaining": 90.0, "redistribution": 0.07}},
            # Social cut from 45. An unconditional payment removes the means test, the
            # stigma and the poverty trap, which are the cohesion costs every other option
            # in this domain carries. What UBI costs is money and political capital, and
            # both are already the highest in the file at 9.0 and 80.
            {"id": "wo_ubi", "label": "Universal basic income",
             "detail": "Every adult gets an unconditional payment. Most other benefits fold into it.", "financial": 9.0, "political": 80, "social": 10,
             "axis": {"bargaining": 40.0, "redistribution": 0.14}},
            # Social cut from 55. Norway has published tax returns for over a century and
            # it is unremarkable there; open pay narrows the gaps that drive workplace
            # resentment. The cost is the privacy friction and the 60 political.
            {"id": "wo_transparency", "label": "Sector bargaining, every salary public",
             "detail": "Industry-wide pay deals, and any salary can be looked up. The viewee sees who looked.", "financial": 1.9, "political": 60, "social": 18,
             "axis": {"bargaining": 80.0, "redistribution": 0.07}},
        ],
    },
    {
        "id": "defence",
        "name": "Defence",
        "axis": "military_burden",
        "options": [
            {"id": "de_neutral", "label": "Neutral, small professional force",
             "detail": "No alliance, no conscription, a force sized for the border only.", "financial": 0.7, "political": 35, "social": 10,
             "axis": {"military_burden": 0.7}},
            # AU queried and KEPT 2026-08-29. The option says "an alliance", not
            # NATO, and it already carries NZ, JP and CL, none of which are NATO
            # members either. Australia's treaty alliance is ANZUS, with AUKUS
            # layered on top, and SIPRI puts its 2025 spend at 1.9% of GDP against
            # this option's 1.8, so both limbs of the detail hold. The government's
            # own 2.8% figure is on the NATO definition and is not comparable.
            # https://www.sbs.com.au/news/article/global-military-spending-reaches-record-4-trillion/5014ife89
            {"id": "de_alliance", "label": "Small force inside an alliance",
             "detail": "Defence is shared with allies, so the standing force is modest.",
             "financial": 1.8, "political": 20, "social": 8,
             "axis": {"military_burden": 1.8}},
            # Political cut from 45. A militia needs no ally's consent and no treaty. See
            # de_conscript below for the reasoning across this domain.
            {"id": "de_militia", "label": "Neutral, with militia conscription",
             "detail": "No alliance. Most men serve, then keep their kit and train for years.", "financial": 1.5, "political": 25, "social": 55,
             "axis": {"military_burden": 1.5}},
            # Political cut from 60. IN DEFENCE THE POLITICAL COST IS MOSTLY WHOSE
            # AGREEMENT YOU NEED. Neutrality means forgoing allies and alliance means
            # negotiating a treaty someone else can refuse. Universal service needs one
            # act of parliament, no ally's consent, no basing agreement and no fleet, so
            # it is the cheapest posture here to enact, which is why states under threat
            # reach for it first. The cost lands on a year of everybody's life: the 75.
            {"id": "de_conscript", "label": "Mandatory service, twelve months",
             "detail": "Everyone serves. The force is large relative to the population.", "financial": 4.5, "political": 12, "social": 75,
             "axis": {"military_burden": 4.5}},
            # Political cut from 40. Same reading: a blue-water navy needs no treaty, no
            # conscript and no constitutional change. It needs a budget, and the budget is
            # already the 3.4.
            {"id": "de_power", "label": "Global force projection",
             "detail": "Bases abroad, a blue-water navy, and the spending that goes with them.", "financial": 3.4, "political": 15, "social": 25,
             "axis": {"military_burden": 3.4}},
        ],
    },
    {
        "id": "immigration",
        "name": "Immigration and Citizenship",
        "axis": "foreign_born",
        "options": [
            {"id": "im_closed", "label": "Very low intake, citizenship by descent",
             "detail": "Few people move in, and being born there is how you become a citizen.", "financial": 0.1, "political": 25, "social": 25,
             "axis": {"foreign_born": 3.0}},
            {"id": "im_controlled", "label": "Controlled intake, long path to citizenship",
             "detail": "Selective entry, and naturalisation takes the better part of a decade.",
             # EE, FI and NL removed 2026-08-29: all three sit on im_open in the matrix.
             # Every EU state is simultaneously open within the bloc and selective
             # outside it, so a country tagged on both makes this domain claim two
             # cells at once and the reveal would print whichever it hit first.
             "financial": 0.3, "political": 20, "social": 20,
             "axis": {"foreign_born": 15.0}},
            # Social cut from 30. An intake selected for skills with a real path to
            # citizenship produces the smallest permanent outsider population of the five,
            # which is the cohesion cost the others are carrying. It was priced highest.
            {"id": "im_points", "label": "High skilled intake, real path to citizenship",
             "detail": "A points system brings people in, and most of them can become citizens.",
             # DE removed 2026-08-29: Germany sits on im_open in the matrix.
             "financial": 0.5, "political": 30, "social": 14,
             "axis": {"foreign_born": 25.0}},
            # Financial cut from 0.2. A guest-worker regime is the cheapest immigration
            # system here to run: no settlement services, no citizenship pathway, no
            # language programmes, and employers carry the rest. The cost is the 60 social
            # of a permanent underclass.
            {"id": "im_guest", "label": "Very high intake, no path to citizenship",
             "detail": "Most residents are foreign workers on visas that never lead anywhere.", "financial": 0.05, "political": 55, "social": 60,
             "axis": {"foreign_born": 85.0}},
            # Social cut from 45. Movement inside a union of peer states is the least
            # disruptive intake in the set where it exists: arrivals hold the same rights
            # as everyone else and many return. The cost is the 65 political of
            # surrendering the border.
            {"id": "im_open", "label": "Open borders within a bloc",
             "detail": "Anyone from the union may live and work without a visa.",
             # DK, FR and SE removed 2026-08-29: all three sit on a third-country cell.
             "financial": 0.4, "political": 65, "social": 18,
             "axis": {"foreign_born": 20.0}},
        ],
    },
    {
        "id": "justice",
        "name": "Justice and Policing",
        "axis": "incarceration",
        "options": [
            {"id": "ju_rehab", "label": "Rehabilitation, short sentences",
             "detail": "Prison is a last resort and the maximum term is low. Few people are inside.",
             "financial": 0.4, "political": 40, "social": 30,
             "axis": {"incarceration": 60.0}},
            {"id": "ju_standard", "label": "Mixed, moderate sentences",
             "detail": "Prison for serious crime, community sentences below it.",
             "financial": 0.5, "political": 10, "social": 10,
             "axis": {"incarceration": 100.0}},
            # Political cut from 15. Tough on crime is the cheapest criminal-justice
            # position in the file to campaign on and needs no institutional change beyond
            # sentencing law, which is why it is the default drift of every democracy in
            # the set. The cost is the prison budget and the people inside it.
            {"id": "ju_tough", "label": "Long sentences, high imprisonment",
             "detail": "Long terms, limited parole, and a large prison population.",
             "financial": 0.9, "political": 8, "social": 35,
             "axis": {"incarceration": 300.0}},
            # Financial cut from 0.4. Caning and execution are the cheapest sanctions in
            # the file to administer and the prison population they leave is small, so the
            # state's outlay is the lowest in the domain. The cost is entirely social.
            {"id": "ju_corporal", "label": "Severe penalties, caning and capital punishment",
             "detail": "Harsh punishments for a wide range of offences, and very low crime.", "financial": 0.15, "political": 55, "social": 65,
             "axis": {"incarceration": 190.0}},
            # Financial cut from 0.5. Treating possession as health rather than crime
            # removes the prosecutions and the prison places; Portugal's dissuasion panels
            # cost less than the court time they replaced.
            {"id": "ju_decriminalised", "label": "Rehabilitation, drugs decriminalised",
             "detail": "Short sentences and a small prison population, and possessing any drug "
                       "is treated as a health matter rather than a crime.", "financial": 0.3, "political": 60, "social": 45,
             "axis": {"incarceration": 90.0}},
        ],
    },
    {
        "id": "family",
        "name": "Family and Children",
        "axis": "family_spend",
        "options": [
            # Social raised from 30. A country that offers families nothing pushes the
            # whole cost of the next generation onto parents, and the withdrawal from work
            # and the birth rate that follow are the largest cohesion cost in the domain.
            {"id": "fa_none", "label": "No state support",
             "detail": "Childcare and leave are between you and your employer.", "financial": 0.6, "political": 5, "social": 42,
             "axis": {"family_spend": 0.6, "redistribution": 0.00}},
            # Social raised from 10. Means-tested help carries the withdrawal tapers, the
            # paperwork and the stigma that universal payments do not. Pricing it as the
            # lowest-friction design in the domain was the artefact.
            {"id": "fa_targeted", "label": "Payments to those who need them",
             "detail": "Means-tested help with childcare and a modest paid leave scheme.",
             "financial": 1.8, "political": 15, "social": 28,
             "axis": {"family_spend": 1.8, "redistribution": 0.02}},
            {"id": "fa_universal", "label": "Universal child benefit and cheap childcare",
             "detail": "Every family is paid per child, and childcare is capped at a low price.",
             # SE and NO removed 2026-08-29: both sit on fa_leave, which is this option
             # plus the long shared parental leave and is the more specific claim.
             "financial": 3.3, "political": 30, "social": 12,
             "axis": {"family_spend": 3.3, "redistribution": 0.05}},
            # Political cut from 45. Cash for children is among the least contested
            # transfers in the file to legislate; almost nobody organises against it, which
            # is why states reach for it when fertility falls. The cost is the money and
            # the 35 social of transfers aimed at one kind of family.
            {"id": "fa_pronatal", "label": "Payments to have more children",
             "detail": "Large transfers, loans forgiven per child, tax relief for big families.", "financial": 3.8, "political": 12, "social": 35,
             "axis": {"family_spend": 3.8, "redistribution": 0.04}},
            # Social cut from 15. A long shared leave is the single thing that most reduces
            # the career penalty of having a child, so it is the lowest-friction option in
            # the domain rather than a surcharge on the universal one.
            {"id": "fa_leave", "label": "Universal, with a long shared parental leave",
             "detail": "Every family gets a per-child benefit and capped-price childcare, plus "
                       "more than a year of paid leave split between parents.", "financial": 3.6, "political": 40, "social": 8,
             "axis": {"family_spend": 3.6, "redistribution": 0.05}},
        ],
    },
]
