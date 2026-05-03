"""Landing / hero section for WellNOVA 3.0."""
from __future__ import annotations

import streamlit as st


def render_hero() -> None:
    st.markdown(
        """
        <div class="wellnova-hero">
            <h1>WellNOVA 3.0</h1>
            <p class="tagline">Intelligent Chronic Disease Management</p>
            <p class="subtitle">Diagnosis &nbsp;·&nbsp; Diet &nbsp;·&nbsp; Movement</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Animated metric cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Diagnostic Sensitivity</div>
                <div class="metric-value">91.5%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Diet Clinical CCR</div>
                <div class="metric-value">96.6%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Exercise Safety Rate</div>
                <div class="metric-value">93.2%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Module descriptions
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            """
            <div class="module-card">
                <div class="module-icon">🩺</div>
                <h3>Diagnosis</h3>
                <p>Rule-based + LLM-powered risk scoring for Type 2 Diabetes, Hypertension, and CVD.
                ICD-11 code prediction with SHAP-style biomarker attribution.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            """
            <div class="module-card">
                <div class="module-icon">🥗</div>
                <h3>Diet</h3>
                <p>7-day personalised meal plan generated against a Structured Dietary Protocol (SDP)
                with per-meal macro tracking and cuisine-aware generation.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            """
            <div class="module-card">
                <div class="module-icon">🏃</div>
                <h3>Exercise</h3>
                <p>Condition-adapted weekly exercise schedule with MET-based intensity caps,
                contraindication checks, and low-energy day modifications.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tech badges
    st.markdown(
        """
        <div style="text-align:center; color:#64748b; font-size:13px; margin-bottom:8px;">
            <span style="background:#1e293b;border:1px solid #334155;padding:4px 12px;border-radius:999px;margin:4px;">Python</span>
            <span style="background:#1e293b;border:1px solid #334155;padding:4px 12px;border-radius:999px;margin:4px;">Streamlit</span>
            <span style="background:#1e293b;border:1px solid #334155;padding:4px 12px;border-radius:999px;margin:4px;">Gemini API</span>
            <span style="background:#1e293b;border:1px solid #334155;padding:4px 12px;border-radius:999px;margin:4px;">XGBoost</span>
            <span style="background:#1e293b;border:1px solid #334155;padding:4px 12px;border-radius:999px;margin:4px;">MCN-BERT</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn = st.columns([1, 2, 1])[1]
    with col_btn:
        if st.button("🚀 Start Your Assessment", use_container_width=True):
            st.session_state.show_form = True
            st.rerun()
