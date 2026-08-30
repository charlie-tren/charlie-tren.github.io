"""IANA timezone to ISO country code, for the twenty MATCHABLE countries plus the
common zones that resolve to them.

This is how the page opens on the visitor's own country with no IP lookup, no
third-party request and no API key. A timezone outside this map falls back to
Australia, which is stated in the copy rather than hidden.

ONLY MATCHABLE COUNTRIES ARE ELIGIBLE. The page opens ON a country, meaning it
loads that country's thirteen choices as the starting design, so a measured-only
country here would open the page on an empty selection. The measured-only rows
carry their own `timezones` because the field is a fact about the country, and
the filter below is what stops those zones becoming a starting point. Some of
them are already mapped by hand to a matchable neighbour in the update block:
Europe/Dublin resolves to the United Kingdom, which is a guess and says so.
"""

from countries import COUNTRIES

TIMEZONES = {tz: c["code"] for c in COUNTRIES if c["matchable"] for tz in c["timezones"]}

# Zones that are not a country's primary zone but resolve to one in the set.
# THESE ARE APPROXIMATIONS and the page must not pretend otherwise. A visitor in
# Dublin opening on the United Kingdom is a guess, and the country picker sits
# right there. Do not extend this map into a claim of accuracy it cannot support.
TIMEZONES.update({
    "Europe/Dublin": "UK",
    "Europe/Lisbon": "FR",
    "Europe/Madrid": "FR",
    "Europe/Rome": "FR",
    "Europe/Vienna": "DE",
    "Europe/Brussels": "NL",
    "Europe/Prague": "DE",
    "Europe/Warsaw": "DE",
    "Europe/Riga": "EE",
    "Europe/Vilnius": "EE",
    "Asia/Hong_Kong": "SG",
    "Asia/Kuala_Lumpur": "SG",
    "Asia/Shanghai": "SG",
    "Asia/Kolkata": "UK",
    "Asia/Bangkok": "SG",
    "Asia/Manila": "SG",
    "Asia/Jakarta": "SG",
    "America/Sao_Paulo": "CL",
    "America/Buenos_Aires": "CL",
    "America/Mexico_City": "US",
    "Africa/Johannesburg": "UK",
    "Asia/Riyadh": "AE",
    "Asia/Qatar": "AE",
})

FALLBACK = "AU"
