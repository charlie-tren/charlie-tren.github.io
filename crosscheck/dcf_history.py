"""Point-in-time Valuation for the reconstructed record, rebuilt from SEC filings.

    python crosscheck/dcf_history.py              # writes "vp" into history.jsonl
    python crosscheck/dcf_history.py --check      # only the agreement check, no write

WHY. The reconstructed cohorts (2021 onward, "b": 1) could not be scored on valuation:
the DCF ratio they carried came from a 2026 snapshot, which is hindsight. This rebuilds
the leg as DCF Studio would have read it at each cohort date, and accounts quality's
twin, strain_history.py, did the same for the other leg.

THE MODEL IS NOT REIMPLEMENTED. Each (company, date) becomes the Fundamentals object
DCF Studio's own normaliser would produce, and dcf-studio/scripts/value-history.ts runs
valueFundamentals on it - the function the live site runs - with the same two rules
publish-valuations.ts applies before a ratio may be ranked. Only the INPUTS differ:

- Statements: SEC XBRL frames, the four fiscal years up to the latest one public by the
  cohort date (1 April after the year, as strain_history.py). Yahoo also gives four.
  Frames return the latest value for a period, so a restated year carries slight
  hindsight; stated, as for accounts.
- Price: the close on the cohort date. Yahoo closes are split-adjusted to today, as-filed
  share counts are not, so the share count is put into today's units with the splits
  after the filing (edge-search's as-filed trap). The ratio is then equity value over
  market cap at that date, whatever the units.
- Beta: 60 monthly returns to the cohort date against the S&P 500, as Yahoo's own.
- Risk-free: the 10-year Treasury that day (FRED DGS10), where live uses ^TNX.
- Financials: declined, from Crosscheck's sector, as live declines them from Yahoo's.
- Leases: Yahoo's total debt includes lease liabilities and this does not. Consistent
  across the record, which is what a rank needs.

CHECK. The same pipeline run on today's inputs (FY2025, today's price, today's yield)
must order companies like live DCF Studio does. Reported as a rank correlation, and the
run stops if it is below 0.6 - the inputs differ (SEC v Yahoo, leases, beta), so this
cannot be the near-identity strain_history.py demands, but it must be the same model.

SCOPE. US only, and percentiles are struck within each cohort date, within sector where
the sector has DCF_SECTOR_MIN names (build.py's rule), else against the whole date.
"""
import argparse
import json
import math
import pickle
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DCF = HERE.parent.parent / "dcf-studio"
HISTORY = HERE / "history.jsonl"
FRAMES = HERE / "dcf_frames.pkl"           # gitignored, like strain_frames.pkl
MARKET = HERE / "dcf_market.pkl"           # monthly closes, splits, yields; gitignored
YEARS = list(range(2016, 2026))
SCORED = list(range(2019, 2026))
CHECK_GATE = 0.6

sys.path.insert(0, str(HERE))
import strain_history as sh  # noqa: E402

