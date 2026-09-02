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
