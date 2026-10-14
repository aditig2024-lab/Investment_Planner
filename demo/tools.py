"""
Function tools exposed to the specialists.  Decorated with @function_tool so
the SDK derives the JSON schema from signature + docstring.  Every tool reads
or writes the shared PlanContext through RunContextWrapper.
"""
from agents import function_tool, RunContextWrapper
from context import PlanContext
from rules import (ruleset, sip_for_target, future_value, stepup_sip_for_target,
                   effective_risk, needs_adviser_signoff)
import data


@function_tool
async def fetch_kyc_and_profile(ctx: RunContextWrapper[PlanContext]) -> dict:
    """KYC, income, dependants, assets, liabilities, monthly surplus, tax regime."""
    return data.INVESTORS[ctx.context.investor_id]


@function_tool
async def fetch_risk_questionnaire(ctx: RunContextWrapper[PlanContext]) -> dict:
    """Validated 12-item questionnaire score (0-100) and band."""
    return data.QUESTIONNAIRE[ctx.context.investor_id]


@function_tool
async def observe_behaviour(ctx: RunContextWrapper[PlanContext], months: int = 36) -> dict:
    """Behavioural risk from the transaction ledger: SIP pauses, redemptions in drawdowns."""
    return data.behaviour_from_ledger(ctx.context.investor_id, months)


@function_tool
async def record_profile(ctx: RunContextWrapper[PlanContext], risk_stated: str,
                         risk_observed: str, reason: str) -> str:
    """Persist the profile; effective risk is min(stated, observed) per R-RISK-03."""
    ctx.context.risk_effective = effective_risk(risk_stated, risk_observed)
    ctx.context.audit("PROFILE", reason)
    return ctx.context.risk_effective


@function_tool
async def compute_goal_corpus(ctx: RunContextWrapper[PlanContext], goal: str, cost_today: float,
                              inflation: float, years: float, existing: float = 0.0,
                              existing_return: float = 0.0, blended_return: float = 0.10,
                              step_up: float = 0.0) -> dict:
    """Target corpus, FV of earmarked assets, gap and the monthly SIP that closes it."""
    target = future_value(cost_today, inflation, years)
    seed = future_value(existing, existing_return, years)
    gap = max(target - seed, 0)
    sip = (stepup_sip_for_target(gap, blended_return, years, step_up) if step_up
           else sip_for_target(gap, blended_return, int(years * 12)))
    return {"goal": goal, "target": round(target), "seed_fv": round(seed),
            "gap": round(gap), "sip": round(sip, -2), "step_up": step_up}


@function_tool
async def graph_find_peer_plans(ctx: RunContextWrapper[PlanContext], age_band: str,
                                income_band: str, goals: list[str], risk: str, k: int = 4) -> list[dict]:
    """Ranked peer plans with recorded outcomes (ON_TRACK, AHEAD, SLIPPED, ABANDONED, REWORKED)."""
    return ctx.context.graph.find_peer_plans(age_band, income_band, goals, risk, k)


@function_tool
async def graph_traverse(ctx: RunContextWrapper[PlanContext], node_id: str, max_depth: int = 2) -> dict:
    """BFS from a node: HOLDS, SATISFIES, ORIGINATED, APPROVED_BY, SIMILAR_TO edges with reasoning."""
    return ctx.context.graph.traverse(node_id, max_depth)


@function_tool
async def check_tax_regime(ctx: RunContextWrapper[PlanContext]) -> dict:
    """Regime, 80C already consumed (EPF, insurance), 80C and 80CCD(1B) headroom."""
    inv = data.INVESTORS[ctx.context.investor_id]
    used = inv["epf_employee_annual"] + inv.get("insurance_80c", 0)
    return {"regime": inv["tax_regime"], "80C_used": used,
            "80C_headroom": max(150_000 - used, 0) if inv["tax_regime"] == "OLD" else 0,
            "80CCD1B_headroom": 50_000 if inv["tax_regime"] == "OLD" else 0}


@function_tool
async def check_eligibility(ctx: RunContextWrapper[PlanContext], product: str) -> dict:
    """Eligibility for REIT/InvIT, direct equity sleeve, AIF/alternatives."""
    return ruleset.eligibility(product, ctx.context)


@function_tool
async def graph_instruments(ctx: RunContextWrapper[PlanContext], category: str,
                            filters: dict | None = None) -> list[dict]:
    """Instrument nodes in a category with quality metrics and the peer plans holding them."""
    return ctx.context.graph.instruments(category, filters or {})


@function_tool
async def graph_fund_quality(ctx: RunContextWrapper[PlanContext], fund_id: str) -> dict:
    """Rolling alpha, tracking error, manager tenure, rating history, open events."""
    return ctx.context.graph.fund_quality(fund_id)


@function_tool
async def record_shortlist(ctx: RunContextWrapper[PlanContext], picks: list[dict]) -> int:
    """Each pick: goal, instrument_id, weight, reasoning, peers[], rules[]."""
    ctx.context.shortlist_raw = picks
    return len(picks)


@function_tool(needs_approval=needs_adviser_signoff)
async def propose_plan(ctx: RunContextWrapper[PlanContext], plan_id: str, monthly_sip: int,
                       lump_sum: int, instruments: int, rules_satisfied: list[str],
                       rules_waived: list[str], adviser: str, summary: str) -> dict:
    """Book the plan. Pauses the run when needs_adviser_signoff(...) is True."""
    ctx.context.audit("BOOKED", summary)
    return {"status": "BOOKED", "plan_id": plan_id, "monthly_sip": monthly_sip,
            "lump_sum": lump_sum, "instruments": instruments, "approved_by": adviser}
