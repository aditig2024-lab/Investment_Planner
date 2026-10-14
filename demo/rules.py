"""
Deterministic finance + rule layer.  No LLM in this file.
"""
from dataclasses import dataclass

RISK_ORDER = ["CONSERVATIVE", "MODERATE", "MOD_AGG", "AGGRESSIVE"]

def effective_risk(stated: str, observed: str) -> str:
    """R-RISK-03: never plan above what the investor has actually tolerated."""
    return min(stated, observed, key=RISK_ORDER.index)

def future_value(pv: float, r: float, years: float) -> float:
    return pv * (1 + r) ** years

def sip_for_target(target: float, r_annual: float, months: int) -> float:
    r = r_annual / 12
    factor = ((1 + r) ** months - 1) / r * (1 + r)      # SIP at start of month
    return target / factor

def stepup_sip_for_target(target: float, r: float, years: int, step: float) -> float:
    def fv(sip):
        tot = 0.0
        for y in range(years):
            block = sip * (1 + step) ** y * (((1 + r / 12) ** 12 - 1) / (r / 12)) * (1 + r / 12)
            tot += block * (1 + r) ** (years - 1 - y)
        return tot
    lo, hi = 0.0, 1e6
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fv(mid) < target else (lo, mid)
    return hi

# Horizon x risk -> (equity, debt, gold, reit) in %
SAA = {
    ("<1y",  "ANY"):      (0, 100, 0, 0),
    ("3-5y", "MODERATE"): (40, 60, 0, 0),
    ("3-5y", "MOD_AGG"):  (40, 60, 0, 0),     # capped by R-HZN-01 regardless of risk
    ("10-15y", "MODERATE"): (65, 25, 10, 0),
    ("20y+", "MODERATE"): (65, 25, 5, 5),
    ("20y+", "MOD_AGG"):  (75, 15, 5, 5),
}

@dataclass
class Rule:
    id: str; text: str; origin: str | None = None

RULES = [
    Rule("R-RISK-03", "effective risk = min(stated, observed)"),
    Rule("R-HZN-01",  "equity ≤ 40% for goals 3–5y; glide to 0% from T-2y", origin="PLN-2024-0931"),
    Rule("R-SIP-01",  "total SIP ≤ 90% of monthly surplus; prefer step-up", origin="PLN-2022-0188"),
    Rule("R-TAX-01",  "ELSS only under old regime and only up to 80C headroom", origin="PLN-2025-1204"),
    Rule("R-TAX-02",  "NPS Tier-I ₹50k/yr for 80CCD(1B) when horizon ≥ 15y"),
    Rule("R-ELIG-01", "REIT/InvIT: horizon ≥ 7y and risk ≥ MODERATE, cap 5%"),
    Rule("R-ELIG-02", "direct-equity sleeve: risk ≥ MOD_AGG and income ≥ ₹25L"),
    Rule("R-ELIG-03", "AIF / alternatives: min ticket ₹1 Cr"),
    Rule("R-GOLD-01", "SGB if a primary tranche is open, else gold ETF"),
    Rule("R-EMG-01",  "emergency fund = 6× essential expenses, before any other goal"),
    Rule("R-DRIFT-01", "rebalance when a sleeve leaves its ±7pp band"),
    Rule("R-FQ-02",   "manager change → WATCH for 2 quarters, no new money"),
]

class ruleset:
    @staticmethod
    def eligibility(product: str, ctx) -> dict:
        p, risk, inc = product.upper(), ctx.risk_effective, ctx.profile.income_annual
        if p in ("REIT", "INVIT"):
            ok = RISK_ORDER.index(risk) >= 1 and ctx.longest_horizon_years >= 7
            return {"product": p, "eligible": ok, "cap_pct": 5, "rule": "R-ELIG-01"}
        if p == "DIRECT_EQUITY":
            ok = RISK_ORDER.index(risk) >= 2 and inc >= 2_500_000
            return {"product": p, "eligible": ok, "rule": "R-ELIG-02",
                    "reason": None if ok else f"risk_effective={risk} (observed behaviour)"}
        if p in ("AIF", "ALTERNATIVES"):
            return {"product": p, "eligible": ctx.profile.investable_lumpsum >= 1e7, "rule": "R-ELIG-03"}
        return {"product": p, "eligible": False, "rule": None}

def fund_plan(ctx) -> dict:
    """Stage-3 fan-in: priority waterfall over the surplus. Pure arithmetic."""
    order = ["emergency", "house", "education", "retirement"]
    surplus, ceiling = ctx.profile.monthly_surplus, 0.90 * ctx.profile.monthly_surplus
    sips, total = {}, 0
    for g in order:
        want = ctx.goals.sip_for(g)
        take = min(want, max(ceiling - total, 0))
        sips[g], total = take, total + take
    redirects = [{"from": "emergency", "to": "house", "amount": sips["emergency"],
                  "when": ctx.goals.months_to_fill("emergency")},
                 {"from": "car_emi", "to": "retirement", "amount": ctx.profile.emi_ending,
                  "when": ctx.profile.emi_months_left}]
    return {"sips": sips, "total": total, "buffer": surplus - total,
            "ceiling_ok": total <= ceiling, "redirects": redirects}

def needs_adviser_signoff(ctx, args: dict) -> bool:
    """Gate for propose_plan / propose_review."""
    new_plan = ctx.context.plan_version == 1
    big_sip_change = abs(args.get("sip_delta", args.get("monthly_sip", 0))) >= 10_000
    rebalance = bool(args.get("rebalances"))
    waiver = bool(args.get("rules_waived"))
    return new_plan or big_sip_change or rebalance or waiver
