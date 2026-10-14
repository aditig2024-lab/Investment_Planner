"""
Context Graph: institutional memory of plans, instruments, rules and outcomes.

Nodes : Investor, Plan, Goal, Instrument, Rule, Adviser, Review, Signal
Edges : PLANNED_FOR, HAS_GOAL, HOLDS(weight, reasoning), SATISFIES(rule, fact),
        ORIGINATED(rule <- plan that taught it), APPROVED_BY(adviser, note),
        SIMILAR_TO(score), REVIEWS, TRIGGERED_BY

In-memory networkx for the demo; the same queries run as Cypher / Gremlin.
"""
from collections import deque
import networkx as nx
import data


class ContextGraph:
    def __init__(self):
        self.g = nx.MultiDiGraph()

    # ---- writes ---------------------------------------------------------
    def add(self, nid, **attrs):
        self.g.add_node(nid, **attrs)

    def link(self, a, b, rel, **attrs):
        self.g.add_edge(a, b, key=rel, rel=rel, **attrs)

    def write_back(self, ctx, approver="R. Menon"):
        pid = ctx.proposal.plan_id
        self.add(pid, type="Plan", outcome="ACTIVE", version=ctx.plan_version,
                 monthly_sip=ctx.funding["total"], as_of=ctx.as_of)
        self.link(pid, ctx.investor_id, "PLANNED_FOR")
        for pick in ctx.shortlist.picks:
            self.link(pid, pick.instrument_id, "HOLDS", weight=pick.weight,
                      goal=pick.goal, reasoning=pick.reasoning)
        for r in ctx.suitability.passed:
            self.link(pid, f"RULE:{r.id}", "SATISFIES", fact=r.fact)
        for peer in ctx.allocation.peers_relied_on:
            self.link(pid, peer, "SIMILAR_TO", score=ctx.allocation.peer_scores[peer])
        self.link(pid, f"ADV:{approver}", "APPROVED_BY", note=ctx.adviser_note)

    # ---- reads ----------------------------------------------------------
    def find_peer_plans(self, age_band, income_band, goals, risk, k=4):
        scored = []
        for n, a in self.g.nodes(data=True):
            if a.get("type") != "Plan" or a.get("outcome") == "ACTIVE":
                continue
            s = 0
            s += 3 if a["age_band"] == age_band else 0
            s += 2 if a["income_band"] == income_band else 0
            s += 2 * len(set(a["goals"]) & set(goals))
            s += 2 if a["risk"] == risk else 0
            scored.append({"plan": n, "relevance": s, "outcome": a["outcome"],
                           "summary": a["summary"]})
        return sorted(scored, key=lambda x: -x["relevance"])[:k]

    def traverse(self, start, max_depth=2):
        seen, out, q = {start}, [], deque([(start, 0)])
        while q:
            n, d = q.popleft()
            if d == max_depth:
                continue
            for _, m, e in self.g.out_edges(n, data=True):
                out.append({"from": n, "rel": e["rel"], "to": m,
                            **{k: v for k, v in e.items() if k != "rel"}})
                if m not in seen:
                    seen.add(m); q.append((m, d + 1))
            for m, _, e in self.g.in_edges(n, data=True):      # ORIGINATED points at rules
                if e["rel"] in ("ORIGINATED", "HOLDS", "REVIEWS"):
                    out.append({"from": m, "rel": e["rel"], "to": n})
                    if m not in seen:
                        seen.add(m); q.append((m, d + 1))
        return {"start": start, "nodes": len(seen), "edges": out}

    def instruments(self, category, filters):
        res = []
        for n, a in self.g.nodes(data=True):
            if a.get("type") != "Instrument" or a.get("category") != category:
                continue
            if all(a.get(k, 0) <= v if k.startswith("max_") else a.get(k, 0) >= v
                   for k, v in filters.items()):
                holders = [(p, self.g.nodes[p]["outcome"]) for p, _, e in self.g.in_edges(n, data=True)
                           if e["rel"] == "HOLDS"]
                res.append({"id": n, **a, "held_by": holders})
        return res

    def fund_quality(self, fund_id):
        a = self.g.nodes[fund_id]
        return {k: a.get(k) for k in ("rolling_alpha_5y", "tracking_error", "expense_ratio",
                                      "manager_tenure_y", "rating", "aum_cr", "open_events")}


def build_demo_graph() -> ContextGraph:
    cg = ContextGraph()
    for nid, attrs in data.NODES.items():
        cg.add(nid, **attrs)
    for a, b, rel, attrs in data.EDGES:
        cg.link(a, b, rel, **attrs)
    return cg
