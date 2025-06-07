# --- Elite-Level NHS Care Companion + Letter Generator ---
# Fully Integrated Streamlit App with 4 Modes:
# 1. Clinical Documentation
# 2. Patient Education
# 3. Voice Notes
# 4. Advocacy & Complaint Letter Generator

import streamlit as st
import os
import json
import openai
from dotenv import load_dotenv
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
import speech_recognition as sr
from functools import lru_cache

# --- Load environment variables ---
load_dotenv()

# --- Page Configuration & Custom Styling ---
st.set_page_config(page_title="NHS Care Companion", page_icon="🩺", layout="wide")
st.markdown(
    """
    <style>
    .sidebar .sidebar-content { background-color: #f0f4f8; }
    .stButton>button { border-radius: 8px; padding: 0.5rem 1rem; }
    .stDownloadButton>button { background-color: #005eb8; color: white; }
    </style>
    """, unsafe_allow_html=True
)

# --- Constants & Configurations ---
VALID_KEYS_FILE = "valid_keys.json"
NHS_TRUSTS = [
    "Barts Health NHS Trust",
    "Manchester University NHS Foundation Trust",
    "Birmingham Women's and Children's NHS FT",
    "Royal Wolverhampton NHS Trust",
    "Walsall Healthcare NHS Trust",
    "Sandwell and West Birmingham Hospitals NHS Trust",
    "University Hospitals Birmingham NHS Foundation Trust",
    "Dudley Group NHS Foundation Trust",
    "Shrewsbury and Telford Hospital NHS Trust",
    "South Staffordshire and Shropshire Healthcare NHS Foundation Trust"
]
CCG_LIST = [
    "NHS Black Country ICB",
    "NHS Birmingham and Solihull ICB",
    "NHS Staffordshire and Stoke-on-Trent ICB",
    "NHS North West London CCG",
    "NHS Bristol, North Somerset and South Gloucestershire CCG"
]

# --- Full Letter Templates (LETTER_STRUCTURE is assumed to be defined earlier in your full code) ---
# Replace this placeholder with the complete LETTER_STRUCTURE from your working version
LETTER_STRUCTURE = {
    "Care Complaint Letter": {
        "Neglect or injury": [
            "Who was harmed?",
            "Where did it happen?",
            "What happened?",
            "What was the result?",
            "Have you raised this already?"
        ],
        "Medication errors": [
            "What medication issue occurred — wrong dose, missed dose, or something else?",
            "Where and when did this happen, if you know?",
            "Who was affected by the error?",
            "What was done about it at the time, if anything?",
            "What do you feel should happen now as a result?"
        ],
        "Staff conduct": [
            "What happened?",
            "Who was involved?",
            "Was this one-time or ongoing?",
            "What was the impact?",
            "Have you spoken to the provider?"
        ]
    },
    "Family Advocacy Letter": {
        "Request a meeting": [
            "Who do you want to meet with?",
            "What is the purpose of the meeting?",
            "Any preferred dates/times?",
            "Is this urgent or routine?"
        ],
        "Disagree with discharge": [
            "Who is being discharged?",
            "What are your concerns?",
            "What support is missing?",
            "Have you spoken to the discharge team?"
        ]
    },
    "Referral Support Letter": {
        "Request community support": [
            "What support do you believe is needed?",
            "Who is the individual needing it?",
            "Have they had this support before?",
            "Why now?"
        ]
    },
    "Thank You & Positive Feedback": {
        "Praise for a staff member": [
            "What did they do well?",
            "When and where?",
            "What impact did it have?",
            "Do you want management to be notified?"
        ]
    },
    "Hospital & Discharge": {
        "Discharge objection": [
            "What discharge is being planned?",
            "Why is it not safe/suitable?",
            "Have you communicated with the ward?",
            "What would be a better plan?"
        ]
    },
    "Other Letters": {
        "Safeguarding concern": [
            "What concern do you want to report?",
            "Who is at risk?",
            "When and where did this happen?",
            "Have you contacted the safeguarding team?"
        ]
    },
    "Escalation & Regulatory": {
        "Raise formal concern with CQC": [
            "What concern do you want CQC to investigate?",
            "Where is the setting and who is affected?",
            "Is this a single incident or ongoing pattern?",
            "Have you tried resolving this locally first?"
        ]
    },
    "Delays & Practical Barriers": {
        "Chase delayed referral or appointment": [
            "Who is waiting for what (referral/test/support)?",
            "How long has the delay been?",
            "What impact is the delay having?",
            "Have you contacted the provider already?"
        ]
    }
}
    # Continue with full letter structure as needed...
}

# --- Utility Functions ---
@lru_cache(maxsize=None)
def load_valid_keys(path: str) -> set:
    try:
        with open(path, 'r') as f:
            return set(json.load(f))
    except Exception:
        return set()

def authenticate_user():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        key = st.sidebar.text_input("🔐 License Key", type="password")
        valid = load_valid_keys(VALID_KEYS_FILE)
        if key and key in valid:
            st.session_state.authenticated = True
            st.sidebar.success("Access granted.")
        else:
            st.sidebar.warning("Invalid or missing key.")
            st.stop()

