# Goalwright — agentic goal-based investment planning (OpenAI Agents SDK demo)

An investor arrives with a profile and a set of goals. A team of specialist
agents produces a **goal-funded plan** — for each goal a target corpus, horizon,
strategic asset allocation, SIP / lump-sum schedule and a shortlist of concrete
instruments — then monitors it. Every recommendation carries its reasoning, the
peer plans it was benchmarked against, the rules it satisfied and the adviser
who approved it, all stored as edges in a **context graph**.

## Pipeline

    Profile & Risk Analyst                        Stage 1  sequential
      └─ gather( Goal Planner ‖ Allocation Strategist ‖ Suitability & Rules )
         └─ fund_plan()                           Stage 3  plain Python
            └─ Instrument Selector                Stage 4  reads the graph
               └─ Plan Composer → propose_plan()  Stage 5  needs_approval

    monitor.py: Portfolio Monitor → gather( Drift ‖ Goal Tracker ‖ Fund Quality )
                → triage() → Review Proposer → propose_review()  needs_approval

## Run

    pip install -r requirements.txt
    export OPENAI_API_KEY=sk-...
    python run_plan.py INV-2026-7731
    python monitor.py PLN-2026-2201 2027-12-05

## Human-in-the-loop

`propose_plan` and `propose_review` are decorated with
`@function_tool(needs_approval=needs_adviser_signoff)`. A new plan, any
rebalance, any SIP change of ₹10,000/month or more, or any rule waiver pauses
the run; `result.to_state()` is handed to the adviser console and resumed with
`state.approve()` / `state.reject()`.

## Rules with provenance

Rules carry an `ORIGINATED` edge back to the plan that taught them:

| rule      | text                                             | origin        |
|-----------|--------------------------------------------------|---------------|
| R-HZN-01  | equity ≤ 40% for 3–5y goals, glide from T-2y      | PLN-2024-0931 |
| R-SIP-01  | SIP ≤ 90% of surplus, prefer step-up              | PLN-2022-0188 |
| R-TAX-01  | ELSS only under old regime, only to 80C headroom  | PLN-2025-1204 |

Synthetic data. Fictional fund houses. Return and inflation assumptions are
illustrative and not investment advice.
