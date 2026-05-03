"""Multi-step intake wizard for WellNOVA 3.0."""
from __future__ import annotations

from typing import Any

import streamlit as st

from modules.utils import DEMO_PATIENT, biomarker_status, compute_bmi, status_badge_html


# ---------- Step indicator HTML ----------
def _step_indicator(current: int) -> str:
    steps = ["Symptoms", "Vitals", "Preferences"]
    parts: list[str] = []
    for i, label in enumerate(steps, start=1):
        if i < current:
            cls = "done"
            icon = "✓"
        elif i == current:
            cls = "active"
            icon = str(i)
        else:
            cls = ""
            icon = str(i)
        parts.append(
            f'<div style="text-align:center">'
            f'<div class="step-dot {cls}">{icon}</div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:4px">{label}</div>'
            f"</div>"
        )
        if i < len(steps):
            line_cls = "done" if i < current else ""
            parts.append(f'<div class="step-line {line_cls}"></div>')

    inner = "".join(parts)
    return f'<div class="step-indicator" style="align-items:flex-start">{inner}</div>'


def _progress_bar(current: int) -> None:
    pct = int((current / 3) * 100)
    st.progress(pct)
    st.markdown(_step_indicator(current), unsafe_allow_html=True)


# ---------- Status-coloured number input label ----------
def _field_label(display: str, key: str, value: float | None) -> str:
    if value is not None and value != 0:
        status = biomarker_status(key, value)
        badge = status_badge_html(status)
        return f"{display} {badge}"
    return display


# ---------- Step 1 — Symptoms ----------
def _step1() -> None:
    st.subheader("Step 1 — Describe Your Symptoms")
    vitals = st.session_state.vitals

    symptoms = st.text_area(
        "Describe your symptoms in your own words",
        value=st.session_state.get("symptoms", ""),
        height=140,
        placeholder=(
            "e.g., I have been feeling unusually thirsty, blurry vision, "
            "and tired most of the day."
        ),
    )
    st.session_state.symptoms = symptoms

    st.file_uploader(
        "Upload Lab Report PDF (optional — simulated extraction in demo)",
        type=["pdf"],
        key="lab_pdf",
    )
    if st.session_state.get("lab_pdf"):
        st.info(
            "Lab report received. In the production system, Clinical-T5 + Tesseract OCR "
            "would extract biomarker values automatically. For this demo the values you "
            "enter below are used."
        )

    col_back, col_next = st.columns([1, 3])
    with col_next:
        if st.button("Next →  Health Vitals", use_container_width=True):
            st.session_state.step = 2
            st.rerun()


# ---------- Step 2 — Health Vitals ----------
def _step2() -> None:
    st.subheader("Step 2 — Health Vitals")
    st.caption(
        "Colour-coded: "
        '<span class="field-status status-normal">Normal</span> '
        '<span class="field-status status-borderline">Borderline</span> '
        '<span class="field-status status-abnormal">Abnormal</span>',
        unsafe_allow_html=True,
    )

    v: dict[str, Any] = st.session_state.vitals

    left, right = st.columns(2)

    with left:
        v["age"] = st.number_input(
            "Age (years)", min_value=18, max_value=90,
            value=int(v.get("age", 40)), step=1,
        )
        v["sex"] = st.selectbox(
            "Sex", ["Male", "Female"],
            index=0 if v.get("sex", "Male") == "Male" else 1,
        )
        v["height_cm"] = st.number_input(
            "Height (cm)", min_value=140.0, max_value=220.0,
            value=float(v.get("height_cm", 170.0)), step=0.5,
        )
        v["weight_kg"] = st.number_input(
            "Weight (kg)", min_value=30.0, max_value=200.0,
            value=float(v.get("weight_kg", 70.0)), step=0.5,
        )

        bmi = compute_bmi(v["height_cm"], v["weight_kg"])
        bmi_status = biomarker_status("bmi", bmi)
        st.markdown(
            f"**BMI** (auto-calculated): **{bmi}** kg/m² "
            + status_badge_html(bmi_status),
            unsafe_allow_html=True,
        )

        fbg_val = float(v.get("fbg", 90.0))
        st.markdown(
            _field_label("Fasting Blood Glucose (mg/dL)", "fbg", fbg_val),
            unsafe_allow_html=True,
        )
        v["fbg"] = st.number_input(
            "fbg", label_visibility="collapsed",
            min_value=70.0, max_value=400.0,
            value=fbg_val, step=1.0, key="inp_fbg",
        )

        hba1c_val = float(v.get("hba1c", 5.0))
        st.markdown(
            _field_label("HbA1c (%)", "hba1c", hba1c_val),
            unsafe_allow_html=True,
        )
        v["hba1c"] = st.number_input(
            "hba1c", label_visibility="collapsed",
            min_value=4.0, max_value=14.0,
            value=hba1c_val, step=0.1, format="%.1f", key="inp_hba1c",
        )

        sbp_val = float(v.get("sbp", 120.0))
        st.markdown(
            _field_label("Systolic BP (mmHg)", "sbp", sbp_val),
            unsafe_allow_html=True,
        )
        v["sbp"] = st.number_input(
            "sbp", label_visibility="collapsed",
            min_value=80.0, max_value=220.0,
            value=sbp_val, step=1.0, key="inp_sbp",
        )

    with right:
        dbp_val = float(v.get("dbp", 80.0))
        st.markdown(
            _field_label("Diastolic BP (mmHg)", "dbp", dbp_val),
            unsafe_allow_html=True,
        )
        v["dbp"] = st.number_input(
            "dbp", label_visibility="collapsed",
            min_value=50.0, max_value=140.0,
            value=dbp_val, step=1.0, key="inp_dbp",
        )

        chol_val = float(v.get("cholesterol", 180.0))
        st.markdown(
            _field_label("Total Cholesterol (mg/dL)", "cholesterol", chol_val),
            unsafe_allow_html=True,
        )
        v["cholesterol"] = st.number_input(
            "cholesterol", label_visibility="collapsed",
            min_value=100.0, max_value=400.0,
            value=chol_val, step=1.0, key="inp_chol",
        )

        ldl_val = float(v.get("ldl", 100.0))
        st.markdown(
            _field_label("LDL (mg/dL)", "ldl", ldl_val),
            unsafe_allow_html=True,
        )
        v["ldl"] = st.number_input(
            "ldl", label_visibility="collapsed",
            min_value=40.0, max_value=300.0,
            value=ldl_val, step=1.0, key="inp_ldl",
        )

        hdl_val = float(v.get("hdl", 55.0))
        st.markdown(
            _field_label("HDL (mg/dL)", "hdl", hdl_val),
            unsafe_allow_html=True,
        )
        v["hdl"] = st.number_input(
            "hdl", label_visibility="collapsed",
            min_value=20.0, max_value=100.0,
            value=hdl_val, step=1.0, key="inp_hdl",
        )

        creat_val = float(v.get("creatinine", 1.0))
        st.markdown(
            _field_label("Creatinine (mg/dL)", "creatinine", creat_val),
            unsafe_allow_html=True,
        )
        v["creatinine"] = st.number_input(
            "creatinine", label_visibility="collapsed",
            min_value=0.5, max_value=10.0,
            value=creat_val, step=0.1, format="%.1f", key="inp_creat",
        )

        hr_val = float(v.get("resting_hr", 72.0))
        st.markdown(
            _field_label("Resting Heart Rate (bpm)", "resting_hr", hr_val),
            unsafe_allow_html=True,
        )
        v["resting_hr"] = st.number_input(
            "resting_hr", label_visibility="collapsed",
            min_value=40.0, max_value=120.0,
            value=hr_val, step=1.0, key="inp_hr",
        )

    st.session_state.vitals = v

    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Next →  Preferences", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


