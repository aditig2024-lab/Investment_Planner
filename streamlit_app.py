"""
Goalwright — Streamlit deployment.

    pip install -r requirements.txt
    streamlit run streamlit_app.py

Pages
  Investor app   the consumer product (two demo investors, guided walkthroughs)
  Agent console  how the plan is built: specialist agents over a context graph
  Plan maths     live goal arithmetic from demo/rules.py
"""
from __future__ import annotations

import pathlib
import sys

import streamlit as st
import streamlit.components.v1 as components

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT / "demo"))
from rules import future_value, sip_for_target, stepup_sip_for_target, SAA  # noqa: E402

st.set_page_config(page_title="Goalwright", page_icon="🎯", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
      .block-container{padding-top:1.2rem;padding-bottom:0;max-width:1400px}
      header[data-testid="stHeader"]{background:transparent}
      iframe{border:1px solid rgba(128,128,128,.25);border-radius:12px}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def read_html(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def inr(n: float) -> str:
    n = float(n)
    if abs(n) >= 1e7:
        return f"₹{n/1e7:.2f} Cr"
    if abs(n) >= 1e5:
        return f"₹{n/1e5:.1f} L"
    return f"₹{n:,.0f}"


with st.sidebar:
    st.markdown("### 🎯 Goalwright")
    st.caption("Agentic goal-based investment planning for Indian investors")
    page = st.radio("View", ["Investor app", "Agent console", "Plan maths", "About"], label_visibility="collapsed")
    st.divider()
    st.caption(
        "Synthetic investors, fictional fund houses. Return, inflation and probability "
        "figures are illustrative projections, not investment advice."
    )

if page == "Investor app":
    st.caption("Sign in as **Priya** (first plan, ready to accept) or **Arjun** (13-month check-up) "
               "and press *Start walkthrough*.")
    components.html(read_html("index.html"), height=1500, scrolling=True)

elif page == "Agent console":
    st.caption("Press **Run agents** to replay the specialist pipeline over the context graph. "
               "Switch scenario for the monitoring review. Architecture and Code tabs inside.")
    components.html(read_html("console.html"), height=2400, scrolling=True)

elif page == "Plan maths":
    st.subheader("Goal arithmetic — the same functions the Goal Planner agent calls")
    st.caption("`demo/rules.py` · future_value · sip_for_target · stepup_sip_for_target · R-SIP-01 ceiling")

    preset = st.selectbox(
        "Start from a demo goal",
        ["Priya · House down-payment (5y)", "Priya · Child's education (12y)", "Priya · Retire at 58 (24y)",
         "Arjun · Aarav's undergraduate abroad (8y)", "Custom"],
    )
    presets = {
        "Priya · House down-payment (5y)": dict(cost=19_50_000, infl=5.0, years=5, existing=6_80_000, exr=8.5, ret=8.5, step=0, surplus=85_000, other=55_167),
        "Priya · Child's education (12y)": dict(cost=25_00_000, infl=8.0, years=12, existing=4_10_000, exr=7.1, ret=11.0, step=10, surplus=85_000, other=62_767),
        "Priya · Retire at 58 (24y)": dict(cost=70_000 * 12 * 25, infl=6.0, years=24, existing=2_72_00_000, exr=0.0, ret=11.0, step=10, surplus=85_000, other=55_767),
        "Arjun · Aarav's undergraduate abroad (8y)": dict(cost=60_00_000, infl=10.0, years=8, existing=30_00_000, exr=10.0, ret=10.0, step=8, surplus=1_30_000, other=58_100),
        "Custom": dict(cost=10_00_000, infl=6.0, years=10, existing=0, exr=0.0, ret=10.0, step=0, surplus=50_000, other=0),
    }
    p = presets[preset]

    c1, c2, c3 = st.columns(3)
    with c1:
        cost = st.number_input("Cost today (₹)", min_value=0, value=int(p["cost"]), step=50_000)
        infl = st.number_input("Goal inflation (% p.a.)", 0.0, 20.0, float(p["infl"]), 0.5)
        years = st.number_input("Years to goal", 1, 40, int(p["years"]))
    with c2:
        existing = st.number_input("Already earmarked (₹)", min_value=0, value=int(p["existing"]), step=50_000)
        exr = st.number_input("Return on earmarked assets (% p.a.)", 0.0, 20.0, float(p["exr"]), 0.5,
                              help="For retirement presets the earmarked figure is already a projected value, so 0%.")
        ret = st.number_input("Blended return on new SIPs (% p.a.)", 0.0, 20.0, float(p["ret"]), 0.5)
    with c3:
        step = st.number_input("Annual SIP step-up (%)", 0, 25, int(p["step"]))
        surplus = st.number_input("Monthly surplus (₹)", min_value=0, value=int(p["surplus"]), step=5_000)
        other = st.number_input("SIPs already committed to other goals (₹/mo)", min_value=0, value=int(p["other"]), step=1_000)

    target = future_value(cost, infl / 100, years)
    seed_fv = future_value(existing, exr / 100, years)
    gap = max(target - seed_fv, 0)
    flat = sip_for_target(gap, ret / 100, int(years * 12)) if gap else 0
    sip = stepup_sip_for_target(gap, ret / 100, int(years), step / 100) if (gap and step) else flat

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Target corpus", inr(target), f"{inr(cost)} today")
    m2.metric("Earmarked assets at goal date", inr(seed_fv))
    m3.metric("Gap to fund", inr(gap))
    m4.metric("Monthly SIP", inr(sip), f"flat would be {inr(flat)}" if step else "flat")

    total = other + sip
    ceiling = 0.9 * surplus
    if surplus:
        share = total / surplus
        if total <= ceiling:
            st.success(f"R-SIP-01 ✓ total SIPs {inr(total)} = {share:.0%} of surplus (ceiling 90% = {inr(ceiling)}).")
        else:
            st.error(f"R-SIP-01 ✗ total SIPs {inr(total)} = {share:.0%} of surplus — above the 90% ceiling ({inr(ceiling)}). "
                     "The plan would use a step-up, extend the horizon, or trim the goal — or the adviser waives the rule.")

    band = "<1y" if years < 1 else "3-5y" if years <= 5 else "10-15y" if years <= 15 else "20y+"
    st.caption(f"Horizon band **{band}** · strategic allocation (equity / debt / gold / REIT) by effective risk: "
               + " · ".join(f"{r}: {'/'.join(str(v) for v in a)}" for (b, r), a in SAA.items() if b == band))

    with st.expander("Show the arithmetic"):
        st.code(
            f"target   = {cost:,.0f} × (1 + {infl/100:.3f})^{years} = {target:,.0f}\n"
            f"seed_fv  = {existing:,.0f} × (1 + {exr/100:.3f})^{years} = {seed_fv:,.0f}\n"
            f"gap      = {gap:,.0f}\n"
            f"sip      = {'stepup_sip_for_target' if step else 'sip_for_target'}(gap, r={ret/100:.3f}, "
            f"{'years=' + str(int(years)) + ', step=' + str(step/100) if step else 'months=' + str(int(years*12))}) = {sip:,.0f}",
            language="text",
        )

else:
    st.subheader("About")
    st.markdown((ROOT / "README.md").read_text(encoding="utf-8"))