def consent_check():
    if not st.sidebar.checkbox("I consent to data processing (GDPR)"):
        st.sidebar.warning("Consent required.")
        st.stop()

def save_draft(doc_type: str, content: str) -> str:
    drafts = st.session_state.setdefault('drafts', {})
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dk = f"{doc_type}_{timestamp}"
    drafts[dk] = content
    return dk

def load_drafts_sidebar():
    drafts = st.session_state.get('drafts', {})
    if drafts:
        st.sidebar.subheader("📄 Your Drafts")
        for k in drafts:
            if st.sidebar.button(k, key=k):
                st.session_state.current_draft = drafts[k]

def transcribe_voice(duration: int = 10) -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(f"Recording for {duration}s...")
        audio = recognizer.listen(source, phrase_time_limit=duration)
    try:
        return recognizer.recognize_google(audio, language='en-GB')
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return ""

def generate_pdf(title: str, content: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(8)
    pdf.set_font("Arial", size=12)
    for line in content.splitlines():
        pdf.multi_cell(0, 8, line)
    return pdf.output(dest='S').encode('latin-1')

def generate_prompt(category, subcategory, answers, user_name, tone):
    ctx = f"Category: {category}\nIssue: {subcategory}\n"
    summary = "\n".join(f"{q}: {a}" for q,a in answers.items() if a.strip())
    if tone == "Serious Formal Complaint":
        style = "formal, cite CQC standards and duty of care"
        temp = 0.3
    else:
        style = "calm, assertive"
        temp = 0.7
    closing = f"\n\nSincerely,\n{user_name}"
    prompt = f"You are an experienced health advocate. {ctx}{summary}\nWrite in a {style} tone.{closing}"
    return prompt, temp

# --- Mode Functions ---
def clinical_documentation():
    st.header("🏥 Clinical Documentation")
    trust = st.selectbox("NHS Trust/CCG", NHS_TRUSTS + CCG_LIST)
    nhs_num = st.text_input("NHS Number")
    details = st.text_area("Clinical Details", height=200, value=st.session_state.get('current_draft', ''))
    if st.button("🎤 Record Voice Note"):
        st.session_state.voice = transcribe_voice()
    if st.session_state.get('voice'):
        st.text_area("Voice Transcript", value=st.session_state.voice, height=150)
    if st.button("Generate Document"):
        prompt = f"Trust: {trust}\nNHS Number: {nhs_num}\nDetails: {details}"
        with st.spinner("Generating document..."):
            rsp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}], temperature=0.5
            )
            doc = rsp.choices[0].message.content
        key = save_draft("ClinicalDoc", doc)
        st.success(f"Saved draft: {key}")
        st.markdown(doc)

def patient_education():
    st.header("📚 Patient Education")
    topic = st.text_input("Health Topic")
    level = st.select_slider("Reading Level", options=["Simple", "Standard", "Detailed"])
    if st.button("Generate Info Sheet"):
        age = {"Simple":8,"Standard":12,"Detailed":16}[level]
        prompt = f"Create NHS-style info on {topic} for reading age {age}: include key facts, self-care tips, UK helplines." 
        with st.spinner("Generating info sheet..."):
            rsp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}], temperature=0.5
            )
            sheet = rsp.choices[0].message.content
        st.markdown(sheet)
        pdf = generate_pdf(f"Info: {topic}", sheet)
        st.download_button("Download PDF", data=pdf, file_name=f"info_{topic.replace(' ','_')}.pdf")

def voice_notes():
    st.header("🎙️ Voice Notes")
    if st.button("Record 10s"): st.session_state.voice = transcribe_voice()
    transcript = st.session_state.get('voice', '')
    if transcript:
        st.text_area("Transcript", value=transcript, height=150)
        if st.button("Save Transcript"):
            key = save_draft("VoiceNote", transcript)
            st.success(f"Saved: {key}")

def advocacy_letters():
    st.header("✉️ Advocacy & Complaint Letters")
    category = st.selectbox("Category", list(LETTER_STRUCTURE.keys()))
    subcat = st.selectbox("Issue", list(LETTER_STRUCTURE[category].keys()))
    answers = {q: st.text_area(q) for q in LETTER_STRUCTURE[category][subcat]}
    name = st.text_input("Your Name")
    tone = st.radio("Tone", ["Standard", "Serious Formal Complaint"])
    if st.button("Generate Letter"):
        prompt, temp = generate_prompt(category, subcat, answers, name, tone)
        with st.spinner("Generating letter..."):
            rsp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}], temperature=temp
            )
            letter = rsp.choices[0].message.content
        key = save_draft("Letter", letter)
        st.success(f"Saved draft: {key}")
        st.text_area("Generated Letter", value=letter, height=300)

# --- App Entry Point ---
def main():
    authenticate_user()
    consent_check()
    load_drafts_sidebar()
    mode = st.sidebar.radio("Mode", ["Clinical Docs", "Patient Education", "Voice Notes", "Advocacy Letters"] )
    if mode == "Clinical Docs":
        clinical_documentation()
    elif mode == "Patient Education":
        patient_education()
    elif mode == "Voice Notes":
        voice_notes()
    else:
        advocacy_letters()

if __name__ == "__main__":
    main()
