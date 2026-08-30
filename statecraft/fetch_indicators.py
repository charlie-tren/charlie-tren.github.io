"""Pull the World Bank axes for the matrix countries.

Run by hand, not at build time. It prints Python dict literals to paste into
countries.py, so the values that ship are checked into the repo and the page has
no runtime dependency on anyone's API. Re-run it when the data is refreshed and
paste again.

The remaining axes are a spreadsheet download each and are transcribed by hand
in Task 7. Six scrapers for a job that runs once would be an integration built
for a one-off.

Step 1 verification, 2026-08-29: all five codes originally listed in the plan
returned a live observation for Denmark, so none had to be replaced.

tax_take IS NOT FETCHED HERE, on purpose. The obvious World Bank series,
GC.TAX.TOTL.GD.ZS, is CENTRAL GOVERNMENT tax revenue and excludes social
security contributions and all sub-national tax. It returned 33.4% for Denmark
against an OECD total tax take of about 44%, 10.9% for Germany against about
38%, 9.5% for Switzerland, 10.8% for the United States and 0.6% for the UAE, and
its most recent Japanese observation is from 1993. The tax domain's `revenue` values in policies.py are
written on the OECD total-tax-take basis, 16.0 for a minimal state up to 46.0
for the Nordic take, so fetching the central government series would put the
visitor's number and the country's number on two different measures and the
track would compare nothing. tax_take is therefore in the hand-transcribed set
in Task 7, sourced from OECD Revenue Statistics total tax revenue as a share of
GDP, which is the basis the option values already use.
"""

import json
import sys
import urllib.request

CODES = {
    "education_spend": ("SE.XPD.TOTL.GD.ZS", "World Bank, government expenditure on education % of GDP"),
    "military_burden": ("MS.MIL.XPND.GD.ZS", "World Bank / SIPRI, military expenditure % of GDP"),
    "health_public": ("SH.XPD.GHED.CH.ZS", "WHO GHED, domestic general government health expenditure % of current health expenditure"),
    "foreign_born": ("SM.POP.TOTL.ZS", "UN DESA / World Bank, international migrant stock % of population"),
}

COUNTRY_CODES = ["AU", "NZ", "US", "GB", "CA", "DE", "FR", "NL", "DK", "SE",
                 "NO", "FI", "EE", "CH", "SG", "JP", "KR", "IL", "CL", "AE",
                 # The twenty-five measured-only countries added 2026-08-30.
                 # Taiwan is deliberately in the list and is expected to return
                 # nothing on all four: it is not a World Bank member and has no
                 # rows in the API. That is a gap to be reported, not filled.
                 "IE", "IT", "ES", "PT", "AT", "BE", "GR", "CZ", "PL", "SK",
                 "SI", "HR", "LT", "LV", "IS", "LU", "HU", "UY", "TW", "SA",
                 "QA", "KW", "MT", "CY", "PA"]

# The World Bank uses GB where the matrix uses UK.
ALIAS = {"GB": "UK"}


def fetch(country, code):
    url = (f"https://api.worldbank.org/v2/country/{country}/indicator/{code}"
           f"?format=json&mrnev=1")
    with urllib.request.urlopen(url, timeout=30) as r:
        body = json.load(r)
    if not isinstance(body, list) or len(body) < 2 or not body[1]:
        return None, None
    row = body[1][0]
    if row["value"] is None:
        return None, None
    return row["value"], int(row["date"])


def main():
    missing = []
    out = {}
    for country in COUNTRY_CODES:
        cell = {}
        for axis, (code, source) in CODES.items():
            value, year = fetch(country, code)
            if value is None:
                missing.append((country, axis))
                continue
            cell[axis] = {"value": round(value, 1), "year": year, "source": source}
        out[ALIAS.get(country, country)] = cell

    for code, cell in out.items():
        print(f'# {code}')
        print(json.dumps(cell, indent=2, sort_keys=True))
        print()

    # The distribution, not just the count. A value that is present but wrong is
    # worse than a missing one, and only the spread catches it.
    for axis in CODES:
        rows = sorted((cell[axis]["value"], code)
                      for code, cell in out.items() if axis in cell)
        print(f"# {axis}: " + ", ".join(f"{code} {v}" for v, code in rows),
              file=sys.stderr)

    print(f"# fetched {sum(len(c) for c in out.values())} of "
          f"{len(COUNTRY_CODES) * len(CODES)} cells", file=sys.stderr)
    if missing:
        print(f"# MISSING, transcribe by hand: {missing}", file=sys.stderr)


if __name__ == "__main__":
    main()
