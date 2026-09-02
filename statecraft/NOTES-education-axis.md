# Replacing education_spend: scoping notes

Written 02/09/2026. SCOPING ONLY. Nothing in `axes.py`, `countries.py` or
`policies.py` was changed by this work.

## The problem, restated with the numbers checked

The education domain's five options are all about WHO PAYS for tertiary study.
Its axis, `education_spend`, is public education spend across all levels as a
share of GDP. That is the SIZE OF THE SCHOOL SYSTEM, not who pays for
university, and the two quantities barely correlate inside this sample.

Confirmed by running the file:

| option | holders | measured | median on education_spend |
|---|---|---|---|
| ed_market | 8 | 7 | 4.30 |
| ed_deferred | 3 | 3 | 5.20 |
| ed_vocational | 9 | 9 | 4.90 |
| ed_free | 24 | 24 | 4.70 |
| ed_free_selective | 1 | 1 | 4.80 |

Span 0.9 on bounds (1.8, 7.7), so travel is 15%, exactly on the floor and the
thinnest of the thirteen spokes. `check_travel.py` agrees. "Free through
university" (4.70) sits BELOW "Free at school, deferred fees after" (5.20),
which is the ordering the axis is supposed to make legible and instead denies.

One correction to the brief: current coverage is **44 of 45, not 45 of 45**.
Taiwan has no `education_spend` cell, because the World Bank does not carry
Taiwan.

## 1. Candidate measures

### A. Share of expenditure on tertiary educational institutions from public sources (LEADING)

