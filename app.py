from dotenv import load_dotenv
import os
import pypdf
import google.generativeai as genai
import streamlit as st
from fpdf import FPDF
import time
from datetime import datetime
import re
from collections import Counter

# -------------------- Load Environment -------------------- #
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# -------------------- Helper Functions -------------------- #

# Enhanced skill/abbreviation normalization dictionary
SKILL_MAP = {
    "ml": "machine learning", "machine learning": "machine learning",
    "ai": "artificial intelligence", "artificial intelligence": "artificial intelligence",
    "dl": "deep learning", "deep learning": "deep learning",
    "ds": "data science", "data science": "data science",
    "nlp": "natural language processing", "natural language processing": "natural language processing",
    "r programming": "r", "r": "r",
    "python": "python", "py": "python",
    "sql": "sql", "mysql": "sql", "postgresql": "sql",
    "aws": "aws", "amazon web services": "aws",
    "hadoop": "hadoop",
    "spark": "spark", "apache spark": "spark",
    "tableau": "tableau",
    "power bi": "power bi", "powerbi": "power bi",
    "excel": "excel", "microsoft excel": "excel",
    "java": "java", "javascript": "javascript", "js": "javascript",
    "react": "react", "react.js": "react", "reactjs": "react",
    "node": "node.js", "node.js": "node.js", "nodejs": "node.js",
    "docker": "docker", "kubernetes": "kubernetes", "k8s": "kubernetes",
    "git": "git", "github": "github", "gitlab": "gitlab",
    "agile": "agile", "scrum": "scrum",
}

# Synonym mapping for soft skills
SOFT_SKILL_SYNONYMS = {
    "problem solving": ["critical thinking", "analytical thinking", "decision making", "troubleshooting"],
    "teamwork": ["collaboration", "team player", "team collaboration", "working with others"],
    "communication": ["presenting", "reporting", "explaining", "written communication", "verbal communication"],
    "leadership": ["managing", "supervising", "guiding", "mentoring"],
    "time management": ["organization", "planning", "prioritization"],
}

def normalize_text(text):
    """Normalize text for better matching"""
    text = text.lower()
    # Remove punctuation and extra spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_pdf_text(uploaded_file):
    if uploaded_file is not None:
        # Change from PyPDF2.PdfReader to pypdf.PdfReader
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    else:
        raise FileNotFoundError("No file uploaded")

def get_gemini_response(input_prompt, resume_text, additional_prompt):
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    full_prompt = f"{input_prompt}\nResume Content:\n{resume_text}\nAdditional Context:\n{additional_prompt}"
    response = model.generate_content(contents=[{"text": full_prompt}])
    return response.text

def save_review_as_pdf(review_text, filename="Resume_Review.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Smart Resume Reviewer", ln=True, align="C")
    pdf.set_font("DejaVu", "", 12)
    pdf.cell(0, 10, "Developed by: Soni Jain & Srishti Vats", ln=True, align="C")
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("DejaVu", "", 12)
    for line in review_text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

# -------------------- Improved Keyword Matching -------------------- #

def extract_keywords_from_jd(job_description):
    """Extract relevant keywords from job description"""
    # Normalize the job description
    jd_normalized = normalize_text(job_description)
    
    # Extract potential keywords (words that are likely skills or requirements)
    words = jd_normalized.split()
    
    # Look for multi-word phrases and technical terms
    keywords = set()
    
    # Check for known skills (2-3 word phrases)
    for skill in SKILL_MAP.keys():
        if len(skill.split()) > 1 and skill in jd_normalized:
            keywords.add(skill)
    
    # Check for single word technical terms
    technical_terms = ['python', 'sql', 'java', 'javascript', 'react', 'node', 'aws', 
                      'docker', 'kubernetes', 'git', 'agile', 'scrum', 'tableau', 'excel']
    
    for term in technical_terms:
        if term in jd_normalized:
            keywords.add(term)
    
    # Add education and experience keywords
    experience_terms = ['bachelor', 'master', 'phd', 'degree', 'years experience', 
                       'experience with', 'knowledge of', 'proficient in']
    
    for term in experience_terms:
        if term in jd_normalized:
            keywords.add(term)
    
    return list(keywords)

def calculate_match_percentage(resume_text, job_description):
    """Calculate match percentage with improved algorithm"""
    resume_normalized = normalize_text(resume_text)
    jd_normalized = normalize_text(job_description)
    
    # Extract keywords from job description
    jd_keywords = extract_keywords_from_jd(job_description)
    
    if not jd_keywords:
        return 0, set()
    
    # Count matches
    matched_keywords = set()
    
    for keyword in jd_keywords:
        # Check for exact match
        if keyword in resume_normalized:
            matched_keywords.add(keyword)
            continue
        
        # Check for skill map equivalents
        if keyword in SKILL_MAP:
            normalized_skill = SKILL_MAP[keyword]
            if normalized_skill in resume_normalized:
                matched_keywords.add(keyword)
                continue
        
        # Check for soft skill synonyms
        for main_skill, synonyms in SOFT_SKILL_SYNONYMS.items():
            if keyword in synonyms or keyword == main_skill:
                for syn in synonyms + [main_skill]:
                    if syn in resume_normalized:
                        matched_keywords.add(keyword)
                        break
    
    # Calculate percentage
    match_percentage = round((len(matched_keywords) / len(jd_keywords)) * 100, 2)
    
    return match_percentage, matched_keywords

