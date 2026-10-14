"""
Monitoring loop — same pipeline shape, run on a schedule per active plan.

Triggers: SIP miss, drift beyond band, goal slippage, life event,
fund-quality change.  The Review Proposer may only PROPOSE; propose_review is
gated by the same needs_adviser_signoff rule as propose_plan.
"""
import asyncio, sys
from agents import Agent, Runner, function_tool, RunContextWrapper, trace
from context import PlanContext
from rules import needs_adviser_signoff

SEVERITY = {"SIP_MISS": 2, "DRIFT_BREACH": 2, "GOAL_SLIP": 3, "MANAGER_CHANGE": 1,
            "LIFE_EVENT": 1, "ASSUMPTION_BREACH": 2}
REVIEW_THRESHOLD = 5


def triage(ctx: PlanContext) -> dict:
    """Stage-3 fan-in. Pure arithmetic over the three reports."""
    score = sum(SEVERITY[s.kind] for s in ctx.signals) \
          + sum(3 for g in ctx.tracking.goals if g.p_success_delta <= -0.10) \
          + sum(2 for d in ctx.drift.sleeves if d.breach)
    return {"score": score, "review_required": score >= REVIEW_THRESHOLD,
            "drivers": sorted({s.kind for s in ctx.signals})}


@function_tool(needs_approval=needs_adviser_signoff)
async def propose_review(ctx: RunContextWrapper[PlanContext], review_id: str, actions: list[dict],
                         sip_delta: int, rebalances: list[dict], rules: list[str],
                         precedents: list[str], adviser: str, summary: str) -> dict:
    """Book the review. Any rebalance or SIP change ≥ ₹10k/mo pauses for the adviser."""
    ctx.context.audit("REVIEW_BOOKED", summary)
    return {"status": "BOOKED", "review_id": review_id, "actions": len(actions)}


portfolio_monitor   = Agent[PlanContext](name="Portfolio Monitor", model="gpt-5-nano",
    instructions="Ingest SIP ledger, NAV feed, HR/life events, fund research feed, macro indices. Record every signal with its evidence.",
    tools=["ingest_signals", "record_signals"])
drift_analyst       = Agent[PlanContext](name="Drift Analyst", model="gpt-5-nano",
    instructions="Compare each goal sleeve to its SAA band (R-DRIFT-01). Propose tax-aware rebalances (R-TAX-04: harvest within the ₹1.25L LTCG exemption).",
    tools=["compute_drift", "rebalance_proposal"])
goal_tracker        = Agent[PlanContext](name="Goal Tracker", model="o4-mini",
    instructions="Re-project every goal with current corpus, revised assumptions and new surplus. Report P(success) and its change since booking.",
    tools=["project_goal"])
fund_quality_review = Agent[PlanContext](name="Fund Quality Reviewer", model="gpt-5-nano",
    instructions="Check open events on every held fund in the context graph; apply R-FQ-02; cite how peers handled the same event.",
    tools=["graph_fund_quality", "graph_find_precedents"])
review_proposer     = Agent[PlanContext](name="Review Proposer", model="gpt-5-nano",
    instructions="Compose one propose_review call from the three reports and the triage score. Every action cites a rule and a precedent.",
    tools=[propose_review])


async def monitor_plan(plan_id: str, as_of: str) -> dict:
    ctx = PlanContext.load(plan_id, as_of=as_of)
    with trace(f"plan-review {plan_id} {as_of}"):
        sig = await Runner.run(portfolio_monitor, f"as_of={as_of}", context=ctx)
        ctx.signals = sig.final_output.signals
        drift, track, fq = await asyncio.gather(
            Runner.run(drift_analyst, ctx.to_json(), context=ctx),
            Runner.run(goal_tracker, ctx.to_json(), context=ctx),
            Runner.run(fund_quality_review, ctx.to_json(), context=ctx))
        ctx.drift, ctx.tracking, ctx.fund_quality = drift.final_output, track.final_output, fq.final_output
        ctx.triage = triage(ctx)
        if not ctx.triage["review_required"]:
            return {"status": "NO_ACTION", "triage": ctx.triage}
        result = await Runner.run(review_proposer, ctx.to_json(), context=ctx)
        if result.interruptions:
            return {"status": "AWAITING_ADVISER", "state": result.to_state().to_json()}
        ctx.graph.write_back_review(ctx)
        return {"status": "BOOKED", "review": result.final_output.model_dump()}


if __name__ == "__main__":
    print(asyncio.run(monitor_plan(sys.argv[1], sys.argv[2])))
