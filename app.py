import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import re

# 📦 Local imports
from resume_parser import extract_resume_text
from utils import match_skills, generate_suggestions

# 🔍 Predefined Job Descriptions per field
JOB_DESCRIPTIONS = {
    "data science": "Python, statistics, machine learning, pandas, numpy, scikit-learn, data visualization, SQL, problem-solving, data cleaning, data storytelling, regression, classification, cloud, Jupyter",
    "web development": "HTML, CSS, JavaScript, React, Angular, Node.js, Express, MongoDB, API development, responsive design, version control (Git), debugging, deployment",
    "mobile app development": "Java, Kotlin, Swift, Flutter, Dart, Android Studio, Xcode, mobile UI/UX, REST APIs, Firebase, push notifications, app store deployment",
    "ui/ux design": "Wireframing, prototyping, user research, Adobe XD, Figma, user testing, design systems, interaction design, usability, visual design",
    "cybersecurity": "Network security, firewalls, penetration testing, threat analysis, encryption, risk assessment, vulnerability scanning, incident response, ethical hacking, compliance",
    "digital marketing": "SEO, SEM, Google Analytics, social media marketing, email marketing, content marketing, PPC, campaign management, branding, copywriting, influencer outreach",
    "ai/machine learning": "Python, machine learning, deep learning, neural networks, TensorFlow, PyTorch, model evaluation, supervised learning, unsupervised learning, computer vision, NLP",
    "cloud computing": "AWS, Azure, Google Cloud, cloud storage, serverless computing, EC2, S3, IAM, cloud security, DevOps integration, monitoring",
    "devops": "CI/CD, Docker, Kubernetes, Jenkins, GitHub Actions, Terraform, Ansible, monitoring (Prometheus, Grafana), logging, cloud infrastructure",
    "software engineering": "Software design patterns, OOP, data structures, algorithms, system design, SDLC, version control, unit testing, debugging, Agile methodologies",
    "business analyst": "Data analysis, requirements gathering, stakeholder communication, SQL, Excel, dashboards, BI tools, user stories, process improvement, documentation",
    "human resources": "Recruitment, onboarding, employee engagement, performance management, HRIS, compliance, training & development, payroll, conflict resolution",
    "sales": "Lead generation, CRM (e.g. Salesforce), client communication, sales pitches, market research, negotiation, cold calling, product demos, KPIs tracking",
    "content writing": "SEO writing, blog writing, copywriting, proofreading, content strategy, research, social media content, WordPress, keyword optimization, editing"
}

# 🎨 Page config
st.set_page_config(page_title="AI Resume Analyzer", page_icon="🧠", layout="centered")

# 🧠 Hero Section
st.markdown("""
    <div style='text-align: center; padding: 20px 0 10px;'>
        <h1 style='color:#4B8BBE;'>🧠 AI Resume Analyzer</h1>
        <p style='font-size:18px; margin-top:-10px;'>Get an intelligent match score and smart resume suggestions.</p>
    </div>
""", unsafe_allow_html=True)

# 📤 Upload & Inputs
with st.container():
    resume_file = st.file_uploader("📄 Upload Your Resume", type=["pdf", "docx"])
    col1, col2 = st.columns(2)
    with col1:
        purpose = st.selectbox("🎯 Applying for", ["Select Purpose", "Internship", "Full-time Job", "Part-time Job", "Freelance"])
    with col2:
        job_field = st.selectbox("💼 Career Field", [
            "Select Career Field", "Data Science", "Web Development", "Mobile App Development", "UI/UX Design",
            "Cybersecurity", "Digital Marketing", "AI/Machine Learning", "Cloud Computing",
            "DevOps", "Software Engineering", "Business Analyst", "Human Resources", "Sales", "Content Writing"
        ])

    # 🤖 Model selector for Ollama
    model_name = st.selectbox("🤖 Ollama Model", ["phi3:mini", "phi3:latest"], index=0)

