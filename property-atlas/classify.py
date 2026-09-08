"""Turn the workbook's prose columns into ordinals, without inverting their meaning.

The first version of this matched bare keywords and got three columns backwards.
"Free. No capital controls." matched "capital control" and scored the United
Kingdom as having them. "No property-based golden visa." matched "golden visa"
and gave the Netherlands a residency-by-purchase route it does not offer.
"Foreigners cannot own land. Can own condo freehold" matched "cannot" and closed
a market that is open to apartments.

All three are the same bug: a keyword carries no polarity. So every match here
goes through `says()`, which refuses a hit that is negated just before it, and
the scorers read clause by clause rather than over the whole cell. The rule is
not "add another keyword" - it is that a match must prove it is not a denial.
"""
import re

# A denial appearing within this many characters BEFORE a keyword flips it.
# "No capital controls" is 3 characters of negator plus a space; "there are no
# significant capital controls" is 30. 34 covers the phrasings in this workbook
# without reaching back into a previous, unrelated clause.
NEG_WINDOW = 34
NEGATORS = re.compile(r"\b(no|not|none|never|without|cannot|can't|free from|free of)\b", re.I)


CLAUSE_END = re.compile(r"[.;,]")


def says(text, *keywords):
    """True if any keyword appears AND is not negated within its own clause.

    The lookback stops at the previous clause boundary. Without that,
    "Foreigners cannot own land. Can own condo freehold" reads the "cannot" from
    the sentence before and denies the condo, which closed two markets that are
    open to apartments. A negator only speaks for the clause it sits in.
    """
    t = (text or "").lower()
    for kw in keywords:
        for m in re.finditer(re.escape(kw.lower()), t):
            window = t[max(0, m.start() - NEG_WINDOW):m.start()]
            cuts = list(CLAUSE_END.finditer(window))
            if cuts:
                window = window[cuts[-1].end():]
            if not NEGATORS.search(window):
                return True
    return False


def clauses(text):
    return [c.strip() for c in re.split(r"[.;]", text or "") if c.strip()]


def ownership(text):
    """0 closed, 1 heavily conditional, 2 qualified, 3 open."""
    t = (text or "").lower()
    apartments_ok = says(t, "can own condo", "own condo freehold", "can buy apartments",
                         "can own apartments", "buy apartments", "condo units", "condominium")
    land_barred = re.search(r"(cannot|can not|may not|not permitted to)\s+(directly\s+)?own\s+(land|freehold land)", t) \
                  or "cannot own land" in t
    if land_barred and apartments_ok:
        return 2, "Apartments yes, land barred"
    if land_barred:
        return 0, "Cannot own"
    if says(t, "equal property rights", "equal rights", "no restrictions on foreign",
            "no federal restrictions", "one of the most open"):
        return 3, "Open to foreigners"
    if says(t, "designated", "state minimum", "above state", "investment areas only"):
        return 1, "Designated zones or a price floor"
    if says(t, "local company", "must use a", "requires a local", "through a company", "fideicomiso", "trust"):
        return 1, "Company or trust required"
    if says(t, "permit", "approval", "reciprocity", "reciprocal"):
        return 2, "Permit or approval needed"
    if apartments_ok:
        return 2, "Apartments yes, land restricted"
    return 2, "Qualified"


