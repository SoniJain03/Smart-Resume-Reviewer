📄 Smart Resume Reviewer

An LLM-powered web application that reviews resumes and provides tailored, constructive feedback for a specific job role. The tool helps job seekers optimize their resumes by aligning them with job descriptions and industry expectations using the power of Large Language Models (LLMs).

## Goal

To assist job seekers in improving their resumes by:

1. Identifying missing skills & keywords.

2. Suggesting improvements in structure, tone, and clarity.

3. Providing role-specific tailoring for better job alignment.

Offering section-wise, actionable feedback.

## Features

🔹 Resume Upload/Input

  Upload resumes in PDF or text format.

🔹 Job Role & Description

Select a target job role (e.g., Data Scientist, Product Manager).

Paste a job description to guide the review.

🔹 AI Engine: Google's Generative AI API (google-generativeai library) with the gemini-pro model.

Analyzes structure, content, and tone.

Provides feedback on:

1. Missing skills or keywords

2. Formatting & readability improvements

3. Redundant or vague language

4. Tailoring achievements to the target job

5. Assigns section-wise scores (Experience, Skills, Education, etc.).


🔹 Output Format

Clear, structured feedback (section-wise).

Highlighted version of resume (strengths vs. gaps).

Export reviewed resume to PDF and TEXT format.

Exports match report to PDF and text format.

## Tech Stack

Frontend & UI: Streamlit

Backend & Core: Python

AI Engine: Google's Generative AI API (google-generativeai library) with the gemini-pro model.

Libraries:

langchain – LLM orchestration

openai– API/model access

PyMuPDF – PDF parsing

streamlit – User interface

dotenv – Secure environment variables

pydantic, fastapi, typer (optional, structured APIs & CLI)

## Installation & Setup

1. Clone the repository:
    
git clone https://github.com/SoniJain03/Smart-Resume-Reviewer/tree/master
cd smart-resume-reviewer
Create a virtual environment (recommended):

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

2. Install dependencies:

pip install -r requirements.txt

Key dependencies include: streamlit, google-generativeai, PyPDF2, python-dotenv

3. Set up your API key:

Obtain an API key from Google AI Studio.

Create a file named .env in the project root.

4. Add your key to the file:

GOOGLE_API_KEY=your_actual_api_key_here

5. Run the application:

streamlit run app.py

The application will open in your default web browser.
