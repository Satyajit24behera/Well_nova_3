"""Module 2 output — 7-Day Meal Plan UI."""
from __future__ import annotations

from typing import Any

import streamlit as st

from modules.diet_engine import SDP_TARGETS


_MEAL_ORDER = ["Breakfast", "Morning Snack", "Lunch", "Evening Snack", "Dinner"]
_MEAL_ICONS = {
    "Breakfast": "🌅",
    "Morning Snack": "🍎",
    "Lunch": "🍽️",
    "Evening Snack": "🥜",
    "Dinner": "🌙",
}


def _compliance_badges(flags: list[str]) -> str:
    if not flags:
        return ""
    return "".join(f'<span class="compliance-badge">✅ {f}</span>' for f in flags)


def _meal_card_html(meal: dict[str, Any]) -> str:
    icon = _MEAL_ICONS.get(meal.get("meal_type", ""), "🍴")
    flags_html = _compliance_badges(meal.get("compliant_flags", []))
    prep = meal.get("preparation_note", "")
    return f"""
    <div class="meal-card">
        <div class="meal-type">{icon} {meal.get('meal_type', '')}</div>
        <div class="meal-name">{meal.get('dish_name', '')}</div>
        <span class="cuisine-badge">{meal.get('cuisine', '')}</span>
        <div class="macro-grid">
            <div class="macro-item">
                <div class="label">🔥 Calories</div>
                <div class="value">{meal.get('calories', 0)} kcal</div>
            </div>
            <div class="macro-item">
                <div class="label">💪 Protein</div>
                <div class="value">{meal.get('protein_g', 0)}g</div>
            </div>
            <div class="macro-item">
                <div class="label">🍞 Carbs</div>
                <div class="value">{meal.get('carbs_g', 0)}g</div>
            </div>
            <div class="macro-item">
                <div class="label">🥑 Fats</div>
                <div class="value">{meal.get('fat_g', 0)}g</div>
            </div>
            <div class="macro-item">
                <div class="label">🧂 Sodium</div>
                <div class="value">{meal.get('sodium_mg', 0)}mg</div>
            </div>
            <div class="macro-item">
                <div class="label">🌿 Fibre</div>
                <div class="value">{meal.get('fibre_g', 0)}g</div>
            </div>
        </div>
        {f'<div>{flags_html}</div>' if flags_html else ''}
        {f'<div class="prep-note">{prep}</div>' if prep else ''}
    </div>
    """


def _daily_summary(totals: dict[str, Any]) -> None:
    targets = SDP_TARGETS
    metrics = [
        ("Calories", "calories", "kcal"),
        ("Carbs", "carbs_g", "g"),
        ("Protein", "protein_g", "g"),
        ("Fats", "fat_g", "g"),
        ("Sodium", "sodium_mg", "mg"),
        ("Fibre", "fibre_g", "g"),
    ]
    cols = st.columns(len(metrics))
    for col, (label, key, unit) in zip(cols, metrics):
        actual = totals.get(key, 0) or 0
        target = targets.get(key, 1)
        pct = min(int((actual / target) * 100), 100)
        over = actual > target
        color = "#ef4444" if over else "#10b981"
        with col:
            st.markdown(
                f'<div style="text-align:center;font-size:11px;color:#94a3b8">{label}</div>'
                f'<div style="text-align:center;font-weight:700;color:{color}">{actual}{unit}</div>',
                unsafe_allow_html=True,
            )
            st.progress(pct)


def render_meal_plan(meal_plan: dict[str, Any]) -> None:
    ccr = meal_plan.get("ccr_percentage", 0)
    source = meal_plan.get("_source", "mock")

    st.markdown("## 🥗 7-Day Personalised Meal Plan")

    if source == "mock":
        st.info(
            "ℹ️ Meal plan generated locally (no Gemini API key set). "
            "Add `GEMINI_API_KEY` to Streamlit secrets for a fully personalised AI-generated plan.",
            icon="ℹ️",
        )

    st.markdown(
        f'<div class="compliance-banner">Clinical Compliance Rate (CCR): {ccr:.1f}% ✅</div>',
        unsafe_allow_html=True,
    )

    week = meal_plan.get("week", []) or []
    if not week:
        st.warning("No meal plan data available.")
        return

    day_tabs = st.tabs([d.get("day", f"Day {i+1}")[:3] for i, d in enumerate(week)])

    for tab, day_data in zip(day_tabs, week):
        with tab:
            meals = day_data.get("meals", []) or []
            # Sort by the canonical meal order
            meals_sorted = sorted(
                meals,
                key=lambda m: _MEAL_ORDER.index(m.get("meal_type", "Breakfast"))
                if m.get("meal_type") in _MEAL_ORDER
                else 99,
            )
            for meal in meals_sorted:
                st.markdown(_meal_card_html(meal), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("**Daily Totals vs SDP Targets**")
            _daily_summary(day_data.get("daily_totals", {}))

    clinical_notes = meal_plan.get("clinical_notes")
    if clinical_notes:
        with st.expander("Clinical Notes"):
            st.info(clinical_notes)

    st.markdown(
        '<div class="disclaimer-box">⚠️ Meal plans are for demonstration only. Consult a registered dietitian before making dietary changes.</div>',
        unsafe_allow_html=True,
    )
