"""
Entry point - deterministic fan-out / fan-in pipeline for a goal-funded plan.

    export OPENAI_API_KEY=sk-...
    pip install -r requirements.txt
    python run_plan.py INV-2026-7731            # build a new plan
    python monitor.py PLN-2026-2201 2027-12-05  # run the monitoring loop

Stage order is a business rule (suitability before selection, selection
before proposal), so Python enforces it; the LLMs do the work inside each
stage.  Stage 2 runs three specialists concurrently with asyncio.gather.
"""
import asyncio, json, sys
from agents import Runner, trace
from agents_def import (profile_analyst, goal_planner, allocation_strategist,
                        suitability_engine, instrument_selector, plan_composer)
from context import PlanContext
from context_graph import build_demo_graph
from rules import fund_plan


async def build_plan(investor_id: str) -> dict:
    ctx = PlanContext(investor_id=investor_id, graph=build_demo_graph())

    with trace(f"goal-plan {investor_id}"):
        # ---- Stage 1: profile + risk reconciliation (sequential) ---------
        profile = await Runner.run(profile_analyst,
                                   "Build the InvestorProfile from KYC, ledger and questionnaire.",
                                   context=ctx)
        ctx.profile = profile.final_output

        # ---- Stage 2: fan-out — three independent specialists -----------
        facts = ctx.profile.model_dump_json()
        goals, alloc, suit = await asyncio.gather(
            Runner.run(goal_planner, facts, context=ctx),
            Runner.run(allocation_strategist, facts, context=ctx),
            Runner.run(suitability_engine, facts, context=ctx),
        )
        ctx.goals, ctx.allocation, ctx.suitability = (
            goals.final_output, alloc.final_output, suit.final_output)

        # ---- Stage 3: fan-in — plain Python, no LLM ----------------------
        ctx.funding = fund_plan(ctx)          # waterfall, ceilings, redirects

        # ---- Stage 4: concrete instruments from the context graph --------
        shortlist = await Runner.run(instrument_selector, ctx.to_json(), context=ctx)
        ctx.shortlist = shortlist.final_output

        # ---- Stage 5: proposal — the only agent allowed to book anything -
        result = await Runner.run(plan_composer, ctx.to_json(), context=ctx)

        # needs_approval paused the run?  Serialise and hand to the adviser.
        if result.interruptions:
            state = result.to_state()
            ctx.audit("PAUSED", "awaiting adviser sign-off on propose_plan")
            return {"status": "AWAITING_ADVISER", "state": state.to_json(),
                    "proposal": ctx.proposal.model_dump()}

        ctx.graph.write_back(ctx)             # new precedent, with reasoning
        return {"status": "BOOKED", "plan": result.final_output.model_dump()}


async def resume(state_json: str, approve: bool, note: str = "") -> dict:
    """Called by the adviser console hours later."""
    from agents import RunState
    ctx = PlanContext.from_state(state_json)
    state = RunState.from_json(plan_composer, state_json)
    for item in state.interruptions:
        state.approve(item) if approve else state.reject(item, rejection_message=note)
    result = await Runner.run(plan_composer, state, context=ctx)
    if approve:
        ctx.graph.write_back(ctx, approver=note or "adviser")
    return result.final_output.model_dump()


if __name__ == "__main__":
    out = asyncio.run(build_plan(sys.argv[1] if len(sys.argv) > 1 else "INV-2026-7731"))
    print(json.dumps(out, indent=2, default=str))