def visa(text):
    """0 none, 1 limited, 2 investor visa, 3 residency by property purchase."""
    t = (text or "").lower()
    # Match the RELATIONSHIP, not the brand. Five markets describe the same thing
    # without naming a scheme - "Yes - USD 400K property = direct citizenship",
    # "Property in ITC can qualify for residency visa" - and matching scheme names
    # alone scored every one of them as having no pathway at all.
    linked = any(
        re.search(r"propert", cl) and re.search(r"residenc|residence|citizenship|permit", cl)
        and not NEGATORS.search(cl)
        for cl in clauses(t)
    )
    if linked:
        if re.search(r"citizenship", t) and not NEGATORS.search(t.split("citizenship")[0][-34:]):
            return 3, "Citizenship by property purchase"
        return 3, "Residency by property purchase"
    if says(t, "golden visa", "citizenship by investment", "residency by investment",
            "residency through property", "property route"):
        # A route that exists but has been shut is worse than one that never did:
        # the reader has probably read about it and needs telling it is gone.
        if re.search(r"(closed|suspended|ended|terminated)", t):
            return 1, "Property route closed"
        return 3, "Residency by property purchase"
    if says(t, "investor visa", "investment visa", "eb-5", "investor residency",
            "elite visa", "retiree visa", "srrv", "rentista"):
        return 2, "Investor visa, not property-specific"
    if says(t, "temporary residency", "residency possible", "elective residency",
            "digital nomad", "non-lucrative", "innovator", "business manager",
            # NAMED long-stay schemes only. Without these Malaysia scored "no
            # pathway" on the strength of MM2H's own sentence saying it is not a
            # property-based golden visa, which is true and not the question.
            # Deliberately not "residence permit" or "permit routes": ordinary
            # immigration exists everywhere, so counting it empties the bottom
            # band and eight markets jumped a level for having a sentence that
            # says they are normal.
            "long-stay", "mm2h"):
        return 1, "Residency, but not through property"
    return 0, "No pathway"


def repatriation(text):
    """0 controls, 2 conditional, 3 free."""
    t = (text or "").lower()
    if says(t, "capital control", "difficult", "restricted", "slow"):
        return 0, "Capital controls"
    if says(t, "register", "registration", "documentation", "bsp", "central bank"):
        return 2, "Free once registered"
    if re.search(r"\bfree\b", t):
        return 3, "Free"
    return 2, "Qualified"


def liquidity(months):
    if months is None:
        return None, ""
    if months <= 2:
        return 3, "1-3 months to sell"
    if months <= 4.5:
        return 2, "3-6 months to sell"
    if months <= 9:
        return 1, "6-12 months to sell"
    return 0, "Over a year to sell"


def costs(pct):
    if pct is None:
        return None, ""
    band = 3 if pct <= 4 else 2 if pct <= 7 else 1 if pct <= 11 else 0
    return band, f"{pct:g}% to buy"


def rights(v):
    if v is None:
        return None, ""
    band = 3 if v >= 85 else 2 if v >= 70 else 1 if v >= 55 else 0
    return band, f"Property rights {v:.0f}/100"

# ---------------------------------------------------------------------------
# Tax cells: a rate where the source states one, an accurate word where it does
# not.
#
# WHY THIS EXISTS. rates_pwc.json carries `rate: null, basis: "schedule"` for 21
# of 34 rent cells and 11 of 34 gain cells, with the note "not stated for
# non-residents on PwC" - and the page rendered every one of them as the word
# "scale", while test_data.py printed "by design, those markets tax on a
# progressive schedule". That was false for over half of them: Albania's cell
# reads "15%", Hungary's "15% flat", Malaysia's "30% flat", Oman's "0%". The
# figure was already in data.json, in the column beside the null, and the page
# was reading the null.
#
# So the parser below is deliberately NARROW. It fires only on a cell that states
# ONE rate plainly and nothing else, which is a transcription rather than an
# interpretation. Anything with a range, a slash, an "or" or a deemed basis is
# left alone and gets the right word: `progressive`, `deemed` or `regimes`. The
# eight that need a judgement live in rates_workbook.json with the quote they
# were read from and which of the four stated rules applied.

#: One rate, at the front of the cell, with an optional basis word and an
#: optional trailing parenthetical. Narrow on purpose: see above.
ONE_RATE = re.compile(r"""^
    ~?\s*
    (?P<rate>\d+(?:\.\d+)?)\s*%
    (?P<tail>(?:\s*(?:flat|WHT|on|of|net|gross|gain|sale\s+price))*)
    (?P<paren>\s*\([^()]*\))?
    \s*$""", re.I | re.X)

