"""Build a comprehensive PDF report for the WellNOVA 3.0 demo.

Uses fpdf2 (core fonts only — ASCII-safe). Returns the PDF as bytes,
ready for st.download_button.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from fpdf import FPDF


# ---------- Helpers ----------
def _ascii(text: str | None) -> str:
    """Strip non-Latin-1 glyphs (emoji, fancy arrows) so core fpdf2 fonts work."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        "✅": "[OK]", "❌": "[X]", "⚠️": "[!]", "→": "->", "•": "-",
        "±": "+/-", "≥": ">=", "≤": "<=", "—": "-", "–": "-",
        "🩺": "", "🥗": "", "🏃": "", "🔥": "", "💪": "", "🍞": "",
        "🥑": "", "🧂": "", "🌿": "", "🟢": "", "🟡": "", "🔴": "",
        "📄": "", "ℹ️": "",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


PRIMARY = (14, 165, 233)
DARK_TEXT = (30, 41, 59)
MUTED = (100, 116, 139)
GREEN = (16, 185, 129)
ORANGE = (245, 158, 11)
RED = (239, 68, 68)


def _tier_color(tier: str) -> tuple[int, int, int]:
    return {
        "Low": GREEN,
        "Moderate": ORANGE,
        "High": (249, 115, 22),
        "Critical": RED,
    }.get(tier, MUTED)


class WellNOVAPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*PRIMARY)
        self.cell(0, 8, "WellNOVA 3.0 - Personalised Health Report", ln=True, align="L")
        self.set_draw_color(*PRIMARY)
        self.set_line_width(0.4)
        self.line(10, 18, 200, 18)
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MUTED)
        self.cell(
            0, 10,
            f"WellNOVA 3.0 - IIT Kharagpur - Page {self.page_no()}",
            align="C",
        )

    # convenience helpers -------------------------------------------------
    def section_title(self, text: str) -> None:
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*DARK_TEXT)
        self.cell(0, 8, _ascii(text), ln=True)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def kv_row(self, label: str, value: str) -> None:
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*MUTED)
        self.cell(60, 6, _ascii(label))
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_TEXT)
        self.cell(0, 6, _ascii(value), ln=True)


# ---------- Page builders ----------
def _add_cover(pdf: WellNOVAPDF, psv: dict[str, Any]) -> None:
    pdf.add_page()
    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*PRIMARY)
    pdf.cell(0, 14, "WellNOVA 3.0", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 8, "Personalised Chronic Disease Management Report", ln=True, align="C")
    pdf.ln(12)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*DARK_TEXT)
    pdf.cell(0, 8, "Patient Profile", ln=True, align="C")
    pdf.ln(4)

    demo = psv.get("demographics", {})
    prefs = psv.get("preferences", {})
    pdf.set_font("Helvetica", "", 11)
    rows = [
        ("Date of Assessment", date.today().isoformat()),
        ("Age", f"{demo.get('age')} years"),
        ("Sex", str(demo.get("sex"))),
        ("Height", f"{demo.get('height_cm')} cm"),
        ("Weight", f"{demo.get('weight_kg')} kg"),
        ("BMI", f"{demo.get('bmi')} kg/m^2"),
        ("Fitness Level", str(prefs.get("fitness_level"))),
        ("Cuisine Preference", str(prefs.get("cuisine_preference"))),
        ("Dietary Restrictions",
         ", ".join(prefs.get("dietary_restrictions", []) or ["None"])),
        ("Severity Tier", str(psv.get("severity_tier", "N/A"))),
    ]
    for label, value in rows:
        pdf.kv_row(label, value)


