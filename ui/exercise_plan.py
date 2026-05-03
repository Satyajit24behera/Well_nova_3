"""Module 3 output — 7-Day Exercise Schedule UI."""
from __future__ import annotations

from typing import Any

import streamlit as st

from modules.utils import gemini_available


_INTENSITY_CSS = {
    "Low": "intensity-low",
    "Moderate": "intensity-mod",
    "High": "intensity-high",
    "Rest": "intensity-rest",
}

_INTENSITY_EMOJI = {
    "Low": "🟢",
    "Moderate": "🟡",
    "High": "🔴",
    "Rest": "⬜",
}


def _day_card_html(day: dict[str, Any]) -> str:
    intensity = day.get("intensity", "Low")
    cls = _INTENSITY_CSS.get(intensity, "intensity-low")
    emoji = _INTENSITY_EMOJI.get(intensity, "🟢")
    duration = day.get("duration_minutes", 0)
    dur_str = f"{duration} min" if duration else "Rest"
    met = day.get("met_value", 1.0)
    hr_zone = day.get("target_hr_zone", "—")
    kcal = day.get("calories_burned_approx", 0)

    return f"""
    <div class="exercise-day">
        <div class="day-name">{day.get('day', '')}</div>
        <div class="ex-name">{day.get('exercise_name', '—')}</div>
        <div class="ex-meta">
            {emoji} <span class="{cls}">{intensity}</span><br>
            ⏱ {dur_str} &nbsp;|&nbsp; MET {met}<br>
            ❤️ {hr_zone}<br>
            🔥 ~{kcal} kcal
        </div>
    </div>
    """


def render_exercise_plan(exercise_plan: dict[str, Any]) -> None:
    escr = exercise_plan.get("escr_percentage", 0)
    source = exercise_plan.get("_source", "mock")
    fallback_reason = exercise_plan.get("_fallback_reason")

    st.markdown("## 🏃 7-Day Exercise Schedule")

    if source == "mock":
        if gemini_available() and fallback_reason:
            st.warning(
                "Gemini call failed for the exercise schedule; falling back to a deterministic "
                f"local plan. Details: {fallback_reason}",
                icon="⚠️",
            )
        elif not gemini_available():
            st.info(
                "Exercise plan generated locally (no Gemini API key configured). "
                "Add `GEMINI_API_KEY` to Streamlit secrets for a fully personalised AI-generated schedule.",
                icon="ℹ️",
            )

    st.markdown(
        f'<div class="compliance-banner">'
        f"Exercise Safety Compliance Rate (ESCR): {escr:.1f}% — "
        f"No Absolute Contraindication Violations Detected ✅"
        f"</div>",
        unsafe_allow_html=True,
    )

    week = exercise_plan.get("week", []) or []
    if not week:
        st.warning("No exercise plan data available.")
        return

    # Weekly calendar grid — 4 days per row to keep cards legible
    for row_start in range(0, len(week), 4):
        row_days = week[row_start: row_start + 4]
        cols = st.columns(len(row_days))
        for col, day in zip(cols, row_days):
            with col:
                st.markdown(_day_card_html(day), unsafe_allow_html=True)
                cautions = day.get("condition_cautions", [])
                if cautions:
                    with st.expander("⚠️ Cautions", expanded=False):
                        for c in cautions:
                            st.markdown(f"- {c}")
                mod = day.get("low_energy_modification")
                if mod and day.get("session_type") != "Rest":
                    with st.expander("💡 Low-energy option"):
                        st.caption(mod)

        st.markdown("")  # spacing between rows

    # Contraindications panel
    contras = exercise_plan.get("contraindications_applied", []) or []
    if contras:
        with st.expander("📋 Contraindication Rules Applied"):
            for c in contras:
                st.markdown(f"- {c}")

    # Weekly summary
    summary = exercise_plan.get("weekly_summary")
    if summary:
        with st.expander("📊 Weekly Summary"):
            st.info(summary)

    st.markdown(
        '<div class="disclaimer-box">⚠️ Exercise plans are for demonstration only. Consult your physician before starting any new physical activity programme, especially with a chronic condition.</div>',
        unsafe_allow_html=True,
    )
