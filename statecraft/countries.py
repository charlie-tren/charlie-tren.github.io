"""The twenty launch countries.

Twenty is a staging decision, not a design position. Build-out to every country
is tracked in hub-notes TODO.md: the axes are automatable and can go wide long
before the matrix does, because every matrix cell is a human judgement with a
citation behind it.

`choices` is the policy matrix and it is the thing the match runs on. Each cell
is a claim about what the country actually does, and it appears in the reveal
next to that country's name, so it is checked against a source before it ships.

`indicators` carries a value, a year and a source per axis. A value of None is
"does not apply" and must never be confused with a missing key, which is "no
data". Both are handled separately in the reveal.

WHERE THE MATRIX IS THIN, measured 2026-08-29 over all 190 pairs. No pair
matches on all thirteen, so no country is unreachable in the reveal, but the
count of shared cells on the closest pairs is the margin the whole match turns
on:

    11  SE NO   work, defence
    10  SE FI   work, immigration, family
    10  NZ EE   tax, education, immigration
    10  AU NZ   energy, voting, work
     9  NZ CL   healthcare, education, retirement, immigration
     9  NZ CA   education, retirement, voting, justice
     9  NO FI   work, defence, immigration, family
     9  DK FI   housing, energy, defence, immigration

Sweden and Norway are separated by two cells, so a visitor who picks the Nordic
package is sorted between them by the work and defence choices alone. Those two
cells carry more weight than any others in this file, and NZ is the country most
often near the top, which makes its row the one to check first. Re-run the pair
script after any cell change: a correction that looks local can quietly push a
pair to thirteen.
"""

