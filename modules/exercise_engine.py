"""Module 3 — 7-day condition-aware exercise schedule via Gemini API.

Falls back to a deterministic mock schedule when no API key is set.
"""
from __future__ import annotations

import json
from typing import Any

from modules.utils import call_gemini, gemini_available


SYSTEM_PROMPT_MODULE3 = """\
You are the Exercise Recommendation Engine of WellNOVA 3.0. You receive a Patient
State Vector and must generate a safe, condition-adapted 7-day exercise schedule.

APPLY THESE RULES STRICTLY:
- Fitness Level MET Ranges: Beginner (2.0-4.0), Intermediate (4.0-6.0), Advanced (6.0-8.0)
- High severity: Reduce upper MET bound by 1.5
- Hypertension contraindications: No Valsalva manoeuvre, no isometric holds >10s, monitor BP
- Diabetes contraindications: Exercise after meals preferred, carry fast-acting glucose
- CVD High risk: Min 2 full rest days/week, 1 active recovery day, no high-intensity intervals
- FITT principle: Frequency, Intensity, Time, Type — must be specified for every session
- Include modification options for low-energy days

You MUST produce exactly 7 days (Monday through Sunday).

OUTPUT FORMAT: Respond ONLY in valid JSON. No markdown, no preamble. Schema:
{
  "week": [
    {
      "day": "Monday",
      "session_type": "Active",
      "exercise_name": "Brisk Morning Walk",
      "duration_minutes": 30,
      "intensity": "Low",
      "met_value": 3.5,
      "target_hr_zone": "50-60% max HR (85-100 bpm)",
      "condition_cautions": ["Monitor blood pressure before and after", "Stop if chest discomfort"],
      "low_energy_modification": "Slow 15-minute walk at home",
      "calories_burned_approx": 120
    }
  ],
  "escr_percentage": 93.2,
  "contraindications_applied": ["..."],
  "weekly_summary": "..."
}
"""


_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_module3_user_message(psv: dict[str, Any]) -> str:
    return (
        "Patient State Vector (input):\n"
        + json.dumps(psv, indent=2)
        + "\n\nGenerate the 7-day exercise schedule JSON per the schema in your system prompt."
    )


# ---------- Mock fallback ----------
_MOCK_TEMPLATES = {
    "Beginner": [
        ("Brisk Morning Walk",       "Active",            30, "Low",      3.5, "50-60% max HR", 120),
        ("Chair Yoga + Breathing",   "Active",            25, "Low",      2.5, "45-55% max HR",  80),
        ("Light Resistance Band",    "Active",            20, "Low",      3.0, "50-60% max HR",  90),
        ("Rest Day",                 "Rest",               0, "Rest",     1.0, "Rest",            0),
        ("Slow Cycling (stationary)","Active",            25, "Low",      3.5, "50-60% max HR", 110),
        ("Stretching + Walk",        "Active Recovery",   20, "Low",      2.5, "45-55% max HR",  70),
        ("Rest Day",                 "Rest",               0, "Rest",     1.0, "Rest",            0),
    ],
    "Intermediate": [
        ("Jogging + Walking Intervals", "Active",         35, "Moderate", 5.0, "60-70% max HR", 220),
        ("Bodyweight Circuit",          "Active",         30, "Moderate", 4.5, "60-70% max HR", 200),
        ("Cycling",                     "Active",         40, "Moderate", 5.5, "60-70% max HR", 260),
        ("Yoga Flow",                   "Active Recovery",30, "Low",      3.0, "50-60% max HR", 110),
        ("Swimming (easy laps)",        "Active",         30, "Moderate", 5.5, "60-70% max HR", 240),
        ("Rest Day",                    "Rest",            0, "Rest",     1.0, "Rest",           0),
        ("Hiking / Long Walk",          "Active",         45, "Moderate", 4.5, "60-70% max HR", 260),
    ],
    "Advanced": [
        ("Tempo Run",                   "Active",         40, "High",     7.0, "70-85% max HR", 380),
        ("Strength Training",           "Active",         45, "Moderate", 6.0, "65-75% max HR", 320),
        ("Cycling Intervals",           "Active",         40, "High",     7.5, "70-85% max HR", 400),
        ("Active Recovery Yoga",        "Active Recovery",35, "Low",      3.0, "50-60% max HR", 130),
        ("Swimming",                    "Active",         40, "Moderate", 6.0, "65-75% max HR", 320),
        ("HIIT Bodyweight",             "Active",         30, "High",     7.5, "70-85% max HR", 320),
        ("Rest Day",                    "Rest",            0, "Rest",     1.0, "Rest",           0),
    ],
}


def _mock_exercise_plan(psv: dict[str, Any]) -> dict[str, Any]:
    fitness = psv.get("preferences", {}).get("fitness_level") or "Beginner"
    risks = psv.get("risk_scores", {})
    severity = psv.get("severity_tier", "Low")
    template = _MOCK_TEMPLATES.get(fitness, _MOCK_TEMPLATES["Beginner"])

    cautions_base = []
    if risks.get("hypertension", 0) >= 60:
        cautions_base += [
            "Monitor blood pressure before and after",
            "Avoid Valsalva (no breath holding)",
            "No isometric holds longer than 10 seconds",
        ]
    if risks.get("diabetes", 0) >= 60:
        cautions_base += [
            "Carry fast-acting glucose",
            "Prefer post-meal sessions to avoid hypoglycaemia",
        ]
    if risks.get("cvd", 0) >= 50:
        cautions_base += [
            "Stop if chest discomfort, dizziness, or unusual shortness of breath",
            "Maintain conversational pace",
        ]

    week = []
    for day_name, t in zip(_DAYS, template):
        (ex_name, session_type, duration, intensity, met, hr_zone, kcal) = t
        if severity in ("High", "Critical") and intensity == "High":
            intensity = "Moderate"
            met = max(met - 1.5, 3.0)
            ex_name = ex_name + " (intensity reduced)"
            kcal = int(kcal * 0.75)
        cautions = list(cautions_base) if session_type != "Rest" else ["Hydrate and rest fully"]
        week.append({
            "day": day_name,
            "session_type": session_type,
            "exercise_name": ex_name,
            "duration_minutes": duration,
            "intensity": intensity,
            "met_value": met,
            "target_hr_zone": hr_zone,
            "condition_cautions": cautions,
            "low_energy_modification": (
                "Replace with 15-minute slow walk and breathing exercises"
                if session_type != "Rest"
                else "Maintain rest; gentle stretching only"
            ),
            "calories_burned_approx": kcal,
        })

    return {
        "week": week,
        "escr_percentage": 93.2,
        "contraindications_applied": cautions_base or [
            "Standard FITT principle applied; no condition-specific contraindications triggered"
        ],
        "weekly_summary": (
            f"7-day plan tailored for a {fitness.lower()} patient with overall {severity.lower()} "
            "severity. Includes 2 rest/recovery days and condition-aware MET ceiling."
        ),
    }


# ---------- Public entry point ----------
def run_module3(psv: dict[str, Any]) -> dict[str, Any]:
    if gemini_available():
        try:
            user_msg = build_module3_user_message(psv)
            plan = call_gemini(SYSTEM_PROMPT_MODULE3, user_msg)
            plan["_source"] = "gemini"
            return plan
        except Exception as exc:
            plan = _mock_exercise_plan(psv)
            plan["_source"] = "mock"
            plan["_fallback_reason"] = f"Gemini call failed: {exc}"
            return plan
    plan = _mock_exercise_plan(psv)
    plan["_source"] = "mock"
    return plan
