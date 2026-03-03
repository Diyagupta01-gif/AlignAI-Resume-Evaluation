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
st.set_page_config(page_title="AlignAI", layout="wide")

st.title("AlignAI - Resume Requirement Evaluation Framework")
st.caption("AI-Powered Skill Gap & KPI-Based Candidate Assessment")

st.divider()

# ---------------- LOAD API ----------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel(
    "gemini-2.5-flash-lite",
    generation_config={
        "temperature": 0.2,
        "max_output_tokens": 600
    }
)

# ---------------- INPUT ----------------
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

with col2:
    job_description = st.text_area("Paste Job Description")

# ---------------- PDF EXTRACTION ----------------
@st.cache_data
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

# ---------------- ANALYSIS ----------------
if st.button("Run Evaluation"):

    if uploaded_file and job_description.strip():

        with st.spinner("Analyzing resume..."):

            uploaded_file.seek(0)
            resume_text = extract_text_from_pdf(uploaded_file)

            # 🔥 Aggressive trimming
            resume_text = resume_text[:1800]
            job_description_trimmed = job_description[:1500]

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

Keep lists short (max 5 items each).

Resume:
{resume_text}

Job Description:
{job_description_trimmed}
"""

            response = model.generate_content(prompt)
            result = response.text.strip()

            if result.startswith("```"):
                result = result.split("```")[1]
            if result.lower().startswith("json"):
                result = result[4:].strip()

            data = json.loads(result)

        # ---------------- PROCESS ----------------
        score = int(data.get("score", 0))
        matched = data.get("matched_keywords", [])
        missing = data.get("missing_keywords", [])

        total_skills = len(matched) + len(missing)
        matched_count = len(matched)
        missing_count = len(missing)
        coverage = int((matched_count / total_skills) * 100) if total_skills > 0 else 0

        if coverage >= 75:
            risk_text = "Low Risk – Strong Alignment"
        elif coverage >= 50:
            risk_text = "Moderate Risk – Partial Alignment"
        else:
            risk_text = "High Risk – Significant Gaps"

        # ---------------- DASHBOARD ----------------
        st.subheader("Evaluation Summary")

        colA, colB, colC, colD = st.columns(4)
        colA.metric("Overall Score", f"{score}/100")
        colB.metric("Coverage %", f"{coverage}%")
        colC.metric("Total Skills", total_skills)
        colD.metric("Risk Level", risk_text)

        st.divider()

        # ---------------- CHART ----------------
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

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Matched Skills")
            for skill in matched:
                st.write(f"- {skill}")

        with col2:
            st.markdown("### Missing Skills")
            for skill in missing:
                st.write(f"- {skill}")

        st.divider()

        st.markdown("### Improvement Suggestions")
        for s in data.get("suggestions", []):
            st.write(f"- {s}")

    else:
        st.warning("Please upload resume and paste job description.")