COUNTRIES = [
    {"code": "AU", "name": "Australia", "timezones": ["Australia/Sydney", "Australia/Melbourne",
        "Australia/Brisbane", "Australia/Perth", "Australia/Adelaide", "Australia/Hobart",
        "Australia/Darwin"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_mixed", "education": "ed_deferred",
                 "housing": "ho_market", "retirement": "re_super", "energy": "en_fossil",
                 "speech": "sp_hate_limits", "voting": "vo_preferential", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "NZ", "name": "New Zealand", "timezones": ["Pacific/Auckland"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_mixed", "education": "ed_deferred",
                 "housing": "ho_market", "retirement": "re_super", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "US", "name": "United States", "timezones": ["America/New_York", "America/Chicago",
        "America/Denver", "America/Los_Angeles", "America/Phoenix", "America/Anchorage",
        "Pacific/Honolulu"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_private", "education": "ed_market",
                 "housing": "ho_market", "retirement": "re_flat", "energy": "en_fossil",
                 "speech": "sp_first_amendment", "voting": "vo_fptp", "work": "wo_at_will",
                 "defence": "de_power", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_none"},
     "indicators": {}},
    {"code": "UK", "name": "United Kingdom", "timezones": ["Europe/London"],
     "choices": {"tax": "tax_continental", "healthcare": "hc_public", "education": "ed_deferred",
                 "housing": "ho_subsidy", "retirement": "re_flat", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_fptp", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_controlled", "justice": "ju_tough",
                 "family": "fa_universal"},
     "indicators": {}},
    {"code": "CA", "name": "Canada", "timezones": ["America/Toronto", "America/Vancouver",
        "America/Edmonton", "America/Winnipeg", "America/Halifax", "America/St_Johns"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_mixed", "education": "ed_free_selective",
                 "housing": "ho_market", "retirement": "re_flat", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_fptp", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_standard",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "DE", "name": "Germany", "timezones": ["Europe/Berlin"],
     "choices": {"tax": "tax_continental", "healthcare": "hc_insurance", "education": "ed_vocational",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_deposit",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_open", "justice": "ju_standard",
                 "family": "fa_universal"},
     "indicators": {}},
    {"code": "FR", "name": "France", "timezones": ["Europe/Paris"],
     "choices": {"tax": "tax_continental", "healthcare": "hc_insurance", "education": "ed_free",
                 "housing": "ho_cooperative", "retirement": "re_generous", "energy": "en_nuclear",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_mandated_leave",
                 "defence": "de_power", "immigration": "im_controlled", "justice": "ju_standard",
                 "family": "fa_pronatal"},
     "indicators": {}},
    {"code": "NL", "name": "Netherlands", "timezones": ["Europe/Amsterdam"],
     "choices": {"tax": "tax_continental", "healthcare": "hc_insurance", "education": "ed_vocational",
                 "housing": "ho_social", "retirement": "re_super", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_open", "justice": "ju_rehab",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "DK", "name": "Denmark", "timezones": ["Europe/Copenhagen"],
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_cooperative", "retirement": "re_earnings", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_alliance", "immigration": "im_controlled", "justice": "ju_rehab",
                 "family": "fa_universal"},
     "indicators": {}},
    # SE housing changed from ho_cooperative to ho_subsidy 2026-08-29. OECD PH4.2
    # excludes Sweden from the social rental housing indicator on the ground that
    # municipal housing company rents are not below market, so the axis this cell
    # feeds has no Swedish social housing to report. The reasoning and the sources
    # are on the ho_subsidy option in policies.py.
    {"code": "SE", "name": "Sweden", "timezones": ["Europe/Stockholm"],
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_mandated_leave",
                 "defence": "de_militia", "immigration": "im_points", "justice": "ju_rehab",
                 "family": "fa_leave"},
     "indicators": {}},
    {"code": "NO", "name": "Norway", "timezones": ["Europe/Oslo"],
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_transparency",
                 "defence": "de_alliance", "immigration": "im_points", "justice": "ju_rehab",
                 "family": "fa_leave"},
     "indicators": {}},
    {"code": "FI", "name": "Finland", "timezones": ["Europe/Helsinki"],
     "choices": {"tax": "tax_nordic", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_bargaining",
                 "defence": "de_militia", "immigration": "im_open", "justice": "ju_rehab",
                 "family": "fa_universal"},
     "indicators": {}},
    {"code": "EE", "name": "Estonia", "timezones": ["Europe/Tallinn"],
     "choices": {"tax": "tax_flat", "healthcare": "hc_mixed", "education": "ed_free",
                 "housing": "ho_market", "retirement": "re_super", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_open", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "CH", "name": "Switzerland", "timezones": ["Europe/Zurich"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_vocational",
                 "housing": "ho_subsidy", "retirement": "re_super", "energy": "en_hydro",
                 "speech": "sp_hate_limits", "voting": "vo_direct", "work": "wo_minimum",
                 "defence": "de_militia", "immigration": "im_controlled", "justice": "ju_standard",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "SG", "name": "Singapore", "timezones": ["Asia/Singapore"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_savings", "education": "ed_market",
                 "housing": "ho_singapore", "retirement": "re_private", "energy": "en_hydro",
                 "speech": "sp_order", "voting": "vo_fptp", "work": "wo_at_will",
                 "defence": "de_conscript", "immigration": "im_points", "justice": "ju_corporal",
                 "family": "fa_none"},
     "indicators": {}},
    {"code": "JP", "name": "Japan", "timezones": ["Asia/Tokyo"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_market",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_hydro",
                 "speech": "sp_order", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_closed", "justice": "ju_rehab",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "KR", "name": "South Korea", "timezones": ["Asia/Seoul"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_market",
                 "housing": "ho_subsidy", "retirement": "re_earnings", "energy": "en_nuclear",
                 "speech": "sp_order", "voting": "vo_proportional", "work": "wo_at_will",
                 "defence": "de_conscript", "immigration": "im_closed", "justice": "ju_standard",
                 "family": "fa_none"},
     "indicators": {}},
    {"code": "IL", "name": "Israel", "timezones": ["Asia/Jerusalem"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_free",
                 "housing": "ho_market", "retirement": "re_flat", "energy": "en_fossil",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_conscript", "immigration": "im_points", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {}},
    {"code": "CL", "name": "Chile", "timezones": ["America/Santiago"],
     "choices": {"tax": "tax_anglo", "healthcare": "hc_insurance", "education": "ed_market",
                 "housing": "ho_market", "retirement": "re_private", "energy": "en_carbon_tax",
                 "speech": "sp_hate_limits", "voting": "vo_proportional", "work": "wo_minimum",
                 "defence": "de_alliance", "immigration": "im_controlled", "justice": "ju_tough",
                 "family": "fa_targeted"},
     "indicators": {}},
    # AE retirement changed from re_private to re_generous 2026-08-29. There are no
    # mandatory individual accounts here: GPSSA is a contributory pay-as-you-go
    # defined-benefit scheme paying up to 100% of the final five years' average
    # salary, with a pension age of 60. Sources and the expatriate caveat are on
    # the re_generous option in policies.py.
    {"code": "AE", "name": "United Arab Emirates", "timezones": ["Asia/Dubai"],
     "choices": {"tax": "tax_minimal", "healthcare": "hc_mixed", "education": "ed_vocational",
                 "housing": "ho_market", "retirement": "re_generous", "energy": "en_fossil",
                 "speech": "sp_restricted", "voting": "vo_none", "work": "wo_at_will",
                 "defence": "de_power", "immigration": "im_guest", "justice": "ju_corporal",
                 "family": "fa_none"},
     "indicators": {}},
]