_RANGE    = re.compile(r"\d+(?:\.\d+)?\s*%?\s*(?:-|to)\s*\d+(?:\.\d+)?\s*%")
_PROGRESS = re.compile(r"\bprogressive\b|\bgraduated\b|\bbasic\b.*\bhigher\b", re.I)
_DEEMED   = re.compile(r"\bdeemed\b|\bcadastral\b", re.I)
_EXEMPT   = re.compile(r"^exempt\b", re.I)
_TWO      = re.compile(r"\bor\b|/|;", re.I)
_PAREN    = re.compile(r"\([^()]*\)")


def tax_from_text(text):
    """(rate, basis) read from a workbook tax cell.

    `rate` is None wherever the cell does not state a single one, and `basis` then
    says WHICH kind of not-a-single-rate it is, because "progressive", "a deemed
    basis" and "two regimes" are three different answers and "scale" was standing
    in for all three.
    """
    t = (text or "").strip()
    if not t:
        return None, "unstated"
    if _EXEMPT.search(t):
        return 0.0, "exempt"

    m = ONE_RATE.match(t)
    if m:
        rate = float(m.group("rate"))
        tail = (m.group("tail") or "").lower()
        if rate == 0:
            basis = "exempt"
        elif "wht" in tail:
            basis = "wht"
        elif "sale price" in tail or "gross" in tail:
            basis = "proceeds"
        elif "gain" in tail:
            basis = "gain"
        else:
            basis = "flat"
        return rate, basis

    # A parenthetical explains; it does not make a cell ambiguous. Panama's
    # "Progressive 0-25% (territorial system; only Panama-source income taxed)"
    # was read as two regimes purely for the semicolon inside its brackets.
    bare = _PAREN.sub("", t)
    if _DEEMED.search(t):
        return None, "deemed"
    if _RANGE.search(bare) or _PROGRESS.search(bare):
        return None, "progressive"
    if _TWO.search(bare):
        return None, "regimes"
    return None, "unclear"


#: What the page prints where there is no single rate. Each says something
#: different, which is the whole point of splitting them.
NO_RATE_LABEL = {
    "progressive": "banded",
    "deemed":      "deemed",
    "regimes":     "2 regimes",
    "unstated":    "",
    "unclear":     "see row",
}


#: Every rate stated anywhere in a cell, in order. A cell that does not reduce to
#: ONE rate usually states two or several, and those numbers are the honest answer
#: for it: "15-45%" says what "banded" was trying to say, in the source's own
#: figures, and needs no glossary.
_RATES = re.compile(r"(\d+(?:\.\d+)?)\s*%")
#: "15-45%" carries its percent sign only on the second number, so a bare hunt
#: for `N%` found 45 and reported Greece as a flat 45. Ranges are expanded to
#: "15% 45%" before the hunt.
_SPAN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*%")


def tax_range(text):
    """(display, low) for a cell with no single rate, or (None, None).

    Charlie, 08/09/2026: "deemed and banded and none sound off. what do they
    mean." They were words I coined to stand in for a range that the source had
    already written down. This returns the range instead.

    `low` is the bottom of it, and it is what the column sorts on. The bottom is
    a stated figure; a midpoint is not, and inventing one is already on this
    project's list of things not to do.
    """
    t = _SPAN.sub(lambda m: f"{m.group(1)}% {m.group(2)}%", (text or ""))
    found = [float(x) for x in _RATES.findall(t)]
    # A deemed cell can state the rate AND the deemed return it applies to, and
    # that second number is not a tax rate: the Netherlands' "~36% on deemed
    # ~5.5% return" must not read as 5.5-36%. But Belgium's "25-50% progressive
    # (on cadastral income basis)" IS a range on a deemed base, so the test is
    # whether the cell states a span, not whether it says "deemed".
    if _DEEMED.search(t) and not _SPAN.search(text or ""):
        return (f"{_num(found[0])}%", found[0]) if found else (None, None)
    if not found:
        return None, None
    lo, hi = min(found), max(found)
    if lo == hi:
        return f"{_num(lo)}%", lo
    # Two stated alternatives read as a choice; three or more read as a band.
    joiner = " / " if len(set(found)) == 2 and _TWO.search(_PAREN.sub("", t)) else "-"
    return f"{_num(lo)}{joiner}{_num(hi)}%", lo


def _num(v):
    return f"{v:g}"
