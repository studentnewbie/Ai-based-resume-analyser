import os
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
import pdfplumber

# Load environment variables
load_dotenv()

# Configure Google Gemini AI using environment variable GEMINI_API_KEY
genai.configure(api_key="AIzaSyBCMBf0VF1C7WS2tPO6FyKX_R7qcpJXgDs")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        # Direct text extraction using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"Direct text extraction failed: {e}")

    # Fallback to OCR for image-based PDFs
    print("Falling back to OCR for image-based PDF.")
    try:
        images = convert_from_path(pdf_path)
        for image in images:
            text += pytesseract.image_to_string(image) + "\n"
    except Exception as e:
        print(f"OCR failed: {e}")

    return text.strip()

# Function to analyze resume using Gemini AI
def analyze_resume(resume_text, job_description=None):
    if not resume_text:
        return {"error": "Resume text is required for analysis."}
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    base_prompt = f"""
    You are an experienced HR professional. Analyze the resume and provide:
    1. Strengths and weaknesses.
    2. Missing key skills for the role.
    3. Suggested certifications or courses with source links.
    4. Alternative career paths.
    5. ATS compatibility check.
    6. ATS Score (x/100).
    7. Job match percentage (if a job description is provided).
    8. Job description match score (x/100).
    9. Resume score (x/100).
    10. Mock interview questions based on the given job description.
    Resume:
    {resume_text}
    """
    
    if job_description:
        base_prompt += f"""
        Job Description:
        {job_description}
        """
    
    response = model.generate_content(base_prompt)
    return response.text.strip()

# Function to get interview feedback from Gemini AI
def get_interview_feedback(question, answer):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an expert interview coach. Evaluate the following answer to the interview question and provide constructive feedback with suggestions for improvement.
    Question: {question}
    Answer: {answer}
    Feedback:"""
    response = model.generate_content(prompt)
    return response.text.strip()

# Initialize Streamlit app
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")
st.title("AI Resume Analyzer")
st.write("Analyze your resume and prepare for interviews using AI.")

# File uploader and job description input
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
with col2:
    job_description = st.text_area("Enter Job Description:", placeholder="Paste the job description here...")

if uploaded_file:
    st.success("Resume uploaded successfully!")
    # Save uploaded file locally
    with open("uploaded_resume.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    resume_text = extract_text_from_pdf("uploaded_resume.pdf")
    
    if st.button("Analyze Resume"):
        with st.spinner("Analyzing resume..."):
            try:
                analysis = analyze_resume(resume_text, job_description)
                st.success("Analysis complete!")
                st.session_state['analysis_report'] = analysis
            except Exception as e:
                st.error(f"Analysis failed: {e}")
else:
    st.warning("Please upload a resume in PDF format.")

st.markdown("---")

# Bottom colored boxes for Analysis Report and Mock Interview
col1, col2 = st.columns(2)
with col1:
    if st.button("📊 Analysis Report", help="View detailed resume analysis"):
        if st.session_state.get('analysis_report'):
            st.write(st.session_state['analysis_report'])
        else:
            st.info("No analysis available. Please analyze your resume first.")
with col2:
    if st.button("🤖 Mock Interview", help="Start a mock interview"):
        st.session_state['chat_active'] = True
        # Initialize interview session state variables if not already set
        if 'interview_questions' not in st.session_state:
            st.session_state['interview_questions'] = [
                "Tell me about yourself.",
                "What are your greatest strengths?",
                "What are your weaknesses?",
                "Why do you want this job?",
                "Describe a challenging situation at work and how you handled it.",
                "How do you handle tight deadlines?",
                "Can you provide an example of a time when you worked effectively in a team?",
                "How do you keep up with industry trends?",
                "Why should we hire you?",
                "Where do you see yourself in five years?"
            ]
        if 'current_question_index' not in st.session_state:
            st.session_state['current_question_index'] = 0
        if 'interview_feedback' not in st.session_state:
            st.session_state['interview_feedback'] = []

# Mock Interview Chat Section
if st.session_state.get('chat_active', False):
    st.subheader("Mock Interview Chat")
    
    questions = st.session_state['interview_questions']
    current_index = st.session_state['current_question_index']
    
    if current_index < len(questions):
        current_question = questions[current_index]
        st.write(f"**Question {current_index+1}:** {current_question}")
        answer = st.text_input("Your answer:", key=f"answer_{current_index}")
        if st.button("Submit Answer", key=f"submit_{current_index}"):
            if answer.strip() == "":
                st.warning("Please provide an answer before submitting.")
            else:
                feedback = get_interview_feedback(current_question, answer)
                st.session_state['interview_feedback'].append({
                    "question": current_question,
                    "answer": answer,
                    "feedback": feedback
                })
                st.success("Feedback:")
                st.write(feedback)
                st.session_state['current_question_index'] += 1
                st.experimental_rerun()  # Refresh to load the next question
    else:
        st.write("### Mock Interview Completed")
        st.write("Here is a summary of your interview:")
        for idx, qa in enumerate(st.session_state['interview_feedback'], start=1):
            st.write(f"**Question {idx}:** {qa['question']}")
            st.write(f"**Your Answer:** {qa['answer']}")
            st.write(f"**Feedback:** {qa['feedback']}")
        if st.button("Restart Interview"):
            # Reset interview session state for a new session
            st.session_state['current_question_index'] = 0
            st.session_state['interview_feedback'] = []
            st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown(
    """<p style='text-align: center;'>Powered by <b>Streamlit</b> and <b>Google Gemini AI</b> | Developed by 
    <a href="https://www.linkedin.com/in/dutta-sujoy/" target="_blank" style="text-decoration: none; color: #FFFFFF">
    <b>Sujoy Dutta</b></a></p>""",
    unsafe_allow_html=True
)