def highlight_keywords(resume_text, keywords):
    """Highlight matched keywords in resume text"""
    highlighted_text = resume_text
    for kw in keywords:
        # Escape special characters for regex
        kw_escaped = re.escape(kw)
        # Use regex to find whole words only
        pattern = r'\b' + kw_escaped + r'\b'
        highlighted_text = re.sub(pattern, f"**{kw}**", highlighted_text, flags=re.IGNORECASE)
    return highlighted_text

# -------------------- Streamlit App -------------------- #

st.set_page_config(page_title="Smart Resume Reviewer", layout="wide")
st.title("📄 Smart Resume Reviewer")

# Sidebar
st.sidebar.header("About")
st.sidebar.info(
    """
    **Smart Resume Reviewer** uses AI (Google Gemini) to analyze your resume
    against a given job description.  

    **Features:**
    - Highlights strengths and weaknesses of your resume
    - Provides keyword insights
    - Generates downloadable PDF and TXT reports

    **Developed by:** Soni Jain & Srishti Vats
    """
)

tab1, tab2 = st.tabs(["Resume Review", "Resume Match"])

# -------------------- Resume Review Tab -------------------- #
with tab1:
    st.subheader("Resume Review Analysis")
    uploaded_file_review = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="review_upload")
    job_description_review = st.text_area("Job Description:", key="review_job", height=150)

    if uploaded_file_review:
        try:
            resume_text_review = extract_pdf_text(uploaded_file_review)
            with st.expander("Preview Resume Text"):
                st.text_area("Resume Content", resume_text_review, height=200)
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

    if st.button("Analyze Resume Review"):
        if uploaded_file_review and job_description_review.strip():
            try:
                resume_text_review = extract_pdf_text(uploaded_file_review)
                review_prompt = """
                You are an experienced HR professional with Tech Experience in Data Science, 
                Full Stack Development, Big Data Engineering, and DevOps.
                
                Please review the provided resume against the job description. Provide:
                1. Key strengths and alignment with the role
                2. Areas for improvement or missing elements
                3. Specific suggestions to better tailor the resume
                4. Overall assessment of fit for the position
                
                Do NOT provide any numerical match percentage.
                Be specific and provide actionable advice.
                """
                with st.spinner("Analyzing the resume with AI..."):
                    response = get_gemini_response(review_prompt, resume_text_review, job_description_review)
                    time.sleep(1)
                st.success("✅ Analysis Complete")
                st.subheader("Resume Review Response:")
                st.write(response)
                
                # Save and offer download
                pdf_file = save_review_as_pdf(response)
                st.download_button("Download Review as PDF", open(pdf_file, "rb").read(), 
                                 file_name=pdf_file, mime="application/pdf")
                st.download_button("Download Review as TXT", response, 
                                 file_name="Resume_Review.txt", mime="text/plain")
            except Exception as e:
                st.error(f"Error during analysis: {e}")
        else:
            st.warning("Please upload the resume and enter the job description.")

# -------------------- Resume Match Tab -------------------- #
with tab2:
    st.subheader("Resume Match Analysis")
    uploaded_file_match = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="match_upload")
    job_description_match = st.text_area("Job Description:", key="match_job", height=150)

    if uploaded_file_match and job_description_match.strip():
        try:
            resume_text_match = extract_pdf_text(uploaded_file_match)
            match_percentage, matched_keywords = calculate_match_percentage(resume_text_match, job_description_match)
            
            # Display match percentage with color coding
            if match_percentage >= 70:
                color = "green"
            elif match_percentage >= 40:
                color = "orange"
            else:
                color = "red"
            
            st.metric("Resume Match Percentage", f"{match_percentage}%", 
                     delta_color="off", help="Based on keyword matching with job description")
            
            # Show matched keywords
            if matched_keywords:
                st.subheader("Matched Keywords:")
                cols = st.columns(3)
                for i, keyword in enumerate(sorted(matched_keywords)):
                    cols[i % 3].success(f"✓ {keyword}")
            
            # Show highlighted resume
            highlighted_resume = highlight_keywords(resume_text_match, matched_keywords)
            with st.expander("Preview Resume Text with Highlighted Keywords"):
                st.markdown(highlighted_resume)
                
        except Exception as e:
            st.error(f"Error processing files: {e}")

    if st.button("Analyze Match"):
        if uploaded_file_match and job_description_match.strip():
            try:
                resume_text_match = extract_pdf_text(uploaded_file_match)
                match_prompt = """
                You are a skilled ATS (Applicant Tracking System) scanner and HR professional.
                Evaluate the resume against the job description and provide:
                
                1. Missing keywords and skills from the job description
                2. Specific suggestions to improve ATS compatibility
                3. Strengths and alignment with the role
                4. Final thoughts and recommendations
                
                Do NOT provide any numerical match percentage.
                Focus on actionable insights and specific improvements.
                """
                with st.spinner("Analyzing resume match with AI..."):
                    response = get_gemini_response(match_prompt, resume_text_match, job_description_match)
                    time.sleep(1)
                st.success("✅ Match Analysis Complete")
                st.subheader("Resume Match Response:")
                st.write(response)
                
                # Save and offer download
                pdf_file = save_review_as_pdf(response, "Resume_Match_Report.pdf")
                st.download_button("Download Match Report as PDF", open(pdf_file, "rb").read(), 
                                 file_name=pdf_file, mime="application/pdf")
                st.download_button("Download Match Report as TXT", response, 
                                 file_name="Resume_Match.txt", mime="text/plain")
            except Exception as e:
                st.error(f"Error during analysis: {e}")
        else:
            st.warning("Please upload the resume and enter the job description.")