# ---------- Step 3 — Preferences ----------
def _step3() -> None:
    st.subheader("Step 3 — Fitness & Dietary Preferences")
    p: dict[str, Any] = st.session_state.preferences

    fitness_options = ["Beginner", "Intermediate", "Advanced"]
    fitness_desc = {
        "Beginner": "New to exercise — mostly sedentary",
        "Intermediate": "Active 3–4 days/week",
        "Advanced": "Athletic — 5+ days/week",
    }
    current_fitness = p.get("fitness_level", "Beginner")
    fitness_idx = fitness_options.index(current_fitness) if current_fitness in fitness_options else 0
    chosen_fitness = st.radio(
        "Fitness Level",
        fitness_options,
        index=fitness_idx,
        format_func=lambda x: f"{x} — {fitness_desc[x]}",
        horizontal=True,
    )
    p["fitness_level"] = chosen_fitness

    restrictions = st.multiselect(
        "Dietary Restrictions",
        ["Vegetarian", "Vegan", "Gluten-Free", "Lactose-Free", "Nut Allergy"],
        default=p.get("dietary_restrictions", []),
    )
    p["dietary_restrictions"] = restrictions

    cuisine_options = ["South Indian", "North Indian", "Mediterranean", "Pan-Asian", "Continental"]
    current_cuisine = p.get("cuisine_preference", "South Indian")
    cuisine_idx = cuisine_options.index(current_cuisine) if current_cuisine in cuisine_options else 0
    p["cuisine_preference"] = st.selectbox(
        "Cuisine Preference",
        cuisine_options,
        index=cuisine_idx,
    )

    p["additional_notes"] = st.text_input(
        "Any additional notes (optional)",
        value=p.get("additional_notes", ""),
        placeholder="e.g., prefer low-spice meals, knee injury",
    )

    st.session_state.preferences = p

    col_back, col_analyse = st.columns([1, 3])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_analyse:
        if st.button("🔬 Analyse My Health", use_container_width=True):
            st.session_state.trigger_analysis = True
            st.rerun()


# ---------- Public entry point ----------
def render_intake_form() -> None:
    step = st.session_state.get("step", 1)

    # Demo patient loader
    col_demo, _ = st.columns([2, 5])
    with col_demo:
        if st.button("⚡ Load Demo Patient", use_container_width=True, help="Pre-fills all fields with a realistic patient profile"):
            dp = DEMO_PATIENT
            st.session_state.symptoms = dp["symptoms"]
            st.session_state.vitals = {
                "age": dp["age"],
                "sex": dp["sex"],
                "height_cm": dp["height_cm"],
                "weight_kg": dp["weight_kg"],
                "fbg": dp["fbg"],
                "hba1c": dp["hba1c"],
                "sbp": dp["sbp"],
                "dbp": dp["dbp"],
                "cholesterol": dp["cholesterol"],
                "ldl": dp["ldl"],
                "hdl": dp["hdl"],
                "creatinine": dp["creatinine"],
                "resting_hr": dp["resting_hr"],
            }
            st.session_state.preferences = {
                "fitness_level": dp["fitness_level"],
                "dietary_restrictions": dp["dietary_restrictions"],
                "cuisine_preference": dp["cuisine_preference"],
                "additional_notes": dp["additional_notes"],
            }
            st.session_state.step = 1
            st.rerun()

    st.markdown("---")
    _progress_bar(step)

    if step == 1:
        _step1()
    elif step == 2:
        _step2()
    elif step == 3:
        _step3()
