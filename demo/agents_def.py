"""
Agent definitions.

    Profile & Risk Analyst
        │  InvestorProfile
        ▼
   ┌────────────── asyncio.gather ──────────────┐
   Goal Planner   Allocation Strategist   Suitability & Rules
   GoalPlan       AllocationPlan          SuitabilityResult
   └────────────────────┬───────────────────────┘
                        ▼  fund_plan()  (plain Python)
                 Instrument Selector      → Shortlist
                        ▼
                 Plan Composer            → propose_plan(needs_approval)
"""
from agents import Agent, ModelSettings
from schemas import (InvestorProfile, GoalPlan, AllocationPlan, SuitabilityResult,
                     Shortlist, PlanProposal)
import tools as T

profile_analyst = Agent[PlanContext](
    name="Profile & Risk Analyst",
    model="gpt-5-nano",
    instructions="""Assemble the InvestorProfile. Pull KYC and ledger facts, the
validated risk questionnaire and 36 months of observed behaviour. Effective
risk is the LOWER of stated and observed (rule R-RISK-03) — explain why.""",
    tools=[T.fetch_kyc_and_profile, T.fetch_risk_questionnaire,
           T.observe_behaviour, T.record_profile],
    output_type=InvestorProfile,
)

goal_planner = Agent[PlanContext](
    name="Goal Planner",
    model="o4-mini",
    instructions="""For each goal compute: target corpus (today's cost grown at the
goal-specific inflation), horizon in months, value of existing assets earmarked
to it, the gap, and the SIP that closes the gap. Prefer a 10% annual step-up
when a flat SIP would exceed 60% of surplus. Use compute_goal_corpus only —
never do the arithmetic in prose.""",
    tools=[T.compute_goal_corpus, T.record_goal_plan],
    output_type=GoalPlan,
)

allocation_strategist = Agent[PlanContext](
    name="Allocation Strategist",
    model="o4-mini",
    instructions="""Set a strategic asset allocation per goal from the horizon x
effective-risk matrix, then benchmark it against peer plans in the context
graph: who looked like this investor, what did they hold, how did it turn out.
Cite the peer plan ids you relied on and any rule whose ORIGINATED edge you
traversed.""",
    tools=[T.graph_find_peer_plans, T.graph_traverse, T.record_allocation],
    output_type=AllocationPlan,
)

suitability_engine = Agent[PlanContext](
    name="Suitability & Rules",
    model="gpt-5-nano",
    instructions="""Run the suitability checks: tax regime and 80C / 80CCD(1B)
headroom, product eligibility (REIT/InvIT, direct equity, AIF), SIP ceiling,
horizon-equity cap. Return every rule with PASS / FAIL / NA and the fact that
decided it.""",
    tools=[T.check_tax_regime, T.check_eligibility, T.record_suitability],
    output_type=SuitabilityResult,
)

instrument_selector = Agent[PlanContext](
    name="Instrument Selector",
    model="o4-mini",
    instructions="""Turn each goal's allocation into concrete instruments from the
context graph: index funds by tracking error and expense ratio, active funds
by rolling alpha and manager tenure, debt by credit quality and duration, ELSS
only to fill 80C headroom, NPS for 80CCD(1B), gold via SGB if a tranche is
open else gold ETF, REIT only if eligible. For every pick record: reasoning,
the peer plans that hold it and how they fared, the rules it satisfies.""",
    tools=[T.graph_instruments, T.graph_fund_quality, T.record_shortlist],
    output_type=Shortlist,
)

plan_composer = Agent[PlanContext](
    name="Plan Composer",
    model="gpt-5-nano",
    model_settings=ModelSettings(tool_choice="required"),
    instructions="""Compose the plan and call propose_plan exactly once. Name the
adviser of record. If the run resumes with a rejection, read the adviser note
and draft v2 with the requested changes.""",
    tools=[T.propose_plan],
    output_type=PlanProposal,
)
