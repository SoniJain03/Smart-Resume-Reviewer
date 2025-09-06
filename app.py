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

# -------------------- Streamlit Layout Configuration -------------------- #
st.set_page_config(
    page_title="Smart Resume Reviewer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to fix layout issues
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 95%;
    }
    .stTextArea textarea {
        min-height: 150px;
    }
    .css-1d391kg {
        padding: 1rem;
    }
    /* Prevent horizontal overflow */
    .element-container {
        overflow-wrap: break-word;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------- Load Environment & API Configuration -------------------- #
load_dotenv()

# Get API key from environment variables or Streamlit secrets
def get_api_key():
    # First try to get from Streamlit secrets (for cloud deployment)
    if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
        return st.secrets['GOOGLE_API_KEY']
    
    # Then try to get from environment variables (for local development)
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return api_key
    
    # If neither works, return None
    return None

# Configure Gemini with the API key
api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("❌ Google API key not found. Please set GOOGLE_API_KEY in your environment variables or Streamlit secrets.")

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
        try:
            # Reset the file pointer to beginning
            uploaded_file.seek(0)
            
            # Use pypdf with the file object directly
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""
    else:
        return ""

def safe_extract_pdf_text(uploaded_file):
    try:
        return extract_pdf_text(uploaded_file)
    except Exception as e:
        st.error(f"Error extracting PDF text: {e}")
        return ""

def get_gemini_response(input_prompt, resume_text, additional_prompt):
    # Check if API key is configured
    if not api_key:
        return "❌ Error: Google API key not configured. Please set GOOGLE_API_KEY in your environment variables or Streamlit secrets."
    
    try:
        # Truncate very long resume text to avoid token limits
        if len(resume_text) > 10000:
            resume_text = resume_text[:10000] + "... [truncated for length]"
        
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        full_prompt = f"{input_prompt}\nResume Content:\n{resume_text}\nAdditional Context:\n{additional_prompt}"
        response = model.generate_content(contents=[{"text": full_prompt}])
        return response.text
    except Exception as e:
        return f"❌ Error calling Gemini API: {str(e)}"

def save_review_as_pdf(review_text, filename="Resume_Review.pdf"):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Add a Unicode font that supports special characters
        try:
            # Try to use DejaVuSans which supports Unicode
            pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
            pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
            pdf.set_font("DejaVu", "", 12)
        except:
            # Fallback to Arial if DejaVu not available
            pdf.set_font("Arial", "", 12)
        
        # Header with bold font
        try:
            pdf.set_font("DejaVu", "B", 16)
        except:
            pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Smart Resume Reviewer", ln=True, align="C")
        
        try:
            pdf.set_font("DejaVu", "", 12)
        except:
            pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "Developed by: Soni Jain & Srishti Vats", ln=True, align="C")
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True, align="C")
        pdf.ln(10)
        
        # Clean the text of unsupported characters
        import unicodedata
        cleaned_text = ''.join(
            c for c in review_text 
            if unicodedata.category(c)[0] != 'C' or c in '\n\t\r'
        )
        
        # Add the cleaned text
        pdf.multi_cell(0, 10, cleaned_text)
        
        pdf.output(filename)
        return filename
    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        # Fallback: create a simple text file instead
        try:
            with open(filename.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
                f.write(review_text)
            return filename.replace('.pdf', '.txt')
        except:
            return "error.txt"
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
    match_percentage = round((len(matched_keywords) / len(jd_keywords)) * 100, 2) if jd_keywords else 0
    
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
                st.text_area("Resume Content", resume_text_review, height=200, key="resume_preview_1")
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

    if st.button("Analyze Resume Review"):
        if uploaded_file_review and job_description_review.strip():
            # Create placeholder for results to ensure they always show
            result_placeholder = st.empty()
            download_placeholder = st.container()
            
            try:
                with st.spinner("Analyzing the resume with AI..."):
                    resume_text_review = safe_extract_pdf_text(uploaded_file_review)
                    if not resume_text_review:
                        st.error("Failed to extract text from PDF")
                        
                    review_prompt = """
                    You are an experienced HR with Tech Experience in Data Science, Full Stack Development, Big Data Engineering, or DevOps.
                    Review the provided resume against the job description. Highlight strengths, weaknesses, and alignment with the role.
                    Do NOT provide any numerical match percentage.
                    """
                    response = get_gemini_response(review_prompt, resume_text_review, job_description_review)
                    time.sleep(1)
                
                # Display results
                result_placeholder.success("✅ Analysis Complete")
                st.subheader("Resume Review Response:")
                
                # Use expandable container for long responses
                with st.expander("View Analysis Results", expanded=True):
                    st.write(response)
                
                # DOWNLOAD BUTTONS - Always show these even if there was an error
                with download_placeholder:
                    col1, col2 = st.columns(2)
                    try:
                        pdf_file = save_review_as_pdf(response)
                        with col1:
                            st.download_button(
                                "Download Review as PDF", 
                                open(pdf_file, "rb").read() if pdf_file != "error.pdf" else b"", 
                                file_name=pdf_file, 
                                mime="application/pdf",
                                key="pdf_download_1"
                            )
                        with col2:
                            st.download_button(
                                "Download Review as TXT", 
                                response, 
                                file_name="Resume_Review.txt", 
                                mime="text/plain",
                                key="txt_download_1"
                            )
                    except Exception as e:
                        st.error(f"Error creating download files: {e}")
                        
            except Exception as e:
                st.error(f"Error during analysis: {e}")
                # Still show download buttons even if analysis failed
                with download_placeholder:
                    st.warning("Analysis failed, but you can try to download any partial results")
                    st.download_button(
                        "Download Error Report", 
                        f"Error: {str(e)}", 
                        file_name="analysis_error.txt", 
                        mime="text/plain",
                        key="error_download_1"
                    )
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
            # Create placeholder for results to ensure they always show
            result_placeholder = st.empty()
            download_placeholder = st.container()
            
            try:
                with st.spinner("Analyzing resume match with AI..."):
                    resume_text_match = safe_extract_pdf_text(uploaded_file_match)
                    if not resume_text_match:
                        st.error("Failed to extract text from PDF")
                        
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
                    response = get_gemini_response(match_prompt, resume_text_match, job_description_match)
                    time.sleep(1)
                
                # Display results
                result_placeholder.success("✅ Match Analysis Complete")
                st.subheader("Resume Match Response:")
                
                # Use expandable container for long responses
                with st.expander("View Match Analysis Results", expanded=True):
                    st.write(response)
                
                # DOWNLOAD BUTTONS - Always show these
                with download_placeholder:
                    col1, col2 = st.columns(2)
                    try:
                        pdf_file = save_review_as_pdf(response, "Resume_Match_Report.pdf")
                        with col1:
                            st.download_button(
                                "Download Match Report as PDF", 
                                open(pdf_file, "rb").read() if pdf_file != "error.pdf" else b"", 
                                file_name=pdf_file, 
                                mime="application/pdf",
                                key="pdf_download_2"
                            )
                        with col2:
                            st.download_button(
                                "Download Match Report as TXT", 
                                response, 
                                file_name="Resume_Match.txt", 
                                mime="text/plain",
                                key="txt_download_2"
                            )
                    except Exception as e:
                        st.error(f"Error creating download files: {e}")
                        
            except Exception as e:
                st.error(f"Error during match analysis: {e}")
                # Still show download buttons even if analysis failed
                with download_placeholder:
                    st.warning("Analysis failed, but you can try to download any partial results")
                    st.download_button(
                        "Download Error Report", 
                        f"Error: {str(e)}", 
                        file_name="match_error.txt", 
                        mime="text/plain",
                        key="error_download_2"
                    )
        else:
            st.warning("Please upload the resume and enter the job description.")
