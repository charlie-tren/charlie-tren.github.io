"""IANA timezone to ISO country code, for the MATCHABLE countries plus the
common zones that resolve to them. All forty-five are matchable as of
31/08/2026, so every country in the file now contributes its own zones.

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

FOUR MORE WENT ON 30/08/2026 for the same reason. Europe/Prague and
Europe/Warsaw resolved to Germany and Europe/Riga and Europe/Vilnius to Estonia,
because Czechia, Poland, Latvia and Lithuania had no matrix. All four now do, and
each zone resolves to its own country through the comprehension above. Bratislava,
Ljubljana, Zagreb and Budapest never had a hand mapping and now resolve on their
own as well, so the whole Central European and Baltic block is exact.

TWO MORE WENT ON 31/08/2026 for the same reason. Asia/Riyadh and Asia/Qatar
resolved to the United Arab Emirates, which was a real answer for a visitor in
Riyadh right up until Saudi Arabia and Qatar got a matrix of their own, and a
wrong one from the moment they did. Asia/Kuwait, Asia/Taipei, Europe/Malta,
Asia/Nicosia, Asia/Famagusta, America/Montevideo and America/Panama never had a
hand mapping and now resolve on their own.

TWO APPROXIMATIONS BELOW ARE NOW ARGUABLE and are deliberately left alone,
because changing them is a judgement about the page rather than a correction.
America/Buenos_Aires resolves to Chile and Uruguay is now available, which is
the nearer neighbour on almost every axis. Asia/Hong_Kong resolves to Singapore
and Taiwan is now available. Neither Argentina nor Hong Kong is in the file, so
neither entry is wrong in the way Riyadh's was; they are guesses that could be
better guesses.
"""

from countries import COUNTRIES

TIMEZONES = {tz: c["code"] for c in COUNTRIES if c["matchable"] for tz in c["timezones"]}

# Zones that are not a country's primary zone but resolve to one in the set.
# THESE ARE APPROXIMATIONS and the page must not pretend otherwise. A visitor in
# Warsaw opening on Germany is a guess, and the country picker sits right there.
# Do not extend this map into a claim of accuracy it cannot support, and delete
# an entry as soon as its own country becomes matchable.
TIMEZONES.update({
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
})

FALLBACK = "AU"
