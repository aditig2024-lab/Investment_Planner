# Goalwright — agentic goal-based investment planning for Indian investors

An investor arrives with a profile (age, income, dependants, assets and liabilities, monthly surplus, tax regime, risk tolerance from a validated questionnaire **and** from observed behaviour) and a set of goals — retirement at 58, a child's education in 12 years, a house down-payment in 5, an emergency fund now. The system produces a **goal-funded plan**: for each goal a target corpus, a time horizon, a strategic asset allocation, a monthly SIP or lump-sum schedule and a shortlist of concrete instruments (index funds, equity and debt mutual funds by category, ELSS for 80C, PPF/EPF/NPS, fixed deposits and short-duration debt, SGBs or gold ETFs, and — for eligible investors — REITs/InvITs or a small direct-equity sleeve).

Every recommendation carries its **reasoning**, the **peers** it was benchmarked against, the **rules** it satisfied and the **adviser** who approved it. The plan is then monitored: SIP misses, drift beyond bands, goal slippage, life events and fund-quality changes trigger a review proposal — again gated by the adviser, then by the investor.

## Live demos

| Demo | Open it | What it shows |
|---|---|---|
| **Goalwright app** — consumer product | [GitHub Pages](https://aditig2024-lab.github.io/Investment_Planner/) · [HTML preview](https://htmlpreview.github.io/?https://github.com/aditig2024-lab/Investment_Planner/blob/main/index.html) · [Claude artifact](https://claude.ai/artifact/TGgwf6LfeFajEJLMeCARDV) | Sign in as one of two demo investors and take the guided walkthrough: **Priya** (34, Bengaluru — first plan, ready to accept) or **Arjun** (42, Pune — 13-month check-up with an adviser-approved review). Home, My plan, Check-ups, Ask Goalwright, Profile & risk. |
| **Goalwright console** — how the plan is built | [GitHub Pages](https://aditig2024-lab.github.io/Investment_Planner/console.html) · [HTML preview](https://htmlpreview.github.io/?https://github.com/aditig2024-lab/Investment_Planner/blob/main/console.html) · [Claude artifact](https://claude.ai/artifact/UACrw7btp6KyF3HMMQA1Zf) | Replay of the specialist-agent pipeline over a **context graph** of peer plans, instruments, rules and advisers: fan-out / fan-in, precedent traversal, rule provenance, adviser gate, monitoring review. Architecture and runnable code tabs. |

Both pages are single self-contained HTML files — open `index.html` or `console.html` locally and they work offline (fonts and syntax highlighting load from CDNs when online).

> **Making the links work for anyone**
> - **GitHub Pages**: in *Settings → Pages*, set *Source* to *Deploy from a branch*, branch `main`, folder `/ (root)`. The two Pages links above go live within a minute.
> - **HTML preview**: works immediately for a public repository, no setup.
> - **Claude artifacts**: private by default. Open each artifact, use its *Share* menu and choose *Anyone with the link* to make them public.

## How it works

```
Profile & Risk Analyst                              Stage 1  sequential · risk = min(stated, observed)
  └─ asyncio.gather( Goal Planner ‖ Allocation Strategist ‖ Suitability & Rules )
     └─ fund_plan()                                  Stage 3  priority waterfall, plain Python
        └─ Instrument Selector                       Stage 4  reads the context graph
           └─ Plan Composer → propose_plan()         Stage 5  @function_tool(needs_approval=adviser rule)

monitor.py: Portfolio Monitor → gather( Drift Analyst ‖ Goal Tracker ‖ Fund Quality Reviewer )
            → triage() → Review Proposer → propose_review()   needs_approval
```

**Context graph.** Nodes: Investor, Plan, Goal, Instrument, Rule, Adviser, Review, Signal. Edges: `PLANNED_FOR`, `HOLDS (weight, reasoning)`, `SATISFIES (rule, fact)`, `ORIGINATED (rule ← the plan that taught it)`, `APPROVED_BY (adviser, note)`, `SIMILAR_TO`, `REVIEWS`, `TRIGGERED_BY`. Every booked plan is written back as a new precedent.

**Rules with provenance** (a selection):

| rule | text | origin |
|---|---|---|
| R-RISK-03 | effective risk = min(stated, observed) | |
| R-HZN-01 | equity ≤ 40% for 3–5y goals; glide to 0% from T−2y | Peer plan #0931 (slipped) |
| R-SIP-01 | total SIP ≤ 90% of surplus; prefer step-up | Peer plan #0188 (abandoned) |
| R-TAX-01 | ELSS only under old regime, only to 80C headroom | Peer plan #1204 (reworked) |
| R-TAX-03 | new regime: only employer NPS (80CCD(2)) is deductible | |
| R-ELIG-02 | direct-equity sleeve: risk ≥ MOD_AGG and income ≥ ₹25 L, cap 10% | |
| R-FQ-02 | manager change → WATCH 2 quarters, no new money | |

**Human in the loop.** `propose_plan` and `propose_review` are decorated with `@function_tool(needs_approval=needs_adviser_signoff)`. A new plan, any rebalance, any SIP change ≥ ₹10,000/month or any rule waiver pauses the run with `result.interruptions`; `result.to_state()` is handed to the adviser console and resumed with `state.approve()` / `state.reject()`. The consumer then accepts in the app.

## Run the agent pipeline (`demo/`)

```bash
cd demo
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python run_plan.py INV-2026-7731            # build Priya's plan
python monitor.py PLN-2026-2201 2027-12-05  # run a monitoring review
```

| file | purpose |
|---|---|
| `run_plan.py` | deterministic fan-out / fan-in pipeline, adviser gate, resume |
| `agents_def.py` | the six specialist agents and their tools |
| `tools.py` | `@function_tool` definitions over the shared `PlanContext` |
| `rules.py` | FV / SIP / step-up arithmetic, SAA matrix, rules, `fund_plan()`, `needs_adviser_signoff()` |
| `context_graph.py` | graph store: peer-plan ranking, BFS traversal, instrument screens, write-back |
| `monitor.py` | monitoring loop: signals → triage → review proposal |
| `data.py` | synthetic investor and graph seed |

## Repository layout

```
index.html      Goalwright consumer app (two demo investors, guided walkthroughs)
console.html    Goalwright console (agent pipeline + context graph replay, architecture, code)
demo/           runnable OpenAI Agents SDK project
.nojekyll       lets GitHub Pages serve the HTML files as-is
```

---
Synthetic investors, fictional fund houses. Return, inflation and probability figures are illustrative projections, not investment advice.
