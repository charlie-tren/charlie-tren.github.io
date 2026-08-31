"""Build data.json for Absentee from the source workbook.

The workbook carries a per-country ten-year growth column, most of it marked
"Est." with no source behind it. None of it is used here. Growth is a reader
input applied identically to every country, so the ranking on this page is
driven only by the things that can be sourced: yield, transaction and holding
costs, and the destination country's own tax rates.

Run: python build_data.py
"""
import json, re, unicodedata
from pathlib import Path
import openpyxl

SRC = Path(__file__).parent / "source" / "International Property.xlsx"
OUT = Path(__file__).parent / "data.json"

# Comparison sheet, header on row 2 (1-indexed), data from row 3.
C_NAME, C_PRICE_LOC, C_CCY, C_PRICE_AUD = 0, 1, 2, 3
C_FXREG, C_GROSS_OUT = 4, 12
C_POPGROWTH, C_RIGHTS = 15, 21
C_OWNERSHIP, C_VISA, C_REPAT = 23, 24, 25
C_PURCH, C_HOLD, C_CGT, C_RENTTAX = 27, 28, 29, 30
C_DTA, C_WHT, C_ESTATE = 31, 32, 33
C_FXVOL, C_LIQ, C_OBSTACLES = 34, 35, 36

# AUD Return Scenarios sheet: the net yield actually modelled.
S_NAME, S_NETYIELD, S_SALE = 0, 2, 5


def clean(v):
    """Excel cells arrive with non-breaking spaces and stray whitespace."""
    if v is None:
        return ""
    s = unicodedata.normalize("NFKC", str(v)).replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def pct(v):
    """Rate and basis from a free-text tax cell.

    Returns (rate, basis). Basis is what the rate is charged ON, which is not
    decorative: "2.5% of sale price" and "27% on net gain" are not comparable
    numbers, and averaging them into one column is how a model ends up ranking
    Egypt above Ireland. Only a rate on the gain or on rent is used in the
    arithmetic; everything else is carried as text for the reader to see.

    A range takes its midpoint. "25-50%" must be matched as a range before the
    single-percentage pattern sees it, or the low end is silently dropped.
    """
    s = clean(v)
    if not s:
        return None, "unknown"
    low = s.lower()
    if low.startswith("exempt") or re.match(r"^(no|none)\b", low) or "no cgt" in low        or "no personal income" in low:
        return 0.0, "exempt"

    # A cell that offers a CHOICE of regimes, or a schedule that steps with the
    # holding period, is not one rate and must not be averaged into one. The US
    # rent cell reads "30% WHT on gross OR elect net basis (10-37% graduated)":
    # averaging 10 and 37 returns 23.5, which is a number the source never
    # states. Refusing these is the fix. Adding a rule per phrasing is not,
    # because the next workbook will phrase it a way the rules do not cover.
    if re.search(r"\bor\b|whichever|;|/", low) and len(re.findall(r"\d+(?:\.\d+)?\s*%", s)) > 1:
        return None, "alternatives"

    rng = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*%", s)
    if rng:
        rate = round((float(rng.group(1)) + float(rng.group(2))) / 2, 2)
    else:
        one = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
        if not one:
            return None, "unknown"
        rate = float(one.group(1))

    if re.search(r"of (the )?(gross|sale|selling) price|of gross|of sale|of fmv|sale price or fmv", low):
        basis = "proceeds"
    elif "deemed" in low or "cadastral" in low or "notional" in low:
        basis = "deemed"
    elif "gross" in low:
        basis = "gross"
    else:
        basis = "gain"
    return rate, basis


def yes_no(v):
    s = clean(v).lower()
    if s.startswith("yes"):
        return True
    if s.startswith("no"):
        return False
    return None


wb = openpyxl.load_workbook(SRC, data_only=True)
comp = wb["Comparison"]
scen = {clean(r[S_NAME]): r for r in wb["AUD Return Scenarios"].iter_rows(min_row=2, values_only=True) if r[S_NAME]}
prof = {clean(r[0]): clean(r[1]) for r in wb["Country Profiles"].iter_rows(min_row=2, values_only=True) if r[0]}

