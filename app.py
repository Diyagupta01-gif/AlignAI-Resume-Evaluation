import streamlit as st
import os
import io
import json
import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AlignAI - Resume Evaluation System",
    layout="wide"
)

# ---------------- CUSTOM STYLING ----------------
st.markdown("""
    <style>
        .main {
            background-color: #f4f6f9;
        }
        .kpi-card {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
        }
        .risk-low {color: green; font-weight: bold;}
        .risk-moderate {color: orange; font-weight: bold;}
        .risk-high {color: red; font-weight: bold;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
col_logo, col_title = st.columns([1, 6])

with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)

with col_title:
    st.markdown("## AlignAI - Resume Requirement Evaluation Framework")
    st.caption("AI-Powered Skill Gap & KPI-Based Candidate Assessment System")

st.divider()

# ---------------- LOAD API ----------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- FILE UPLOAD ----------------
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

with col2:
    job_description = st.text_area("Paste Job Description")

# ---------------- PDF EXTRACTION ----------------
def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf_bytes = uploaded_file.read()
    pdf_stream = io.BytesIO(pdf_bytes)

    with pdfplumber.open(pdf_stream) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted
    return text

# ---------------- ANALYZE ----------------
if st.button("Run Evaluation"):

    if uploaded_file and job_description.strip():

        uploaded_file.seek(0)
        resume_text = extract_text_from_pdf(uploaded_file)

        prompt = f"""
Return ONLY valid JSON:
{{
  "score": number,
  "matched_keywords": [],
  "missing_keywords": [],
  "strengths": [],
  "weaknesses": [],
  "suggestions": []
}}

Resume:
{resume_text}

Job Description:
{job_description}
"""

        response = model.generate_content(prompt)
        result = response.text.strip()

        if result.startswith("```"):
            result = result.split("```")[1]
        if result.lower().startswith("json"):
            result = result[4:].strip()

        data = json.loads(result)

        score = int(data.get("score", 0))
        matched = data.get("matched_keywords", [])
        missing = data.get("missing_keywords", [])

        total_skills = len(matched) + len(missing)
        matched_count = len(matched)
        missing_count = len(missing)
        coverage = int((matched_count / total_skills) * 100) if total_skills > 0 else 0

        if coverage >= 75:
            risk_text = "Low Risk – Strong Alignment"
            risk_class = "risk-low"
        elif coverage >= 50:
            risk_text = "Moderate Risk – Partial Alignment"
            risk_class = "risk-moderate"
        else:
            risk_text = "High Risk – Significant Gaps"
            risk_class = "risk-high"

        st.divider()
        st.subheader("KPI Dashboard")

        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Overall Score", f"{score}/100")
        k2.metric("Coverage %", f"{coverage}%")
        k3.metric("Total Skills", total_skills)
        k4.markdown(f"<p class='{risk_class}'>Risk: {risk_text}</p>", unsafe_allow_html=True)

        st.divider()

        st.subheader("Skill Gap Visualization")

        df = pd.DataFrame({
            "Category": ["Matched", "Missing"],
            "Count": [matched_count, missing_count]
        })

        fig, ax = plt.subplots()
        ax.bar(df["Category"], df["Count"])
        ax.set_ylabel("Number of Skills")
        ax.set_title("Skill Gap Analysis")

        st.pyplot(fig)

        st.divider()

        colA, colB = st.columns(2)

        with colA:
            st.markdown("### Matched Skills")
            for skill in matched:
                st.write(f"- {skill}")

        with colB:
            st.markdown("### Missing Skills")
            for skill in missing:
                st.write(f"- {skill}")

        st.divider()

        st.markdown("### Improvement Suggestions")
        for s in data.get("suggestions", []):
            st.write(f"- {s}")

        report = f"""
ALIGNAI - ATS EVALUATION REPORT
--------------------------------
Overall Score: {score}/100
Coverage: {coverage}%
Risk Level: {risk_text}

Matched Skills:
{chr(10).join(matched)}

Missing Skills:
{chr(10).join(missing)}
"""

        st.download_button(
            label="Download Business Report",
            data=report,
            file_name="AlignAI_Report.txt",
            mime="text/plain"
        )

    else:
        st.warning("Please upload resume and paste job description.")

st.divider()
st.caption("© 2026 AlignAI | Business Requirement Evaluation System")