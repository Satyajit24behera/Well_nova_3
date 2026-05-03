"""WellNOVA 3.0 — Intelligent Chronic Disease Management Demo.

Entry point for Streamlit Community Cloud deployment.
"""
from __future__ import annotations

import streamlit as st

# ---- Page config (must be first Streamlit call) ----
st.set_page_config(
    page_title="WellNOVA 3.0 — Intelligent Chronic Disease Management",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Google Fonts ----
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700;800&family=IBM+Plex+Sans:wght@400;600&family=JetBrains+Mono&display=swap" rel="stylesheet">
    """,
    unsafe_allow_html=True,
)

# ---- Local imports (after page config) ----
from modules.utils import inject_css, gemini_available
from modules.risk_engine import run_module1
from modules.diet_engine import run_module2
from modules.exercise_engine import run_module3
from modules.pdf_export import build_pdf
from ui.hero import render_hero
from ui.intake_form import render_intake_form
from ui.risk_dashboard import render_risk_dashboard
from ui.meal_plan import render_meal_plan
from ui.exercise_plan import render_exercise_plan

inject_css()

# ---- Session state initialisation ----
_defaults = {
    "step": 1,
    "show_form": False,
    "vitals": {},
    "symptoms": "",
    "preferences": {},
    "patient_state_vector": None,
    "risk_scores": None,
    "meal_plan": None,
    "exercise_plan": None,
    "analysis_complete": False,
    "trigger_analysis": False,
}
for key, val in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ---- Sidebar ----
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:12px 0">
            <div style="font-size:32px">🩺</div>
            <div style="font-size:20px;font-weight:800;background:linear-gradient(135deg,#0ea5e9,#6366f1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent">WellNOVA 3.0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("About WellNOVA", expanded=False):
        st.markdown(
            "WellNOVA 3.0 is an AI-powered chronic disease management research prototype "
            "developed at IIT Kharagpur. It integrates diagnostic risk scoring, personalised "
            "diet planning, and condition-aware exercise scheduling into a single pipeline."
        )
    st.markdown("---")
    st.markdown(
        """
        **Project:** MTP-II, Spring 2025-26
        **Student:** Satyajit Behera (21AG3EP15)
        **Supervisor:** Dr. Ram Babu Roy
        **Institute:** IIT Kharagpur
        """
    )
    st.markdown("---")
    if gemini_available():
        st.success("Gemini API: Connected ✅")
    else:
        st.warning(
            "Gemini API key not found. The app will run with deterministic mock outputs. "
            "Add `GEMINI_API_KEY` to Streamlit secrets to enable AI generation."
        )
    st.markdown("---")
    st.caption(
        "⚠️ This tool is for academic demonstration purposes only "
        "and does not constitute medical advice."
    )


# ---- Analysis trigger ----
if st.session_state.trigger_analysis:
    st.session_state.trigger_analysis = False

    vitals = st.session_state.vitals
    symptoms = st.session_state.symptoms
    preferences = st.session_state.preferences

    # Validate required vitals
    required_fields = ["age", "height_cm", "weight_kg", "fbg", "hba1c", "sbp", "dbp",
                       "cholesterol", "ldl", "hdl", "creatinine", "resting_hr"]
    missing = [f for f in required_fields if not vitals.get(f)]
    if missing:
        st.error(f"Please complete all vitals before analysing. Missing: {', '.join(missing)}")
    else:
        with st.spinner("🧠 Analysing health vitals with Neural Diagnostic Core..."):
            risk_payload = run_module1(vitals, symptoms, preferences)
            st.session_state.risk_scores = risk_payload

        with st.spinner("🥗 Generating your personalised 7-day meal plan..."):
            psv = risk_payload["psv"]
            meal_plan = run_module2(psv)
            st.session_state.meal_plan = meal_plan
            st.session_state.patient_state_vector = psv

        with st.spinner("🏃 Building your condition-safe exercise schedule..."):
            exercise_plan = run_module3(psv)
            st.session_state.exercise_plan = exercise_plan

        st.session_state.analysis_complete = True
        st.success("✅ Analysis complete! Scroll down to view your personalised health report.")


# ---- Main content ----
if not st.session_state.analysis_complete:
    render_hero()

    if st.session_state.show_form or st.session_state.step > 1:
        st.markdown("---")
        render_intake_form()
    else:
        # Show the intake form directly below hero as well on first load
        st.markdown("---")
        render_intake_form()

else:
    # Results view
    st.markdown(
        """
        <div style="text-align:center;padding:16px 0 8px 0">
            <span style="font-size:32px;font-weight:800;background:linear-gradient(135deg,#0ea5e9,#6366f1);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent">
                WellNOVA 3.0 — Your Health Report
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_reset, col_pdf = st.columns([3, 1])
    with col_reset:
        if st.button("← New Assessment", use_container_width=False):
            for key in ["analysis_complete", "risk_scores", "meal_plan", "exercise_plan",
                        "patient_state_vector", "vitals", "symptoms", "preferences"]:
                st.session_state[key] = _defaults.get(key)
            st.session_state.step = 1
            st.rerun()

    with col_pdf:
        # PDF export
        try:
            pdf_bytes = build_pdf(
                psv=st.session_state.patient_state_vector or {},
                risk_payload=st.session_state.risk_scores or {},
                meal_plan=st.session_state.meal_plan or {},
                exercise_plan=st.session_state.exercise_plan or {},
            )
            st.download_button(
                "📄 Download Full Health Report (PDF)",
                data=pdf_bytes,
                file_name="WellNOVA_Health_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"PDF generation failed: {exc}")

    st.markdown("---")
    render_risk_dashboard(st.session_state.risk_scores or {})

    st.markdown("---")
    render_meal_plan(st.session_state.meal_plan or {})

    st.markdown("---")
    render_exercise_plan(st.session_state.exercise_plan or {})


# ---- Footer ----
st.markdown(
    """
    <hr style="border-color:#334155;margin-top:40px">
    <div style="text-align:center;color:#475569;font-size:12px;padding:12px 0 24px 0">
        WellNOVA 3.0 — Research Demo &nbsp;|&nbsp; IIT Kharagpur &nbsp;|&nbsp; Spring 2025-26<br>
        Developed by Satyajit Behera (21AG3EP15) &nbsp;|&nbsp; Supervised by Dr. Ram Babu Roy<br>
        Department of Agricultural &amp; Food Engineering and Entrepreneurship &amp; Innovation Engineering<br>
        <span style="color:#f59e0b">⚠️ This tool is for academic demonstration purposes only and does not constitute medical advice.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