def _add_risk_dashboard(pdf: WellNOVAPDF, risk_payload: dict[str, Any]) -> None:
    pdf.add_page()
    pdf.section_title("1. Health Risk Dashboard")

    risk = risk_payload.get("risk_data", {})
    tiers = risk.get("tiers", {})
    clinical = risk_payload.get("clinical", {})

    # risk score table
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 8, "Condition", border=1, fill=True)
    pdf.cell(40, 8, "Risk Score", border=1, fill=True, align="C")
    pdf.cell(40, 8, "Severity Tier", border=1, fill=True, align="C", ln=True)

    pdf.set_text_color(*DARK_TEXT)
    pdf.set_font("Helvetica", "", 10)
    for label, key in [
        ("Type 2 Diabetes", "diabetes"),
        ("Hypertension", "hypertension"),
        ("Cardiovascular Disease", "cvd"),
    ]:
        score = risk.get(key, 0)
        tier = tiers.get(key, "Low")
        pdf.cell(70, 8, label, border=1)
        pdf.cell(40, 8, f"{score}/100", border=1, align="C")
        r, g, b = _tier_color(tier)
        pdf.set_text_color(r, g, b)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 8, tier, border=1, align="C", ln=True)
        pdf.set_text_color(*DARK_TEXT)
        pdf.set_font("Helvetica", "", 10)
    pdf.ln(6)

    # interpretations
    interp = clinical.get("interpretations", {})
    for label, key in [
        ("Diabetes", "diabetes"),
        ("Hypertension", "hypertension"),
        ("Cardiovascular", "cvd"),
    ]:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(0, 6, _ascii(f"{label} interpretation"), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 5, _ascii(interp.get(key, "-")))
        pdf.ln(2)

    # ICD codes
    icd_codes = clinical.get("icd_codes", []) or []
    if icd_codes:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(0, 6, "Top ICD-11 Predictions", ln=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(230, 240, 250)
        pdf.cell(30, 7, "Code", border=1, fill=True)
        pdf.cell(120, 7, "Description", border=1, fill=True)
        pdf.cell(30, 7, "Confidence", border=1, fill=True, align="C", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for c in icd_codes[:5]:
            pdf.cell(30, 7, _ascii(c.get("code", "")), border=1)
            pdf.cell(120, 7, _ascii(c.get("description", "")), border=1)
            pdf.cell(30, 7, f"{c.get('confidence', 0):.1f}%", border=1, align="C", ln=True)

    # key risk factors
    factors = clinical.get("key_risk_factors", []) or []
    if factors:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "Top Contributing Risk Factors", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for f in factors[:6]:
            pdf.cell(
                0, 5,
                _ascii(
                    f"- {f.get('biomarker', '?')}: {f.get('value', '?')} "
                    f"{f.get('unit', '')} ({f.get('impact', '?')} impact)"
                ),
                ln=True,
            )


def _add_meal_plan(pdf: WellNOVAPDF, meal_plan: dict[str, Any]) -> None:
    pdf.add_page()
    pdf.section_title("2. 7-Day Personalised Meal Plan")
    ccr = meal_plan.get("ccr_percentage", 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*GREEN)
    pdf.cell(0, 6, _ascii(f"Clinical Compliance Rate (CCR): {ccr:.1f}%"), ln=True)
    pdf.ln(2)

    pdf.set_text_color(*DARK_TEXT)
    for day in meal_plan.get("week", []) or []:
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(0, 7, _ascii(day.get("day", "")), ln=True)
        pdf.set_text_color(*DARK_TEXT)

        # header row
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(230, 240, 250)
        widths = [28, 70, 14, 14, 14, 14, 18, 14]
        headers = ["Meal", "Dish", "Cal", "Carbs", "Prot", "Fat", "Sodium", "Fibre"]
        for w, h in zip(widths, headers):
            pdf.cell(w, 6, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_font("Helvetica", "", 8)
        for m in day.get("meals", []) or []:
            row = [
                m.get("meal_type", ""),
                m.get("dish_name", ""),
                str(m.get("calories", "")),
                f"{m.get('carbs_g', '')}g",
                f"{m.get('protein_g', '')}g",
                f"{m.get('fat_g', '')}g",
                f"{m.get('sodium_mg', '')}mg",
                f"{m.get('fibre_g', '')}g",
            ]
            for w, val in zip(widths, row):
                pdf.cell(w, 6, _ascii(val)[: int(w / 1.6)], border=1)
            pdf.ln()
        # totals
        totals = day.get("daily_totals", {}) or {}
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(245, 245, 245)
        totals_row = [
            "Daily Totals", "",
            str(totals.get("calories", "")),
            f"{totals.get('carbs_g', '')}g",
            f"{totals.get('protein_g', '')}g",
            f"{totals.get('fat_g', '')}g",
            f"{totals.get('sodium_mg', '')}mg",
            f"{totals.get('fibre_g', '')}g",
        ]
        for w, val in zip(widths, totals_row):
            pdf.cell(w, 6, _ascii(val), border=1, fill=True)
        pdf.ln(8)

    notes = meal_plan.get("clinical_notes")
    if notes:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 5, _ascii(f"Clinical notes: {notes}"))


def _add_exercise_plan(pdf: WellNOVAPDF, exercise_plan: dict[str, Any]) -> None:
    pdf.add_page()
    pdf.section_title("3. 7-Day Exercise Schedule")
    escr = exercise_plan.get("escr_percentage", 0)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*GREEN)
    pdf.cell(
        0, 6,
        _ascii(f"Exercise Safety Compliance Rate (ESCR): {escr:.1f}%"),
        ln=True,
    )
    pdf.ln(2)

    pdf.set_text_color(*DARK_TEXT)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(230, 240, 250)
    widths = [22, 56, 18, 22, 14, 58]
    headers = ["Day", "Exercise", "Duration", "Intensity", "MET", "HR Zone"]
    for w, h in zip(widths, headers):
        pdf.cell(w, 7, h, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    for day in exercise_plan.get("week", []) or []:
        row = [
            day.get("day", ""),
            day.get("exercise_name", ""),
            f"{day.get('duration_minutes', 0)} min",
            day.get("intensity", ""),
            f"{day.get('met_value', 0)}",
            day.get("target_hr_zone", ""),
        ]
        for w, val in zip(widths, row):
            pdf.cell(w, 6, _ascii(val)[: int(w / 1.6)], border=1)
        pdf.ln()
    pdf.ln(4)

    # contraindications
    contras = exercise_plan.get("contraindications_applied", []) or []
    if contras:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "Contraindications Applied", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for c in contras:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5, _ascii(f"- {c}"))
        pdf.ln(2)

    summary = exercise_plan.get("weekly_summary")
    if summary:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MUTED)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 5, _ascii(f"Weekly summary: {summary}"))


