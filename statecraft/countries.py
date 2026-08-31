"""Forty-five countries, all of them matchable.

TWO KINDS OF COUNTRY LIVE IN THIS FILE and the difference is `matchable`.

A MATCHABLE country has all thirteen `choices` and can be the answer the reveal
gives. There are forty-five of them: the launch twenty, plus Ireland, Italy,
Spain, Portugal, Austria, Belgium, Greece, Luxembourg and Iceland, then Czechia,
Poland, Slovakia, Slovenia, Croatia, Lithuania, Latvia and Hungary on 30/08/2026,
and finally Uruguay, Taiwan, Saudi Arabia, Qatar, Kuwait, Malta, Cyprus and
Panama on 31/08/2026.

A MEASURED-ONLY country has `choices == {}` and `matchable == False`. It can
appear on an axis and it counts towards indicator coverage, but it can never be
a nearest neighbour, because there is nothing to match against. Twenty-five were
added on 30/08/2026 and THERE ARE NONE LEFT: seventeen were coded the same day
and the last eight on 31/08/2026. The category and every guard that enforces it
are deliberately kept, in `matchable`, in match.js and in both test files,
because the next country added will arrive measured-only again. An empty
`choices` must keep failing loudly rather than quietly scoring zero.

This was the build-out predicted below: the axes are automatable and went wide
first, and the matrix followed one country at a time, because every matrix cell
is a human judgement with a citation behind it.

THE FINAL EIGHT ARE THE ONES THE MENU WAS NOT WRITTEN FOR, and the record of
where it did not reach them is the point of that batch rather than an apology
for it. See THE MENU GAPS AFTER THE LAST EIGHT at the end of this docstring.

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

THE LAST EIGHT, coded 31/08/2026: Uruguay, Taiwan, Saudi Arabia, Qatar, Kuwait,
Malta, Cyprus and Panama. Re-measured over all 990 pairs of the forty-five.

THE CEILING DID NOT MOVE. It is still eleven and still the same four pairs,
SI HR, SE NO, IT PT and BE LU, and no pair matches on all thirteen. The closest
new pairs are UY CY, IE MT, GR CY, AE SA and AE QA, all at ten.

THE GULF DID NOT COLLAPSE INTO ONE COUNTRY, which was the risk this batch was
run to test. Against the UAE, Saudi Arabia and Qatar each differ on three cells
and Kuwait on seven; the closest Gulf pairs are AE SA and AE QA at ten. Each
difference is sourced on the row that carries it. The five cells all four share,
no income tax, a citizen health service with a private tier, an unpriced fossil
grid, no competitive national elections and a migrant majority with no path to
citizenship, are the same policy in all four and the sources say so.

THE MENU GAPS AFTER THE LAST EIGHT, which is the deliverable this batch was
really for. Everything below is a case where NO OPTION HONESTLY DESCRIBED THE
COUNTRY and the least wrong one was taken. It is the evidence for what the menu
needs before any low or middle income country is added.

  a SINGLE-PAYER health system. Taiwan's NHI and Cyprus's GESY are one
  compulsory insurer contracting private providers, and hc_insurance says a
  regulated MARKET of insurers. Greece is already coded there with the same
  caveat, so this now affects three countries and is the most-repeated gap in
  the file.

  a SEGMENTED health system. Panama runs a contributory fund for formal workers
  and a separate ministry network for everyone else, which is neither
  hc_insurance nor hc_private nor hc_mixed.

  a PROGRESSIVE INCOME TAX WITH A VERY LOW TAKE. Panama collects 11.3% of GDP
  and Taiwan about 13%, against tax_anglo's 34.0. tax_minimal is the only option
  priced near them and its sentence is "no income tax", which is false of both.

  COMPULSORY VOTING THAT IS NOT PREFERENTIAL. Uruguay enforces the duty with
  fines and exam bans, and the only compulsory option in the menu is Australia's
  ranked ballot.

  MIXED-MEMBER ELECTORAL SYSTEMS, again. Taiwan and Panama join Hungary and
  Lithuania, and the two blocks were coded to opposite cells: Taiwan and Panama
  are vo_proportional and Hungary and Lithuania vo_fptp. THE RULE THAT DECIDED
  IT IS MEASURED DISPROPORTIONALITY, not the seat tiers: Taiwan's 8.19 and
  Panama's 9.77 sit inside the vo_proportional band beside Japan 8.92, Greece
  8.97 and Chile 9.58, while Hungary's 11.76 and Lithuania's 13.58 sit above it.
  Four countries now hang on a rule the menu does not state.

  AN ELECTED LEGISLATURE UNDER A HEREDITARY EXECUTIVE, and its suspension.
  Kuwait's National Assembly had real power until it was dissolved in May 2024
  and Qatar elected two-thirds of its Shura Council in 2021 before abolishing
  the elections by referendum in 2024. Both are coded vo_none, which is true
  today and cannot say that one is suspended and the other was repealed. The
  file also has one None where it needs two: no elections at all, and elections
  with no political parties, which is why Kuwait's Gallagher cell is empty.

  A CITIZEN-ONLY WELFARE STATE. Free university, free healthcare, a pension, a
  house and a child allowance in the Gulf reach citizens, who are a minority of
  residents in three of the four states. Every welfare option in the menu is
  written as though a resident is a citizen. The UAE's retirement cell raised
  this first and it now runs through twelve cells across four countries.

  A TWO-TIER LABOUR MARKET. wo_at_will and wo_minimum describe the law that
  applies; neither can say that most workers are migrants whose right to remain
  depends on an employer.

  AN INFORMAL LABOUR MARKET. About half of Panama's workforce is outside every
  contributory scheme the menu describes, which is what makes its tax, health
  and work cells all read wrong at once.

  ABOLITION OF THE ARMED FORCES. Panama abolished its military in 1990 and
  banned it in the constitution in 1994. de_neutral's "a force sized for the
  border only" is literally true of SENAFRONT and its "professional force" is
  not. Costa Rica and Iceland would hit the same wall.

  A HEAVY-SPENDING ARMS IMPORTER. Saudi Arabia spends 7.3% of GDP, the most in
  the file, with no conscription, no alliance and no bases abroad. de_power is
  the only option priced for it and it describes power projection Saudi Arabia
  does not have.

  A CLEAN GRID NOBODY PRICED. Panama is 221 g/kWh on majority hydro with no
  carbon price at all, so it is on en_fossil at 480. The energy domain assumes
  pricing and cleanliness travel together.

  STATE-SUBSIDISED OWNER-OCCUPATION, which the Central European block already
  logged for Hungary and which Saudi Arabia and Qatar now join: land grants and
  interest-free state loans that put citizens into ownership without the state
  building the housing. All three are coded ho_market, whose sentence is that
  the state does nothing.

  A MANDATORY FUNDED PILLAR BESIDE AN EARNINGS-RELATED PENSION, which the
  Central European block logged for Croatia and Latvia, and which Uruguay and
  Taiwan now join.
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
     "matchable": True,
     # Coded 31/08/2026. URUGUAY AND PANAMA WERE THE TWO THE MENU WAS LEAST
     # READY FOR, and Uruguay turned out to fit better than Panama: a
     # progressive income tax, a contributory national health fund, free
     # university and sector-wide wage councils are all things the options
     # already describe. Where it does not fit is recorded cell by cell below.
     "choices": {
                 # 27.3% of GDP, the highest tax take in Latin America and the
                 # lowest of the fifteen countries on this option. IRPF has been
                 # progressive since the 2007 reform and sits on top of a 22%
                 # VAT, so the shape of the option is right and the level is 6.7
                 # points below its 34.0. Nothing describes a progressive system
                 # collecting under 30%.
                 "tax": "tax_anglo",
                 # SNIS since 2007: FONASA is a single national fund financed by
                 # earnings-related contributions, and the insured choose between
                 # the state provider ASSE and the non-profit mutualistas. Cover
                 # is compulsory and no provider may refuse a member, which is
                 # what puts it here. Measured public share 72.4 against the
                 # option's 78.0.
                 "healthcare": "hc_insurance",
                 # UdelaR charges no tuition and is where most students go. Same
                 # gap as Greece: free and underfunded are different claims, and
                 # the 4.8% of GDP measured is 1.5 points under the option.
                 "education": "ed_free",
                 # THE FAMOUS CASE THAT DOES NOT SURVIVE THE NUMBER. FUCVAM's
                 # mutual-aid housing cooperatives are cited worldwide, but they
                 # are about 35,000 households across 730 cooperatives against a
                 # stock of roughly 1.4 million dwellings, so ho_cooperative's
                 # "a large regulated rental sector" is not true of Uruguay.
                 # Tenure is dominated by private owner-occupation.
                 # https://www.housinginternational.coop/co-ops/uruguay/
                 "housing": "ho_market",
                 # BPS pays an earnings-related contributory pension. There is
                 # also a compulsory funded AFAP pillar above an income
                 # threshold, and NO OPTION CARRIES BOTH LIMBS: re_super pairs
                 # mandatory saving with a means-tested state pension, and
                 # Uruguay's is contributory rather than means-tested.
                 "retirement": "re_earnings",
                 # A CO2 tax inside the IMESI since January 2022, at about
                 # USD 167 a tonne the highest headline carbon price in the
                 # world, though it reaches only petrol and so about a tenth of
                 # emissions. Cars are kept. The grid is 80.4 g/kWh, cleaner than
                 # every other country on this option except New Zealand, and
                 # en_hydro was rejected because Uruguay has no network that
                 # makes a car optional.
                 # https://www.iea.org/policies/19297-decree-441021-uruguay-co2-tax
                 "energy": "en_carbon_tax",
                 # Law 17.677 criminalises incitement to hatred. The measured
                 # 0.931 is the second highest in the file, above every other
                 # country on this option, which is the same known looseness the
                 # option already carries for Denmark and Canada.
                 "speech": "sp_hate_limits",
                 # THE VOLUNTARY LIMB IS FALSE AND IT IS THE CLEANEST EXAMPLE OF
                 # A MISSING CELL. Uruguay's voting is compulsory and actually
                 # enforced: a fine, doubled for public employees and public
                 # university graduates, students barred from two exam periods.
                 # Greece and Belgium were coded here on compulsory-but-unenforced
                 # grounds and Uruguay does not have that excuse. The only
                 # compulsory option in the menu is vo_preferential, and Uruguay
                 # does not use a ranked ballot, so the closed-list PR limb wins.
                 # Gallagher 2.14, the second lowest in the file.
                 "voting": "vo_proportional",
                 # The Consejos de Salarios are tripartite sector-wide wage
                 # councils whose agreements are extended erga omnes, restored in
                 # 2005 after fifteen years dormant. This is the only country
                 # outside western Europe in the file on sector bargaining and it
                 # is the strongest single cell in this row.
                 # https://journals.sagepub.com/doi/full/10.1177/14680181251326845
                 "work": "wo_bargaining",
                 # No alliance, no conscription, a volunteer force. The 2.3% of
                 # GDP is three times the option's 0.7, and the reason is that
                 # Uruguay's army is sized for UN peacekeeping export rather than
                 # for the border, which no option describes.
                 "defence": "de_neutral",
                 # BOTH LIMBS ARE LOOSER THAN THE OPTION SAYS. Entry is not
                 # selective, and legal citizenship comes in three years with
                 # family or five without, not the better part of a decade.
                 # im_open was considered and rejected: the MERCOSUR residence
                 # agreement does give nationals of nine South American states a
                 # right to reside on nationality alone, but it is applied for
                 # rather than automatic, and Chile is a signatory of the same
                 # agreement and is already coded im_controlled. Coding Uruguay
                 # differently would make the file contradict itself.
                 "immigration": "im_controlled",
                 # 449 per 100,000, the second highest in the file after Panama
                 # and well above this option's 300.
                 "justice": "ju_tough",
                 # Asignaciones Familiares under the Plan de Equidad is a
                 # non-contributory transfer to households in socioeconomic
                 # vulnerability, which is a means test.
                 # https://dds.cepal.org/bpsnc/programme?id=38
                 "family": "fa_targeted"},
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
     "matchable": True,
     # Coded 31/08/2026 AGAINST THE THINNEST MEASURED ROW IN THE FILE, 6 of 14.
     # Taiwan is in none of the World Bank, WHO GHED or OECD collections, so
     # seven of these thirteen cells have no measured axis to argue with. That
     # is a reason to cite harder, not to code more loosely, and every cell
     # below is sourced to Taiwanese law or a Taiwanese ministry rather than
     # inferred from Japan and Korea. Where the East Asian precedent decided a
     # cell, the comment says so.
     "choices": {
                 # Taiwan's tax burden is about 13 to 14% of GDP, less than half
                 # this option's 34.0 and the lowest of any developed economy
                 # here. The rates are genuinely progressive, 5% to 40%, so the
                 # shape is right and the level is not, and there is no measured
                 # tax_take cell to print the disagreement. No option describes a
                 # progressive income tax collecting under 20%.
                 "tax": "tax_anglo",
                 # SINGLE-PAYER NATIONAL HEALTH INSURANCE, AND NO OPTION SAYS SO.
                 # NHI since 1995 is compulsory, premium-financed, nobody may be
                 # refused, and the providers are overwhelmingly private on
                 # fee-for-service with copayments. What it is not is the
                 # "regulated market" of competing insurers this option
                 # describes: there is one insurer. Coded here on the same
                 # reading applied to Greece's EOPYY, which is also one fund on a
                 # contributory basis. hc_public was rejected because NHI is
                 # financed by premiums, not general taxation.
                 "healthcare": "hc_insurance",
                 # Twelve years of basic education are free, and university is
                 # not: roughly seven students in ten are at private
                 # universities, whose fees run well above the public schools'.
                 # The NT$35,000 annual subsidy for private-university students
                 # from 2024 closes about 70% of the public-private gap without
                 # removing fees.
                 # https://focustaiwan.tw/politics/202306290013
                 "education": "ed_market",
                 # Owner-occupation is around 85% and the social rental stock is
                 # a rounding error. The government's main instrument is now a
                 # rent subsidy reaching a few hundred thousand households, which
                 # is ho_subsidy's instrument, but that is roughly 3% of
                 # households against the 12% social stock ho_subsidy's axis
                 # carries, so the state role is still closer to none than to
                 # Britain's or Germany's.
                 "housing": "ho_market",
                 # Labour Insurance pays an earnings-related old-age benefit and
                 # is the pillar that matters for employees. As in Uruguay there
                 # is a compulsory funded pillar beside it, the employer's 6%
                 # into an individual account under the Labor Pension Act, and no
                 # option carries both limbs. re_super was rejected because
                 # Taiwan's state pension is not means-tested.
                 # https://law.moj.gov.tw/ENG/LawClass/LawAll.aspx?pcode=N0030020
                 "retirement": "re_earnings",
                 # THIS CELL BECAME TRUE IN 2026 AND WOULD HAVE BEEN FALSE IN
                 # 2024. The carbon fee under the Climate Change Response Act
                 # applies to 2025 emissions from 465 facilities above 25,000
                 # tonnes at NT$300 a tonne, and the first cycle was actually
                 # collected by 31 May 2026, raising close to NT$5bn. Emissions
                 # are priced and people still drive, which is exactly what the
                 # option claims.
                 # https://focustaiwan.tw/business/202606030008
                 # KNOWN WIDE AND WIDENED FURTHER: at 633.2 g/kWh Taiwan is now
                 # the dirtiest grid on an option whose marker sits at 180, ahead
                 # of Estonia's 319. That is the gap this option was already
                 # documented as carrying, since it names an instrument and the
                 # axis measures an outcome, but Taiwan stretches it further than
                 # any country on it and check_spread.py should be read with that
                 # in mind.
                 "energy": "en_carbon_tax",
                 # No hate-speech statute of the European kind; what limits
                 # speech is criminal defamation in Article 310 of the Criminal
                 # Code, upheld by the Constitutional Court in 2023. That is the
                 # same basis on which Japan and Korea were moved onto this
                 # option, and at 0.838 Taiwan sits between them.
                 "speech": "sp_hate_limits",
                 # MIXED-MEMBER MAJORITARIAN, WHICH THE MENU DOES NOT HAVE. 73 of
                 # 113 seats are single-member plurality districts, 34 are
                 # party-list PR and 6 are indigenous, and the presidency is
                 # plurality with no runoff. Gallagher is 8.19, nowhere near this
                 # option's 3.0. Coded here because Japan and Korea run the same
                 # family of system, Taiwan's 2005 reform was modelled on Japan's,
                 # and both are already on vo_proportional. Coding Taiwan
                 # vo_fptp would make the file say two things about one system.
                 "voting": "vo_proportional",
                 # A statutory wage floor under the Minimum Wage Act 2024, and
                 # collective agreement coverage in the low teens at best.
                 "work": "wo_minimum",
                 # Conscription was restored to twelve months from 1 January
                 # 2024, having been cut to four months of training in 2018. The
                 # option's words are exact. Its 4.5% of GDP is not: Taiwan
                 # measures 2.1%, less than half, because it buys a year of
                 # everyone's time cheaply and its defence spending problem is
                 # widely argued to be that it is too low rather than too high.
                 "defence": "de_conscript",
                 # Foreign-born 4.9%, several hundred thousand migrant workers on
                 # visas that do not convert, and naturalisation that has
                 # required renouncing the previous citizenship. The same shape
                 # as Japan and Korea, who are the other two on this option.
                 "immigration": "im_closed",
                 # 280 per 100,000, close to this option's 300 and the third
                 # highest in the file. Taiwan also retains and uses the death
                 # penalty, which no justice option mentions; Japan does too and
                 # sits on ju_rehab, so the file already reads these options as
                 # claims about sentence length and prison population rather than
                 # about capital punishment.
                 "justice": "ju_tough",
                 # The child-rearing allowance of NT$5,000 a month to age six had
                 # its income test removed, so it is paid to every family, and
                 # the quasi-public childcare scheme contracts private centres at
                 # capped fees. Both limbs of the option hold, which is rare.
                 # https://basicincome.org/news/2026/06/taiwan-is-moving-toward-a-child-basic-income-it-should-not-stop-half-way/
                 "family": "fa_universal"},
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
     "matchable": True,
     # ----------------------------------------------------------------------
     # THE THREE GULF ROWS, CODED 31/08/2026 AGAINST THE UAE RATHER THAN FROM
     # IT. The UAE's matrix is the calibration for this block and every cell
     # here was checked against a source of its own, because the risk in coding
     # four Gulf monarchies is that they come out as one country said four
     # times. They do not. Against the UAE's thirteen:
     #
     #   Saudi Arabia differs on three   education, retirement, family
     #   Qatar        differs on three   education, work, defence
     #   Kuwait       differs on seven   education, housing, speech, work,
     #                                   defence, justice, family
     #
     # and against each other SA/QA share nine, QA/KW nine and SA/KW six. The
     # ceiling for the file is eleven, so none of these pairs is near it.
     #
     # WHAT THEY GENUINELY SHARE is not laziness: no income tax, a public health
     # service for citizens with a private tier, an unpriced fossil grid, no
     # competitive national elections, and a migrant majority on visas that lead
     # nowhere. Those five are the same policy in all four states and the
     # sources say so.
     #
     # THE CAVEAT THE UAE'S RETIREMENT CELL ALREADY CARRIES APPLIES TO THIS
     # WHOLE BLOCK. Pensions, housing, family payments, free university and free
     # healthcare are citizen entitlements, and citizens are a minority of
     # residents in three of the four. Where a cell describes the citizen system
     # and not the country, it says so.
     # ----------------------------------------------------------------------
     "choices": {
                 # No personal income tax. 15% VAT since 2020, zakat on Saudi
                 # and GCC-owned businesses, 20% corporate tax on foreign
                 # shareholders, and the rest is oil.
                 "tax": "tax_minimal",
                 # Free Ministry of Health care for citizens, a private tier
                 # alongside it, and mandatory cooperative health insurance for
                 # everyone in private-sector employment including expatriates
                 # since the 2005 Act. Measured public share 77.8, between this
                 # option's 80.0 and hc_public's 81.3. Same cell as the UAE.
                 "healthcare": "hc_mixed",
                 # DIFFERS FROM THE UAE, which is on ed_vocational. Saudi public
                 # universities charge citizens no tuition and pay them a monthly
                 # stipend of SAR 850 to 1,000 for the length of the degree,
                 # which is this option's second limb exactly. There is no
                 # early vocational streaming of the German or Emirati kind.
                 # https://saudipedia.com/en/article/3104/government-and-politics/education-and-training/are-stipends-provided-to-university-students-in-saudi-arabia
                 "education": "ed_free",
                 # Sakani has signed over a million subsidised housing contracts
                 # since 2017 and citizen home ownership has gone from 47% to
                 # 66%, but the instrument is subsidised finance, land and
                 # off-plan purchase rather than a state housebuilder, and
                 # developers build. THE UAE SETS THE BAR HERE: it runs the same
                 # kind of citizen housing grant programme and is coded ho_market,
                 # so Saudi Arabia is too. What neither is, is this option's "the
                 # state zones and nothing else".
                 # https://momah.gov.sa/en/node/15202
                 "housing": "ho_market",
                 # DIFFERS FROM THE UAE, which is on re_generous, and this is the
                 # difference most likely to be challenged so it is sourced
                 # twice. The new Social Insurance Law of 3 July 2024, in force
                 # from 3 July 2025, sets the retirement age for new entrants at
                 # 65 and cuts the accrual rate from 2.5% to 2.25% a year. The
                 # UAE's cell was justified by a pension age of 60, a resignation
                 # pension from 50 and a 100% ceiling, which is re_generous's "a
                 # low pension age". Sixty-five is not a low pension age, so what
                 # is left is an earnings-related state pension.
                 # https://knowledge.dlapiper.com/dlapiperknowledge/globalemploymentlatestdevelopments/2024/new-social-insurance-law-raises-the-retirement-age
                 "retirement": "re_earnings",
                 # 692 g/kWh, the dirtiest grid in the file, no carbon price, and
                 # domestic crude and gas burned for power.
                 "energy": "en_fossil",
                 # 0.092 on the expression index, the second lowest in the file
                 # after the UAE. Criticism of the ruler is prosecuted under the
                 # counter-terror and cybercrime laws.
                 "speech": "sp_restricted",
                 # No national legislative elections of any kind. The Shura
                 # Council is wholly appointed and even the municipal elections,
                 # last held in 2015, have not been repeated. The measured
                 # disproportionality cell is None for the same reason.
                 "voting": "vo_none",
                 # Same cell as the UAE. No trade unions, only workplace labour
                 # committees, and NO STATUTORY MINIMUM WAGE for the private
                 # sector: the SAR 4,000 figure is a Nitaqat threshold for
                 # counting a Saudi towards a firm's localisation quota, not a
                 # wage floor. That is the fact that keeps Saudi Arabia on
                 # wo_at_will while Qatar and Kuwait move off it.
                 "work": "wo_at_will",
                 # 7.3% of GDP, the highest military burden in the file by two
                 # points, and an all-volunteer force with no conscription. THE
                 # OPTION IS THE LEAST WRONG RATHER THAN RIGHT: Saudi Arabia has
                 # the spending and led a foreign war in Yemen, but it has no
                 # network of bases abroad and no blue-water navy, so what the
                 # menu lacks is a heavy-spending arms importer without power
                 # projection.
                 "defence": "de_power",
                 # 40.3% foreign-born, kafala reformed but still employer-tied,
                 # and naturalisation available to almost nobody. The premium
                 # residency introduced in 2019 is a paid permit, not a path.
                 "immigration": "im_guest",
                 # Judicial corporal punishment and capital punishment are both
                 # in use: discretionary flogging was abolished by the Supreme
                 # Court in 2020 but hudud sentences were not, and executions run
                 # at record numbers. Measured 140 per 100,000 against the
                 # option's 190.
                 "justice": "ju_corporal",
                 # DIFFERS FROM THE UAE, which is on fa_none. Qurrah pays up to
                 # 50% of childcare costs to a cap of SAR 1,600 a month for
                 # working mothers in the private sector earning under SAR 8,000,
                 # which is means-tested help with childcare, and maternity leave
                 # is twelve weeks paid. That is this option's sentence.
                 # https://www.hrdf.org.sa/en/products-and-services/programs/individuals/enable/childcare-support-for-working-women/
                 "family": "fa_targeted"},
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
     "matchable": True,
     "choices": {
                 # No personal income tax and, alone among the four, still no
                 # VAT: the GCC framework agreement was signed in 2016 and Qatar
                 # has not brought it into force.
                 "tax": "tax_minimal",
                 # Hamad Medical Corporation and the primary health centres are
                 # free or near-free for citizens with a private tier alongside,
                 # and mandatory health insurance for visitors and expatriates
                 # under Law 22 of 2021. Measured public share 83.0, the second
                 # highest in the file.
                 "healthcare": "hc_mixed",
                 # DIFFERS FROM THE UAE. Education is free to Qatari citizens
                 # through university, with full state scholarships at Qatar
                 # University and at approved universities abroad. Measured
                 # education spend is 3.2% of GDP against this option's 6.3,
                 # which is the largest education disagreement in the block and
                 # reflects a small citizen cohort rather than thin provision.
                 "education": "ed_free",
                 # Housing Law 2 of 2007 gives citizens a free land plot and a
                 # long-term interest-free state loan, plus a furniture grant.
                 # That is subsidised owner-occupation on the Emirati model, not
                 # a state housebuilder, so the same cell as the UAE and Saudi
                 # Arabia. Kuwait is the one that moves off it.
                 # https://hukoomi.gov.qa/en/articles/housing-loans
                 "housing": "ho_market",
                 # Social Insurance Law 1 of 2022, in force January 2023: a
                 # pension age of 60, a minimum of 15 years' service and a high
                 # replacement rate on final salary. Same reading as the UAE's
                 # GPSSA cell, and covering Qatari and GCC nationals only.
                 "retirement": "re_generous",
                 # 581.5 g/kWh on an almost entirely gas-fired grid, and no
                 # carbon price.
                 "energy": "en_fossil",
                 # 0.055, the lowest expression score in the file.
                 "speech": "sp_restricted",
                 # THE 2021 ELECTION HAS BEEN UNDONE, WHICH IS WHY THIS CELL IS
                 # NOT A DIFFERENCE FROM THE UAE. Qatar elected 30 of the Shura
                 # Council's 45 members in October 2021, and the constitutional
                 # referendum of 5 November 2024 abolished the elected element by
                 # 90.6% on an 84% turnout. All 45 are appointed by the Emir
                 # again. Had this been coded in 2023 the honest answer would
                 # have been that no option describes an elected consultative
                 # chamber under a hereditary executive.
                 # https://www.idea.int/blog/stability-or-elections-look-qatars-2024-constitutional-referendum
                 "voting": "vo_none",
                 # DIFFERS FROM THE UAE. Law 17 of 2020 gave Qatar the first
                 # non-discriminatory statutory minimum wage in the Gulf, QAR
                 # 1,000 plus food and accommodation allowances, applying to every
                 # worker of every nationality in every sector including domestic
                 # work. Migrant workers still cannot form or join a union, so
                 # bargaining is individual, which is the rest of this option.
                 # https://www.ilo.org/resource/news/qatar-adopts-non-discriminatory-minimum-wage
                 "work": "wo_minimum",
                 # DIFFERS FROM THE UAE, which is on de_power. Law 5 of 2018
                 # raised national service from three months to one year and made
                 # it compulsory for every Qatari male between 18 and 35, with
                 # employment and professional licences withheld until it is
                 # done. The option's twelve months is exact. The force is small
                 # in absolute terms and large against a citizen population of
                 # roughly a tenth of residents, and the 6.5% military burden is
                 # well above the option's 4.5.
                 # https://althanilawfirm.com/en/national-service-system/
                 "defence": "de_conscript",
                 # 76.7% foreign-born, the second highest in the file after the
                 # UAE, and no path to citizenship.
                 "immigration": "im_guest",
                 # Flogging remains a judicial sentence for alcohol and illicit
                 # sex offences and the death penalty is retained and has been
                 # carried out. THE AXIS DISAGREES LOUDLY: 69 per 100,000 against
                 # the option's 190, the lowest imprisonment rate of the eight
                 # coded here, and the reason is that foreign offenders are
                 # deported rather than held.
                 "justice": "ju_corporal",
                 # Same cell as the UAE. The children's allowance that appears in
                 # Qatari payroll is a salary component for public-sector
                 # employees rather than a benefit paid to families, and there is
                 # no child benefit, no subsidised childcare and 50 days of
                 # maternity leave.
                 "family": "fa_none"},
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
     "matchable": True,
     # KUWAIT IS THE ONE THAT IS NOT A COPY. It differs from the UAE on seven of
     # thirteen and from Saudi Arabia on seven, which is what a Gulf state with
     # legal trade unions, a state housebuilder, a universal child allowance, no
     # judicial corporal punishment and the freest press in the region should
     # look like. It differs from Qatar on four despite sharing the tax, health,
     # education, energy, voting, work, defence and immigration cells.
     "choices": {
                 # No personal income tax, no VAT, and no zakat levy on
                 # individuals. Kuwait legislated a 15% domestic minimum top-up
                 # tax on large multinationals from 2025, which does not change
                 # the option.
                 "tax": "tax_minimal",
                 # Free public healthcare for citizens with a private tier
                 # alongside, and expatriates pay health fees and are covered by
                 # a separate insurance scheme. Measured public share 88.5, the
                 # highest in the file.
                 "healthcare": "hc_mixed",
                 # Free through university for citizens, with a monthly student
                 # grant and fully funded scholarships abroad. Measured
                 # education spend 6.4% of GDP, which for once agrees with the
                 # option's 6.3 almost exactly.
                 "education": "ed_free",
                 # DIFFERS FROM EVERY OTHER GULF ROW, and it is a difference of
                 # kind rather than degree. The Public Authority for Housing
                 # Welfare under Law 47 of 1993 does not lend against a purchase;
                 # it builds. Al-Mutlaa alone is planned for 400,000 people in
                 # twelve suburbs, against a citizen population of about 1.5
                 # million, and Jaber al-Ahmad, Saad al-Abdullah and Khiran add
                 # more than 50,000 units between them. The state builds the
                 # housing and transfers it to citizens who then own it, which is
                 # this option's sentence. Two caveats the reveal should carry:
                 # the tenure is freehold rather than Singapore's 99-year lease,
                 # and it reaches citizens only, so most residents of Kuwait rent
                 # privately and are outside it entirely.
                 # https://www.pahw.gov.kw/About_en
                 "housing": "ho_singapore",
                 # PIFSS is the most generous scheme in the file: retirement from
                 # age 50 with as little as seven and a half years of service,
                 # and replacement rates from 65% at fifteen years upward.
                 # https://www.pifss.gov.kw/sites/En/Pages/PensionSocialSecuritySector/FAQ.aspx
                 "retirement": "re_generous",
                 # 635.3 g/kWh on oil and gas, and no carbon price.
                 "energy": "en_fossil",
                 # DIFFERS FROM THE OTHER THREE, and the measured axis is the
                 # evidence rather than an impression: 0.532 against Saudi
                 # Arabia's 0.092, Qatar's 0.055 and the UAE's 0.063, and above
                 # Singapore's 0.40 on this same option. Kuwait has the most
                 # contentious press in the Gulf and simultaneously prosecutes
                 # criticism of the Emir and speech held to harm national unity,
                 # which is what this option describes. sp_restricted would put
                 # it with three countries it is half a scale point clear of.
                 "speech": "sp_order",
                 # THE HARDEST CELL IN THE BLOCK AND THE ANSWER CHANGED IN 2024.
                 # Kuwait's National Assembly was the one elected chamber in the
                 # Gulf with real power, able to question and force out ministers.
                 # On 10 May 2024 the Emir dissolved it and suspended the
                 # constitutional articles governing it for up to four years, and
                 # the Emir and the Council of Ministers have exercised the
                 # legislative power since. As at August 2026 the suspension is
                 # still running and is expected to last to 2028, so there are no
                 # competitive national elections and this is the honest cell.
                 # https://constitutionnet.org/news/kuwaits-monarch-dissolves-parliament-and-suspends-constitutional-provisions
                 # TWO THINGS THE MENU CANNOT SAY. First, that a country's
                 # elections are suspended rather than absent, which is a
                 # different claim from the UAE's. Second, that the Assembly when
                 # sitting was elected by single non-transferable vote with
                 # political parties banned, so the measured disproportionality
                 # cell is None because there are no party lists to compare, NOT
                 # because nobody voted. Those are two different Nones and the
                 # file has one.
                 "voting": "vo_none",
                 # DIFFERS FROM THE UAE. Kuwaiti citizens may form and join trade
                 # unions, bargain collectively and strike, subject to compulsory
                 # arbitration, and there is a statutory private-sector minimum
                 # wage set by ministerial decree. Alone in the Gulf it has a
                 # union federation that has actually struck: the oil workers
                 # stopped production in 2016.
                 # https://www.state.gov/reports/2024-country-reports-on-human-rights-practices/kuwait
                 "work": "wo_minimum",
                 # DIFFERS FROM THE UAE. Conscription was reinstated by Law 20 of
                 # 2015 and enforced from 2017: twelve months for every Kuwaiti
                 # male at 18, four months' training and eight months' service,
                 # tightened again by decree in February 2026 which extended the
                 # reporting window to 180 days and raised the penalties.
                 # https://www.thenationalnews.com/news/gulf/2026/02/23/kuwait-ratifies-amendments-to-military-service-law/
                 "defence": "de_conscript",
                 # 67.3% foreign-born, kafala, and naturalisation capped by law
                 # at a nominal annual quota that is not filled.
                 "immigration": "im_guest",
                 # DIFFERS FROM THE OTHER THREE. Judicial corporal punishment is
                 # unlawful in Kuwait: there is no provision for it in the
                 # Criminal Code 1960, the Criminal Procedure Code or the
                 # Juveniles Act, and Article 31 of the 1962 Constitution
                 # prohibits degrading treatment. Draft legislation to add
                 # flogging and amputation in 2001 was never enacted. So
                 # ju_corporal's first limb is simply false, and the measured 101
                 # per 100,000 sits on this option's 100.
                 # https://www.endcorporalpunishment.org/wp-content/uploads/country-reports/Kuwait.pdf
                 # WHAT THIS CELL DOES NOT SAY is that Kuwait retains the death
                 # penalty and has executed at least 24 people since 2013. No
                 # option outside ju_corporal mentions capital punishment, and
                 # Japan sits on ju_rehab with the same problem, so the file
                 # already reads this domain as sentence length and prison
                 # population rather than as the existence of a gallows.
                 "justice": "ju_standard",
                 # DIFFERS FROM THE OTHER THREE. Kuwait pays a child allowance to
                 # citizens with no income test, KD 50 a month per child and
                 # raised towards KD 100, with the seven-child cap removed. That
                 # is a universal per-child benefit, which is this option's first
                 # limb. THE SECOND LIMB FAILS: there is no capped-price
                 # childcare scheme, and the benefit reaches citizens only.
                 # https://www.lexis.ae/2023/08/02/kuwait-child-allowance-increase/
                 "family": "fa_universal"},
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
     "matchable": True,
     # Malta and Cyprus were predicted to fit the menu about as well as Greece
     # and they do. Eight of Malta's thirteen cells needed no argument at all.
     "choices": {
                 # 28.7% of GDP, the second lowest tax take of the EU members in
                 # the file after Ireland's distorted figure, on progressive rates
                 # to 35% with a flat 10% each side in social security. Not
                 # tax_continental: Maltese social contributions are a flat rate
                 # rather than the heavy payroll wedge that option describes, and
                 # 28.7 is fourteen points under it.
                 "tax": "tax_anglo",
                 # THE ONLY COUNTRY OTHER THAN THE UNITED KINGDOM ON THIS OPTION,
                 # and it earns it: Malta runs a Beveridge national health
                 # service, tax-funded and free at the point of use, with an
                 # unsubsidised private sector alongside for GP and outpatient
                 # care. The disagreement is the measured public share, 66.0
                 # against the option's 81.3, because out-of-pocket spending is
                 # about 30% of the total and among the highest in the EU. A
                 # tax-funded service is a claim about how care is financed at
                 # the point of use, and the OOP share says a third of Maltese
                 # health spending never reaches that point.
                 # https://eurohealthobservatory.who.int/publications/i/malta-health-system-summary-2024
                 "healthcare": "hc_public",
                 # Free through university and, unusually, a maintenance stipend
                 # paid to every Maltese undergraduate since 1988. Both limbs of
                 # the option hold.
                 "education": "ed_free",
                 # THE CLOSEST OF THE FIVE AND NOT A GOOD FIT. The Housing
                 # Authority's Private Rent Housing Benefit Scheme caps a
                 # tenant's rent at 25% of income and paid EUR 10.7m to just under
                 # 4,000 families in 2025, which is this option's cash help with
                 # rent. But the measured social rental stock is 5.5%, closer to
                 # ho_market's 4.0 than to this option's 12.0, and the Authority
                 # also runs home-ownership grant schemes that neither option
                 # mentions. Coded on the instrument rather than the stock, which
                 # is how Sweden was coded here.
                 # https://housingauthority.gov.mt/
                 "housing": "ho_subsidy",
                 # The two-thirds pension is contributory and earnings-related,
                 # with no compulsory second pillar. The retirement age is rising
                 # to 65.
                 "retirement": "re_earnings",
                 # In the EU ETS, and in ETS2 for buildings and road transport
                 # from 2027. The grid is 484 g/kWh, gas plus the interconnector
                 # to Sicily, which is the known gap on this option between
                 # pricing emissions and having decarbonised.
                 "energy": "en_carbon_tax",
                 # Malta abolished criminal libel in 2018 but retains the
                 # incitement-to-hatred offence in Article 82A of the Criminal
                 # Code, as Framework Decision 2008/913/JHA requires of every EU
                 # member.
                 "speech": "sp_hate_limits",
                 # SINGLE TRANSFERABLE VOTE, WHICH THE MENU DOES NOT HAVE, and
                 # Ireland is the precedent: STV is a preferential ballot that
                 # produces a proportional result, and Ireland is already coded
                 # vo_proportional rather than vo_preferential because the
                 # preferential option also requires compulsory voting and Irish
                 # and Maltese voting are both voluntary. Gallagher 2.24, helped
                 # by the constitutional top-up that guarantees a party with a
                 # first-preference majority a seat majority. The one thing the
                 # option's detail gets wrong is "coalitions are normal": Malta
                 # has a two-party parliament and has never had one.
                 "voting": "vo_proportional",
                 # A statutory national minimum wage, and bargaining that happens
                 # at enterprise level with coverage under half. Union density is
                 # high by EU standards, which is why wo_bargaining was
                 # considered, but there is no sector-wide agreement machinery.
                 "work": "wo_minimum",
                 # Constitutionally neutral since 1974 and outside NATO, with an
                 # Armed Forces of Malta of about 2,000 whose main task is search
                 # and rescue and border patrol. At 0.5% of GDP it is the lowest
                 # military burden in the file, against the option's 0.7.
                 "defence": "de_neutral",
                 # THE WEAKEST CELL IN THIS ROW. Malta is in the EU and Schengen,
                 # so the option's sentence is true as far as it goes, and
                 # Luxembourg is the precedent for coding a small EU state with a
                 # very large foreign-born share this way. What it misses is that
                 # most of Malta's 37% foreign-born are now third-country
                 # nationals on employment permits with no realistic path to
                 # citizenship, which is nearer im_guest, and that the
                 # citizenship-by-investment scheme that did offer a path was
                 # struck down by the Court of Justice in April 2025. No option
                 # describes a country running EU free movement and a
                 # guest-worker regime side by side.
                 "immigration": "im_open",
                 # 120 per 100,000 and moderate sentencing.
                 "justice": "ju_standard",
                 # Children's Allowance is paid to every family with children,
                 # at a higher rate below an income threshold and a flat EUR 640
                 # a year per child above it, and childcare for working parents
                 # is free rather than merely capped. Both limbs hold and the
                 # second is stronger than the option claims.
                 # https://socialsecurity.gov.mt/en/information-and-applications-for-benefits-and-services/family-benefits/childrens-allowance-annual-income-less-than-threshold/
                 "family": "fa_universal"},
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
     "matchable": True,
     # EVERY CELL HERE DESCRIBES THE REPUBLIC OF CYPRUS, which is what the
     # indicators measure and what the sources cover. The northern third has
     # been outside the Republic's effective control since 1974 and none of
     # these thirteen claims reaches it. The file has no way to say that and it
     # is said here instead.
     "choices": {
                 # 37.6% of GDP including net social contributions on the
                 # Eurostat basis for 2024, three points below the EU average.
                 # Progressive to 35% with a large exempt band, low social
                 # contributions and heavy reliance on consumption and corporate
                 # tax, so tax_anglo rather than tax_continental: Cyprus is not
                 # funded by a payroll wedge. There is no measured tax_take cell
                 # on this row, so the 37.6 is not plotted anywhere.
                 # https://cyprus-mail.com/2025/11/04/cyprus-tax-to-gdp-ratio-ticked-up-in-2024
                 "tax": "tax_anglo",
                 # GESY since 2019 is a single-payer contributory scheme: the
                 # Health Insurance Organisation collects earnings-related
                 # contributions from employees, employers, the self-employed and
                 # the state, and contracts public and private providers. Cover is
                 # compulsory and universal. SAME MENU GAP AS TAIWAN AND GREECE:
                 # the option says a regulated market of insurers and there is
                 # one insurer. Measured public share 76.8, close to the option's
                 # 78.0.
                 # https://eurohealthobservatory.who.int/publications/i/cyprus-health-system-summary-2024
                 "healthcare": "hc_insurance",
                 # The state pays the tuition of Cypriot and EU undergraduates at
                 # the public universities. Measured spend 4.7% of GDP against
                 # the option's 6.3.
                 "education": "ed_free",
                 # Cyprus has essentially no social rental sector. Housing policy
                 # is home-ownership support and the displaced-persons estates
                 # built after 1974, and the ownership rate is among the highest
                 # in the EU. Same reading as Greece, and the absence of a
                 # measured social_housing cell is itself the evidence.
                 "housing": "ho_market",
                 # The Social Insurance Scheme pays an earnings-related
                 # contributory pension at 65 with a flat basic component, and
                 # there is no compulsory funded pillar. Not re_generous, which is
                 # where Greece sits: Cyprus cut its replacement rates in the
                 # 2012 adjustment and never restored them.
                 "retirement": "re_earnings",
                 # In the EU ETS. The grid is 489 g/kWh, almost entirely heavy
                 # fuel oil and diesel, because Cyprus is the last EU member with
                 # no electricity interconnection to anywhere. The same
                 # instrument-versus-outcome gap this option is documented as
                 # carrying, and Cyprus is the extreme case of it in the EU.
                 "energy": "en_carbon_tax",
                 # Incitement to hatred is criminal, as Framework Decision
                 # 2008/913/JHA requires. Measured 0.812.
                 "speech": "sp_hate_limits",
                 # List PR with a 3.6% threshold. Compulsory voting was abolished
                 # in 2017, so unlike Uruguay the voluntary limb of this option is
                 # now true. Gallagher 6.44, high for PR because of the threshold
                 # and a fragmented party system.
                 "voting": "vo_proportional",
                 # A national minimum wage only since January 2023, and sectoral
                 # collective agreements in hotels, construction and banking with
                 # coverage under half. Not wo_bargaining: there is no erga omnes
                 # extension, so the agreements bind their signatories and not an
                 # industry.
                 "work": "wo_minimum",
                 # THE CELL MOST LIKELY TO BE ARGUED WITH, AND THE ARGUMENT IS
                 # AGAINST GREECE'S. Cyprus conscripts every male citizen for
                 # fourteen months into the National Guard and holds him in the
                 # reserve until fifty, and it is outside NATO. That is
                 # de_militia's shape rather than de_conscript's, and the measured
                 # 1.6% of GDP sits on de_militia's 1.5 against de_conscript's
                 # 4.5. Greece went to de_conscript because its standing force is
                 # 140,000 and its burden 3.1%; Cyprus is an order of magnitude
                 # smaller in both. The one limb that fails is the Swiss detail
                 # in the option's text, since Cypriot reservists do not keep
                 # their weapons at home.
                 # https://ebco-beoc.org/cyprus/2024
                 "defence": "de_militia",
                 # 14.9% foreign-born, almost exactly Greece's 14.2, and Cyprus is
                 # coded the same way for the same reason: naturalisation takes
                 # seven to eight years of residence and is discretionary. EU free
                 # movement applies, which is the case for coding it im_open, and
                 # the file's practice is to pick one cell per country rather than
                 # claim both.
                 "immigration": "im_controlled",
                 # 117 per 100,000 and moderate sentencing.
                 "justice": "ju_standard",
                 # The child benefit has been income-tested since the 2012
                 # adjustment, with an asset test on top, and childcare is neither
                 # free nor capped.
                 # https://www.estatefy.com/cyprus/child-benefit-in-cyprus-everything-you-need-to-know
                 "family": "fa_targeted"},
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
     "matchable": True,
     # PANAMA IS THE WORST FIT IN THE FILE AND THIS ROW IS THE EVIDENCE FOR
     # WIDENING THE MENU. Four of its thirteen cells are the least wrong option
     # rather than the right one, and three of its axes disagree with their own
     # cell by more than any other country's. Two facts about Panama are absent
     # from all sixty-nine options and they are the ones that explain the rest:
     # roughly half the labour force is informal and outside every contributory
     # scheme the menu describes, and the country is dollarised, so it has no
     # monetary policy at all. Coded 31/08/2026 anyway, because the alternative
     # is a page on which only rich countries exist.
     "choices": {
                 # 11.3% of GDP, THE LOWEST TAX TAKE IN THE FILE and 22.7 points
                 # under this option's 34.0, which is the largest cell-versus-axis
                 # disagreement anywhere in the matrix. The reason it is here and
                 # not on tax_minimal is that tax_minimal's sentence is "no income
                 # tax", and Panama has a progressive one at 15% and 25%. What is
                 # true is the option's third clause: territorial taxation, a
                 # large exempt band and a huge informal sector mean the take is
                 # a third of what the option prices. No option describes a
                 # progressive system that collects almost nothing.
                 "tax": "tax_anglo",
                 # TWO PUBLIC SYSTEMS SIDE BY SIDE AND NO OPTION FOR IT. The CSS
                 # is a payroll-funded fund covering formal employees and their
                 # dependants; MINSA runs a separate network open to everyone
                 # else at one to three dollars a visit; and a private sector sits
                 # above both. hc_insurance was rejected because "everyone must
                 # buy cover" is false where half the workforce is informal, and
                 # hc_private was rejected because the CSS is a public fund and
                 # the option's word is "private". What is left is universal
                 # public provision with a paid fast lane, which is roughly what
                 # happens even if it is not how it is organised. The measured
                 # public share, 51.2%, is nearer hc_private's 50.0 than this
                 # option's 80.0 and that disagreement should be read as real.
                 "healthcare": "hc_mixed",
                 # Public education is free including the public universities.
                 # Measured spend is 2.5% of GDP, the lowest in the file and 3.8
                 # points under the option: the same free-and-underfunded gap
                 # recorded on Greece, at twice the size.
                 "education": "ed_free",
                 # A private market with a large self-built informal sector, and
                 # state activity limited to down-payment grants and the Techos
                 # de Esperanza programme. No option mentions informal housing,
                 # which is where a substantial minority of Panamanians live.
                 "housing": "ho_market",
                 # Law 462 of 18 March 2025 merged Panama's two pension
                 # programmes into a Unified Capitalization System: funded
                 # individual accounts with a guaranteed solidarity minimum of
                 # B/.265 a month and a non-contributory floor of B/.144 for
                 # those who could not contribute enough. That is this option's
                 # sentence almost word for word, and it is the same "mostly"
                 # caveat Chile carries, since the old defined-benefit subsystem
                 # runs until 2032 for those already in it.
                 # https://www.mef.gob.pa/wp-content/uploads/2025/05/250428-Republic-of-Panama-CSS-Reform-Takeaways.pdf
                 "retirement": "re_private",
                 # NO CARBON PRICE OF ANY KIND, which is this option's first
                 # sentence and the reason it is here. Its second sentence is
                 # also true of a country that has just built a third metro line
                 # only in its capital. What is not true is the axis: 221.2 g/kWh
                 # on a grid that is majority hydro, against the option's 480,
                 # which is the largest energy disagreement in the file. A clean
                 # grid that nobody priced has no cell in this menu.
                 "energy": "en_fossil",
                 # Criminal defamation remains in the penal code and Law 7 of
                 # 2018 penalises discrimination and incitement. Measured 0.812.
                 "speech": "sp_hate_limits",
                 # MIXED AGAIN, LIKE TAIWAN. 45 of the 71 National Assembly seats
                 # are open-list PR in multi-member circuits and 26 are plurality
                 # single-member seats, and the president is elected by plurality
                 # in one round. Coded on the majority of seats, and consistent
                 # with Japan, Korea and Taiwan. Gallagher 9.77, more than three
                 # times this option's 3.0 and the highest of any country on it.
                 "voting": "vo_proportional",
                 # A statutory minimum wage set by region and sector, and unions
                 # that are strong in construction and weak everywhere else.
                 # THE LIMB THE OPTION CANNOT CARRY is that a wage floor governs
                 # only the formal half of the labour market.
                 "work": "wo_minimum",
                 # PANAMA HAS NO ARMED FORCES. The military was abolished in 1990
                 # and the prohibition written into the constitution in 1994, and
                 # what remains is a police force plus the 4,000-strong SENAFRONT
                 # border service. The option's own words, "a force sized for the
                 # border only", are literally true, and its label, "small
                 # professional force", is the part that is wrong: there is no
                 # force at all in the sense the domain means. The menu has no
                 # cell for abolition, which also affects Costa Rica and Iceland
                 # if either is ever coded. The measured 1.0% is from 1999 and is
                 # the stalest indicator in the file.
                 "defence": "de_neutral",
                 # Selective entry with a residency-by-investment tier, and
                 # naturalisation after five years. 10.6% foreign-born.
                 "immigration": "im_controlled",
                 # 522 per 100,000, THE HIGHEST INCARCERATION RATE IN THE FILE and
                 # well above even this option's 300.
                 "justice": "ju_tough",
                 # Means-tested conditional transfers, Red de Oportunidades and
                 # the 120 a los 65 pension, rather than a universal child
                 # benefit.
                 "family": "fa_targeted"},
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
