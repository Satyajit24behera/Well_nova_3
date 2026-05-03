"""Module 1 — Risk scoring + clinical narrative.

Risk scores are computed by deterministic rules (no ML in the demo). The
Gemini call generates the ICD-11 mapping, plain-English interpretation,
and SHAP-style key risk factors.
"""
from __future__ import annotations

from typing import Any

from modules.utils import (
    build_patient_state_vector,
    call_gemini,
    compute_bmi,
    gemini_available,
    severity_tier,
)


SYSTEM_PROMPT_MODULE1 = """\
You are Health-LLM, a clinical AI assistant embedded in WellNOVA 3.0, a chronic disease
management system. You receive a patient's biomarker data and pre-computed risk scores
for Type 2 Diabetes, Hypertension, and Cardiovascular Disease.

Your job is to:
1. Map symptoms and biomarkers to the top-3 most likely ICD-11 codes with confidence percentages.
2. Write a brief, clinically accurate 2-sentence risk interpretation for each condition.
3. Identify the top 5 biomarkers most responsible for elevated risk (SHAP-style explanation).
4. Assign an overall severity tier: Low / Moderate / High / Critical.

Respond ONLY in valid JSON. No markdown, no preamble. Schema:
{
  "icd_codes": [
    {"code": "E11.9", "description": "Type 2 Diabetes Mellitus, unspecified", "confidence": 82.0}
  ],
  "interpretations": {
    "diabetes": "...",
    "hypertension": "...",
    "cvd": "..."
  },
  "severity_tier": "High",
  "key_risk_factors": [
    {"biomarker": "HbA1c", "value": 7.8, "unit": "%", "impact": "high", "direction": "positive"}
  ]
}
"""


# ---------- Deterministic risk scoring ----------
def compute_diabetes_risk(hba1c: float, fbg: float, bmi: float, age: int) -> int:
    score = 0
    if hba1c >= 6.5: score += 40
    elif hba1c >= 5.7: score += 20
    if fbg >= 126: score += 30
    elif fbg >= 100: score += 15
    if bmi >= 30: score += 15
    elif bmi >= 25: score += 8
    if age >= 45: score += 15
    return min(score, 100)


def compute_hypertension_risk(sbp: float, dbp: float, age: int, bmi: float) -> int:
    score = 0
    if sbp >= 180: score += 50
    elif sbp >= 140: score += 35
    elif sbp >= 130: score += 20
    if dbp >= 120: score += 30
    elif dbp >= 90: score += 20
    elif dbp >= 80: score += 10
    if bmi >= 30: score += 10
    if age >= 55: score += 10
    return min(score, 100)


def compute_cvd_risk(
    cholesterol: float,
    ldl: float,
    hdl: float,
    sbp: float,
    age: int,
    bmi: float,
) -> int:
    score = 0
    if ldl >= 190: score += 30
    elif ldl >= 160: score += 20
    elif ldl >= 130: score += 10
    if hdl < 40: score += 20
    elif hdl < 60: score += 10
    if cholesterol >= 240: score += 15
    if sbp >= 140: score += 15
    if age >= 55: score += 10
    if bmi >= 30: score += 10
    return min(score, 100)


def compute_risk_scores(vitals: dict[str, Any]) -> dict[str, Any]:
    bmi = compute_bmi(vitals.get("height_cm", 0), vitals.get("weight_kg", 0))
    age = int(vitals.get("age", 0))
    diabetes = compute_diabetes_risk(
        float(vitals["hba1c"]), float(vitals["fbg"]), bmi, age
    )
    hypertension = compute_hypertension_risk(
        float(vitals["sbp"]), float(vitals["dbp"]), age, bmi
    )
    cvd = compute_cvd_risk(
        float(vitals["cholesterol"]),
        float(vitals["ldl"]),
        float(vitals["hdl"]),
        float(vitals["sbp"]),
        age,
        bmi,
    )
    return {
        "diabetes": diabetes,
        "hypertension": hypertension,
        "cvd": cvd,
        "tiers": {
            "diabetes": severity_tier(diabetes)[0],
            "hypertension": severity_tier(hypertension)[0],
            "cvd": severity_tier(cvd)[0],
        },
    }


# ---------- Prompt builder ----------
def build_module1_user_message(
    vitals: dict[str, Any],
    symptoms: str,
    risk_data: dict[str, Any],
) -> str:
    bmi = compute_bmi(vitals.get("height_cm", 0), vitals.get("weight_kg", 0))
    return f"""\
Patient symptoms (free text):
{symptoms or '[not provided]'}

Demographics: Age={vitals.get('age')}, Sex={vitals.get('sex')}, BMI={bmi}

Biomarkers:
- Fasting Blood Glucose: {vitals.get('fbg')} mg/dL
- HbA1c: {vitals.get('hba1c')} %
- Blood Pressure: {vitals.get('sbp')}/{vitals.get('dbp')} mmHg
- Total Cholesterol: {vitals.get('cholesterol')} mg/dL
- LDL: {vitals.get('ldl')} mg/dL
- HDL: {vitals.get('hdl')} mg/dL
- Creatinine: {vitals.get('creatinine')} mg/dL
- Resting HR: {vitals.get('resting_hr')} bpm

Pre-computed risk scores (0-100):
- Type 2 Diabetes: {risk_data['diabetes']} ({risk_data['tiers']['diabetes']})
- Hypertension: {risk_data['hypertension']} ({risk_data['tiers']['hypertension']})
- CVD: {risk_data['cvd']} ({risk_data['tiers']['cvd']})

Generate the JSON output per the schema in your system prompt."""