def _add_disclaimer(pdf: WellNOVAPDF) -> None:
    pdf.add_page()
    pdf.section_title("Clinical Disclaimer")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK_TEXT)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        pdf.epw, 6,
        _ascii(
            "This report was generated by WellNOVA 3.0, an AI-powered research prototype "
            "developed at IIT Kharagpur. The risk scores are computed using a deterministic "
            "rule-based heuristic for demonstration; the production system uses an XGBoost "
            "model trained on NHANES data. Meal and exercise plans are generated by a large "
            "language model with clinical constraint prompting.\n\n"
            "This tool is intended for academic and research demonstration only. It is NOT a "
            "substitute for professional medical advice, diagnosis, or treatment. Always seek "
            "the advice of your physician or other qualified health provider with any questions "
            "you may have regarding a medical condition.\n\n"
            "Do not retain personal data through this tool: no information is stored on the "
            "WellNOVA server beyond the active session."
        ),
    )
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(
        0, 5,
        "Developed by Satyajit Behera (21AG3EP15) - Supervised by Dr. Ram Babu Roy",
        ln=True, align="C",
    )
    pdf.cell(0, 5, "IIT Kharagpur - Spring 2025-26", ln=True, align="C")


# ---------- Public entry point ----------
def build_pdf(
    psv: dict[str, Any],
    risk_payload: dict[str, Any],
    meal_plan: dict[str, Any],
    exercise_plan: dict[str, Any],
) -> bytes:
    pdf = WellNOVAPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    _add_cover(pdf, psv)
    _add_risk_dashboard(pdf, risk_payload)
    _add_meal_plan(pdf, meal_plan)
    _add_exercise_plan(pdf, exercise_plan)
    _add_disclaimer(pdf)
    out = pdf.output(dest="S")
    # fpdf2 returns bytearray; coerce to bytes for st.download_button
    return bytes(out)
