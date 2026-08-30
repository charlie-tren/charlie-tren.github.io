"""Forty-five countries, of which thirty-seven are matchable.

TWO KINDS OF COUNTRY LIVE IN THIS FILE and the difference is `matchable`.

A MATCHABLE country has all thirteen `choices` and can be the answer the reveal
gives. There are thirty-seven of them: the launch twenty, plus Ireland, Italy,
Spain, Portugal, Austria, Belgium, Greece, Luxembourg and Iceland, and then
Czechia, Poland, Slovakia, Slovenia, Croatia, Lithuania, Latvia and Hungary, all
coded on 30/08/2026 out of the measured-only pool.

A MEASURED-ONLY country has `choices == {}` and `matchable == False`. It can
appear on an axis and it counts towards indicator coverage, but it can never be
a nearest neighbour, because there is nothing to match against. Twenty-five were
added on 30/08/2026 and seventeen of them were coded the same day, leaving eight.
This is the build-out predicted below: the axes are
automatable and went wide first, and the matrix follows one country at a time
because every matrix cell is a human judgement with a citation behind it.

`matchable` is redundant with `choices` on purpose. It is the field the page and
the JS read, so neither has to infer intent from an empty dict, and
test_matchable_agrees_with_choices fails loudly if the two ever disagree. A
country with SOME of the thirteen is a fault, not a third kind, and
test_every_country_has_exactly_one_option_in_every_domain rejects it.

`choices` is the policy matrix and it is the thing the match runs on. Each cell
is a claim about what the country actually does, and it appears in the reveal
next to that country's name, so it is checked against a source before it ships.

`nonTaxRevenue` is income the state has that is not tax, in % of GDP, and it is
inherited from the starting country rather than chosen. A state's income is tax
PLUS non-tax income, and for thirty-six of the thirty-seven matchable countries the
second term rounds to nothing. On the eight measured-only rows it is 0.0
because it could not be sourced, which is a different claim and is written out
above those rows. For the UAE it is most of the budget. Total capacity is the realised
value of the chosen tax rate plus this, floored at what the country already
spends. See budget.js.

`indicators` carries a value, a year and a source per axis. A value of None is
"does not apply" and must never be confused with a missing key, which is "no
data". Both are handled separately in the reveal.

WHERE THE MATRIX IS THIN, re-measured 30/08/2026 over all 666 pairs of the
thirty-seven matchable countries. The measured-only rows have no matrix and cannot
appear. No pair matches on all thirteen, so no country is unreachable in the
reveal, but the count of shared cells on the closest pairs is the margin the
whole match turns on:

    11  SI HR   retirement, justice
    11  SE NO   work, defence
    11  IT PT   education, justice
    11  BE LU   retirement, work
    10  SE FI / PL LU / PL HU / NZ LV / NZ EE / NL SI / NL HR / IT HR

ADDING THE CENTRAL EUROPEAN AND BALTIC BLOCK DID NOT MOVE THE CEILING, which
stayed at eleven, and added one pair to it. Slovenia and Croatia are separated by
retirement, Croatia kept the compulsory funded second pillar it legislated in
2002 and Slovenia's is voluntary, and by justice, 69 per 100,000 against 128.
Those two cells carry more weight than any others in this block and are the first
to check if the pair ever reaches thirteen. Re-run the pair script after any cell
change: a correction that looks local can quietly push a pair to thirteen.

WHY SO MUCH OF EUROPE AGREES. Seven of the nine western European countries added
first sit on tax_continental, and five of the eight added second; all seventeen
sit on sp_hate_limits; and fifteen of the seventeen on vo_proportional. None of
that is laziness. Every EU member of the set runs heavy payroll-funded social
insurance, every one is bound by Framework Decision 2008/913/JHA to criminalise
incitement to hatred, and almost every one elects its parliament proportionally.
The discrimination therefore comes from the domains where Europe genuinely
differs: retirement, housing, defence, immigration and family. In the eight coded
second it also comes from energy, where Slovakia runs most of its grid on
reactors, and from voting, where Hungary and Lithuania run mixed systems whose
majoritarian tier holds more seats than the list tier.

WHERE THE MENU DOES NOT REACH THIS BLOCK, recorded because it is information
about the menu rather than a failure of it. Four features of post-communist
policy have no option:

  a mandatory funded second pillar alongside an EARNINGS-RELATED state pension.
  re_super pairs compulsory saving with a MEANS-TESTED pension, which is the
  Australian model. Croatia and Latvia are coded there for the compulsory-saving
  limb and the caveat is on their rows.

  mass subsidised OWNER-OCCUPATION. Hungary puts people into ownership with
  forgivable loans and a 3% state mortgage, and the only option with a state that
  does that is ho_singapore, which requires the state to build the flats.

  a large volunteer army inside an alliance. Poland spends 4.5% of GDP on
  defence, the most in NATO, and de_alliance says the standing force is modest.

  a mixed-member electoral system. Hungary and Lithuania are coded vo_fptp on the
  tier that holds more seats and on measured disproportionality, which is the
  domain's axis.
"""