# The thirteen fields app.js reads. Anything else in the workbook stays in the
# workbook.
KEEP = {
    "country", "price_aud", "currency", "net_yield", "purchase_costs", "sale_costs",
    "foreign_rental_tax", "foreign_rental_basis", "foreign_cgt", "foreign_cgt_basis",
    "rental_tax_text", "cgt_text", "au_dta",
}

rows, skipped = [], []
for r in comp.iter_rows(min_row=3, values_only=True):
    name = clean(r[C_NAME])
    if not name or name not in scen:
        if name:
            skipped.append(name)
        continue
    s = scen[name]
    rent_rate, rent_basis = pct(r[C_RENTTAX])
    cgt_rate, cgt_basis = pct(r[C_CGT])
    net_yield = s[S_NETYIELD]
    purch, sale = pct(r[C_PURCH])[0], s[S_SALE]
    if net_yield is None or purch is None or sale is None:
        skipped.append(name)
        continue
    row = {
        "country": name,
        "price_aud": r[C_PRICE_AUD],
        "price_local": clean(r[C_PRICE_LOC]),
        "currency": clean(r[C_CCY]),
        "fx_regime": clean(r[C_FXREG]),
        "gross_yield": r[C_GROSS_OUT],
        "net_yield": float(net_yield),
        "purchase_costs": float(purch),
        "sale_costs": float(sale),
        "holding_costs": pct(r[C_HOLD])[0],
        # Destination-country rates. The reader's OWN rates are inputs on the
        # page; these are what the destination withholds before the reader's
        # home country looks at the income at all.
        "foreign_rental_tax": rent_rate,
        "foreign_rental_basis": rent_basis,
        "foreign_cgt": cgt_rate,
        "foreign_cgt_basis": cgt_basis,
        "rental_tax_text": clean(r[C_RENTTAX]),
        "cgt_text": clean(r[C_CGT]),
        "wht_rent_text": clean(r[C_WHT]),
        "estate_text": clean(r[C_ESTATE]),
        "au_dta": yes_no(r[C_DTA]),
        "au_dta_text": clean(r[C_DTA]),
        "ownership": clean(r[C_OWNERSHIP]),
        "visa": clean(r[C_VISA]),
        "repatriation": clean(r[C_REPAT]),
        "property_rights": r[C_RIGHTS],
        "pop_growth": r[C_POPGROWTH],
        "fx_vol": clean(r[C_FXVOL]),
        "liquidity": clean(r[C_LIQ]),
        "obstacles": clean(r[C_OBSTACLES]),
        "profile": prof.get(name, ""),
    }
    rows.append({k: v for k, v in row.items() if k in KEEP})

# Only the sources behind something the page actually shows. The workbook
# cites eighteen, for columns like property rights, corruption score and
# sovereign rating that this page does not display. Listing all eighteen
# advertises a provenance the page does not have, and one of them was
# "Expected 10yr Growth: author estimates" for a column deliberately removed.
USED = {
    "Price-to-Income, Gross Rental Yields",
    "Price per sqm (city centre)",
    "Converted Price (AUD)",
    "Non-Resident Tax Rates (CGT, Rental, WHT)",
    "Australia Double Tax Agreements",
    "Purchase/Holding Costs",
}

sources = []
for r in wb["Sources"].iter_rows(min_row=2, values_only=True):
    if not r[0] or clean(r[0]) not in USED:
        continue
    sources.append({
        "measure": clean(r[0]),
        "name": clean(r[1]),
        "url": clean(r[2]),
        "caveat": clean(r[4]) if len(r) > 4 else "",
    })

rows.sort(key=lambda d: d["country"])
OUT.write_text(json.dumps({"countries": rows, "sources": sources}, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{len(rows)} countries and {len(sources)} sources written to {OUT.name}")
if skipped:
    print(f"skipped {len(skipped)}: {', '.join(skipped)}")