- Source: OECD Education at a Glance, UOE finance collection.
- Dataflow: `OECD.EDU.IMEP:DSD_EAG_UOE_FIN@DF_UOE_FIN_SOURCE_GV_PR_NDOM`
  ("Distribution of government, private and non-domestic expenditure on
  educational institutions"), version 3.2.
- Key: `EDUCATION_LEV = ISCED11_5T8`, `EXP_SOURCE = S13` (general government),
  `UNIT_MEASURE = PT_EXP` (percentage of expenditure),
  `EXP_DESTINATION = INST_EDU`, `EXPENDITURE_TYPE = DIR_EXP`.
- Machine readable, no key:
  `https://sdmx.oecd.org/public/rest/data/OECD.EDU.IMEP,DSD_EAG_UOE_FIN@DF_UOE_FIN_SOURCE_GV_PR_NDOM,/..ISCED11_5T8.....PT_EXP.?startPeriod=2015&format=csvfilewithlabels`
- Corresponds to the EAG indicator published as Table C3.1 / C3.2.
- The complement, `EXP_SOURCE = S1D_NON_EDU`, is the private (household plus
  other private) share on exactly the same 34 countries. It is the same series
  read the other way round, not an independent candidate. `S2` (international
  sources) is the small remainder and is reported for only 28 of the 45.

### B. Average annual tuition fees charged by public institutions to national students

- OECD Education at a Glance, Table C5.1 (bachelor's or equivalent, USD PPP,
  national students, public institutions).
- **Not available through the OECD SDMX API.** A search of all 1,546 published
  OECD dataflows returns no dataflow whose id or name contains "fee" or
  "tuition". It exists only in the EAG report tables and their Excel annexes,
  so it would be a hand transcription per edition.
- It also carries a definitional trap that would matter here: a blank cell in
  that table means "no tuition fees charged" for some countries and "not
  available" for others, distinguished only by footnote. Transcribing it
  without reading the footnotes would put zeros where there is no data.
- On the merits it is the most direct measure of the thing the labels describe.
  On availability it is worse than A on every count.

### C. Household expenditure on tertiary education as a share of the total

- Same OECD dataflow as A, `EXP_SOURCE = S1D_NON_EDU`. Identical coverage
  (34 of 45), mirror-image values. Not a separate option.
- The UNESCO cut of this, `UIS.XUNIT.GDPCAP.5T8.FSHH` ("initial household
  funding per tertiary student as a percentage of GDP per capita", available
  through the World Bank EdStats API), reads **25 of 45** and its latest
  observation for most countries is **2017**. Missing: AE, AT, DE, DK, FI, FR,
  IS, JP, KW, LU, NL, NO, PA, QA, SA, SE, SG, TW, US, UY. Losing Germany,
  France, the Nordics and the United States guts the very comparison the axis
  exists to draw. Rejected.

### D. Share of tertiary enrolment in private institutions (`SE.TER.PRIV.ZS`)

- Best coverage of anything checked, **42 of 45** (missing CA, GR, TW), World
  Bank / UIS, most values 2018.
- **Rejected on validity, not coverage.** It measures who OWNS the institution,
  not who pays the bill. It reads the United Kingdom at 100% (UK universities
  are legally private bodies), Finland at 47.5% (polytechnics), Belgium at
  57.4%, Latvia at 91.7%, Denmark at 1.0%. Adopting it would put the UK, whose
  fees are deferred through a state loan book, at the private extreme for a
  reason that has nothing to do with fees, and would separate Denmark from
  Finland, which run the same tuition regime. This is the same class of error
  the current axis makes, dressed differently.

### E. Eurostat `educ_uoe_fine01`, government share of total tertiary expenditure

- Checked as a possible filler for the countries the OECD misses.
- **Rejected: not the same quantity.** It returns Norway at 129.9% and Sweden
  at 106.2%, which is a different denominator (total educational expenditure
  including transfers, rather than expenditure on institutions). Germany reads
  94.5 against the OECD's 82.7 and Italy 90.5 against 62.6. It also does not
  carry Switzerland. Mixing it into candidate A would be worse than the gap.

## 2. Measured coverage of the leading candidate

Pulled 02/09/2026 from the SDMX URL above, latest observation per country in
2015 to 2024.

**34 of 45.**

| code | public share % | year |
|---|---|---|
| AT | 87.7 | 2023 |
| AU | 33.9 | 2023 |
| BE | 82.2 | 2023 |
| CA | 53.7 | 2019 |
| CL | 41.4 | 2023 |
| CZ | 71.9 | 2023 |
| DE | 82.7 | 2023 |
| DK | 81.5 | 2023 |
| EE | 80.0 | 2023 |
| ES | 64.0 | 2023 |
| FI | 87.7 | 2023 |
| FR | 66.6 | 2022 |
| GR | 76.4 | 2023 |
| HR | 74.9 | 2022 |
| HU | 69.0 | 2023 |
| IE | 57.9 | 2023 |
| IL | 41.4 | 2023 |
| IS | 87.9 | 2023 |
| IT | 62.6 | 2023 |
| JP | 35.7 | 2023 |
| KR | 47.3 | 2023 |
| LT | 71.9 | 2023 |
| LU | 88.3 | 2023 |
| LV | 48.1 | 2023 |
| NL | 71.7 | 2023 |
| NO | 91.2 | 2023 |
| NZ | 53.5 | 2024 |
| PL | 77.4 | 2023 |
| PT | 55.4 | 2023 |
| SE | 80.0 | 2024 |
| SI | 82.1 | 2023 |
| SK | 81.6 | 2023 |
| UK | 21.8 | 2023 |
| US | 38.4 | 2022 |

**Missing, all eleven named: AE, CH, CY, KW, MT, PA, QA, SA, SG, TW, UY.**

Switzerland is the one that hurts and it is a real absence, not a query
mistake. Switzerland reports general government (`S13`) and international
(`S2`) tertiary expenditure to the OECD in national currency for every year
2015 to 2023, but reports no private (`S1D_NON_EDU`) figure and therefore no
`PT_EXP` share at tertiary level. There is nothing to divide by. It cannot be
filled from Eurostat either, which does not carry Switzerland in
`educ_uoe_fine01`.

The other ten are the file's usual non-OECD gap: the four Gulf states, Cyprus,
Malta, Panama, Singapore, Uruguay and Taiwan.

## 3. Does it separate the options?

Medians over the holders read off the `choices` matrix, exactly as
`build_data.py` derives them.

| option | n with a value | holders | values | median |
|---|---|---|---|---|
| ed_deferred | 3/3 | AU NZ UK | 21.8, 33.9, 53.5 | **33.90** |
| ed_market | 6/8 | JP US CL KR LV IT (no SG, TW) | 35.7, 38.4, 41.4, 47.3, 48.1, 62.6 | **44.35** |
| ed_free_selective | 1/1 | CA | 53.7 | **53.70** |
| ed_free | 17/24 | IL PT IE ES FR HU LT GR PL EE SE DK BE FI IS LU NO (no UY, SA, QA, KW, MT, CY, PA) | 41.4 to 91.2 | **77.40** |
| ed_vocational | 7/9 | NL CZ HR SK SI DE AT (no CH, AE) | 71.7 to 87.7 | **81.60** |

**It separates them hard, and it does NOT order them the way the labels
imply.** Both ends are wrong against the brief's test:

- **ed_market is not lowest. ed_deferred is**, at 33.9 against 44.35. This is
  substantively correct rather than a data fault. A deferred-fee system charges
  the full sticker price and books it to the household, with the state acting
  as lender rather than payer, so the United Kingdom (21.8) and Australia
  (33.9) genuinely shift more of the tertiary bill onto private accounts than
  Italy (62.6) or Korea (47.3) do. The label "Fees at every level past school"
  is doing less work than "deferred fees after" is.
- **ed_free is not highest. ed_vocational is**, 77.4 against 81.6. Also
  defensible: the vocational-track holders (DE, AT, NL, SI, SK, CZ) are free
  AND publicly funded, and the ed_free group is dragged down by Israel (41.4),
  Portugal (55.4) and Ireland (57.9), which are coded free but are not.

What the axis DOES get right is the cleavage that matters. The two fee-charging
options sit at 33.9 and 44.35; the two free options sit at 77.4 and 81.6. A
44-point gap between charging and not charging, on a measure that is explicitly
about who pays. That is a real reading of the domain, which the current axis
does not give at all.

Two classification problems the new axis exposes rather than causes, both
pre-existing and both out of scope for this note:

- **CA is coded `ed_free_selective`, "Free, and selective from twelve".**
  Canadian universities charge substantial tuition. Canada reads 53.7, the
  middle of the fee-charging pack, which is what a fee-charging country should
  read. The option has one holder and that holder looks wrong.
- **IL, PT and IE are coded `ed_free`** and read 41.4, 55.4 and 57.9. All three
  charge tertiary tuition. They are what pulls the ed_free median down.

Fixing either would widen the separation further, not narrow it.

## 4. Projected travel

Bounds re-derived by the `derive_bounds.py` rule (observed span padded 6%,
snapped outward to the axis step, floored at zero, step 1 as for
`health_public`):

- occupants run 21.8 (UK) to 91.2 (NO), option values inside that
- padded span 69.4 * 0.06 = 4.16
- **bounds (17, 96)**

Option span 81.60 - 33.90 = 47.70 on a 79-wide track.

**Travel 60%.** Against the current 15%. That moves education from thinnest of
the thirteen spokes to fifth widest, between grid_carbon (65%) and family
(60%), and puts four percentage points of clear air above the tax spoke.

## 5. What it costs

**Ten cells.** Education goes from 44 of 45 measured to 34 of 45. Total
indicator coverage goes from 570 of 630 to **560 of 630**, 90.5% to 88.9%.

**That breaks the build.** `test_data.py` sets `COVERAGE_FLOOR = 0.89` and
`build_data.py` refuses to write `data.json` when the tests fail, so installing
this axis without also moving the floor produces exactly the intended failure
mode: yesterday's data, loudly. The floor would have to come down to about
0.88. That is a decision, not a formality: the floor was raised to 0.89 on
30/08/2026 precisely so a later addition could not quietly absorb a drop, and
lowering it to admit this change re-opens that slack for everything else.

**Eleven countries would have no education reading at all**, up from one:
AE, CH, CY, KW, MT, PA, QA, SA, SG, TW, UY.

Ten of those eleven already have no reading on `bargaining`, and nine of them
already have none on `pension_spend`, `family_spend` or `redistribution`. So
for ten of the eleven this adds a fifth hole to a row that already has four,
and the new axis would tie `bargaining` as the joint-thinnest axis in the file
at 34 of 45.

**Switzerland is the exception and the real cost.** It currently has a value on
all fourteen axes. Under the new axis it becomes the only OECD country in the
file with an education hole, and Switzerland is also one of the nine
`ed_vocational` holders, so the option loses a holder that is central to what
it describes. `ed_vocational`'s median is computed off 7 of 9 either way,
because AE has no value under the new axis and had one under the old.

## Recommendation

**Switch to the OECD public share of expenditure on tertiary educational
institutions (candidate A).**

The current axis measures the wrong quantity and admits it: `test_data.py`'s
own `REVIEWED_HAND_VS_DERIVED` entry for `ed_free` already says "free tuition
is a question of who pays, not of how much is spent", and names this option as
why the spoke sits on its floor. A 15% travel spoke whose ordering contradicts
its own labels is decoration with a number attached.

The replacement measures the quantity the options actually describe, separates
them by 47.7 points, and lifts travel to 60%.

The two things to decide before installing it, neither of which this note
should decide alone:

1. **The coverage floor has to move from 0.89 to about 0.88, or the build stops.**
2. **The label ordering claim has to be dropped or reworded.** The measure puts
   deferred fees below market fees and vocational above free, and both of those
   are correct readings of who pays. If the page states or implies a ranking
   from ed_market to ed_free anywhere, that copy is now wrong. The honest framing
   is the fee-charging versus free cleavage, not a five-step ladder.

If neither is acceptable, the fallback is NOT to keep `education_spend`. It is
to accept that the domain has no separable measured axis at 45-country
coverage, drop education's spoke from the reveal, and say so, rather than draw
a spoke that moves 15% and points the wrong way.

---

# Filling the eleven: what is findable and what is not

Written 02/09/2026, same day, after the scoping above. RESEARCH ONLY. Nothing
in `axes.py`, `countries.py` or `policies.py` was changed by this work either.

## 0. Two corrections to the premise before anything else

**The file is at 572 of 630, not 570.** Counted by running `countries.py` and
`axes.py` on 02/09/2026: 14 axes x 45 countries = 630, of which 572 are
populated (90.79%). Two cells have been added since the scoping note.

**That means the swap does NOT break the build, with or without any fills.**
572 - 44 + 34 = 562. 562 / 630 = 0.8921, and `test_data.py` asserts
`have / total >= COVERAGE_FLOOR` with `COVERAGE_FLOOR = 0.89`, so 562 passes.
The floor bites at 561 cells (630 x 0.89 = 560.7). Section 5 of the scoping
note is wrong on this point, and the recommendation's decision 1, "the coverage
floor has to move from 0.89 to about 0.88, or the build stops", does not hold.

The margin is one cell, which is not comfortable. The two fills below take it
to 564 / 630 = 0.8952 and a margin of three.

## 1. The eleven

| code | filled | value | year | source |
|---|---|---|---|---|
| CY | **yes** | **43.76** | 2023 | Eurostat UOE, reassembled from `educ_uoe_fine02` + `educ_uoe_fine03` + `educ_uoe_fine01`, see 2 |
| MT | **yes** | **78.30** | 2022 | same construction, see 2 |
| CH | no | - | - | reports no private tertiary figure to anyone, see 3 |
| TW | no | - | - | MOE publishes a public/private split on a domestic definition that is not a source split, see 4 |
| SG | no | - | - | not in the OECD collection; every UIS finance series for Singapore is government-only |
| UY | no | - | - | not in the OECD collection; UIS household tertiary series empty in all years |
| PA | no | - | - | same as UY |
| SA | no | - | - | in the OECD collection but public institutions only: no private or international source rows at all, and every share observation null |
| AE | no | - | - | not in the collection; the only UIS split is initial funding per student, a different quantity |
| QA | no | - | - | UIS tertiary government series last observed 1978 |
| KW | no | - | - | UIS tertiary series stop 2004-2006, with a household zero that predates the private sector |

**Two of eleven.** Both are the two the scoping note ranked most likely after
Switzerland, and neither of them is Switzerland.

The URL for both fills, with `geo` and `time` varied:

```
https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/educ_uoe_fine02
  ?format=JSON&lang=EN&geo=CY&isced11=ED5-8&time=2023
  &unit=MIO_EUR&sector=S13&sector2=TOT_SEC&expend=DIR
https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/educ_uoe_fine03
  ?format=JSON&lang=EN&geo=CY&isced11=ED5-8&time=2023
  &unit=MIO_EUR&sector=S1D&sector2=TOT_SEC&expend=PAY
https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/educ_uoe_fine01
  ?format=JSON&lang=EN&geo=CY&isced11=ED5-8&time=2023
  &unit=MIO_EUR&sector=ORG_INTL
```

Source string in the file's style: `Eurostat UOE education finance, government
share of expenditure on tertiary educational institutions`.

The underlying numbers, EUR million: Cyprus 2023 government 217.6, private
249.2, international 30.5. Malta 2022 government 189.1, private 50.7,
international 1.7.

## 2. How CY and MT were built, and how accurate the method is

The OECD cut does not carry Cyprus or Malta, but both report to the same UOE
collection through Eurostat. Eurostat does not publish the C3.1 share directly.
`educ_uoe_fine01` was already rejected in the scoping note for returning Norway
at 129.9%, and that rejection was right: it is total educational expenditure,
which includes government transfers to households.

The share can be reassembled from the components:

```
public share = S13 direct expenditure on institutions
               / (that + S1D payments to institutions + international organisations)
```

- numerator and first denominator term: `educ_uoe_fine02`, `sector=S13`,
  `sector2=TOT_SEC`, `expend=DIR`, `isced11=ED5-8`
- second: `educ_uoe_fine03`, `sector=S1D`, `sector2=TOT_SEC`, `expend=PAY`
- third: `educ_uoe_fine01`, `sector=ORG_INTL`

**Validated against the OECD, same year, same level, 21 countries.** It
reproduces the published OECD figure exactly to two decimals for eleven:
DE 82.70, IT 62.58, NO 91.17, SE 81.72, NL 71.73, AT 87.70, DK 81.49,
FI 87.66, CZ 71.92, LU 88.29, IS 87.91 against 87.92. Within 1.0 point for five
more: ES 63.96 against 63.69, PT 55.38 against 54.41, BE 82.20 against 81.96,
PL 77.45 against 77.24, HU 68.95 against 68.75.

It is materially off for five, all central and eastern European, and the sign is
always the same, the reconstruction reading low:

| code | OECD | reconstruction | gap |
|---|---|---|---|
| LT | 71.93 | 64.33 | -7.60 |
| SK | 81.61 | 78.12 | -3.49 |
| SI | 82.14 | 79.04 | -3.10 |
| LV | 48.14 | 45.03 | -3.11 |
| EE | 79.99 | 77.49 | -2.50 |

This is not a vintage effect: the same five are off by the same sign and similar
size at 2022, where DE and IT still land exactly. The cause was not identified.
`PAY_NET`, `PAY_SEA` and `TOTAL` are not reported for any of them, so the
alternative private aggregate could not be tested.

**So CY and MT carry an error of zero to about 3 points, with an outside case
of 7.6.** On bounds (17, 96) that worst case is 10% of the track. That is worse
than the OECD-sourced cells and it should be said in the cell comment, not
hidden. It does not change either country's side of the axis: Cyprus is a
fee-charging system at 43.8 whether the truth is 44 or 51, and Malta is a free
system at 78.3 whether the truth is 78 or 86.

**Malta's year is 2022, not 2023, deliberately.** The 2023 observation computes
to 64.47 and is a reporting break, not an event. Government direct expenditure
on tertiary institutions falls from 189.1 to 125.0 EUR million in one year, and
essentially the whole fall is two components collapsing: capital expenditure
50.6 to 21.2 and R&D 38.7 to 5.9. An 85% one-year fall in the R&D spending of a
national university sector is not a thing that happens. Eurostat carries no flag
on the cell. Every year 2013 to 2022 trends smoothly from 94.3 down to 78.3.
2022 is the last trustworthy observation. The file already carries CA at 2019
and FR at 2022, so a 2022 year is not an exception.

Cyprus by contrast is smooth and credible across the whole series: 54.8 (2013),
51.8, 50.6, 52.7, 53.4, 47.5, 44.6, 44.7, 47.0, 45.7, 43.8 (2023). The level is
what it should be for a country whose private universities enrol a majority of
its tertiary students, most of them fee-paying and many of them foreign.

## 3. Switzerland: not fillable, and this was tested rather than assumed

Confirmed at source. Switzerland reports general government (S13, CHF 9448.2m
in 2023) and international (S2, CHF 214.7m) tertiary expenditure on
institutions for every year 2018 to 2023, and reports **no** `S1D_NON_EDU`
value at any tertiary level, at any level of aggregation, in any year. Not
ISCED 5T8, not 6T8, not 5 alone. There is no denominator.

Eurostat does carry Switzerland, which the scoping note said it did not, but it
carries the same hole. `educ_uoe_fine03` returns for CH at ED5-8 only two
things: household **total** educational expenditure counterparted to the total
economy (EUR 893.7m, 2023), and other private entities' **R&D** expenditure on
institutions (EUR 1004.0m, 2023). Neither is the payments-to-institutions
aggregate the method in section 2 needs.

A substitute is available: use household total in place of household payments,
and other-private R&D in place of all other-private payments. That gives
Switzerland **82.95%**, which looks entirely reasonable and would be a
comfortable value to write.

**It was tested against 25 countries where the true answer is known, and it is
not good enough.** Substituting those two components for the correct one, on
2023 data, against the validated construction:

- small: NO +0.22, EE +0.96, MT +1.25, LV +1.40, CY -0.32, IT -0.42, PT -0.62,
  PL -0.63, EL -1.05, AT -1.18, LU +1.59, NL +2.15, LT +2.45, ES -2.42
- then: SK -2.95, BE -3.48, SE -4.03, CZ +6.80, IS -6.85, SI -7.39, DE +8.33,
  FR +9.03
- then: **FI -16.52, DK -19.84, HU +28.83**

Mean error -0.19, standard deviation **8.62**, range -19.84 to +28.83. An
estimator with a 20-point tail cannot be used to place a country on a 79-point
axis. Denmark's true 81.49 comes out at 61.65. Finland's 87.66 comes out at
71.14. Either of those errors would move a country across the whole
fee-charging versus free divide the axis exists to draw.

The Swiss Federal Statistical Office does not close the gap either. Its
education finance statistics (`Bildungsfinanzen`) are public expenditure only.
The one cost-coverage table it publishes, `px-x-1506030100_204`, "Deckung der
Kosten der universitaeren Hochschulen nach Jahr, Fachbereich, Leistung,
Erloeskategorie und Hochschule", fails on two counts at once. It covers
universitaere Hochschulen only, excluding the Fachhochschulen, the
paedagogische Hochschulen and the whole of the hoehere Berufsbildung, which is
about half of Swiss ISCED 5-8 and the half that is most privately financed. And
its revenue categories put `Drittmittel` in one bucket that mixes the SNSF,
Innosuisse and the EU with private research contracts, so the public and
private parts cannot be separated.

**Switzerland becomes the only OECD country in the file with an education hole,
and that is the real price of the swap.** It cannot be bought off.

## 4. Taiwan, and why the number that exists is the wrong number

Taiwan's Ministry of Education does publish an OECD-styled public and private
split by level. Table 4-1 of the 2025 edition of *International Comparison of
Education Statistical Indicators* gives tertiary FY2022 as 1.599% of GDP total,
1.079 public and 0.520 private, which is a public share of **67.5%**.
https://stats.moe.gov.tw/files/ebook/International_Comparison/2025/i2025.pdf

It is the wrong number twice over, and either reason alone disqualifies it.

**It is on the wrong side of the transfers split.** The OECD C3.1 column this
axis uses is final funds, after government transfers to households. Table 4-1 is
built on the OECD's percentage-of-GDP-by-source table, which is initial funds,
before transfers. Taiwan's own United Kingdom row in that table gives 46.6%,
against the 21.8% the axis carries for the UK. Anything compiled on that sheet
sits in a different column from every other cell in the file.

**It is not a source split at all.** Taiwan's public and private is a domestic
definition. National universities' self-raised revenue, which includes their
tuition income and their teaching hospitals' operating income, is counted as
PUBLIC; government subsidies paid to private universities are counted as
PRIVATE. That is institutional ownership with a government overlay, which is
candidate D from the scoping note wearing a different hat, and it is at its most
distorting exactly at Taiwan's tertiary level, where about two thirds of
students are in private institutions and the national universities run large
hospitals. The all-levels share from Table 4-1 (79.43%) reconciles to the digit
with the domestic ownership table in the education yearbook (79.44%), which is
the proof.

Building a correct Taiwanese figure would mean aggregating per-institution
revenue by source across every public and private tertiary institution from the
MOE's institutional disclosure platform. That is a build, not a lookup, and it
was not done.

## 5. The resulting coverage

**Education: 36 of 45.** Up from the scoping note's 34, still down from the
current axis's 44.

**Total: 564 of 630, 89.52%.** Against `COVERAGE_FLOOR = 0.89`, which needs
561. **The build passes and the floor does not have to move.** Margin three
cells.

Without the two fills it would be 562 / 630 = 89.21%, which also passes, with a
margin of one cell. The fills are not what saves the build. What saves the build
is that the file is at 572 rather than the 570 the scoping note assumed.

**Nine countries would have no education reading**, down from the eleven
projected: AE, CH, KW, PA, QA, SA, SG, TW, UY. Eight of those nine already have
no reading on `bargaining`. At 36 of 45 the new axis would not be the
joint-thinnest axis in the file; `bargaining` stays thinnest at 34.

## 6. The four suspected miscodings

All four are real. All four countries charge tertiary tuition, and none of the
four codings survives contact with a source.

| code | reads | coded | what it actually does | should hold |
|---|---|---|---|---|
| CA | 53.68 | ed_free_selective | average domestic undergraduate tuition **CAD 7,734** in 2025/26, from CAD 3,746 in Newfoundland and Labrador to CAD 9,988 in Nova Scotia. No examination at twelve anywhere in Canada. Federal and provincial loans repay on a fixed schedule with hardship relief, not income-contingently through the tax system. | **ed_market** |
| IL | 41.44 | ed_free | standard undergraduate tuition **NIS 12,017** for 2025/26, set nationally by the Council for Higher Education and indexed to CPI, charged by every university | **ed_market** |
| PT | 55.38 | ed_free | *propina* capped by law at **EUR 697** a year for a first cycle in 2025/26, rising to EUR 710 for 2026/27 when the government unfreezes it | **ed_market**, weakly |
| IE | 57.86 | ed_free | the state pays tuition for eligible EU undergraduates under the Free Fees Initiative, but every one of them still owes the **student contribution charge, EUR 2,500** in 2025/26, falling to EUR 2,000 from 2026/27. Postgraduate study is full fee. | **ed_market** |

Sources:

- Canada: Statistics Canada, *Tuition in Canada: modest increases and widening
  gaps, 2025/2026*, The Daily, 10/09/2025.
  https://www150.statcan.gc.ca/n1/daily-quotidien/250910/dq250910d-eng.pdf
- Israel: Council for Higher Education standard rate, as published by the
  charging institutions. https://en.studentsadmin.huji.ac.il/tuition-structure
  and https://www.biu.ac.il/en/registration-and-admission/tuition/rates-and-related-fees
- Portugal: DGES, *Propinas*. https://www.dges.gov.pt/pt/pagina/propinas
- Ireland: Higher Education Authority, *Free Fees Initiative*.
  https://hea.ie/funding-governance-performance/funding/student-finance/course-fees/
  and UCD, *Student Contribution*.
  https://www.ucd.ie/students/fees/studentcontribution/

**CA is the worst of the four and it is wrong on both halves of its label.**
Canadian universities charge, and Canada does not select at twelve. It is the
only holder of `ed_free_selective`, which suggests the coding was made to give
the option a holder rather than because it describes Canada.

**PT is the weakest recommendation.** EUR 697 is an order of magnitude below
Canada's CAD 7,734 and Israel's NIS 12,017, and it is set by statute rather than
by the university, which is the opposite of `ed_market`'s detail line,
"Universities set their own prices". The five options have no home for a country
that charges a small nationally-capped fee. Portugal is a reason to consider a
sixth option, not a reason to trust the fifth.

**Recoding all four empties `ed_free_selective` completely.** With the two fills
and all four moves:

| option | n | median | holders |
|---|---|---|---|
| ed_deferred | 3 | 33.95 | UK AU NZ |
| ed_market | 10 | 47.72 | JP US CL IL KR LV CA PT IE IT |
| ed_free | 16 | 79.15 | CY ES FR HU LT GR PL MT EE SE DK BE FI IS LU NO |
| ed_vocational | 7 | 81.61 | NL CZ HR SK SI DE AT |
| ed_free_selective | **0** | none | none |

The option span is 47.66 either way, because it is set by ed_deferred at the
bottom and ed_vocational at the top and neither moves. **The recodings do not
widen the axis.** What they do is make ed_market and ed_free honest, at the cost
of leaving one of the five options with no country at all. `build_data.py`
derives option axis values from holders; an option with no holders has no median
to derive from and would need a hand value, or would need deleting.

No country in the file fits "Free, and selective from twelve" as written. The
countries that stream early are already in `ed_vocational`. The countries that
select hard at twelve, in the sense of one examination deciding the school, are
Singapore and Taiwan, and both charge fees.

## 7. Reasons the swap might still be a bad idea

Three found. None is fatal on its own. The first is the one that would change my
mind.

**The measure is after transfers, and the page never says so.** The C3.1 column
this axis uses attributes government-to-household transfers to the household.
When a state lends a student the fee and the student pays the university, the
university's money is counted as private. That is what puts the United Kingdom
at 21.8, below Chile, Israel, Korea, Latvia and Japan. It is a defensible
reading of who pays, and the scoping note argues for it, but it is not the only
one: the same OECD table's initial-funds column puts the UK at 44.05 against
Italy's 73.65, and on that column the ordering the labels imply comes closer to
holding. Adopting the after-transfers column is an editorial position on whether
a student loan is the state paying or the student paying. It should be stated on
the page, because a reader who assumes the other convention will read the UK's
spoke as an error.

**Cyprus and Malta show what the measure picks up besides fees.** Cyprus reads
43.8, in the fee-charging band, and Cyprus charges its own nationals nothing at
its public universities. What the 43.8 measures is that Cyprus has a large
private university sector selling to foreign students. Malta reads 78.3 for the
mirror-image reason. The same mechanism runs through the OECD countries and is
part of why Japan and Korea sit low. So the axis is partly a measure of how big
a country's private and international tertiary market is, which is a cousin of
candidate D, rejected in the scoping note on exactly that ground.

It is a cousin and not a twin, and this was measured. Correlation between the
new axis and share of tertiary enrolment in private institutions
(`SE.TER.PRIV.ZS`, World Bank, mostly 2018) across the 32 countries with both is
**r = -0.64**. Real, and not dominant. Finland has 47.5% of its students in
private institutions and reads 87.66; Belgium 57.4% and reads 82.20; the United
Kingdom is 100% private on that measure and reads 21.76. The new axis separates
cases that candidate D collapses, which was the whole reason for rejecting D.

**Nine holes, and one of them is Switzerland.** Section 3 could not fix it and
established that it cannot be fixed from any public source. Switzerland loses a
reading it currently has on all fourteen axes, and it is one of the countries
that most needs to read on this domain, because it holds `ed_vocational` and is
the archetype of it.

## 8. What this changes about the recommendation

The scoping note's recommendation stands, and one of its two conditions falls
away.

1. **The coverage floor does not have to move.** It was never going to break.
   Section 0.
2. **The label ordering claim still has to be dropped or reworded**, and section
   7's first point makes the case sharper than the scoping note did. The
   after-transfers convention is not a detail; it is the reason the ordering
   comes out the way it does, and it belongs in the copy.

Two to add:

3. **CA, IL, PT and IE should be recoded with the swap, not after it.** The
   scoping note called them pre-existing and out of scope. They are pre-existing,
   but the new axis is what makes them visible, and shipping an axis that reads
   Ireland at 57.9 next to a label saying "Free through university" invites
   exactly the objection the axis exists to answer. Recoding empties
   `ed_free_selective`, which is a separate decision and probably means deleting
   the option or rewriting it.
4. **CY and MT carry a wider error bar than the other 34 cells.** Their comments
   should say so, along with Malta's 2022 year and why it is not 2023.

---

# Uruguay, investigated 02/09/2026 and deliberately left empty

Written after the axis shipped, so that nobody rediscovers this number and reads
it as a free win.

A defensible-looking public share of about **88.3% for 2024 IS constructible**
for Uruguay, from INEEd Mirador indicators 51 and 53. It was not added, and the
reason is basis rather than availability. Four gaps, any one of which disqualifies
it:

- the numerator is public expenditure on **education**, not government
  expenditure on **institutions**, so student aid and transfers to households sit
  inside it, as does UdelaR's Hospital de Clinicas at about 22% of UdelaR's
  budget
- the household side excludes payments to public institutions, so the Fondo de
  Solidaridad falls in the public series and is counted as public
- there are no business, non-profit or international funds at all by level
- the underlying series is interpolated between two household-survey waves

That is a different quantity wearing the right label, which is the exact failure
this file has had before: a number that is individually defensible and measures
something else. It would also land Uruguay near the top of the axis, so the error
would be loud rather than harmless. Panama is simpler: the denominator does not
exist.

Education stays at 36 cells and the nine countries without one stay at nine.

## The four Gulf states, checked and closed

SA, AE, QA and KW were researched properly rather than assumed, and all four are
NOT AVAILABLE. None of the four national statistical systems publishes
expenditure on tertiary institutions split by source of funds, so the DENOMINATOR
of the ratio does not exist. All four publish government budget allocation to
education, which is a numerator on a budget basis, and enrolment, staff and
graduate counts on the education side. Nothing in those systems combines into
this measure without inventing the private half.

The UAE is confirmed at table level, which is the strongest of the four. FCSC's
"Higher Education Statistics 2023/2024" contains exactly six tables: students by
gender, students by ISCED level, graduates by field, inbound mobile students,
academic staff, and a set of ratio indicators. Its own methodology paper says the
source is Ministry of Education administrative records and that the report covers
student numbers. No expenditure variable is collected at all.

Saudi Arabia: a full-site search of stats.gov.sa for expenditure on education
returns three documents, none about tertiary financing. Qatar: the open data
portal carries 238 education-tagged datasets, all enrolment-side, and "tuition"
returns zero. Kuwait: the CSB education bulletin's own component manifest has no
finance section.

THREE PLAUSIBLE-LOOKING SUBSTITUTES ARE IN CIRCULATION AND ALL THREE ARE WRONG,
which is why this is written down rather than left as "no data":

  - education as a share of total GOVERNMENT expenditure (Saudi 17%, Qatar 8.9%).
    A different concept, and it is the figure a search engine hands you first.
  - KHDA's tuition-revenue totals for Dubai (Dh7.5bn). Those are PRIVATE SCHOOLS,
    ISCED 0 to 3. KHDA publishes no revenue figure for higher education.
  - the share of tertiary students enrolled in private institutions (UAE about
    70%). An enrolment share is not an expenditure share, and the two come apart
    hardest exactly where the state subsidises private provision.

The structural reason is the same in all four: tertiary data is collected from
ministry enrolment registers and education finance is collected from the state
budget, so the private half is never collected by anyone. That matters most for
the UAE and Qatar, where the private and branch-campus sector is the majority of
provision and therefore the majority of the number.

If a figure is ever genuinely needed the only defensible routes are a bespoke
request to GASTAT, FCSC, PSA or CSB, or the UNESCO UIS finance questionnaire
returns. There is no evidence any of the four reports the private-source tertiary
split to UIS either, so check before assuming that route yields anything.
