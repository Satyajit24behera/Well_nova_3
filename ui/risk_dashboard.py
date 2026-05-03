"""Module 1 output — Health Risk Dashboard UI."""
from __future__ import annotations

import json
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from modules.utils import gemini_available, severity_tier


def _risk_score_card(label: str, score: int, tier: str, interpretation: str) -> str:
    _, cls = severity_tier(score)
    return f"""
    <div class="risk-score-card {cls}">
        <div class="score-label">{label}</div>
        <div class="score-value">{score}<span style="font-size:22px;font-weight:400">/100</span></div>
        <div style="margin-top:8px">
            <span class="risk-badge risk-{cls}">{tier}</span>
        </div>
        <div style="color:#94a3b8;font-size:12px;margin-top:10px;text-align:left;line-height:1.5">
            {interpretation}
        </div>
    </div>
    """


def _shap_chart(key_risk_factors: list[dict[str, Any]]) -> None:
    if not key_risk_factors:
        return

    factors = key_risk_factors[:8]
    labels = [f"{f.get('biomarker', '?')} ({f.get('value', '')} {f.get('unit', '')})" for f in factors]
    # Map impact to numeric magnitude
    impact_map = {"high": 0.9, "moderate": 0.55, "low": 0.25}
    values = []
    colors = []
    for f in factors:
        mag = impact_map.get(str(f.get("impact", "moderate")).lower(), 0.5)
        direction = str(f.get("direction", "positive")).lower()
        if direction == "negative":
            values.append(-mag)
            colors.append("#22c55e")
        else:
            values.append(mag)
            colors.append("#ef4444")

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{'+' if v > 0 else ''}{v:.2f}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title="SHAP-Style Biomarker Contribution",
        paper_bgcolor="#1e293b",
        plot_bgcolor="#1e293b",
        font=dict(color="#f1f5f9", size=12),
        xaxis=dict(
            title="Feature Impact",
            range=[-1.2, 1.2],
            gridcolor="#334155",
            zerolinecolor="#475569",
        ),
        yaxis=dict(gridcolor="#334155", automargin=True),
        margin=dict(l=20, r=40, t=40, b=20),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_risk_dashboard(risk_payload: dict[str, Any]) -> None:
    risk = risk_payload.get("risk_data", {})
    clinical = risk_payload.get("clinical", {})
    tiers = risk.get("tiers", {})
    interp = clinical.get("interpretations", {})
    source = risk_payload.get("source", "mock")
    fallback_reason = clinical.get("_fallback_reason") if isinstance(clinical, dict) else None

    if source == "mock":
        if gemini_available() and fallback_reason:
            st.warning(
                "Gemini call failed for risk interpretation; falling back to a deterministic "
                f"local result. Details: {fallback_reason}",
                icon="⚠️",
            )
        elif not gemini_available():
            st.info(
                "Risk analysis generated locally (no Gemini API key configured). "
                "Add `GEMINI_API_KEY` to Streamlit secrets for AI-powered ICD mapping "
                "and clinical interpretation.",
                icon="ℹ️",
            )

    st.markdown("## 🩺 Health Risk Dashboard")

    # Compliance / overall severity
    overall_tier = clinical.get("severity_tier", "Moderate")
    _, cls = severity_tier(
        max(risk.get("diabetes", 0), risk.get("hypertension", 0), risk.get("cvd", 0))
    )
    st.markdown(
        f'<div class="compliance-banner">Overall Severity — '
        f'<span class="risk-badge risk-{cls}">{overall_tier}</span></div>',
        unsafe_allow_html=True,
    )

    # Three risk score cards
    c1, c2, c3 = st.columns(3)
    for col, (label, key) in zip(
        [c1, c2, c3],
        [
            ("Type 2 Diabetes Risk", "diabetes"),
            ("Hypertension Risk", "hypertension"),
            ("Cardiovascular Disease Risk", "cvd"),
        ],
    ):
        score = risk.get(key, 0)
        tier = tiers.get(key, "Low")
        interpretation = interp.get(key, "—")
        with col:
            st.markdown(
                _risk_score_card(label, score, tier, interpretation),
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ICD codes + SHAP chart
    left, right = st.columns([1, 1])

    with left:
        st.markdown("### ICD-11 Predictions")
        icd_codes = clinical.get("icd_codes", []) or []
        if icd_codes:
            for c in icd_codes[:3]:
                conf = c.get("confidence", 0)
                st.markdown(
                    f"""
                    <div class="icd-row">
                        <span>
                            <span class="icd-code">{c.get('code', '')}</span>
                            &nbsp; {c.get('description', '')}
                        </span>
                        <span class="icd-conf">{conf:.1f}%</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No ICD codes available.")

    with right:
        _shap_chart(clinical.get("key_risk_factors", []) or [])

    # Patient State Vector expander
    psv = risk_payload.get("psv", {})
    if psv:
        with st.expander("🔍 Patient State Vector (PSV) — for technical evaluators"):
            st.code(json.dumps(psv, indent=2), language="json")

    # Demo limitations
    with st.expander("ℹ️ Demo Limitations"):
        st.markdown(
            """
- Risk scores are computed using a rule-based heuristic for demonstration. The production system uses an XGBoost model trained on NHANES data (AUC > 0.89).
- ICD mapping and clinical interpretation are generated by the Gemini API. In production, Llama-3-Med with FAISS RAG is used.
- PDF lab report parsing is simulated. The production system uses Tesseract OCR + Clinical-T5.
- This demo does not retain any data between sessions.
            """
        )

    st.markdown(
        '<div class="disclaimer-box">⚠️ This tool is for academic demonstration only and does not constitute medical advice. Always consult a qualified healthcare professional.</div>',
        unsafe_allow_html=True,
    )
