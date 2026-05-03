# WellNOVA 3.0 — Streamlit Demo

> **Intelligent Chronic Disease Management** — Diagnosis. Diet. Movement.
> Research demo developed at **IIT Kharagpur**, Spring 2025-26.

A public-facing Streamlit application that simulates the full WellNOVA 3.0 pipeline:

1. **Module 1 — Diagnosis.** Symptom + 14-biomarker intake → deterministic risk scoring (Type 2 Diabetes, Hypertension, CVD) + LLM-generated ICD-11 mapping and SHAP-style biomarker attribution.
2. **Module 2 — Diet.** 7-day personalised meal plan generated against a Structured Dietary Protocol (SDP) with cuisine-aware recipes and per-meal macro tracking.
3. **Module 3 — Movement.** Condition-aware 7-day exercise schedule applying FITT principles, MET caps, and contraindication rules.

A downloadable PDF report compiles all three modules into a single document.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/<yourusername>/wellnova-demo.git
cd wellnova-demo/wellnova_demo

# 2. Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Set the Gemini API key (optional — see "Mock mode" below)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml and paste your key

# 4. Run
streamlit run app.py
```

Open the URL Streamlit prints (typically http://localhost:8501).

### Mock mode

If `GEMINI_API_KEY` is not set, the app runs in **mock mode**: every module returns a deterministic, hand-crafted output so the entire UI can be evaluated without a key. A banner in the sidebar makes the active mode obvious.

---

## Public deployment (Streamlit Community Cloud)

1. Push the repo to **public** GitHub.
2. Go to <https://share.streamlit.io> → **New app**.
3. Pick the repo, branch `main`, and the file `wellnova_demo/app.py`.
4. In the **Secrets** tab paste:
   ```toml
   GEMINI_API_KEY = "AIza-YOUR_KEY_HERE"
   ```
5. **Deploy.** A public URL is generated, e.g. `https://wellnova-demo.streamlit.app`.

> Free tier of Gemini (`gemini-1.5-flash`) is plenty for evaluation: 15 req/min, 1500 req/day.

---

## Project structure

```
wellnova_demo/
├── app.py                       # Streamlit entry point
├── requirements.txt
├── .streamlit/
│   ├── config.toml              # dark theme
│   └── secrets.toml.example     # template for the Gemini key
├── modules/
│   ├── utils.py                 # BMI, ranges, demo patient, Gemini wrapper
│   ├── risk_engine.py           # Module 1
│   ├── diet_engine.py           # Module 2
│   ├── exercise_engine.py       # Module 3
│   └── pdf_export.py            # fpdf2 report builder
├── ui/
│   ├── hero.py
│   ├── intake_form.py           # 3-step wizard
│   ├── risk_dashboard.py
│   ├── meal_plan.py
│   └── exercise_plan.py
└── styles/
    └── main.css                 # injected via st.markdown
```

---

## Architecture notes

- **LLM backend.** `google-generativeai` (`gemini-1.5-flash`), `temperature=0.3`, `response_mime_type="application/json"`. Three system prompts (`SYSTEM_PROMPT_MODULE{1,2,3}`) live next to their respective engine modules.
- **Risk scoring is deterministic.** No ML model is loaded in the demo; the rule-based scoring functions in `modules/risk_engine.py` reproduce the published thresholds for HbA1c, FBG, BP, lipids, BMI, and age. The production system uses an XGBoost model trained on NHANES data.
- **Patient State Vector (PSV).** `build_patient_state_vector()` in `utils.py` assembles the canonical input that flows into Modules 2 and 3 — visible in a collapsible JSON panel inside the dashboard for transparency.
- **Mock mode.** Every engine module contains a deterministic `_mock_*` builder, used automatically when `GEMINI_API_KEY` is missing or a Gemini call fails. This guarantees the demo never breaks during a presentation.

---

## Demo limitations

- Risk scoring is rule-based; the production model is XGBoost (AUC > 0.89 on NHANES).
- ICD mapping and clinical narrative are LLM-generated; production uses Llama-3-Med + FAISS RAG.
- PDF lab parsing is simulated — the production system uses Tesseract OCR + Clinical-T5.
- No data is persisted: refreshing clears the session.

---

## Credits

- **Student:** Satyajit Behera (21AG3EP15)
- **Supervisor:** Dr. Ram Babu Roy
- **Departments:** Agricultural & Food Engineering · Entrepreneurship & Innovation Engineering
- **Institute:** IIT Kharagpur

> ⚠️ This tool is for academic demonstration purposes only and does not constitute medical advice.