DURATION, INSTANT = "duration", "instant"
# The lines the engine needs that Shortfall's sweep does not carry. Order is the chain.
EXTRA = {
    "DandA": (DURATION, ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
                         "DepreciationAndAmortization"]),
    "Depreciation": (DURATION, ["Depreciation"]),
    "Amortisation": (DURATION, ["AmortizationOfIntangibleAssets"]),
    "Capex": (DURATION, ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"]),
    "NwcChange": (DURATION, ["IncreaseDecreaseInOperatingCapital"]),
    "Interest": (DURATION, ["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt"]),
    "CashSTI": (INSTANT, ["CashCashEquivalentsAndShortTermInvestments"]),
    "Cash": (INSTANT, ["CashAndCashEquivalentsAtCarryingValue",
                       "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]),
    "STI": (INSTANT, ["ShortTermInvestments", "MarketableSecuritiesCurrent",
                      "AvailableForSaleSecuritiesDebtSecuritiesCurrent"]),
    "DebtCurrent": (INSTANT, ["LongTermDebtCurrent", "DebtCurrent"]),
    "ShortBorrow": (INSTANT, ["ShortTermBorrowings", "CommercialPaper"]),
    "Payables": (INSTANT, ["AccountsPayableCurrent"]),
}
PRETAX = ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
          "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]


def available_from(fy: int) -> str:
    return sh.available_from(fy)


def periods(fy):
    return f"CY{fy}", f"CY{fy}Q4I"


def sweep(edgar):
    frames = pickle.load(open(FRAMES, "rb")) if FRAMES.exists() else {}
    base = pickle.load(open(sh.CACHE, "rb"))       # Shortfall's own tags, already swept
    for fy in YEARS:
        dur, ins = periods(fy)
        got = frames.setdefault(fy, {dur: {}, ins: {}})
        for concept, (kind, chain) in EXTRA.items():
            p = ins if kind == INSTANT else dur
            for tag in chain:
                if tag not in got[p]:
                    got[p][tag] = edgar.frame(tag, "USD", p)
        pickle.dump(frames, open(FRAMES, "wb"))
        for p in (dur, ins):
            for tag, v in base[fy].get(p, {}).items():
                got[p].setdefault(tag, v)
        print(f"  frames FY{fy}", flush=True)
    return frames


def first(fr, period, chain, cik):
    for tag in chain:
        v = fr.get(period, {}).get(tag, {}).get(cik)
        if v is not None:
            return v, tag
    return None, None


def S(v, field, derived=False):
    p = {"sourceField": field, "derived": derived}
    if derived:
        p["derivation"] = field
    return {"value": float(v), "provenance": p}


def year(frames, cik, fy, tags):
    """One FiscalYear in DCF Studio's shape, following lib/normalise.ts's chains and signs."""
    if fy not in frames:
        return None
    dur, ins = periods(fy)
    fr = frames[fy]
    rev, _ = first(fr, dur, tags.CHAINS["Revenue"], cik)
    if rev is None or rev <= 0:
        return None
    pretax, _ = first(fr, dur, PRETAX, cik)
    interest, _ = first(fr, dur, EXTRA["Interest"][1], cik)
    op, _ = first(fr, dur, ["OperatingIncomeLoss"], cik)
    if op is not None:
        ebit = S(op, "OperatingIncomeLoss")
    elif interest is not None:
        ebit = S((pretax or 0) + interest, "pretax + interest", True)
    else:
        ebit = S(pretax or 0, "pretax income", True)
    tax, _ = first(fr, dur, ["IncomeTaxExpenseBenefit"], cik)
    da, _ = first(fr, dur, EXTRA["DandA"][1], cik)
    da = da or 0.0
    dep, _ = first(fr, dur, EXTRA["Depreciation"][1], cik)
    if dep is None:
        am, _ = first(fr, dur, EXTRA["Amortisation"][1], cik)
        if am is not None and da - am >= 0:
            dep = da - am
    capex, _ = first(fr, dur, EXTRA["Capex"][1], cik)        # XBRL payments are positive outflows
    nwc, _ = first(fr, dur, EXTRA["NwcChange"][1], cik)      # positive = increase = outflow, as canonical
    if nwc is None and fy - 1 in frames:
        _, pins = periods(fy - 1)
        pr = frames[fy - 1]
        parts = [(tags.CHAINS["Receivables"], 1), (tags.CHAINS["Inventory"], 1), (EXTRA["Payables"][1], -1)]
        tot = found = 0
        for chain, sign in parts:
            a, _ = first(fr, ins, chain, cik)
            b, _ = first(pr, pins, chain, cik)
            if a is not None and b is not None:
                tot += sign * (a - b)
                found += 1
        nwc = tot if found else None
    debt, dtag = first(fr, ins, tags.CHAINS["TotalDebt"], cik)
    debt = debt or 0.0
    if dtag in ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"):
        debt += first(fr, ins, EXTRA["DebtCurrent"][1], cik)[0] or 0.0
    if dtag != "DebtLongtermAndShorttermCombinedAmount":
        debt += first(fr, ins, EXTRA["ShortBorrow"][1], cik)[0] or 0.0
    cash, _ = first(fr, ins, EXTRA["CashSTI"][1], cik)
    if cash is None:
        c, _ = first(fr, ins, EXTRA["Cash"][1], cik)
        s, _ = first(fr, ins, EXTRA["STI"][1], cik)
        cash = None if c is None else c + (s or 0.0)
    cash = cash or 0.0
    shares, _ = first(fr, dur, tags.CHAINS["DilutedShares"], cik)
    if not shares:
        return None
    equity, _ = first(fr, ins, tags.CHAINS["Equity"], cik)
    ic = None if equity is None else equity + debt - cash
    return {
        "periodEnd": f"{fy}-12-31",
        "revenue": S(rev, "Revenue"),
        "ebit": ebit,
        "taxProvision": S(tax or 0, "IncomeTaxExpenseBenefit"),
        "pretaxIncome": S(pretax or 0, "pretax income"),
        "dAndA": S(da, "DandA"),
        "depreciation": None if dep is None else S(dep, "Depreciation"),
        "capex": S(capex or 0, "Capex"),
        "changeInNwc": S(nwc or 0, "NwcChange"),
        "totalDebt": S(debt, "TotalDebt"),
        "cash": S(cash, "Cash"),
        "shares": S(shares, "DilutedShares"),
        "interestExpense": None if interest is None else S(interest, "Interest"),
        "investedCapital": None if ic is None or ic <= 0 else S(ic, "equity + debt - cash", True),
    }


def market_data(tickers):
    """Monthly closes (for beta), splits and the 10-year yield, cached.

    ONE batched Yahoo download with actions=True carries the closes and the splits
    together. The first version asked yf.Ticker(t).splits once per company, ~600 calls,
    and Yahoo answered every one of them "possibly delisted" (rate-limited, 08/10/2026).
    """
    cached = pickle.load(open(MARKET, "rb")) if MARKET.exists() else {}
    have = set(cached.get("monthly", pd.DataFrame()).columns)
    if not set(tickers) <= have:
        import yfinance as yf
        allt = sorted(set(tickers) | (have - {"^GSPC"}))
        raw = yf.download(allt + ["^GSPC"], start="2015-01-01", interval="1d", auto_adjust=True,
                          actions=True, progress=False, threads=True)
        close = raw["Close"]
        got = [t for t in allt if t in close.columns and close[t].notna().sum() > 250]
        assert len(got) >= 0.9 * len(allt), f"Yahoo returned prices for only {len(got)} of {len(allt)}"
        cached["monthly"] = close.resample("ME").last()
        sp = raw["Stock Splits"]
        cached["splits"] = {t: [(str(k.date()), float(v)) for k, v in sp[t].items() if v and v > 0]
                            for t in got if t in sp.columns}
        pickle.dump(cached, open(MARKET, "wb"))
        print(f"  prices and splits for {len(got)} of {len(allt)}", flush=True)
    if "dgs10" not in cached or cached["dgs10"].index.max() < pd.Timestamp(date.today()) - pd.Timedelta(days=7):
        for attempt in range(3):
            txt = subprocess.run(["curl", "-s", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"],
                                 capture_output=True, text=True).stdout
            rows = [l.strip().split(",") for l in txt.strip().splitlines()[1:]]
            s = pd.Series({pd.Timestamp(a): float(b) / 100 for a, b in (r for r in rows if len(r) == 2)
                           if b not in (".", "")})
            if len(s) > 10000:
                break
        assert len(s) > 10000, f"FRED DGS10 came back short: {txt[:200]!r}"
        cached["dgs10"] = s.sort_index()
        pickle.dump(cached, open(MARKET, "wb"))
    return cached


def split_factor(splits, after: str) -> float:
    f = 1.0
    for d, r in splits:
        if d > after:
            f *= r
    return f


def beta_at(monthly, t, d):
    if t not in monthly.columns:
        return None
    m = monthly[[t, "^GSPC"]]
    m = m[m.index <= pd.Timestamp(d)].pct_change().dropna().tail(60)
    if len(m) < 36:
        return None
    var = m["^GSPC"].var()
    return None if var <= 0 else float(m[t].cov(m["^GSPC"]) / var)


def rate_at(dgs10, d):
    s = dgs10[dgs10.index <= pd.Timestamp(d)]
    return float(s.iloc[-1])


def fundamentals(t, sector, yrs, price, d, beta):
    shares = yrs[0]["shares"]["value"]
    flags = []
    if sector == "Financials":
        flags.append({"code": "FINANCIAL_SECTOR", "severity": "error", "message": "financial"})
    return {
        "ticker": t, "name": t, "exchange": "", "sector": sector, "industry": None,
        "reportingCurrency": "USD", "quoteCurrency": "USD", "years": yrs,
        "price": price, "priceAsOf": d, "marketCap": price * shares, "rawBeta": beta,
        "analystRevenue": [], "flags": flags,
    }


def run_engine(entries):
    inp, out = HERE / "_dcf_in.json", HERE / "_dcf_out.json"
    inp.write_text(json.dumps(entries))
    r = subprocess.run("npx tsx scripts/value-history.ts " + f'"{inp}" "{out}"',
                       cwd=DCF, shell=True, capture_output=True, text=True)
    print("  engine:", (r.stdout or r.stderr).strip().splitlines()[-1], flush=True)
    res = json.loads(out.read_text())
    inp.unlink()
    out.unlink()
    return res


def sectors():
    html = (HERE / "index.html").read_text(encoding="utf-8")
    rows = json.loads(re.search(r'<script id="rows"[^>]*>(.*?)</script>', html, re.S).group(1))
    return {r["ticker"]: r.get("sector") for r in rows}


def rank_corr(a, b):
    return sh.rank_corr(a, b)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    sec = sectors()
    build_data, edgar, fetch_us = sh.load_shortfall()
    import tags  # Shortfall's chains, so the shared lines resolve exactly as its build does
    meta = sh.us_meta(edgar)
    cik_of = {m["ticker"]: cik for cik, m in meta.items()}
    frames = sweep(edgar)

    def years_for(t, fy):
        cik = cik_of.get(t)
        if cik is None:
            return None
        ys = [year(frames, cik, y, tags) for y in range(fy, fy - 4, -1)]
        ys = [y for y in ys if y is not None]
        return ys if ys and ys[0]["periodEnd"].startswith(str(fy)) else None

    lines = [json.loads(l) for l in HISTORY.read_text(encoding="utf-8").splitlines() if l.strip()]
    recon = [r for r in lines if r.get("b") and not r["t"].endswith(".AX")]
    live = json.load(open(DCF / "public" / "valuations.json", encoding="utf-8"))
    live_us = {t: v for t, v in live["ratios"].items() if not t.endswith(".AX") and t in cik_of}
    mk = market_data(sorted({r["t"] for r in recon} | set(live_us)))
    today = date.today().isoformat()

    # 1. Agreement with live: FY2025 statements, live's own price, today's yield and beta.
    entries = []
    for t, _ in live_us.items():
        ys = years_for(t, 2025)
        price = live["prices"][t][0]
        if not ys:
            continue
        f = split_factor(mk["splits"].get(t, []), available_from(2025))
        for y in ys:
            y["shares"]["value"] *= f
        entries.append({"key": t, "fundamentals": fundamentals(t, sec.get(t), ys, price, today,
                                                                beta_at(mk["monthly"], t, today)),
                        "riskFree": {"rate": rate_at(mk["dgs10"], today), "source": "DGS10", "assumed": False}})
    res = run_engine(entries)
    mine = {k: v["ratio"] for k, v in res.items() if v["ratio"] is not None}
    both = set(mine) & set(live_us)
    rho = rank_corr({k: mine[k] for k in both}, {k: live_us[k] for k in both})
    print(f"agreement with live DCF Studio, today's inputs: rank correlation {rho:.3f} over {len(both)} "
          f"names (live values {len(live_us)}, this values {len(mine)})")
    if rho < CHECK_GATE:
        print(f"STOP: below {CHECK_GATE}; the rebuilt inputs do not reproduce the live model's ordering")
        return 1
    if args.check:
        return 0

    # 2. Every reconstructed US line, at its own date.
    px = pd.read_pickle(HERE / "bbg" / "daily_closes.pkl")
    entries = []
    for r in recon:
        d, t = r["d"], r["t"]
        usable = [y for y in SCORED if available_from(y) <= d]
        if not usable or t not in px.columns:
            continue
        fy = max(usable)
        ys = years_for(t, fy)
        s = px[t].dropna()
        s = s[s.index <= pd.Timestamp(d)]
        if not ys or s.empty:
            continue
        f = split_factor(mk["splits"].get(t, []), available_from(fy))
        for y in ys:
            y["shares"]["value"] *= f
        entries.append({"key": f"{t}|{d}", "fundamentals": fundamentals(t, sec.get(t), ys, float(s.iloc[-1]), d,
                                                                         beta_at(mk["monthly"], t, d)),
                        "riskFree": {"rate": rate_at(mk["dgs10"], d), "source": "DGS10", "assumed": False}})
    res = run_engine(entries)
    ratio = {k: v["ratio"] for k, v in res.items() if v["ratio"] is not None}

    # Percentile per date: within sector where it has DCF_SECTOR_MIN, else the whole date.
    sys.path.insert(0, str(HERE))
    import build  # noqa: E402
    by_date: dict = {}
    for k, v in ratio.items():
        t, d = k.split("|")
        by_date.setdefault(d, []).append((t, v))
    pct = {}
    for d, items in by_date.items():
        groups: dict = {}
        for t, v in items:
            groups.setdefault(sec.get(t), []).append((t, v))
        big = {g for g, it in groups.items() if g is not None and len(it) >= build.DCF_SECTOR_MIN}
        for g in big:
            for (t, _), p in zip(groups[g], build._percentiles([v for _, v in groups[g]])):
                pct[f"{t}|{d}"] = p
        rest = [(t, v) for t, v in items if sec.get(t) not in big]
        allp = dict(zip([t for t, _ in items], build._percentiles([v for _, v in items])))
        for t, _ in rest:
            pct[f"{t}|{d}"] = allp[t]

    raw = HISTORY.read_text(encoding="utf-8").splitlines()
    added = 0
    for r in lines:
        if not r.get("b"):
            continue
        r.pop("vp", None)
        k = f"{r['t']}|{r['d']}"
        if k in pct:
            r["vp"] = round(pct[k], 4)
            added += 1
    out = [json.dumps(r, separators=(",", ":")) for r in lines]
    kept = [l for l in raw if l.strip()]
    assert sum(1 for a, b, r in zip(kept, out, lines) if not r.get("b") and a != b) == 0
    HISTORY.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"vp on {added} of {len(recon)} US reconstructed lines ({len(entries)} modelled)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
