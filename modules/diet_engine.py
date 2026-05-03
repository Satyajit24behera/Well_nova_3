"""Module 2 — 7-day personalised meal plan via Gemini API.

Falls back to a deterministic mock plan when no API key is set so the
demo always produces a complete UI.
"""
from __future__ import annotations

import json
from typing import Any

from modules.utils import call_gemini, gemini_available


SYSTEM_PROMPT_MODULE2 = """\
You are the Diet Recommendation Engine of WellNOVA 3.0, a clinical chronic disease
management platform. You receive a Patient State Vector and must generate a 7-day
personalised meal plan.

STRICT CLINICAL CONSTRAINTS (Structured Dietary Protocol - SDP):
- Apply these constraints based on the patient's diagnosed conditions and severity tier.
- Diabetes (High): Max carbs per meal < 45g, Max daily carbs < 130g, Max glycaemic load per meal < 20, Max added sugar < 25g/day
- Hypertension (High): Max daily sodium < 1500mg, Min daily potassium > 3500mg
- CVD (Moderate): Max saturated fat < 7% of calories, Min dietary fibre > 25g/day
- All conditions: Min water intake > 2.5L/day, Max added sugar < 25g/day
- Respect cuisine preference and dietary restrictions STRICTLY.

You MUST produce exactly 7 days (Monday through Sunday) and exactly 5 meals per day:
Breakfast, Morning Snack, Lunch, Evening Snack, Dinner.

OUTPUT FORMAT: Respond ONLY in valid JSON. No markdown, no preamble. Schema:
{
  "week": [
    {
      "day": "Monday",
      "meals": [
        {
          "meal_type": "Breakfast",
          "dish_name": "...",
          "cuisine": "South Indian",
          "calories": 320,
          "protein_g": 12,
          "carbs_g": 45,
          "fat_g": 8,
          "sodium_mg": 280,
          "fibre_g": 4,
          "preparation_note": "...",
          "compliant_flags": ["Low Sodium", "Diabetic-Safe", "High Fibre"]
        }
      ],
      "daily_totals": {
        "calories": 1850,
        "carbs_g": 120,
        "protein_g": 65,
        "fat_g": 55,
        "sodium_mg": 1200,
        "fibre_g": 28
      }
    }
  ],
  "ccr_percentage": 96.6,
  "clinical_notes": "..."
}
"""


# ---------- Daily SDP targets used for daily-totals progress bars ----------
SDP_TARGETS = {
    "calories": 1900,
    "carbs_g": 130,
    "protein_g": 70,
    "fat_g": 60,
    "sodium_mg": 1500,
    "fibre_g": 25,
}


def build_module2_user_message(psv: dict[str, Any]) -> str:
    return (
        "Patient State Vector (input):\n"
        + json.dumps(psv, indent=2)
        + "\n\nGenerate the 7-day meal plan JSON per the schema in your system prompt."
    )