# ---------- Mock fallback ----------
def _mock_clinical_interpretation(
    vitals: dict[str, Any], risk_data: dict[str, Any]
) -> dict[str, Any]:
    """Used when GEMINI_API_KEY is missing — keeps the demo viewable."""
    overall = max(
        ("diabetes", "hypertension", "cvd"),
        key=lambda k: risk_data[k],
    )
    overall_tier = risk_data["tiers"][overall]
    icd = []
    if risk_data["diabetes"] >= 60:
        icd.append({
            "code": "5A11", "description": "Type 2 Diabetes Mellitus",
            "confidence": min(60 + risk_data["diabetes"] * 0.3, 95),
        })
    if risk_data["hypertension"] >= 50:
        icd.append({
            "code": "BA00.Z", "description": "Essential (primary) hypertension",
            "confidence": min(55 + risk_data["hypertension"] * 0.3, 92),
        })
    if risk_data["cvd"] >= 50:
        icd.append({
            "code": "BD40.Z", "description": "Cardiovascular disease, unspecified",
            "confidence": min(50 + risk_data["cvd"] * 0.3, 88),
        })
    if not icd:
        icd.append({
            "code": "QA00", "description": "Routine general health examination",
            "confidence": 70.0,
        })

    bmi = compute_bmi(vitals.get("height_cm", 0), vitals.get("weight_kg", 0))
    factors = [
        {"biomarker": "HbA1c", "value": vitals["hba1c"], "unit": "%",
         "impact": "high" if vitals["hba1c"] >= 6.5 else "moderate", "direction": "positive"},
        {"biomarker": "Fasting Blood Glucose", "value": vitals["fbg"], "unit": "mg/dL",
         "impact": "high" if vitals["fbg"] >= 126 else "moderate", "direction": "positive"},
        {"biomarker": "Systolic BP", "value": vitals["sbp"], "unit": "mmHg",
         "impact": "high" if vitals["sbp"] >= 140 else "moderate", "direction": "positive"},
        {"biomarker": "LDL", "value": vitals["ldl"], "unit": "mg/dL",
         "impact": "high" if vitals["ldl"] >= 130 else "moderate", "direction": "positive"},
        {"biomarker": "HDL", "value": vitals["hdl"], "unit": "mg/dL",
         "impact": "moderate", "direction": "negative" if vitals["hdl"] < 40 else "positive"},
        {"biomarker": "BMI", "value": bmi, "unit": "kg/m²",
         "impact": "moderate" if bmi >= 25 else "low", "direction": "positive"},
    ]
    return {
        "icd_codes": icd[:3],
        "interpretations": {
            "diabetes": (
                f"HbA1c of {vitals['hba1c']}% and fasting glucose of {vitals['fbg']} mg/dL "
                f"indicate {risk_data['tiers']['diabetes'].lower()} diabetes risk. "
                "Lifestyle and dietary modification recommended; consider clinical follow-up."
            ),
            "hypertension": (
                f"Blood pressure of {vitals['sbp']}/{vitals['dbp']} mmHg places you in the "
                f"{risk_data['tiers']['hypertension'].lower()} hypertension risk category. "
                "Sodium restriction and regular monitoring are advised."
            ),
            "cvd": (
                f"Lipid profile (LDL {vitals['ldl']}, HDL {vitals['hdl']}) combined with BMI of "
                f"{bmi} suggests {risk_data['tiers']['cvd'].lower()} cardiovascular risk. "
                "Mediterranean-style diet and consistent aerobic activity recommended."
            ),
        },
        "severity_tier": overall_tier,
        "key_risk_factors": factors,
    }


# ---------- Public entry point ----------
def run_module1(
    vitals: dict[str, Any],
    symptoms: str,
    preferences: dict[str, Any],
) -> dict[str, Any]:
    """Return a dict with risk_data, clinical_interp, psv, and source flag."""
    risk_data = compute_risk_scores(vitals)

    if gemini_available():
        try:
            user_msg = build_module1_user_message(vitals, symptoms, risk_data)
            clinical = call_gemini(SYSTEM_PROMPT_MODULE1, user_msg)
            source = "gemini"
        except Exception as exc:
            clinical = _mock_clinical_interpretation(vitals, risk_data)
            clinical["_fallback_reason"] = f"Gemini call failed: {exc}"
            source = "mock"
    else:
        clinical = _mock_clinical_interpretation(vitals, risk_data)
        source = "mock"

    psv = build_patient_state_vector(
        vitals, symptoms, preferences,
        risk_scores={
            "diabetes": risk_data["diabetes"],
            "hypertension": risk_data["hypertension"],
            "cvd": risk_data["cvd"],
        },
    )
    return {
        "risk_data": risk_data,
        "clinical": clinical,
        "psv": psv,
        "source": source,
    }