COUNTRIES = [
    {"code": "AU", "name": "Australia", "timezones": ["Australia/Sydney", "Australia/Melbourne",
        "Australia/Brisbane", "Australia/Perth", "Australia/Adelaide", "Australia/Hobart",
        "Australia/Darwin"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_mixed", "education": "ed_deferred",
                 "housing": "ho_market", "retirement": "re_super", "energy": "en_fossil",
                 "speech": "sp_hate_limits", "voting": "vo_preferential", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 73.7, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.1, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 1.9, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 30.4, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 29.5, "year": 2021,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 3.2, "year": 2021,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 3.4, "year": 2022,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.9, "year": 2022,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.122, "year": 2020,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 525.2, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.915, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 23.11, "year": 2025,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 59.7, "year": 2023,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 170.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "NZ", "name": "New Zealand", "timezones": ["Pacific/Auckland"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_mixed", "education": "ed_deferred",
                 "housing": "ho_market", "retirement": "re_super", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 77.7, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.2, "year": 2023,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 1.2, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 28.2, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 33.8, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 3.8, "year": 2020,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; centrally funded public housing places only"},
         "pension_spend": {"value": 5.1, "year": 2022,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 2.5, "year": 2022,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.131, "year": 2022,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 92.8, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.927, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 2.63, "year": 2023,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 18.7, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 210.0, "year": 2026,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "US", "name": "United States", "timezones": ["America/New_York", "America/Chicago",
        "America/Denver", "America/Los_Angeles", "America/Phoenix", "America/Anchorage",
        "Pacific/Honolulu"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_private", "education": "ed_market",
                 "housing": "ho_market", "retirement": "re_flat", "energy": "en_fossil",
                 "speech": "sp_first_amendment", "voting": "vo_fptp", "work": "wo_at_will",
                 "defence": "de_power", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_none"},
     "indicators": {
         "health_public": {"value": 54.0, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.4, "year": 2021,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 3.4, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 15.2, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 27.7, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 3.6, "year": 2019,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 7.3, "year": 2023,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 0.6, "year": 2023,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.112, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 384.4, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.729, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 1.01, "year": 2024,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 11.1, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 542.0, "year": 2023,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "UK", "name": "United Kingdom", "timezones": ["Europe/London"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental", "healthcare": "hc_public", "education": "ed_deferred",
                 "housing": "ho_subsidy", "retirement": "re_flat", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_fptp", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_controlled", "justice": "ju_tough",
                 "family": "fa_universal"},
     "indicators": {
         "health_public": {"value": 81.8, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.9, "year": 2021,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.3, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 17.1, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 35.3, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 16.4, "year": 2022,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; England only"},
         "pension_spend": {"value": 7.1, "year": 2022,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.9, "year": 2022,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.155, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 217.4, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.833, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 23.64, "year": 2024,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 40.2, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 136.0, "year": 2026,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population; England and Wales"},
     }},
    {"code": "CA", "name": "Canada", "timezones": ["America/Toronto", "America/Vancouver",
        "America/Edmonton", "America/Winnipeg", "America/Halifax", "America/St_Johns"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_mixed", "education": "ed_free_selective",
                 "housing": "ho_market", "retirement": "re_flat", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_fptp", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_standard",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 70.2, "year": 2024,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.8, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 1.3, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 22.2, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 33.2, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 3.5, "year": 2022,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 5.9, "year": 2022,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.6, "year": 2022,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.127, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 190.7, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.933, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 5.01, "year": 2025,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 30.2, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 98.0, "year": 2023,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "DE", "name": "Germany", "timezones": ["Europe/Berlin"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental", "healthcare": "hc_insurance", "education": "ed_vocational",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_deposit",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_open", "justice": "ju_standard",
                 "family": "fa_universal"},
     "indicators": {
         "health_public": {"value": 79.1, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.2, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 1.9, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 19.8, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 39.3, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 2.6, "year": 2021,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 10.8, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 2.7, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.19, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 329.7, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.914, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 6.49, "year": 2025,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 49.0, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 69.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "FR", "name": "France", "timezones": ["Europe/Paris"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental", "healthcare": "hc_insurance", "education": "ed_free",
                 "housing": "ho_cooperative", "retirement": "re_generous", "energy": "en_nuclear",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_mandated_leave",
                 "defence": "de_power", "immigration": "im_controlled", "justice": "ju_standard",
                 "family": "fa_pronatal"},
     "indicators": {
         "health_public": {"value": 68.4, "year": 2024,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.3, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.1, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 13.8, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 46.1, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 14.0, "year": 2018,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 13.4, "year": 2022,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 2.6, "year": 2022,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.218, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 41.4, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.959, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 7.79, "year": 2024,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 98.0, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 131.0, "year": 2026,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    # NL energy changed from en_hydro to en_carbon_tax 2026-08-29. The Dutch grid is
    # 253.6 g/kWh, which is not the clean grid en_hydro claims, and the Netherlands
    # prices carbon through the EU ETS plus a national industrial CO2 levy. Sources
    # are on the en_carbon_tax option in policies.py.
    {"code": "NL", "name": "Netherlands", "timezones": ["Europe/Amsterdam"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental", "healthcare": "hc_insurance", "education": "ed_vocational",
                 "housing": "ho_social", "retirement": "re_super", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_open", "justice": "ju_rehab",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 68.4, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.2, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 1.9, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 16.2, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 38.0, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 34.1, "year": 2021,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 6.4, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.6, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.147, "year": 2024,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 253.6, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.91, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 1.46, "year": 2023,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 72.1, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 70.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "DK", "name": "Denmark", "timezones": ["Europe/Copenhagen"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_cooperative", "retirement": "re_earnings", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_controlled", "justice": "ju_rehab",
                 "family": "fa_universal"},
     "indicators": {
         "health_public": {"value": 83.4, "year": 2024,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 6.4, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.4, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 14.2, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 41.9, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 21.3, "year": 2022,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 7.5, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 3.2, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.166, "year": 2022,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 114.4, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.98, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 1.13, "year": 2022,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 81.6, "year": 2023,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 70.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    # SE housing changed from ho_cooperative to ho_subsidy 2026-08-29. OECD PH4.2
    # excludes Sweden from the social rental housing indicator on the ground that
    # municipal housing company rents are not below market, so the axis this cell
    # feeds has no Swedish social housing to report. The reasoning and the sources
    # are on the ho_subsidy option in policies.py.
    {"code": "SE", "name": "Sweden", "timezones": ["Europe/Stockholm"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_mandated_leave",
                 "defence": "de_militia", "immigration": "im_points", "justice": "ju_rehab",
                 "family": "fa_leave"},
     "indicators": {
         "health_public": {"value": 86.1, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 7.3, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.0, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 21.4, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 41.3, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": None, "year": 2022,
                            "source": "n/a",
                            "na_reason": "municipal housing associations house a large share of low-income households, but rents are not below market, so the OECD does not count them as social housing"},
         "pension_spend": {"value": 8.0, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 3.3, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.142, "year": 2024,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 35.3, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.946, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 0.64, "year": 2022,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 88.0, "year": 2024,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 106.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "NO", "name": "Norway", "timezones": ["Europe/Oslo"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_transparency",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_rehab",
                 "family": "fa_leave"},
     "indicators": {
         "health_public": {"value": 86.1, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.4, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.1, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 18.2, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 44.3, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 4.1, "year": 2022,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; municipal dwellings only, about 75% of the stock"},
         "pension_spend": {"value": 6.5, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 2.8, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.173, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 28.1, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.953, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 3.65, "year": 2021,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 72.0, "year": 2022,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 54.0, "year": 2026,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "FI", "name": "Finland", "timezones": ["Europe/Helsinki"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_militia", "immigration": "im_open", "justice": "ju_rehab",
                 "family": "fa_universal"},
     "indicators": {
         "health_public": {"value": 81.1, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 6.4, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.3, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 9.2, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 43.0, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 10.9, "year": 2021,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 12.2, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 3.1, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.243, "year": 2024,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 57.5, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.946, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 3.99, "year": 2023,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 88.8, "year": 2022,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 58.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "EE", "name": "Estonia", "timezones": ["Europe/Tallinn"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_flat", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_market", "retirement": "re_super", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_open", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 75.8, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.2, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 3.4, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 14.9, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 32.8, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 1.1, "year": 2017,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 6.8, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 3.0, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.157, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 319.2, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.969, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 4.66, "year": 2023,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 19.1, "year": 2021,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 128.0, "year": 2026,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "CH", "name": "Switzerland", "timezones": ["Europe/Zurich"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_vocational",
                 "housing": "ho_subsidy", "retirement": "re_super", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_direct", "work": "wo_minimum",
                 "defence": "de_militia", "immigration": "im_controlled", "justice": "ju_standard",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 33.1, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.9, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 0.7, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 31.1, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 27.2, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 8.0, "year": 2013,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 6.6, "year": 2021,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.7, "year": 2021,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.083, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 39.2, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.967, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 3.6, "year": 2023,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 51.5, "year": 2021,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 78.0, "year": 2026,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    # SG energy changed from en_hydro to en_carbon_tax 2026-08-29. The public
    # transport half of en_hydro is true of Singapore and the clean grid half is
    # not: the grid is 497.1 g/kWh, close to the fossil end of the axis. Singapore
    # has taxed carbon since 2019 and raised the rate five-fold in 2024. Sources are
    # on the en_carbon_tax option in policies.py. The speech cell is unchanged and
    # Singapore is now the only country on sp_order.
    {"code": "SG", "name": "Singapore", "timezones": ["Asia/Singapore"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_savings", "education": "ed_market",
                 "housing": "ho_singapore", "retirement": "re_private", "energy": "en_carbon_tax",
                 "speech": "sp_order", "voting": "vo_fptp", "work": "wo_at_will",
                 "defence": "de_conscript", "immigration": "im_points", "justice": "ju_corporal",
                 "family": "fa_none"},
     "indicators": {
         "health_public": {"value": 58.5, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 2.2, "year": 2024,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.8, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 48.7, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 12.1, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "grid_carbon": {"value": 497.1, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.4, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 16.88, "year": 2025,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "incarceration": {"value": 178.0, "year": 2024,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    # JP changed on two cells 2026-08-29. Energy en_hydro to en_carbon_tax: the
    # grid has been coal and gas heavy since Fukushima at 477.3 g/kWh, and Japan
    # has had a carbon tax since 2012 with the GX-ETS mandatory from April 2026.
    # Speech sp_order to sp_hate_limits: at 0.847 Japan sits above the UK and
    # Israel, both of which are on sp_hate_limits, so the lower bucket was not
    # supportable. This is the weaker of the two speech moves and the caveat, that
    # the 2016 hate speech act carries no penalty, is recorded on the option in
    # policies.py rather than hidden.
    {"code": "JP", "name": "Japan", "timezones": ["Asia/Tokyo"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_market",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_closed", "justice": "ju_rehab",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 84.8, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 3.3, "year": 2021,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 1.4, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 2.8, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 34.1, "year": 2021,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 3.1, "year": 2018,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 9.2, "year": 2022,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 2.0, "year": 2022,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.175, "year": 2021,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 477.3, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.847, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 8.92, "year": 2024,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 15.2, "year": 2023,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 33.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    # KR changed on two cells 2026-08-29. Energy en_nuclear to en_carbon_tax:
    # nuclear is the largest single source at 31.1% of generation but coal and LNG
    # are about 56% together, so "most power from reactors" is false, and the
    # K-ETS has priced emissions since 2015. Speech sp_order to sp_hate_limits:
    # V-Dem puts Korean freedom of expression at 0.933, level with Canada, so a
    # public-order restriction cell was a claim about Korea that the measure
    # contradicts. Sources are on both options in policies.py.
    {"code": "KR", "name": "South Korea", "timezones": ["Asia/Seoul"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_market",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_at_will",
                 "defence": "de_conscript", "immigration": "im_closed", "justice": "ju_standard",
                 "family": "fa_none"},
     "indicators": {
         "health_public": {"value": 56.6, "year": 2024,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.4, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 2.6, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 3.5, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 32.0, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 8.9, "year": 2018,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 3.8, "year": 2022,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.7, "year": 2022,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.069, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 417.1, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.933, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 15.27, "year": 2024,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 16.3, "year": 2023,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 127.0, "year": 2026,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "IL", "name": "Israel", "timezones": ["Asia/Jerusalem"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_free",
                 "housing": "ho_market", "retirement": "re_flat", "energy": "en_fossil",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_conscript", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 65.2, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.9, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 8.8, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 22.3, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 32.9, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": 1.8, "year": 2023,
                            "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 4.5, "year": 2023,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.9, "year": 2023,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.108, "year": 2023,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 492.7, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.822, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 4.4, "year": 2022,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 45.8, "year": 2023,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 217.0, "year": 2023,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    {"code": "CL", "name": "Chile", "timezones": ["America/Santiago"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_market",
                 "housing": "ho_market", "retirement": "re_private", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_controlled", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {
         "health_public": {"value": 48.5, "year": 2024,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.9, "year": 2022,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 1.6, "year": 2024,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 7.8, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "tax_take": {"value": 23.9, "year": 2022,
                      "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "social_housing": {"value": None, "year": 2022,
                            "source": "n/a",
                            "na_reason": "the OECD records virtually no social rental sector"},
         "pension_spend": {"value": 3.7, "year": 2023,
                           "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "family_spend": {"value": 1.8, "year": 2023,
                          "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.043, "year": 2022,
                            "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"},
         "grid_carbon": {"value": 289.5, "year": 2025,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.926, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 9.58, "year": 2021,
                                "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 19.3, "year": 2023,
                        "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "incarceration": {"value": 329.0, "year": 2025,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},
    # AE retirement changed from re_private to re_generous 2026-08-29. There are no
    # mandatory individual accounts here: GPSSA is a contributory pay-as-you-go
    # defined-benefit scheme paying up to 100% of the final five years' average
    # salary, with a pension age of 60. Sources and the expatriate caveat are on
    # the re_generous option in policies.py.
    {"code": "AE", "name": "United Arab Emirates", "timezones": ["Asia/Dubai"],
     # THE ONLY NON-ZERO CELL IN THE FILE, and the reason the field exists.
     # IMF general government revenue for the UAE is 27.8% of GDP in 2024,
     # against a total TAX take of about 16.0. The 11.8 points between them
     # are hydrocarbon and investment income, which no tax-to-GDP series
     # captures a cent of. It was modelled as tax until 2026-08-30, which
     # meant a visitor who moved the UAE off tax_minimal lost the oil.
     # https://www.imf.org/external/datamapper/rev@FPP/ARE
     # Cross-checked against the same dataset's expenditure series (21.4%,
     # and 27.8 less 21.4 is the 6.4% surplus the 2025 Article IV states)
     # and against CBUAE's Quarterly Economic Review (26.9% in H1 2024).
     "nonTaxRevenue": 11.8,
     "matchable": True,
     "choices": {"tax": "tax_minimal", "healthcare": "hc_mixed", "education": "ed_vocational",
                 "housing": "ho_market", "retirement": "re_generous", "energy": "en_fossil",
                 "speech": "sp_restricted", "voting": "vo_none", "work": "wo_at_will",
                 "defence": "de_power", "immigration": "im_guest", "justice": "ju_corporal",
                 "family": "fa_none"},
     "indicators": {
         "health_public": {"value": 66.8, "year": 2023,
                           "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 3.9, "year": 2021,
                             "source": "World Bank, government expenditure on education % of GDP"},
         "military_burden": {"value": 5.6, "year": 2014,
                             "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 74.0, "year": 2024,
                          "source": "UN DESA / World Bank, international migrant stock % of population"},
         "grid_carbon": {"value": 467.5, "year": 2024,
                         "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.063, "year": 2025,
                        "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": None, "year": 2024,
                                "source": "n/a",
                                "na_reason": "no competitive national elections"},
         "incarceration": {"value": 104.0, "year": 2014,
                           "source": "World Prison Brief, prison population rate per 100,000 of national population"},
     }},

    # ----------------------------------------------------------------------
    # MEASURED ONLY, added 30/08/2026. `choices` is deliberately empty and
    # `matchable` is False: these countries can appear on an axis but can never
    # be the answer, because there is no policy matrix to match against. The
    # thirteen cells are a separate job, and a half-filled `choices` is a fault
    # that test_every_country_has_exactly_one_option_in_every_domain will fail
    # on rather than quietly accept.
    #
    # nonTaxRevenue is 0.0 on all twenty-five, INCLUDING Saudi Arabia, Qatar and
    # Kuwait, which is the UAE's case and where a real figure would be worth
    # having. It is 0.0 because it could not be sourced, not because it is
    # believed to be zero. The IMF Fiscal Monitor gives general government
    # revenue for 2024 (Saudi Arabia 27.1, Qatar 26.7, Kuwait 74.2, and the UAE
    # at 27.8, which reproduces the figure on the UAE's own row), but no source
    # consulted gives a tax take for the three on the same basis as the tax_take
    # axis: the OECD Global Revenue Statistics database does not cover them. The
    # only available subtraction, IMF revenue less the UNU-WIDER GRD tax series,
    # puts the UAE at 7.8 against the 11.8 on its row, so the two bases disagree
    # by four points of GDP on the one country where the answer is known. A
    # number built that way would look right and be wrong, so the field is 0.0
    # and the gap is stated here. It is also inert for these rows: nonTaxRevenue
    # is inherited from the STARTING country, and a measured-only country can
    # never be one.
    # ----------------------------------------------------------------------
    {"code": "IE", "name": "Ireland", "timezones": ["Europe/Dublin"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     # THREE OF IRELAND'S MEASURED CELLS ARE GDP-DISTORTED AND ARE NOT EVIDENCE
     # AGAINST THE CHOICE ABOVE THEM. tax_take 21.7, education_spend 2.9 and
     # pension_spend 2.9 are all shares of a GDP inflated by roughly two-fifths
     # by multinational intellectual property and contract manufacturing that no
     # Irish resident consumes. On the modified gross national income (GNI*)
     # basis the CSO publishes for exactly this reason, the tax take is close to
     # 35% rather than 21.7%. So Ireland is coded on what the policies ARE,
     # and the three low cells are flagged here rather than read as facts about
     # the policy.
     # https://www.cso.ie/en/releasesandpublications/ep/p-nie/nie2023/modifiedgrossnationalincomegni/
     "choices": {"tax": "tax_anglo",
                 # THE WELL-KNOWN EXCEPTION, and it is hc_mixed rather than
                 # hc_public. Ireland is a tax-funded public system in which
                 # roughly 46% of the population also holds private cover and
                 # uses it to be seen sooner, including in private beds inside
                 # public hospitals. The public inpatient charge was abolished in
                 # April 2023, so the public tier is now free at the point of
                 # use, but the paid fast lane is the defining feature and
                 # Slaintecare's single-tier target is not expected before 2030.
                 # https://www.irishtimes.com/opinion/2026/08/20/slaintecare-is-meant-to-move-us-towards-universal-healthcare-so-why-has-this-not-happened/
                 # Checked 2026-08-30.
                 "healthcare": "hc_mixed",
                 # Undergraduate tuition was abolished in 1996. What remains is a
                 # flat state-set student contribution, EUR 2,000 to 3,000, plus
                 # means-tested SUSI maintenance grants. Not ed_deferred: there
                 # is no income-contingent loan of any kind.
                 "education": "ed_free",
                 # OECD PH4.2 places Ireland in the 10-19% band and the measured
                 # cell reads 12.7%, but the instrument that has grown is the
                 # Housing Assistance Payment, cash to a tenant renting
                 # privately, which is ho_subsidy rather than state building.
                 # https://www.oecd.org/content/dam/oecd/en/data/datasets/affordable-housing-database/ph4-2-social-rental-housing-stock.pdf
                 "housing": "ho_subsidy",
                 # Flat State Pension (Contributory), EUR 299.30 a week for
                 # everyone at the full rate, and the My Future Fund
                 # auto-enrolment that began on 1 January 2026 is opt-out from
                 # month seven rather than compulsory, so saving is encouraged
                 # and not required. That is re_flat, not re_super.
                 # https://www.citizensinformation.ie/en/money-and-tax/personal-finance/pensions/auto-enrolment/
                 # Checked 2026-08-30.
                 "retirement": "re_flat",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 # PR-STV. The voter ranks candidates, but voting is voluntary,
                 # and vo_preferential requires both, so this is vo_proportional.
                 "voting": "vo_proportional",
                 "work": "wo_minimum",
                 # The de_neutral tag in policies.py holds. Militarily neutral,
                 # no alliance, no conscription, and 0.2% of GDP, the lowest
                 # military burden of the forty-five.
                 "defence": "de_neutral",
                 "immigration": "im_open", "justice": "ju_standard",
                 # Child Benefit is universal at EUR 140 a month per child, but
                 # fa_universal's second limb, childcare capped at a low price,
                 # is false for Ireland: childcare is among the dearest in the
                 # EU and the National Childcare Scheme subsidy is largely
                 # income-assessed. Coded on the childcare limb and the 1.3% of
                 # GDP, with the universal benefit noted as the tension.
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 21.7, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 76.6, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 2.9, "year": 2021,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 12.7, "year": 2016,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 2.9, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 256.5, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.97, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 5.77, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 34.0, "year": 2017,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 0.2, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 23.1, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 103.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 1.3, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.197, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "IT", "name": "Italy", "timezones": ["Europe/Rome"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental",
                 # The SSN is Beveridge in design, but hc_public's "free at the
                 # point of use" is not true of it and hc_mixed's paid fast lane
                 # is. Regional tickets of EUR 36 to 55 are charged for
                 # specialist and diagnostic care, and intramoenia lets a public
                 # hospital's own consultants sell faster appointments inside
                 # the public hospital, to the point that in many hospitals the
                 # private slots now outnumber the public ones. Spain, coded
                 # hc_public below, has no equivalent of either.
                 # https://feather-insurance.com/en-it/blog/public-health-insurance-ssn-guide
                 # Checked 2026-08-30.
                 "healthcare": "hc_mixed",
                 # The only one of the nine coded ed_market, and the fit is on
                 # the fee-charging limb only. Italian public universities set
                 # their own fees between about EUR 500 and EUR 4,000 a year
                 # within a national cap, graduated by ISEE household income.
                 # The other half of the option, "loans, not grants", is false:
                 # Italian support is regional borse di studio. Coded here
                 # rather than ed_free because EUR 4,000 is not no tuition, and
                 # the measured 4.1% of GDP sits on ed_market's 4.2.
                 # https://eurydice.eacea.ec.europa.eu/countries/italy/national-student-fee
                 # Checked 2026-08-30.
                 "education": "ed_market",
                 "housing": "ho_market",
                 # Pension spend of 16.1% of GDP is the highest in the file
                 # after Greece, and OECD Pensions at a Glance 2025 puts Italy
                 # in the 70%-plus net replacement band. THE SECOND LIMB OF THIS
                 # OPTION, a low pension age, IS THE ONE PLACE IT DOES NOT FIT:
                 # the same report lists Italy among the countries whose future
                 # normal retirement age is 70 or more. Coded on the spend and
                 # the replacement rate, with the age recorded as the tension.
                 # https://www.oecd.org/en/publications/2025/11/pensions-at-a-glance-2025_76510fe4/full-report/current-retirement-ages_0f63b747.html
                 "retirement": "re_generous",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 # THE MEASURED CELL AND THIS CHOICE DISAGREE AND THE REASON IS
                 # A MENU GAP, not an error in either. Italy's Gallagher index
                 # is 12.37, the second highest of the matchable set after the
                 # UK, because the Rosatellum is a mixed system: about 37% of
                 # seats are single-member and won on a plurality, and 61% are
                 # allocated proportionally. There is no mixed-member option in
                 # this domain. vo_fptp would be the false half, since Italy
                 # elects most of its parliament by list PR and coalition
                 # government is the norm, so it is coded on the larger half.
                 "voting": "vo_proportional",
                 "work": "wo_bargaining", "defence": "de_alliance",
                 # The im_controlled tag in policies.py holds: entry by decreto
                 # flussi quota, and naturalisation after ten years of residence,
                 # which the June 2025 referendum to cut to five failed to carry.
                 "immigration": "im_controlled",
                 # The ju_standard tag in policies.py holds. 110 per 100,000.
                 "justice": "ju_standard",
                 # The Assegno Unico e Universale is paid for every child, but
                 # it is graduated by ISEE from about EUR 57 to EUR 201 a month
                 # and Italy spends 1.4% of GDP on family benefits against
                 # fa_universal's 3.3, with nursery coverage among the lowest in
                 # the EU. Coded on the amount rather than the name.
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 42.8, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 73.1, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.1, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 2.4, "year": 2022,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 16.1, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 284.8, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.756, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 12.37, "year": 2022,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 100.0, "year": 2024,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.6, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 11, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 110.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 1.4, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.184, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "ES", "name": "Spain", "timezones": ["Europe/Madrid", "Atlantic/Canary"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental",
                 # The one of the three southern Beveridge systems that is
                 # genuinely hc_public. The SNS is funded from general taxation,
                 # covers about 99.5% of residents and charges nothing at the
                 # point of use for consultations or hospital care; the only
                 # standing co-payment is on pharmaceuticals. Private cover
                 # exists and is unsubsidised for the general population. Italy
                 # and Portugal both charge user fees for care and are coded
                 # hc_mixed on that difference.
                 # https://www.commonwealthfund.org/sites/default/files/2026-04/2026_Country-Profiles_Spain.pdf
                 # Checked 2026-08-30.
                 "healthcare": "hc_public",
                 # Fees are set by the regions inside a national band, roughly
                 # EUR 700 to 2,000 a year, and several regions have cut or
                 # abolished them outright. Grants, not loans.
                 "education": "ed_free",
                 "housing": "ho_market",
                 # OECD Pensions at a Glance 2025 names Spain among the
                 # countries with a net replacement rate of 85% or more, and the
                 # measured pension spend is 12.3% of GDP.
                 # https://www.oecd.org/en/publications/2025/11/pensions-at-a-glance-2025_76510fe4/full-report/net-pension-replacement-rates_a7a9e376.html
                 "retirement": "re_generous",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance",
                 # NOT im_controlled, and this is where Spain and Portugal part.
                 # Spain runs the most permissive third-country regime in the
                 # set: arraigo regularisation after two years of presence under
                 # Royal Decree 1155/2024, an extraordinary regularisation of up
                 # to 500,000 people that ran to 30 June 2026, and naturalisation
                 # after two years for nationals of Latin American states. The
                 # menu has no "liberal third-country entry" option, so this is
                 # coded on the EU free movement limb.
                 # https://www.cidob.org/en/publications/understanding-spains-extraordinary-regularisation-key-elements
                 # Checked 2026-08-30.
                 "immigration": "im_open",
                 # 121 per 100,000, below the 128 to 542 band of ju_tough, even
                 # though Spanish sentences served are long by EU standards.
                 "justice": "ju_standard",
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 36.7, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 73.2, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.6, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 1.1, "year": 2019,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; may also include other reduced-rent housing such as employer-provided dwellings"},
         "pension_spend": {"value": 12.3, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 153.6, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.843, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 5.67, "year": 2023,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 92.1, "year": 2024,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.4, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 18.5, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 121.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 1.5, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.164, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "PT", "name": "Portugal", "timezones": ["Europe/Lisbon", "Atlantic/Madeira", "Atlantic/Azores"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental",
                 # The SNS is tax-funded and universal, but the public share of
                 # health spending is 61.4%, the lowest of the nine and the
                 # lowest of any Beveridge system in the file. Taxas moderadoras
                 # are charged for emergency, diagnostic and some GP care, the
                 # ADSE subsystem covers more than 1.3 million public servants
                 # through private providers, and private hospital use is
                 # substantial. That is a universal service with a paid tier
                 # beside it, which is hc_mixed and not hc_public.
                 # https://www.internationalinsurance.com/countries/portugal/healthcare/
                 # Checked 2026-08-30.
                 "healthcare": "hc_mixed",
                 # The propina is capped at about EUR 697 a year for a first
                 # cycle degree. Nominal by the standards of ed_market, and
                 # support is by grant rather than loan.
                 "education": "ed_free",
                 "housing": "ho_market",
                 # OECD Pensions at a Glance 2025 names Portugal among the
                 # countries with a net replacement rate of 85% or more, against
                 # 12.9% of GDP of pension spend.
                 # https://www.oecd.org/en/publications/2025/11/pensions-at-a-glance-2025_76510fe4/full-report/net-pension-replacement-rates_a7a9e376.html
                 "retirement": "re_generous",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance",
                 # PORTUGAL WAS THE LIBERAL CASE AND IS NOT ANY MORE, which is
                 # what separates it from Spain. Organic Law 1/2026, in force
                 # from 19 May 2026, raises the residence needed for
                 # naturalisation from five years to seven for EU and CPLP
                 # nationals and ten for everyone else, counts only lawful
                 # residence, and ends the manifestacao de interesse route.
                 # "The better part of a decade" is now literally true.
                 # https://www.sovereigngroup.com/news/portugal-nationality-law-update/
                 # Checked 2026-08-30.
                 "immigration": "im_controlled",
                 # The ju_decriminalised tag in policies.py holds: possession of
                 # any drug has been a matter for a dissuasion commission rather
                 # than a court since 2001. NOTE the option's "small prison
                 # population" reads oddly beside Portugal's 120 per 100,000,
                 # which is mid-table and above Ireland, Italy and Austria. The
                 # decriminalisation claim is what is unique and is true; the
                 # prison-size claim is the loose half, and the derived axis
                 # value now moves from the hand 90 to Portugal's own 120.
                 "justice": "ju_decriminalised",
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 35.1, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 61.4, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.6, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 1.1, "year": 2021,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 12.9, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 127.9, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.899, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 5.46, "year": 2025,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 83.3, "year": 2023,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.5, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 10.8, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 120.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 1.3, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.184, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "AT", "name": "Austria", "timezones": ["Europe/Vienna"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental",
                 "healthcare": "hc_insurance",
                 # Public university is free for EU students within the standard
                 # duration, and about two in five of a cohort go through the
                 # dual apprenticeship system. Both limbs of the option, which
                 # is why Austria is the only one of the nine coded here.
                 "education": "ed_vocational",
                 # Limited-profit housing associations, 97 co-operatives and 85
                 # capital-based companies under the GBV federation, hold close
                 # to a quarter of Austrian homes and let them on a cost-rent
                 # capped at about 80% of market. The measured cell is 23.6%,
                 # which is ho_cooperative's 22 rather than ho_social's 29.
                 # https://www.oecd.org/en/publications/oecd-economic-surveys-austria-2026_7cea027b-en/full-report/restoring-the-affordability-and-improving-the-functioning-of-the-housing-market_7403868f.html
                 # Checked 2026-08-30.
                 "housing": "ho_cooperative",
                 # 85%-plus net replacement rate in OECD Pensions at a Glance
                 # 2025, 14.0% of GDP, and a corridor pension from 62.
                 "retirement": "re_generous",
                 # BOTH LIMBS OF en_hydro HOLD, which is the test the 2026-08-29
                 # review applied when it moved NL, JP and SG off this option
                 # for having the transport without the grid. Austria's
                 # electricity is about 85% renewable and 46% hydro, and the
                 # nationwide KlimaTicket buys unlimited public transport across
                 # the country on one annual ticket. Austria also prices carbon
                 # nationally at EUR 55/t on top of the EU ETS, so
                 # en_carbon_tax is true of it as well; en_hydro is the more
                 # specific claim and is the one coded.
                 # https://oesterreichsenergie.at/en/our-electricity-system-1/renewables-in-austria
                 # https://www.oecd.org/en/publications/ipac-policies-in-practice_22632907-en/austria-s-klimaticket-to-promote-low-carbon-mobility_408c8de9-en.html
                 # Checked 2026-08-30. NOTE the grid is 116.9 g/kWh against 28
                 # to 58 for the four countries already on this option, so
                 # Austria widens it: clean by European standards, not Nordic.
                 "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional",
                 "work": "wo_bargaining",
                 # Constitutionally neutral since 1955, in no alliance, and six
                 # months of conscription for men with a nine-month civilian
                 # alternative. de_neutral is Ireland's cell and requires no
                 # conscription, so this is de_militia.
                 # https://www.thelocal.at/20220307/explained-how-does-austrias-mandatory-military-service-work/
                 "defence": "de_militia",
                 # Ten years of lawful residence for naturalisation, five of them
                 # on a settlement permit, no dual nationality in the standard
                 # case, and a points-scored Red-White-Red Card for third-country
                 # workers. Textbook im_controlled, and the cell that separates
                 # Austria from Germany, which sits on im_open.
                 # https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/
                 # Checked 2026-08-30.
                 "immigration": "im_controlled",
                 "justice": "ju_standard",
                 # Familienbeihilfe is paid for every child at EUR 200 to 250 a
                 # month by age, with a sibling supplement, alongside subsidised
                 # and in Vienna free kindergarten.
                 "family": "fa_universal"},
     "indicators": {
         "tax_take": {"value": 43.4, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 76.5, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 23.6, "year": 2019,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; main residence dwellings only"},
         "pension_spend": {"value": 14.0, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 116.9, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.918, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 3.24, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 98.0, "year": 2024,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.0, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 25.5, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 105.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.6, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.203, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "BE", "name": "Belgium", "timezones": ["Europe/Brussels"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental",
                 # Registering with a mutualite is compulsory for every legal
                 # resident, six non-profit national associations plus one public
                 # fund compete for members and none may refuse anyone, and
                 # INAMI/RIZIV sets the tariffs. hc_insurance exactly.
                 # https://www.commissioner.brussels/joining-a-mutual-health-insurance-fund-compulsory-insurance/
                 "healthcare": "hc_insurance",
                 # About EUR 900 a year for EU students, and Belgium's 6.3% of
                 # GDP is the highest public education spend of the nine after
                 # Iceland. Not ed_vocational: the technical and vocational
                 # secondary tracks are school-based rather than apprenticeship,
                 # and they are not where most students go.
                 "education": "ed_free",
                 "housing": "ho_market",
                 # NOT re_generous, and the exclusion is the evidence. OECD
                 # Pensions at a Glance 2025 lists the 85%-plus replacement
                 # countries as Austria, Greece, Luxembourg, the Netherlands,
                 # Portugal, Spain and Turkiye, and Belgium is in neither that
                 # group nor the 70%-plus one, on 10.7% of GDP.
                 # https://www.oecd.org/en/publications/2025/11/pensions-at-a-glance-2025_76510fe4/full-report/net-pension-replacement-rates_a7a9e376.html
                 "retirement": "re_earnings",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 # VOTING IN BELGIUM IS LEGALLY COMPULSORY, since 1893, with
                 # fines of EUR 40 to 200 that are almost never enforced. The
                 # menu's only compulsory option is vo_preferential, which is
                 # Australia's ranked ballot, and Belgium uses list PR with a
                 # Gallagher index of 3.83. There is no proportional-and-
                 # compulsory option, so this is coded on proportionality, which
                 # is what the domain's axis measures.
                 # https://en.wikipedia.org/wiki/Voting_rights_in_Belgium
                 "voting": "vo_proportional",
                 # Coverage of 100%, joint committees per sector, national
                 # interprofessional agreements and automatic wage indexation.
                 "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_open",
                 "justice": "ju_standard",
                 # The Groeipakket and its Walloon and Brussels equivalents are
                 # paid for every child regardless of income, and creche places
                 # are income-scaled from a low cap.
                 "family": "fa_universal"},
     "indicators": {
         "tax_take": {"value": 42.6, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 73.7, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 6.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 4.2, "year": 2018,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 10.7, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 149.8, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.969, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 3.83, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 100.0, "year": 2024,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.3, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 20, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 113.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.8, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.232, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "GR", "name": "Greece", "timezones": ["Europe/Athens"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {"tax": "tax_continental",
                 # THE WEAKEST FIT OF THE 117 CELLS AND IT IS RECORDED AS SUCH.
                 # Greek health financing is roughly a third compulsory social
                 # insurance through EOPYY, which has been the single purchaser
                 # since 2011 and collects contributions via EFKA, a third state
                 # budget, and over a third private, with out-of-pocket payments
                 # at 34% of spending against an EU average of 16%. The
                 # contributory limb is what puts it on hc_insurance, but EOPYY
                 # is one public fund rather than the regulated market of
                 # insurers the option describes, and the measured public share
                 # of 50.6% is the lowest of the forty-five. No option in this
                 # domain describes a universal system carrying a third of its
                 # cost out of patients' pockets.
                 # https://pmc.ncbi.nlm.nih.gov/articles/PMC12733077/
                 # https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/12/country-health-profile-2025-country-notes_7e72146d/greece_71e37e79/9ca0bb52-en.pdf
                 # Checked 2026-08-30.
                 "healthcare": "hc_insurance",
                 # Public universities charge no tuition for a first degree and
                 # supply textbooks free. The cleanest ed_free of the nine, and
                 # it disagrees with its own axis: Greece spends 3.4% of GDP on
                 # education against the option's 6.3. Free and underfunded are
                 # not the same claim, and the axis measures the second.
                 "education": "ed_free",
                 # Greece has essentially no social rental stock at all, which is
                 # why the measured cell is absent rather than low: the Workers'
                 # Housing Organisation was abolished in 2012. Owner-occupation
                 # and family transfer carry the housing system.
                 "housing": "ho_market",
                 # THE WELL-KNOWN EXCEPTION, and the measured cell agrees with
                 # the choice: 16.2% of GDP, the highest in the file, with an
                 # 85%-plus net replacement rate in OECD Pensions at a Glance
                 # 2025 even after the post-2010 cuts.
                 # https://www.oecd.org/en/publications/2025/11/pensions-at-a-glance-2025_76510fe4/full-report/net-pension-replacement-rates_a7a9e376.html
                 "retirement": "re_generous",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 # Compulsory on paper and unenforced in practice, same gap as
                 # Belgium and Luxembourg. List PR with a majority bonus that
                 # applies from the second election, which is what lifts the
                 # Gallagher index to 8.97.
                 "voting": "vo_proportional",
                 # Collective bargaining coverage fell from 100% to 13 to 26%
                 # after the memoranda, agreements are mostly at company level,
                 # and the wage floor is now set directly by government, EUR 880
                 # a month from 1 April 2025. A statutory minimum with weak
                 # unions is wo_minimum, and Greece is at the bottom end of it.
                 # https://www.etui.org/sites/default/files/2025-06/Greece_Collective%20bargaining%20and%20the%20minimum%20wage%20regime_2025.pdf
                 # Checked 2026-08-30.
                 "work": "wo_minimum",
                 # A NATO member that still conscripts, which the option does not
                 # exclude: twelve months of service, an active force above
                 # 140,000, and 3.1% of GDP, the highest military burden of the
                 # nine by a factor of two. de_alliance's "the standing force is
                 # modest" is the limb Greece fails.
                 # https://greekreporter.com/2025/07/24/greece-unveils-sweeping-defense-reforms/
                 # Checked 2026-08-30.
                 "defence": "de_conscript",
                 "immigration": "im_controlled", "justice": "ju_standard",
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 39.8, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 50.6, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 3.4, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "pension_spend": {"value": 16.2, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 315.1, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.81, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 8.97, "year": 2023,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 13.1, "year": 2017,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 3.1, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 14.2, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 111.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 1.7, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.187, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "CZ", "name": "Czechia", "timezones": ["Europe/Prague"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # SOCIAL CONTRIBUTIONS ARE 45.5% OF CZECH TAX REVENUE, the
                 # highest share in the OECD against an average of 25.5%, so
                 # "funded by payroll" is more literally true here than of
                 # Germany or France. The flat 15% income tax ENDED in 2021 and
                 # a 23% band now applies above CZK 1,762,812, so tax_flat is
                 # out: it wants one rate on all income. The limb this cell fits
                 # least is "high": the take is 34.0% of GDP against 38.7 for
                 # the four countries the option was written on.
                 # https://www.oecd.org/en/publications/revenue-statistics-2025_3a264267-en/full-report/tax-revenue-trends-1965-2024_98c75833.html
                 # https://www.accace.com/tax-guideline-for-the-czech-republic/
                 # Checked 2026-08-30.
                 "tax": "tax_continental",
                 # Seven competing health insurance funds, compulsory
                 # membership, one free switch a year, and none may refuse an
                 # applicant. The public share is 84.3%, the highest of the
                 # eight coded here.
                 "healthcare": "hc_insurance",
                 # Public universities charge no tuition in Czech, and 71% of
                 # upper secondary pupils are in vocational programmes, level
                 # with Slovenia and above the Netherlands and Austria, which
                 # already hold this option. The apprenticeship limb of the
                 # detail is the weak one: Czech VET is mostly school-based
                 # technical schools rather than dual apprenticeships.
                 # https://ec.europa.eu/eurostat/web/products-eurostat-news/-/edn-20201109-1
                 "education": "ed_vocational",
                 # THE ONE OF THE EIGHT WITH A REAL CASH HOUSING INSTRUMENT.
                 # OECD PH3.1 names Czechia in the nine countries spending over
                 # 0.5% of GDP on housing allowances, alongside Iceland,
                 # Ireland, Norway and Sweden, which are already on this option.
                 # The social rental stock is only 3.6%, so the state's tool is
                 # money and not building, which is exactly what ho_subsidy
                 # says. Greece is on ho_market because it has neither.
                 # https://webfs.oecd.org/els-com/Affordable_Housing_Database/PH3-1-Public-spending-on-housing-allowances.pdf
                 # Checked 2026-08-30.
                 "housing": "ho_subsidy",
                 # No mandatory funded pillar: the 2013 second pillar was
                 # abolished in 2016 and the third pillar is voluntary and
                 # state-subsidised. The state pension is formally
                 # earnings-related, though OECD Pensions at a Glance 2025 calls
                 # the benefit structure "very compressed" and the gap between a
                 # low and an average earner one of the highest in the OECD, so
                 # re_flat was the near miss. Earnings still decide the amount,
                 # and 8.2% of GDP sits on re_earnings rather than re_flat.
                 # https://www.oecd.org/en/publications/pensions-at-a-glance-2025-country-notes_8a53ef12-en/czechia_dd7aae9d-en.html
                 "retirement": "re_earnings",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance",
                 # Five years of residence to naturalise and dual nationality
                 # permitted since 2014, which is the Germany end of the range
                 # rather than the Austria end.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_open",
                 "justice": "ju_tough",
                 # The child allowance is means-tested and the universal piece
                 # is the parental allowance. Places for under-threes are scarce
                 # and dear, so fa_universal's childcare limb fails the same way
                 # it failed for Ireland.
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 34.0, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 84.3, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 3.6, "year": 2021,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; centrally provided dwellings only"},
         "pension_spend": {"value": 8.2, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 401.5, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.947, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 10.34, "year": 2021,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 43.2, "year": 2024,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.9, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 9.5, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 174.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.2, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.186, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "PL", "name": "Poland", "timezones": ["Europe/Warsaw"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # Progressive 12%/32% income tax, and social security funds
                 # take 37.8% of revenue from taxes and contributions, which is
                 # the German neighbourhood. Not tax_flat: Poland has never had
                 # a flat personal rate.
                 # https://www.oecd.org/en/publications/revenue-statistics-2025_3a264267-en/full-report/tax-revenue-trends-1965-2024_98c75833.html
                 "tax": "tax_continental",
                 # One national fund, the NFZ, financed by a compulsory
                 # earmarked health contribution rather than out of general
                 # taxation. A single carrier is not a bar: France and Korea are
                 # already on this option with one payer each.
                 "healthcare": "hc_insurance",
                 # Free full-time study at public universities and a
                 # means-tested maintenance grant. Vocational enrolment is 58.9%
                 # at medium level, above the EU average but ten points below
                 # the four coded here on ed_vocational.
                 # https://op.europa.eu/webpub/eac/education-and-training-monitor/en/country-reports/poland.html
                 "education": "ed_free",
                 # THE CELL THAT DISAGREES MOST WITH ITS OWN AXIS IN THIS
                 # COUNTRY. Poland holds 6.6% of its stock as municipal social
                 # rental, twice ho_market's derived 3.35 and the highest of the
                 # eight coded here, and the state builds through the SIM and
                 # TBS schemes. But ho_subsidy is the wrong shape for the same
                 # reason: its claim is cash help INSTEAD of building, and
                 # Poland's dodatek mieszkaniowy is small while its building
                 # programmes are not. Coded on the larger of the two claims,
                 # which is that housing is overwhelmingly privately owned:
                 # owner-occupation is about 87% after the 1990s privatisation.
                 "housing": "ho_market",
                 # WHAT IS TRUE NOW, not what was legislated in 1999. The OFE
                 # second pillar was stripped of its bond holdings in 2014 and
                 # made opt-in, and PPK from 2019 is auto-enrolment with an
                 # opt-out, so nothing here is compulsory saving. The pillar
                 # that pays is the ZUS notional defined contribution account,
                 # which is earnings-related, and 11.2% of GDP is the second
                 # highest of the eight.
                 "retirement": "re_earnings",
                 # In the EU ETS, so emissions are priced. The grid is 588.6
                 # g/kWh, the dirtiest in the EU and the highest value on this
                 # option by 90 points: pricing carbon is not the same claim as
                 # having decarbonised, which is the spread check_spread.py
                 # already records against en_carbon_tax.
                 "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional",
                 # Bargaining coverage of 11.6%, the lowest of the eight and one
                 # of the lowest in the OECD, against a statutory minimum wage.
                 "work": "wo_minimum",
                 # NATO, no conscription since 2009, and the cell that fits
                 # worst in this row: Poland spends 4.5% of GDP on defence, the
                 # highest in NATO, against this option's 1.9, and "so the
                 # standing force is modest" is plainly false. The other four
                 # are worse. See the note in the report: a large volunteer army
                 # inside an alliance has no option on this menu.
                 # https://notesfrompoland.com/2025/09/02/poland-largest-relative-defence-spender-in-nato-new-figures-confirm/
                 "defence": "de_alliance",
                 # Three years of permanent residence to naturalise, the
                 # shortest of the eight, and dual nationality permitted.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_open",
                 # From 1 October 2023 the 15 and 25 year terms were replaced by
                 # a single term of up to 30 years and absolute life without
                 # parole was introduced. 194 per 100,000.
                 # https://jdp-law.pl/en/newsletter/latest-changes-to-the-polish-criminal-code/
                 "justice": "ju_tough",
                 # 800+ pays PLN 800 a month for every child with no means test,
                 # and the PIT-0 law signed on 16 October 2025 exempts parents
                 # of two or more children from income tax altogether. Large
                 # transfers plus tax relief for big families is two of
                 # fa_pronatal's three limbs, and both were legislated as a
                 # natalist programme. fa_universal fails on childcare, which
                 # Poland does not cap. Loans forgiven per child is the limb
                 # Hungary has and Poland does not.
                 # https://www.gov.pl/web/family/family-800
                 # https://www.nextbigfuture.com/2025/10/poland-has-no-income-tax-to-parents-to-2-or-more-children.html
                 # Checked 2026-08-30.
                 "family": "fa_pronatal"},
     "indicators": {
         "tax_take": {"value": 36.6, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 77.1, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 6.6, "year": 2020,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 11.2, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 588.6, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.917, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 6.46, "year": 2023,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 11.6, "year": 2023,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 4.2, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 4.5, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 194.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 3.3, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.185, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "SK", "name": "Slovakia", "timezones": ["Europe/Bratislava"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # The famous 2004 flat tax is GONE: a 25% band was added in
                 # 2013 and the rates are 19% and 25%. Social contributions are
                 # 42.6% of total tax revenue, third highest in the OECD behind
                 # Czechia and Slovenia.
                 # https://www.oecd.org/en/publications/revenue-statistics-2025_3a264267-en/full-report/tax-revenue-trends-1965-2024_98c75833.html
                 "tax": "tax_continental",
                 # Three competing health insurers, two of them private and for
                 # profit, compulsory membership, no refusals.
                 "healthcare": "hc_insurance",
                 # Free full-time study at public universities, and 68% of upper
                 # secondary pupils in vocational programmes, level with the
                 # Netherlands and Austria.
                 # https://ec.europa.eu/eurostat/web/products-eurostat-news/-/edn-20201109-1
                 "education": "ed_vocational",
                 # 2.5% social rental stock and about 93% owner-occupation after
                 # the 1990s privatisation. OECD PH3.1 records that Slovak
                 # housing allowance spending is not even reported.
                 "housing": "ho_market",
                 # A points-based earnings-related first pillar. The second
                 # pillar has been automatic entry with a two-year opt-out since
                 # 2023, which is auto-enrolment and not compulsory saving; that
                 # is the same reading applied to Ireland's 2025 scheme above,
                 # so this is not re_super.
                 "retirement": "re_earnings",
                 # NUCLEAR IS MOST OF SLOVAK POWER, which is true of only three
                 # countries and France is the other one in this file. Five
                 # VVER-440 reactors at Bohunice and Mochovce ran 61% of
                 # generation in 2024 and the fleet is heading for about 70%
                 # with Mochovce 4. The grid is 94.9 g/kWh, the cleanest of the
                 # eight coded here by 44 points. Slovakia also runs a
                 # deposit-return scheme, but en_deposit's first limb is a clean
                 # grid AND that option is Germany's at 329.7, so the nuclear
                 # claim is the specific one.
                 # https://world-nuclear.org/information-library/country-profiles/countries-o-s/slovakia
                 # https://balkangreenenergynews.com/slovakia-set-to-overtake-france-in-nuclear-power-share-as-it-readies-to-start-up-new-reactor/
                 # Checked 2026-08-30.
                 "energy": "en_nuclear",
                 "speech": "sp_hate_limits", "voting": "vo_proportional",
                 "work": "wo_minimum", "defence": "de_alliance",
                 # Eight years of continuous permanent residence to naturalise.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_controlled",
                 # 152 per 100,000, high by west European standards, but the
                 # February 2024 criminal code amendment cut penalties for a
                 # list of offences, roughly halved limitation periods and
                 # widened suspended sentences. A country that has just
                 # legislated shorter sentences is not ju_tough, and this is the
                 # cell that separates Slovakia from Czechia at 174.
                 # https://www.osw.waw.pl/en/publikacje/analyses/2024-02-12/slovakia-controversial-changes-to-criminal-law-and-a-dispute
                 "justice": "ju_standard",
                 # The child allowance is universal, paid regardless of income,
                 # unlike the means-tested schemes in Czechia, Slovenia and
                 # Croatia.
                 # https://ec.europa.eu/social/main.jsp?catId=1127&intPageId=4761&langId=en
                 "family": "fa_universal"},
     "indicators": {
         "tax_take": {"value": 35.6, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 78.9, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.7, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 2.5, "year": 2021,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 7.4, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 94.9, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.765, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 7.44, "year": 2023,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 27.6, "year": 2024,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 2.0, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 5.9, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 152.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.1, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.2, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "SI", "name": "Slovenia", "timezones": ["Europe/Ljubljana"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # Five income tax bands running to 50%, the steepest of the
                 # eight, and social contributions at 42.9% of total tax
                 # revenue, second highest in the OECD. A 38.3% take.
                 # https://www.oecd.org/en/publications/revenue-statistics-2025_3a264267-en/full-report/tax-revenue-trends-1965-2024_98c75833.html
                 "tax": "tax_continental",
                 # Compulsory insurance through a single carrier, the ZZZS. The
                 # complementary insurance that covered co-payments was
                 # abolished on 1 January 2024 and replaced by a flat COMPULSORY
                 # health contribution, so the compulsion got stronger, not
                 # weaker. Out-of-pocket spending is 13%, below the EU average.
                 # https://eurohealthobservatory.who.int/publications/i/slovenia-health-system-summary-2024
                 "healthcare": "hc_insurance",
                 # Free full-time study, 5.3% of GDP on education, the highest
                 # of the eight, and 71% of upper secondary pupils in vocational
                 # programmes, the joint highest in the EU with Czechia.
                 # https://ec.europa.eu/eurostat/web/products-eurostat-news/-/edn-20201109-1
                 "education": "ed_vocational",
                 "housing": "ho_market",
                 # Earnings-related state pension at 10.6% of GDP. The second
                 # pillar is voluntary and occupational except for hazardous
                 # occupations, which is what separates this cell from Croatia's
                 # and Latvia's compulsory funded accounts.
                 "retirement": "re_earnings",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 "voting": "vo_proportional",
                 # 83.1% bargaining coverage, the highest in central and eastern
                 # Europe and inside the band of the countries already on this
                 # option.
                 "work": "wo_bargaining",
                 # NATO, no conscription, and 1.3% of GDP, the lowest military
                 # burden in the alliance.
                 "defence": "de_alliance",
                 # Ten years of residence and no dual nationality in the
                 # standard case, which is the Austrian test applied above.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_controlled",
                 # 69 per 100,000, the lowest of the eight by 59 points and in
                 # the band of Norway, Denmark and the Netherlands rather than
                 # its neighbours. This is one of the two cells separating
                 # Slovenia from Croatia.
                 "justice": "ju_rehab",
                 # The child allowance is income-tested. What Slovenia does have
                 # is cheap near-universal childcare, but fa_universal needs
                 # both limbs and the payment limb fails.
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 38.3, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 73.2, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 5.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 4.7, "year": 2018,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 10.6, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 183.3, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.691, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 11.49, "year": 2022,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 83.1, "year": 2016,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.3, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 14.9, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 69.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 1.9, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.182, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "HR", "name": "Croatia", "timezones": ["Europe/Zagreb"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # A 38.4% take, the highest of the eight, on a two-band income
                 # tax whose rates municipalities set between 15% and 23% and
                 # 25% and 34%, plus 20% employee and 16.5% employer
                 # contributions. Not flat and not middling.
                 # https://taxsummaries.pwc.com/croatia/individual/other-taxes
                 "tax": "tax_continental",
                 # Compulsory insurance through a single carrier, the HZZO, with
                 # supplementary cover for co-payments alongside it. 84.0%
                 # public share.
                 "healthcare": "hc_insurance",
                 # Free full-time study at public universities, and 69% of upper
                 # secondary pupils in vocational programmes.
                 # https://ec.europa.eu/eurostat/web/products-eurostat-news/-/edn-20201109-1
                 "education": "ed_vocational",
                 # About 91% owner-occupation and no OECD social rental figure
                 # at all, which is the Greek pattern: the measured cell is
                 # absent because there is essentially nothing to measure. The
                 # state's housing instrument is subsidised purchase through
                 # APN, not rental.
                 "housing": "ho_market",
                 # THE MENU HAS NO OPTION FOR AN EARNINGS-RELATED STATE PENSION
                 # PLUS A COMPULSORY FUNDED ACCOUNT, and Croatia is one of the
                 # two countries here that kept the mandatory second pillar it
                 # legislated. 5% of gross wage goes into an individual account
                 # for everyone born after 1962, and since 2021 there is a
                 # means-tested national allowance for over-65s with no pension
                 # entitlement. re_super is coded for the compulsory-saving limb
                 # that no other option carries; its "means-tested pension" limb
                 # describes the residual allowance, not the main pillar, and
                 # 8.9% of GDP is well above the option's derived 6.4. This is
                 # one of the two cells separating Croatia from Slovenia.
                 # https://cms.law/en/int/expert-guides/cms-expert-guide-to-pensions/croatia
                 # Checked 2026-08-30.
                 "retirement": "re_super",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 "voting": "vo_proportional",
                 # Coverage reached 60.4% of the workforce by December 2024,
                 # up from 46.5% in 2021, on twelve sectoral agreements that
                 # extend by law to every employee in the sector, members or
                 # not. That is the mechanism this option names.
                 # https://www.oecd.org/en/publications/oecd-reviews-of-labour-market-and-social-policies-croatia-2025_90b78cc3-en/full-report/making-best-use-of-croatia-s-labour-force-potential_65e5096c.html
                 "work": "wo_bargaining",
                 # NATO at 1.8% of GDP. Croatia legislated a two-month
                 # compulsory basic military training in 2025 with the first
                 # intake in 2026, which is nowhere near de_conscript's twelve
                 # months and large standing force.
                 "defence": "de_alliance",
                 # Eight years of residence and renunciation of the previous
                 # citizenship in the standard case.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_controlled",
                 "justice": "ju_standard",
                 # The doplatak za djecu is explicitly means-tested: a household
                 # over the income threshold gets nothing.
                 # https://www.ijf.hr/upload/files/file/ENG/newsletter/118.pdf
                 "family": "fa_targeted"},
     "indicators": {
         "tax_take": {"value": 38.4, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 84.0, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.1, "year": 2021,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "pension_spend": {"value": 8.9, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 158.5, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.743, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 7.04, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "military_burden": {"value": 1.8, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 13.6, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 128.0, "year": 2024,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.0, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.149, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "LT", "name": "Lithuania", "timezones": ["Europe/Vilnius"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # NOT ESTONIA'S CELL, which is the thing to check here. The
                 # flat rate ended in 2019: income tax is 20% and 32%, and the
                 # 2019 reform folded employer contributions into gross pay, so
                 # the payroll wedge sits on the employee at 19.5%. A 33.1%
                 # take, the lowest of the eight, on progressive rates.
                 # https://www.oecd.org/en/publications/taxing-wages-2026_3a5169ef-en/full-report/lithuania_a4118e07.html
                 "tax": "tax_anglo",
                 # Compulsory health insurance financed by an earmarked
                 # contribution and administered by the VLK, separately from the
                 # state budget. This is the cell that separates Lithuania from
                 # Latvia, whose service is funded out of general taxation.
                 "healthcare": "hc_insurance",
                 # State-funded places are awarded on exam score and carry no
                 # tuition, and the majority of students hold one; Eurydice puts
                 # Lithuania in the 30% to 50% fee-paying band, with Hungary.
                 # Latvia is the one that crosses the line at 57.2%.
                 # https://eurydice.eacea.ec.europa.eu/data-and-visuals/national-student-fees
                 "education": "ed_free",
                 # 0.8% social rental stock, the lowest figure in this file, and
                 # about 89% owner-occupation.
                 "housing": "ho_market",
                 # The general part of the state pension is a flat amount paid
                 # from the state budget, and the second pillar stopped being
                 # automatic: the Seimas ended auto-enrolment from 2026 and
                 # opened a two-year window to 31 December 2027 for participants
                 # to withdraw what they had saved. Saving is now encouraged and
                 # not required, which is re_flat, and 6.5% of GDP is exactly
                 # this option's derived value.
                 # https://socmin.lrv.lt/en/news/reform-approved-second-pillar-pension-scheme-to-become-more-attractive-and-flexible/
                 # Checked 2026-08-30.
                 "retirement": "re_flat",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 # A MIXED SYSTEM AND THE MENU HAS NO CELL FOR ONE. 71 of the
                 # 141 Seimas seats are single-member constituencies decided by
                 # two-round majority and 70 are national list PR, allocated in
                 # parallel rather than compensating. A majority of the seats is
                 # majoritarian, and the Gallagher index was 13.58 in 2024, the
                 # highest of the eight and well above vo_proportional's 4.20.
                 # Coded on the tier that holds more seats, and on
                 # proportionality, which is what this domain's axis measures.
                 # The detail's "most votes wins" describes a runoff loosely.
                 "voting": "vo_fptp",
                 # 29.0% bargaining coverage against a statutory minimum wage.
                 "work": "wo_minimum",
                 # NATO. Conscription was reinstated in 2015, but 3,865 of the
                 # 25,149 eligible men were called up in 2025, about 15%, so
                 # "everyone serves" is false and de_conscript is out. The
                 # burden, 3.1% of GDP, is well above this option's 1.9.
                 # https://www.baltictimes.com/conscription_list_for_2025_published_in_lithuania/
                 "defence": "de_alliance",
                 # Ten years of permanent residence and no dual nationality; the
                 # 2019 referendum to allow it failed.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_controlled",
                 "justice": "ju_standard",
                 # A universal child benefit since 2018, paid for every child
                 # under 18 with no means test, EUR 129.50 a month from January
                 # 2026 with supplements on top for large and low-income
                 # families.
                 # https://ec.europa.eu/social/BlobServlet?docId=20686&langId=en
                 "family": "fa_universal"},
     "indicators": {
         "tax_take": {"value": 33.1, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 65.0, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 0.8, "year": 2020,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; share computed against the previous year's total dwelling stock"},
         "pension_spend": {"value": 6.5, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 138.4, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.917, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 13.58, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 29.0, "year": 2023,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 3.1, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 6.1, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 154.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.8, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.15, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "LV", "name": "Latvia", "timezones": ["Europe/Riga"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # ALSO NOT ESTONIA'S CELL. Latvia's flat 23% ended in 2018 and
                 # the 2025 reform left two rates, 25.5% and 33%. A 34.9% take
                 # on progressive rates is the middle of tax_anglo.
                 # https://www.oecd.org/en/publications/revenue-statistics-2025_b1943459-en/latvia_96bd4e8f-en.html
                 "tax": "tax_anglo",
                 # THE ONE OF THE EIGHT THAT IS NOT AN INSURANCE SYSTEM. The
                 # 2017 compulsory health insurance law was postponed and then
                 # abandoned, and the WHO observatory classifies Latvia as a
                 # tax-funded national health service. It is coded hc_mixed
                 # rather than hc_public for the same reason Denmark, Sweden,
                 # Italy and Portugal are: universal public cover with a private
                 # tier people pay to use. Out-of-pocket spending is 27% of
                 # health spending, among the highest in the EU, and the public
                 # share of 59.5% is the lowest of the eight.
                 # https://eurohealthobservatory.who.int/publications/i/latvia-health-system-summary-2024
                 # Checked 2026-08-30.
                 "healthcare": "hc_mixed",
                 # MOST LATVIAN STUDENTS PAY. In 2024/25, 57.2% were private
                 # contributors paying tuition and 42.8% held a state-budget
                 # place awarded on entrance marks, so ed_free's "no tuition at
                 # any level" is false for the majority. Universities set the
                 # fee on paying places and support is largely by state-
                 # guaranteed loan. The imperfect limb is that two in five do
                 # study free, which no ed_market country offers.
                 # https://stat.gov.lv/en/statistics-themes/education/higher-education/press-releases/22128-topicalities-higher-education
                 # Checked 2026-08-30.
                 "education": "ed_market",
                 # 1.9% social rental stock and about 82% owner-occupation.
                 "housing": "ho_market",
                 # The second country here that kept its compulsory funded
                 # pillar: 6% of the 20% pension contribution goes to a
                 # mandatory individual account, and there is a means-tested
                 # state social security benefit under it. Same reading and same
                 # caveat as Croatia above: the first pillar is a notional
                 # defined contribution scheme rather than a means-tested
                 # pension, and 7.5% of GDP is above the option's derived 6.4.
                 # https://www.imf.org/-/media/files/publications/selected-issues-papers/2025/english/sipea2025134.pdf
                 "retirement": "re_super",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 # Pure list PR for the Saeima across five districts with a 5%
                 # threshold, unlike Lithuania's half-majoritarian Seimas.
                 "voting": "vo_proportional",
                 "work": "wo_minimum",
                 # NATO at 3.3% of GDP. The State Defence Service Law of 2023
                 # obliges every male citizen to serve eleven months, but only
                 # 1,076 conscripts had begun service in the first two years, so
                 # "everyone serves" is a law rather than a fact yet and
                 # de_conscript would over-claim.
                 # https://www.fpri.org/article/2025/06/latvias-renewed-conscription-turns-two/
                 "defence": "de_alliance",
                 # Five years of permanent residence and dual nationality
                 # permitted with EU, EEA and NATO states, which is the Estonian
                 # cell rather than the Lithuanian one.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_open",
                 # 188 per 100,000, second highest of the eight.
                 "justice": "ju_tough",
                 # The family state benefit is paid for every child with no
                 # means test and rises steeply with the number of children:
                 # EUR 25 a month for one, EUR 100 each for four or more.
                 # https://eng.lsm.lv/article/society/society/state-family-benefit-to-increase-from-next-year-in-latvia.a403442/
                 "family": "fa_universal"},
     "indicators": {
         "tax_take": {"value": 34.9, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 59.5, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 1.9, "year": 2016,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 7.5, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 138.8, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.932, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 10.65, "year": 2022,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 25.8, "year": 2022,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 3.3, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 11.8, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 188.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.9, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.133, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "IS", "name": "Iceland", "timezones": ["Atlantic/Reykjavik"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # NOT tax_nordic, on the number. Iceland's tax take is 36.9% of
                 # GDP in 2024, fourteenth of the thirty-eight OECD members and
                 # 2.8 points above the OECD average, against 41 to 44 for the
                 # four countries on tax_nordic. The structure argues the other
                 # way, an income-tax-heavy mix and a 24% VAT, but the level is
                 # nine points below the option and three above tax_anglo's. It
                 # reads low for a Nordic because the second pension pillar is
                 # funded rather than paid out of tax: employers pay in at least
                 # 11.5% of wages and employees 4%, and the only general employer
                 # social contribution is 6.35%.
                 # https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/12/revenue-statistics-2025-country-notes_3708be73/iceland_af992b4b/43c3175c-en.pdf
                 # Checked 2026-08-30.
                 "tax": "tax_anglo",
                 "healthcare": "hc_mixed",
                 # Public universities charge a registration fee of about
                 # ISK 75,000 and no tuition, and Iceland's 7.3% of GDP is the
                 # highest public education spend of the forty-five.
                 "education": "ed_free",
                 "housing": "ho_subsidy",
                 # Mandatory funded occupational pensions, minimum 15.5% of wages
                 # between employer and employee, on top of a means-tested state
                 # pension. Same design as the Netherlands, Switzerland and
                 # Australia. The 2.9% of GDP public pension spend is low FOR
                 # THAT REASON and is not evidence against the cell.
                 # https://www.norden.org/en/info-norden/icelandic-pension-system
                 "retirement": "re_super",
                 # THE MEASURED CELL DISAGREES WITH THIS CHOICE AND NEITHER SIDE
                 # IS WRONG. Iceland's electricity is 100% renewable, about 70%
                 # hydro and 30% geothermal, at 27.8 g/kWh, the cleanest grid in
                 # the file. That is en_hydro's first limb. Its second limb, a
                 # network good enough that a car is optional, is decisively
                 # false: Iceland has no railway at all, buses are the only
                 # public transport, and car ownership is among the two or three
                 # highest in the world at over 630 per 1,000 people. The
                 # 2026-08-29 review moved NL, JP and SG off en_hydro for having
                 # the transport without the grid, and Iceland is the mirror of
                 # that case. It has priced carbon since 2010 and people drive,
                 # which is what en_carbon_tax says and is true, so it is coded
                 # here and the grid figure is the honest tension.
                 # https://www.guinnessworldrecords.com/world-records/highest-rate-of-car-ownership
                 # https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/02/effective-carbon-rates-2025-country-notes_b08aeef1/iceland_37de81ee/47cd4da8-en.pdf
                 # Checked 2026-08-30.
                 "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional",
                 # No statutory minimum wage at all. Pay floors are set by
                 # sectoral collective agreements, which cover about 90% of
                 # employees.
                 "work": "wo_bargaining",
                 # No armed forces of any kind, 0.0% of GDP, and a NATO founding
                 # member since 1949. The extreme end of de_alliance rather than
                 # de_neutral, which requires no alliance.
                 "defence": "de_alliance",
                 "immigration": "im_open",
                 # 36 per 100,000, the lowest of the forty-five and barely half
                 # the ju_rehab hand value of 60.
                 "justice": "ju_rehab",
                 # Twelve months of leave split six and six between parents for
                 # children born from 2021, of which only six weeks is
                 # transferable, plus municipal childcare and 3.8% of GDP, the
                 # highest family spend in the file. THE CAVEAT: Icelandic child
                 # benefit is income-tested, so fa_leave's universal per-child
                 # benefit does not hold. Coded on the leave, which is the
                 # option's distinguishing claim, and on the spend.
                 # https://pub.norden.org/temanord2025-547/parental-leave-in-iceland.html
                 # Checked 2026-08-30.
                 "family": "fa_leave"},
     "indicators": {
         "tax_take": {"value": 36.9, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 83.6, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 7.3, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 11.1, "year": 2016,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings; may also include student housing"},
         "pension_spend": {"value": 2.9, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 27.8, "year": 2024,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.846, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 5.31, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 90.0, "year": 2024,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 0.0, "year": 2025,
                       "source": "SIPRI via Our World in Data, military expenditure % of GDP; SIPRI records Iceland at zero for every year of the series, it has no standing armed forces"},
         "foreign_born": {"value": 25.1, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 36.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 3.8, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.137, "year": 2019,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "LU", "name": "Luxembourg", "timezones": ["Europe/Luxembourg"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     # LUXEMBOURG'S SPENDING RATIOS ARE ALL DIVIDED BY THE WRONG POPULATION.
     # Roughly half the people who work in Luxembourg live in France, Belgium or
     # Germany and commute in. They produce the GDP and are not residents, so
     # every "% of GDP" cell on this row reads low against countries that do the
     # same thing: education 3.7, pensions 8.6, health and family alike. Where a
     # cell below disagrees with its axis, that is the first thing to suspect.
     "choices": {"tax": "tax_continental",
                 # Compulsory statutory health insurance through the Caisse
                 # Nationale de Sante, a single public fund since the 2008 merger
                 # rather than the competing insurers of the Belgian or Dutch
                 # model, but Bismarckian and compulsory, which is the option's
                 # claim. Public share 86.9%, the highest of the forty-five.
                 # https://cns.public.lu/en/employeur/bases-bonnes-pratiques/assurance-maladie-bref.html
                 "healthcare": "hc_insurance",
                 # About EUR 800 a year at the University of Luxembourg. Not
                 # ed_vocational: apprenticeship is a real track but not where
                 # most students go.
                 "education": "ed_free",
                 "housing": "ho_market",
                 # THE CELL THAT DISAGREES MOST SHARPLY WITH ITS OWN AXIS AND IS
                 # STILL RIGHT. Pension spend of 8.6% of GDP sits on re_earnings'
                 # 9.0, not re_generous' 14.0, so the number says one thing. Both
                 # of the option's own limbs say the other, and on the OECD's
                 # authority: Pensions at a Glance 2025 names Luxembourg among
                 # the countries with a net replacement rate of 85% or more, AND
                 # lists it with Colombia and Slovenia as the three lowest future
                 # normal retirement ages in the OECD at 62. Early retirement
                 # runs from 57 on a forty-year career and the effective
                 # retirement age, 60 in 2022, is the lowest in the OECD. A high
                 # replacement rate and a low pension age is what re_generous
                 # says. The 8.6% is the cross-border denominator described
                 # above, plus a young population. This cell is why check_spread
                 # now reports re_generous as wide, and the width is real.
                 # https://www.oecd.org/en/publications/2025/11/pensions-at-a-glance-2025_76510fe4/full-report/current-retirement-ages_0f63b747.html
                 # https://www.oecd.org/en/publications/oecd-economic-surveys-luxembourg-2025_803b3ea1-en/full-report/securing-the-pension-system-for-future-generations_cc54d632.html
                 # Checked 2026-08-30.
                 "retirement": "re_generous",
                 "energy": "en_carbon_tax", "speech": "sp_hate_limits",
                 # Compulsory in law, unpunished since 1964. Same menu gap as
                 # Belgium and Greece; coded on proportionality.
                 "voting": "vo_proportional",
                 # The highest statutory minimum wage in the EU, about EUR 2,570
                 # a month, and collective bargaining coverage of 57% that is
                 # largely company-level, with sectoral extension available but
                 # not the norm. Between wo_minimum's 28 and wo_bargaining's 80,
                 # and coded on the statutory floor doing the work. Switzerland
                 # sits on wo_minimum at a similar coverage.
                 # https://www.etui.org/sites/default/files/2025-06/Luxembourg_Collective%20bargaining%20and%20minimum%20wage%20regime_2025.pdf
                 # Checked 2026-08-30.
                 "work": "wo_minimum",
                 "defence": "de_alliance",
                 # 51.2% foreign-born, the highest of the forty-five outside the
                 # Gulf, and overwhelmingly Portuguese, French and Italian EU
                 # citizens. The purest case of open borders within a bloc in the
                 # file, and it pulls this option's derived axis value up.
                 "immigration": "im_open",
                 "justice": "ju_standard",
                 # The allocation pour l'avenir des enfants is paid per child
                 # without a means test, and every child gets twenty hours a week
                 # of free childcare.
                 "family": "fa_universal"},
     "indicators": {
         "tax_take": {"value": 41.5, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 86.9, "year": 2024,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 3.7, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 1.6, "year": 2011,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 8.6, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 123.4, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.957, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 5.96, "year": 2023,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 57.3, "year": 2022,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 1.0, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 51.2, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 110.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 3.2, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.165, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "HU", "name": "Hungary", "timezones": ["Europe/Budapest"],
     "nonTaxRevenue": 0.0,
     "matchable": True,
     "choices": {
                 # THE ONLY GENUINELY FLAT RATE OF THE EIGHT. Personal income
                 # tax is 15% on all income and the law carries it into 2026.
                 # Estonia's cell is not copied across: Czechia, Slovakia,
                 # Lithuania and Latvia all abolished their flat rates between
                 # 2013 and 2025, and Poland, Slovenia and Croatia never had
                 # one. The exemptions Hungary layers on top run the other way
                 # from progressivity, exempting mothers of four or more
                 # children entirely.
                 # https://www.oecd.org/en/publications/taxing-wages-2026_3a5169ef-en/full-report/hungary_11ca4ba3.html
                 # Checked 2026-08-30.
                 "tax": "tax_flat",
                 # Compulsory health insurance financed by an earmarked
                 # contribution, administered by the NEAK.
                 "healthcare": "hc_insurance",
                 # State-funded places carry no tuition and hold the majority of
                 # students; Eurydice puts Hungary in the 30% to 50% fee-paying
                 # band with Lithuania. Education spending is 3.8% of GDP, the
                 # lowest of the eight, against this option's derived 5.9: free
                 # and underfunded are different claims and the axis measures
                 # the second, which is the reading already applied to Greece.
                 # https://eurydice.eacea.ec.europa.eu/data-and-visuals/national-student-fees
                 "education": "ed_free",
                 # 2.6% social rental stock and about 91% owner-occupation. THE
                 # MENU HAS NO CELL FOR WHAT HUNGARY ACTUALLY DOES, which is
                 # large-scale subsidised owner-occupation through CSOK, the
                 # forgivable family loans and the 3% Otthon Start mortgage.
                 # ho_singapore is the only option with a state that puts people
                 # into ownership, and it requires the state to build the flats,
                 # which Hungary does not. Coded on the true half: the stock is
                 # privately owned and there is almost no social rental sector.
                 "housing": "ho_market",
                 # The mandatory private second pillar was effectively
                 # nationalised in 2010 and 2011, when all but a fraction of
                 # members were moved back into the state scheme. What is left
                 # is a single earnings-related state pension at 7.6% of GDP.
                 "retirement": "re_earnings",
                 "energy": "en_carbon_tax",
                 # THE CELL IN THIS FILE MOST AT ODDS WITH ITS OWN AXIS, and it
                 # is recorded rather than smoothed over. Section 332 of the
                 # Criminal Code makes incitement to violence or hatred against
                 # a national, ethnic, racial or religious group, or a group
                 # defined by disability or sexual orientation, an offence
                 # carrying up to three years, which is exactly what this option
                 # claims. Hungary measures 0.493 on V-Dem freedom of expression
                 # and alternative sources of information, the lowest of any
                 # country on this option by 0.20 and nearer Singapore's 0.40
                 # than to Slovenia's 0.691. The axis is low because of media
                 # ownership and state advertising, which is the "alternative
                 # sources of information" half of what V-Dem measures, and not
                 # because criticism is prosecuted: sp_restricted's detail is
                 # false here and sp_order describes a standing public-order
                 # speech regime Hungary does not have. Same shape as the
                 # Japanese caveat in policies.py, and the first cell to revisit
                 # if a sixth speech option is ever added.
                 # https://hatecrime.osce.org/hate-crime-legislation-hungary
                 # Checked 2026-08-30.
                 "speech": "sp_hate_limits",
                 # MIXED-MEMBER MAJORITARIAN, and the menu has no cell for one.
                 # 106 of the 199 seats are single-member constituencies decided
                 # by plurality in one round, the 93 list seats are allocated in
                 # parallel rather than compensating, and losing and surplus
                 # constituency votes are added to the winner's list total. In
                 # 2022 that turned 54% of the vote into 135 of 199 seats, and
                 # the Gallagher index reads 11.76. Coded on the tier that holds
                 # more seats and on proportionality, which is the domain's
                 # axis; vo_proportional's "seats match the national vote share"
                 # is the more clearly false claim.
                 # https://commonslibrary.parliament.uk/research-briefings/cbp-9519/
                 # Checked 2026-08-30.
                 "voting": "vo_fptp",
                 # 20.4% bargaining coverage against a statutory minimum wage.
                 "work": "wo_minimum", "defence": "de_alliance",
                 # Eight years of residence, and the 2023 Guest Worker Act caps
                 # third-country workers at three years with no family
                 # reunification and no route to settlement. The liberal limb of
                 # Hungarian citizenship law is simplified naturalisation for
                 # ethnic Hungarians abroad, which is descent, not intake.
                 # https://www.europarl.europa.eu/RegData/etudes/BRIE/2025/769502/EPRS_BRI(2025)769502_EN.pdf
                 "immigration": "im_controlled",
                 # 206 per 100,000, the highest of the eight, with life
                 # imprisonment without parole and a three-strikes rule making
                 # it mandatory for repeat violent offenders.
                 # https://helsinki.hu/en/submission-to-the-ombudsman-on-the-three-strikes-rule/
                 "justice": "ju_tough",
                 # THE fa_pronatal TAG IN policies.py IS CORRECT AND SURVIVES.
                 # Large transfers, the baby-expecting loan forgiven at three
                 # children, and lifetime income tax exemption for mothers of
                 # four or more, extended to mothers of two under forty from
                 # 2026. All three of the option's limbs hold, which is true of
                 # no other country in this file. The measured family_spend of
                 # 2.3% of GDP is below the option's 2.6 because OECD SOCX
                 # counts cash and in-kind benefits and most of Hungary's
                 # programme is delivered as tax relief.
                 # https://www.oecd.org/en/publications/taxing-wages-2026_3a5169ef-en/full-report/hungary_11ca4ba3.html
                 # Checked 2026-08-30.
                 "family": "fa_pronatal"},
     "indicators": {
         "tax_take": {"value": 34.4, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 73.4, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 3.8, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 2.6, "year": 2018,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "pension_spend": {"value": 7.6, "year": 2021,
                       "source": "OECD SOCX, public expenditure on old age and survivors cash benefits % of GDP"},
         "grid_carbon": {"value": 163.0, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.493, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 11.76, "year": 2022,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "bargaining": {"value": 20.4, "year": 2022,
                       "source": "OECD/AIAS ICTWSS via OECD Data Explorer, collective bargaining coverage, % of employees with the right to bargain"},
         "military_burden": {"value": 2.2, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 7.1, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 206.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"},
         "family_spend": {"value": 2.3, "year": 2021,
                       "source": "OECD SOCX, public expenditure on family benefits (cash and in kind) % of GDP"},
         "redistribution": {"value": 0.143, "year": 2023,
                       "source": "OECD Income Distribution Database, market Gini less disposable Gini, whole population"}
     }},
    {"code": "UY", "name": "Uruguay", "timezones": ["America/Montevideo"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "tax_take": {"value": 27.3, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 72.4, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.8, "year": 2023,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "grid_carbon": {"value": 80.4, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.931, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 2.14, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "military_burden": {"value": 2.3, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 4.7, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 449.0, "year": 2024,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
    {"code": "TW", "name": "Taiwan", "timezones": ["Asia/Taipei"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "grid_carbon": {"value": 633.2, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.838, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 8.19, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "military_burden": {"value": 2.1, "year": 2025,
                       "source": "SIPRI via Our World in Data, military expenditure % of GDP"},
         "foreign_born": {"value": 4.9, "year": 2024,
                       "source": "UN DESA via Our World in Data, international migrant stock % of population"},
         "incarceration": {"value": 280.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
    {"code": "SA", "name": "Saudi Arabia", "timezones": ["Asia/Riyadh"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "health_public": {"value": 77.8, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.5, "year": 2023,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "grid_carbon": {"value": 692.0, "year": 2024,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.092, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": None, "year": 2025,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election; no entry",
                       "na_reason": "no national legislative election contested by party lists, so vote shares and seat shares cannot be compared"},
         "military_burden": {"value": 7.3, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 40.3, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 140.0, "year": 2019,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
    {"code": "QA", "name": "Qatar", "timezones": ["Asia/Qatar"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "health_public": {"value": 83.0, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 3.2, "year": 2020,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "grid_carbon": {"value": 581.5, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.055, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": None, "year": 2025,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election; no entry",
                       "na_reason": "no national legislative election contested by party lists, so vote shares and seat shares cannot be compared"},
         "military_burden": {"value": 6.5, "year": 2022,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 76.7, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 69.0, "year": 2022,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
    {"code": "KW", "name": "Kuwait", "timezones": ["Asia/Kuwait"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "health_public": {"value": 88.5, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 6.4, "year": 2024,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "grid_carbon": {"value": 635.3, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.532, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": None, "year": 2025,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election; no entry",
                       "na_reason": "no national legislative election contested by party lists, so vote shares and seat shares cannot be compared"},
         "military_burden": {"value": 4.8, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 67.3, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 101.0, "year": 2023,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
    {"code": "MT", "name": "Malta", "timezones": ["Europe/Malta"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "tax_take": {"value": 28.7, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 66.0, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.7, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "social_housing": {"value": 5.5, "year": 2011,
                       "source": "OECD Affordable Housing Database PH4.2, social rental dwellings % of total dwellings"},
         "grid_carbon": {"value": 484.0, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.829, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 2.24, "year": 2022,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "military_burden": {"value": 0.5, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 37, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 120.0, "year": 2025,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
    {"code": "CY", "name": "Cyprus", "timezones": ["Asia/Nicosia", "Asia/Famagusta"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "health_public": {"value": 76.8, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 4.7, "year": 2022,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "grid_carbon": {"value": 489.0, "year": 2025,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.812, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 6.44, "year": 2021,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "military_burden": {"value": 1.6, "year": 2024,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 14.9, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 117.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
    {"code": "PA", "name": "Panama", "timezones": ["America/Panama"],
     "nonTaxRevenue": 0.0,
     "matchable": False,
     "choices": {},
     "indicators": {
         "tax_take": {"value": 11.3, "year": 2024,
                       "source": "OECD Global Revenue Statistics Database, total tax revenue (all levels of government) % of GDP"},
         "health_public": {"value": 51.2, "year": 2023,
                       "source": "WHO GHED, domestic general government health expenditure % of current health expenditure"},
         "education_spend": {"value": 2.5, "year": 2023,
                       "source": "World Bank, government expenditure on education % of GDP"},
         "grid_carbon": {"value": 221.2, "year": 2024,
                       "source": "Our World in Data / Ember, carbon intensity of electricity generation gCO2 per kWh"},
         "expression": {"value": 0.812, "year": 2025,
                       "source": "V-Dem via Our World in Data, freedom of expression and alternative sources of information index (v2x_freexp_altinf), central estimate"},
         "disproportionality": {"value": 9.77, "year": 2024,
                       "source": "Gallagher, Election indices (Trinity College Dublin), 16 June 2025 edition, least squares index at the most recent national legislative election"},
         "military_burden": {"value": 1.0, "year": 1999,
                       "source": "World Bank / SIPRI, military expenditure % of GDP"},
         "foreign_born": {"value": 10.6, "year": 2024,
                       "source": "UN DESA / World Bank, international migrant stock % of population"},
         "incarceration": {"value": 522.0, "year": 2026,
                       "source": "World Prison Brief, prison population rate per 100,000 of national population"}
     }},
]
