"""Helpers for WellNOVA 3.0 demo.

Contains: BMI calc, biomarker reference-range checks, severity-tier mapping,
demo patient profile, the Gemini API wrapper, and a deterministic mock
fallback used when the API key is missing or a call fails.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st


# ---------- Demo patient ----------
DEMO_PATIENT: dict[str, Any] = {
    "symptoms": (
        "I have been feeling unusually thirsty for the past month, "
        "experiencing blurry vision, and feeling fatigued even after a full "
        "night's sleep. I also notice frequent urination, especially at night."
    ),
    "age": 52,
    "sex": "Male",
    "height_cm": 172,
    "weight_kg": 84,
    "fbg": 145,
    "hba1c": 7.8,
    "sbp": 148,
    "dbp": 92,
    "cholesterol": 218,
    "ldl": 142,
    "hdl": 38,
    "creatinine": 1.1,
    "resting_hr": 78,
    "fitness_level": "Beginner",
    "dietary_restrictions": ["Vegetarian"],
    "cuisine_preference": "South Indian",
    "additional_notes": "",
}


# ---------- Reference ranges (WHO / ADA / ACC-AHA) ----------
# Each tuple: (normal_low, normal_high, borderline_low, borderline_high)
# Anything outside borderline range -> abnormal.
REFERENCE_RANGES: dict[str, dict[str, float]] = {
    "fbg":         {"normal_low": 70,  "normal_high": 99,  "borderline_high": 125},
    "hba1c":       {"normal_low": 4.0, "normal_high": 5.6, "borderline_high": 6.4},
    "sbp":         {"normal_low": 90,  "normal_high": 119, "borderline_high": 139},
    "dbp":         {"normal_low": 60,  "normal_high": 79,  "borderline_high": 89},
    "cholesterol": {"normal_low": 100, "normal_high": 199, "borderline_high": 239},
    "ldl":         {"normal_low": 40,  "normal_high": 99,  "borderline_high": 159},
    "hdl":         {"normal_low": 40,  "normal_high": 100, "borderline_low": 39},
    "creatinine":  {"normal_low": 0.6, "normal_high": 1.3, "borderline_high": 2.0},
    "resting_hr":  {"normal_low": 60,  "normal_high": 100, "borderline_high": 110},
    "bmi":         {"normal_low": 18.5,"normal_high": 24.9,"borderline_high": 29.9},
}


def compute_bmi(height_cm: float, weight_kg: float) -> float:
    if not height_cm or height_cm <= 0:
        return 0.0
    h = height_cm / 100.0
    return round(weight_kg / (h * h), 1)


def biomarker_status(name: str, value: float) -> str:
    """Return one of 'normal' | 'borderline' | 'abnormal' for a biomarker."""
    r = REFERENCE_RANGES.get(name)
    if not r:
        return "normal"
    if name == "hdl":
        if value >= r["normal_low"]:
            return "normal"
        if value >= r["borderline_low"]:
            return "borderline"
        return "abnormal"
    if r["normal_low"] <= value <= r["normal_high"]:
        return "normal"
    if value <= r.get("borderline_high", r["normal_high"]):
        return "borderline"
    return "abnormal"


def status_badge_html(status: str) -> str:
    label = {"normal": "Normal", "borderline": "Borderline", "abnormal": "Abnormal"}[status]
    cls = {"normal": "status-normal", "borderline": "status-borderline", "abnormal": "status-abnormal"}[status]
    return f'<span class="field-status {cls}">{label}</span>'


def severity_tier(score: float) -> tuple[str, str]:
    """Map a 0-100 score to (label, css-class-suffix)."""
    if score <= 30:
        return "Low", "low"
    if score <= 60:
        return "Moderate", "mod"
    if score <= 80:
        return "High", "high"
    return "Critical", "crit"


def overall_severity(scores: dict[str, float]) -> str:
    """Pick the worst severity across the three risk scores for global tier."""
    order = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
    worst = "Low"
    for v in scores.values():
        tier, _ = severity_tier(v)
        if order[tier] > order[worst]:
            worst = tier
    return worst


def build_patient_state_vector(
    vitals: dict[str, Any],
    symptoms: str,
    preferences: dict[str, Any],
    risk_scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Assemble the full Patient State Vector (PSV) used downstream."""
    bmi = compute_bmi(vitals.get("height_cm", 0), vitals.get("weight_kg", 0))
    psv: dict[str, Any] = {
        "demographics": {
            "age": vitals.get("age"),
            "sex": vitals.get("sex"),
            "height_cm": vitals.get("height_cm"),
            "weight_kg": vitals.get("weight_kg"),
            "bmi": bmi,
        },
        "vitals": {
            "fbg_mg_dl": vitals.get("fbg"),
            "hba1c_pct": vitals.get("hba1c"),
            "sbp_mmHg": vitals.get("sbp"),
            "dbp_mmHg": vitals.get("dbp"),
            "total_cholesterol_mg_dl": vitals.get("cholesterol"),
            "ldl_mg_dl": vitals.get("ldl"),
            "hdl_mg_dl": vitals.get("hdl"),
            "creatinine_mg_dl": vitals.get("creatinine"),
            "resting_hr_bpm": vitals.get("resting_hr"),
        },
        "symptoms_text": symptoms,
        "preferences": {
            "fitness_level": preferences.get("fitness_level"),
            "dietary_restrictions": preferences.get("dietary_restrictions", []),
            "cuisine_preference": preferences.get("cuisine_preference"),
            "additional_notes": preferences.get("additional_notes", ""),
        },
    }
    if risk_scores:
        psv["risk_scores"] = {
            "diabetes": risk_scores.get("diabetes"),
            "hypertension": risk_scores.get("hypertension"),
            "cvd": risk_scores.get("cvd"),
        }
        psv["severity_tier"] = overall_severity(risk_scores)
    return psv


# ---------- Gemini wrapper ----------
# Default model. `gemini-1.5-flash` was retired by Google; the current
# stable, fast, JSON-capable replacement is `gemini-2.5-flash`. Override via
# the GEMINI_MODEL env var or a `GEMINI_MODEL` Streamlit secret if needed.
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _get_api_key() -> str | None:
    try:
        key = st.secrets.get("GEMINI_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        key = None
    if not key:
        key = os.environ.get("GEMINI_API_KEY")
    return key or None


def _get_model_name() -> str:
    try:
        m = st.secrets.get("GEMINI_MODEL")  # type: ignore[attr-defined]
    except Exception:
        m = None
    return m or os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL


def gemini_available() -> bool:
    return bool(_get_api_key())


def call_gemini(system_prompt: str, user_message: str) -> dict[str, Any]:
    """Call Gemini API and return parsed JSON. Raises on failure."""
    import google.generativeai as genai  # local import — keeps cold-start light

    key = _get_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set in Streamlit secrets or env.")

    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        model_name=_get_model_name(),
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )
    response = model.generate_content(user_message)
    text = (response.text or "").strip()

    if text.startswith("```"):
        # defensive strip of accidental markdown fences
        text = text.split("```", 2)[1]
        if text.lstrip().lower().startswith("json"):
            text = text.split("\n", 1)[1] if "\n" in text else text[4:]
    return json.loads(text)


# ---------- CSS injection ----------
def inject_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "styles" / "main.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def page_anchor(name: str) -> None:
    st.markdown(f'<div id="{name}"></div>', unsafe_allow_html=True)
