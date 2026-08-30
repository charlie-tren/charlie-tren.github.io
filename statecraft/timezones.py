"""IANA timezone to ISO country code, for the twenty-nine MATCHABLE countries
plus the common zones that resolve to them.

This is how the page opens on the visitor's own country with no IP lookup, no
third-party request and no API key. A timezone outside this map falls back to
Australia, which is stated in the copy rather than hidden.

ONLY MATCHABLE COUNTRIES ARE ELIGIBLE. The page opens ON a country, meaning it
loads that country's thirteen choices as the starting design, so a measured-only
country here would open the page on an empty selection. The measured-only rows
carry their own `timezones` because the field is a fact about the country, and
the filter below is what stops those zones becoming a starting point.

SIX HAND MAPPINGS WERE DELETED ON 30/08/2026 and that is the point of recording
this. Europe/Dublin resolved to the United Kingdom, Lisbon, Madrid and Rome to
France, Vienna to Germany and Brussels to the Netherlands, because those six
countries had no matrix to open on. They have one now, so the guesses are gone
and each zone resolves to its own country through the comprehension above. A
hand mapping that outlives the reason for it is worse than no mapping, because
it keeps overriding the right answer silently.
"""

from countries import COUNTRIES

TIMEZONES = {tz: c["code"] for c in COUNTRIES if c["matchable"] for tz in c["timezones"]}

# Zones that are not a country's primary zone but resolve to one in the set.
# THESE ARE APPROXIMATIONS and the page must not pretend otherwise. A visitor in
# Warsaw opening on Germany is a guess, and the country picker sits right there.
# Do not extend this map into a claim of accuracy it cannot support, and delete
# an entry as soon as its own country becomes matchable.
TIMEZONES.update({
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