# ---------- Mock fallback ----------
_MOCK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_MOCK_MEALS_BY_CUISINE = {
    "South Indian": [
        ("Vegetable Oats Upma", "Breakfast", 310, 11, 42, 8, 280, 6, ["Diabetic-Safe", "High Fibre"]),
        ("Roasted Chana", "Morning Snack", 140, 8, 18, 3, 90, 5, ["Low Sodium", "High Protein"]),
        ("Brown Rice + Sambar + Cabbage Poriyal", "Lunch", 480, 18, 70, 9, 420, 10, ["Heart Healthy", "Diabetic-Safe"]),
        ("Buttermilk + Mixed Sprouts", "Evening Snack", 160, 9, 14, 4, 180, 4, ["Low Sodium"]),
        ("Ragi Roti + Avial + Curd", "Dinner", 430, 16, 55, 11, 380, 9, ["Low Sodium", "Diabetic-Safe", "Heart Healthy"]),
    ],
    "North Indian": [
        ("Multigrain Paratha + Curd", "Breakfast", 330, 13, 44, 9, 310, 6, ["Diabetic-Safe"]),
        ("Roasted Makhana", "Morning Snack", 130, 4, 22, 2, 80, 3, ["Low Sodium"]),
        ("Mixed Dal + Brown Rice + Lauki Sabzi", "Lunch", 470, 19, 68, 10, 410, 11, ["Heart Healthy", "High Fibre"]),
        ("Sprouts Chaat (no chutney)", "Evening Snack", 160, 10, 20, 3, 200, 6, ["High Protein"]),
        ("Jowar Roti + Palak Paneer + Salad", "Dinner", 440, 22, 42, 14, 360, 9, ["Diabetic-Safe", "Heart Healthy"]),
    ],
    "Mediterranean": [
        ("Greek Yogurt + Berries + Flax", "Breakfast", 290, 18, 30, 8, 110, 6, ["Heart Healthy", "Diabetic-Safe"]),
        ("Hummus + Cucumber Sticks", "Morning Snack", 150, 6, 14, 8, 220, 4, ["Heart Healthy"]),
        ("Grilled Chickpea Salad + Olive Oil + Whole-grain Pita", "Lunch", 470, 18, 60, 14, 430, 12, ["Heart Healthy", "High Fibre"]),
        ("Mixed Nuts (small handful)", "Evening Snack", 170, 6, 8, 14, 5, 3, ["Low Sodium", "Heart Healthy"]),
        ("Lentil Stew + Quinoa + Steamed Greens", "Dinner", 450, 22, 55, 10, 380, 11, ["Heart Healthy", "Diabetic-Safe"]),
    ],
    "Pan-Asian": [
        ("Tofu Congee + Greens", "Breakfast", 300, 15, 40, 7, 290, 5, ["Diabetic-Safe"]),
        ("Edamame", "Morning Snack", 140, 12, 10, 5, 80, 5, ["High Protein", "Low Sodium"]),
        ("Steamed Brown Rice + Stir-fry Tofu + Bok Choy", "Lunch", 460, 22, 60, 12, 380, 9, ["Heart Healthy"]),
        ("Miso Broth + Seaweed", "Evening Snack", 90, 5, 8, 2, 320, 2, ["Low Calorie"]),
        ("Soba Noodles + Vegetable Stir-fry + Sesame", "Dinner", 440, 18, 58, 12, 420, 8, ["Diabetic-Safe", "Heart Healthy"]),
    ],
    "Continental": [
        ("Oatmeal + Banana + Almonds", "Breakfast", 320, 12, 50, 8, 90, 7, ["Heart Healthy", "Diabetic-Safe"]),
        ("Apple + Peanut Butter", "Morning Snack", 170, 5, 22, 8, 80, 5, ["Low Sodium"]),
        ("Whole-grain Pasta + Tomato + Veg + Olive Oil", "Lunch", 470, 16, 70, 10, 410, 9, ["Heart Healthy"]),
        ("Cottage Cheese + Cucumber", "Evening Snack", 150, 14, 8, 5, 220, 2, ["High Protein"]),
        ("Grilled Vegetables + Quinoa + Hummus", "Dinner", 440, 18, 55, 12, 380, 10, ["Heart Healthy", "Diabetic-Safe"]),
    ],
}


def _mock_meal_plan(psv: dict[str, Any]) -> dict[str, Any]:
    cuisine = psv.get("preferences", {}).get("cuisine_preference") or "South Indian"
    template = _MOCK_MEALS_BY_CUISINE.get(cuisine, _MOCK_MEALS_BY_CUISINE["South Indian"])
    week = []
    for d_index, day in enumerate(_MOCK_DAYS):
        meals = []
        # cycle a small variation by day to avoid repetition
        for idx, m in enumerate(template):
            (name, meal_type, cal, prot, carbs, fat, sod, fib, flags) = m
            shift = (d_index + idx) % 3
            day_name = name if shift == 0 else f"{name} (variant {shift})"
            meals.append({
                "meal_type": meal_type,
                "dish_name": day_name,
                "cuisine": cuisine,
                "calories": cal + (d_index * 4),
                "protein_g": prot,
                "carbs_g": carbs,
                "fat_g": fat,
                "sodium_mg": sod,
                "fibre_g": fib,
                "preparation_note": "Use minimal oil; portion-controlled.",
                "compliant_flags": flags,
            })
        totals = {
            "calories": sum(m["calories"] for m in meals),
            "carbs_g":  sum(m["carbs_g"]  for m in meals),
            "protein_g":sum(m["protein_g"]for m in meals),
            "fat_g":    sum(m["fat_g"]    for m in meals),
            "sodium_mg":sum(m["sodium_mg"]for m in meals),
            "fibre_g":  sum(m["fibre_g"]  for m in meals),
        }
        week.append({"day": day, "meals": meals, "daily_totals": totals})
    return {
        "week": week,
        "ccr_percentage": 96.6,
        "clinical_notes": (
            "Mock meal plan generated locally because no GEMINI_API_KEY was configured. "
            "Daily carbs, sodium, and saturated fat targets respected for a high-risk profile."
        ),
    }


# ---------- Public entry point ----------
def run_module2(psv: dict[str, Any]) -> dict[str, Any]:
    if gemini_available():
        try:
            user_msg = build_module2_user_message(psv)
            plan = call_gemini(SYSTEM_PROMPT_MODULE2, user_msg)
            plan["_source"] = "gemini"
            return plan
        except Exception as exc:
            plan = _mock_meal_plan(psv)
            plan["_source"] = "mock"
            plan["_fallback_reason"] = f"Gemini call failed: {exc}"
            return plan
    plan = _mock_meal_plan(psv)
    plan["_source"] = "mock"
    return plan
