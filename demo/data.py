"""
Synthetic data for the demo.  Fictional investor and fund houses.

INV-2026-7731  Priya Raghavan, 34, Bengaluru — four goals, old tax regime,
               stated risk MOD_AGG but paused SIPs in the 2025 drawdown.
"""
INVESTORS = {
    "INV-2026-7731": {
        "name": "Priya Raghavan", "age": 34, "city": "Bengaluru",
        "income_annual": 3_200_000, "take_home_monthly": 200_000,
        "expenses_monthly": 115_000, "essential_monthly": 85_000,
        "monthly_surplus": 85_000, "tax_regime": "OLD",
        "dependants": [{"rel": "child", "age": 6}, {"rel": "mother", "age": 63, "partial": True}],
        "assets": {"EPF": 1_420_000, "PPF": 410_000, "equity_mf": 680_000, "savings": 350_000},
        "liabilities": {"car_loan": {"outstanding": 320_000, "emi": 19_500, "months_left": 18}},
        "epf_employee_annual": 86_400, "epf_monthly_total": 14_400,
        "goals": [
            {"id": "emergency",  "label": "Emergency fund",       "when": "now",  "basis": "6 × essential"},
            {"id": "house",      "label": "House down-payment",   "years": 5,     "cost_today": 1_950_000, "inflation": 0.05},
            {"id": "education",  "label": "Child's education",    "years": 12,    "cost_today": 2_500_000, "inflation": 0.08},
            {"id": "retirement", "label": "Retire at 58",         "years": 24,    "expense_today_m": 70_000, "inflation": 0.06, "multiple": 25},
        ],
    },
}

QUESTIONNAIRE = {"INV-2026-7731": {"score": 68, "band": "MOD_AGG", "items": 12, "validated": "2026-09-30"}}

def behaviour_from_ledger(investor_id, months):
    return {"score": 54, "band": "MODERATE",
            "evidence": ["SIPs paused Mar–Apr 2025 during −14% drawdown",
                         "₹1.2L redeemed within 3% of the trough",
                         "resumed after 2 months at a lower amount"]}

# ---- context graph seed -------------------------------------------------------
NODES = {
    "INV-2026-7731": dict(type="Investor"),
    "PLN-2021-0077": dict(type="Plan", outcome="AHEAD", age_band="30-35", income_band="25-40L", risk="MODERATE",
                          goals=["retirement", "education"], summary="10% step-up, index core + NPS active choice; 1.3y ahead"),
    "PLN-2023-0412": dict(type="Plan", outcome="ON_TRACK", age_band="30-35", income_band="25-40L", risk="MODERATE",
                          goals=["house", "education", "retirement"], summary="house 5y at 40/60 with glide; on track"),
    "PLN-2024-0931": dict(type="Plan", outcome="SLIPPED", age_band="30-35", income_band="25-40L", risk="MOD_AGG",
                          goals=["house"], summary="house 4y funded 65% equity; sold −18% in 2025; goal slipped 2y"),
    "PLN-2022-0188": dict(type="Plan", outcome="ABANDONED", age_band="35-40", income_band="25-40L", risk="MODERATE",
                          goals=["retirement"], summary="flat SIP at 100% of surplus; abandoned after 7 months"),
    "PLN-2025-1204": dict(type="Plan", outcome="REWORKED", age_band="30-35", income_band="25-40L", risk="MODERATE",
                          goals=["retirement", "education"], summary="ELSS recommended under NEW regime; no 80C benefit; reworked"),
    "FND:Arbor Nifty 50 Index":    dict(type="Instrument", category="large-cap index", expense_ratio=0.10, tracking_error=0.07, aum_cr=18_400, rating=None),
    "FND:Arbor Midcap 150 Index":  dict(type="Instrument", category="midcap index",    expense_ratio=0.20, tracking_error=0.12, aum_cr=4_100),
    "FND:Kestrel Flexi Cap":       dict(type="Instrument", category="flexi-cap active", expense_ratio=0.68, rolling_alpha_5y=1.8, manager_tenure_y=6, rating=4, aum_cr=22_900, open_events=[]),
    "FND:Kestrel Tax Saver":       dict(type="Instrument", category="ELSS", expense_ratio=0.72, rolling_alpha_5y=1.1, lock_in_y=3),
    "FND:Sarovar Short Duration":  dict(type="Instrument", category="debt short-duration", aaa_sov_pct=92, mod_duration_y=2.1, ytm=7.3),
    "FND:Arbor Liquid":            dict(type="Instrument", category="liquid", aaa_sov_pct=100, mod_duration_y=0.1),
    "ETF:Sarovar Gold ETF":        dict(type="Instrument", category="gold", expense_ratio=0.50, tracking_error=0.3),
    "REIT:Meridian Office REIT":   dict(type="Instrument", category="REIT", dist_yield=6.4, occupancy=0.89),
    "NPS:Tier-I active E75":       dict(type="Instrument", category="NPS", section="80CCD(1B)"),
    "RULE:R-HZN-01": dict(type="Rule"), "RULE:R-SIP-01": dict(type="Rule"), "RULE:R-TAX-01": dict(type="Rule"),
    "RULE:R-RISK-03": dict(type="Rule"), "RULE:R-FQ-02": dict(type="Rule"),
    "ADV:R. Menon": dict(type="Adviser", reg="INA000012345"),
}

EDGES = [
    ("PLN-2021-0077", "FND:Arbor Nifty 50 Index", "HOLDS", dict(weight=0.45, reasoning="low-cost core for 24y horizon")),
    ("PLN-2021-0077", "NPS:Tier-I active E75", "HOLDS", dict(weight=0.10, reasoning="80CCD(1B) + lock-in suits retirement")),
    ("PLN-2021-0077", "RULE:R-SIP-01", "SATISFIES", dict(fact="SIP 62% of surplus with 10% step-up")),
    ("PLN-2023-0412", "FND:Arbor Nifty 50 Index", "HOLDS", dict(weight=0.40, reasoning="house sleeve equity capped at 40%")),
    ("PLN-2023-0412", "FND:Sarovar Short Duration", "HOLDS", dict(weight=0.45, reasoning="5y goal debt core, AAA/sovereign")),
    ("PLN-2023-0412", "RULE:R-HZN-01", "SATISFIES", dict(fact="equity 40% ≤ cap")),
    ("PLN-2024-0931", "FND:Kestrel Flexi Cap", "HOLDS", dict(weight=0.65, reasoning="investor requested growth tilt")),
    ("PLN-2024-0931", "RULE:R-HZN-01", "ORIGINATED", dict(lesson="65% equity on a 4y goal forced a sale at −18%")),
    ("PLN-2022-0188", "FND:Kestrel Flexi Cap", "HOLDS", dict(weight=0.70)),
    ("PLN-2022-0188", "RULE:R-SIP-01", "ORIGINATED", dict(lesson="SIP at 100% of surplus is abandoned at the first shock")),
    ("PLN-2025-1204", "FND:Kestrel Tax Saver", "HOLDS", dict(weight=0.20)),
    ("PLN-2025-1204", "RULE:R-TAX-01", "ORIGINATED", dict(lesson="ELSS lock-in bought nothing under the new regime")),
    ("PLN-2023-0412", "PLN-2024-0931", "SIMILAR_TO", dict(score=0.81)),
    *[(p, "ADV:R. Menon", "APPROVED_BY", dict()) for p in
      ("PLN-2021-0077", "PLN-2023-0412", "PLN-2024-0931", "PLN-2022-0188")],
]