# 🚀 Analyze Button
if st.button("🚀 Analyze Resume", use_container_width=True):
    if resume_file and purpose != "Select Purpose" and job_field != "Select Career Field":
        with st.spinner("Analyzing your resume..."):
            resume_text = extract_resume_text(resume_file)

            if not resume_text:
                st.error("❌ Could not read your resume. Try uploading a valid PDF or DOCX.")
            else:
                resume_lower = resume_text.lower()
                required_sections = ["education", "skills", "experience", "projects", "summary", "contact"]
                matched_sections = [sec for sec in required_sections if re.search(rf"\b{sec}\b[:\s]?", resume_lower, re.IGNORECASE)]

                word_count = len(resume_text.split())

                # 🧩 Detected Resume Sections
                st.markdown("### 🧩 Detected Resume Sections")
                if matched_sections:
                    st.success(f"✅ Found sections: {', '.join(matched_sections)}")
                else:
                    st.warning("⚠️ No standard sections like Education, Skills, Experience found.")

                # 📊 Structure Score
                structure_score = int((len(matched_sections) / len(required_sections)) * 100)
                st.progress(structure_score, text=f"Resume Structure Score: {structure_score}%")

                if word_count < 100:
                    st.error("⚠️ The document seems too short to be a valid resume. Please upload a more detailed file.")
                else:
                    # ✅ Perform the match using Ollama
                    job_desc = JOB_DESCRIPTIONS.get(job_field.lower().strip(), "")
                    match_result = match_skills(resume_text, job_desc, model=model_name)
                    suggestions = generate_suggestions(resume_text, job_desc, purpose.lower(), model=model_name)
                    score = match_result["score"]

                    # ✅ Score Result Section
                    st.success("✅ Analysis Complete!")
                    st.markdown("### 🎯 Match Score")
                    st.markdown(f"""
                        <div style='text-align:center; padding:10px; border:2px solid #1ABC9C; border-radius:10px; background-color:#ECFDF5;'>
                            <h2 style='color:#1ABC9C; font-size:36px;'>{score}% Match</h2>
                            <p style='margin-top:-10px; font-size:14px;'>Based on your resume and selected field</p>
                        </div>
                    """, unsafe_allow_html=True)


                    # 🧠 Skill Alignment
                    st.markdown("### 🧠 Skill Alignment")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Matched Skills**")
                        ms = match_result.get("matched_skills", [])
                        st.write(", ".join(sorted(set(ms))) if ms else "_None detected_")
                    with col_b:
                        st.markdown("**Missing/Weak Skills**")
                        mis = match_result.get("missing_skills", [])
                        st.write(", ".join(sorted(set(mis))) if mis else "_None detected_")

                    # 💡 Suggestions
                    st.markdown("---")
                    st.markdown("### 💡 How to Improve")
                    if not suggestions:
                        suggestions.append("Your resume looks great! Just make sure it's tailored to the job.")
                    for s in suggestions:
                        st.markdown(f"""<div style='background:#f0f4f8; padding:10px; margin-bottom:5px; border-left: 4px solid #4B8BBE;'>{s}</div>""", unsafe_allow_html=True)

                    # 📥 Downloadable Feedback
                    st.markdown("---")
                    st.markdown("### 📥 Download Report")
                    feedback_text = f"""AI Resume Analyzer Report

Match Score: {score}%
Structure Score: {structure_score}%
Matched Sections: {', '.join(matched_sections)}

Matched Skills: {', '.join(match_result.get("matched_skills", []))}
Missing Skills: {', '.join(match_result.get("missing_skills", []))}

Suggestions:
{chr(10).join([f"- {s}" for s in suggestions])}
"""
                    buffer = BytesIO(feedback_text.encode())
                    st.download_button("⬇️ Download Feedback (TXT)", buffer, file_name="resume_feedback.txt", mime="text/plain")
    else:
        st.warning("⚠️ Please upload your resume and select both purpose and field.")
