import streamlit as st
from dotenv import load_dotenv
import os
import openai
from fpdf import FPDF
import json
import speech_recognition as sr
from datetime import datetime
from functools import lru_cache

# Load environment variables
load_dotenv()

# --- Constants & Configurations ---
VALID_KEYS_FILE = os.getenv("VALID_KEYS_FILE", "valid_keys.json")
NHS_TRUSTS = [
    "Barts Health NHS Trust",
    "Manchester University NHS Foundation Trust",
    "Birmingham Women's and Children's NHS FT",
    "Royal Wolverhampton NHS Trust",
    "Leeds Teaching Hospitals NHS Trust",
    "University Hospitals Bristol and Weston NHS Foundation Trust",
    "Nottingham University Hospitals NHS Trust",
    "Sheffield Teaching Hospitals NHS Foundation Trust",
    "Oxford University Hospitals NHS Foundation Trust",
    "University Hospitals of Leicester NHS Trust",
    "Newcastle upon Tyne Hospitals NHS Foundation Trust",
    "East Kent Hospitals University NHS Foundation Trust",
    "Liverpool University Hospitals NHS Foundation Trust"
]
CCG_LIST = [
    "NHS North West London CCG",
    "NHS Bristol, North Somerset and South Gloucestershire CCG",
]
# Templates stored for easy extension
UK_SCENARIO_TEMPLATES = {
    "Geriatrics": {
        "Initial Assessment": {
            "prompt": (
                "Write an initial assessment for a geriatric patient including presenting complaint, "
                "history, medication, and next steps."
            )
        }
    }
}
LETTER_STRUCTURE = {
    "Care Home Complaint": {
        "Neglect": [
            "Describe what happened",
            "When and where did this occur?",
            "What was the outcome or impact?",
        ]
    }
}

# --- Caching ---
@lru_cache(maxsize=None)
def load_valid_keys(path: str) -> set:
    try:
        with open(path, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

# --- Helper Functions ---
def authenticate_user(key: str) -> bool:
    keys = load_valid_keys(VALID_KEYS_FILE)
    return key in keys

def save_draft(document_type: str, content: str) -> str:
    if 'drafts' not in st.session_state:
        st.session_state.drafts = {}
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    draft_key = f"{document_type}_{timestamp}"
    st.session_state.drafts[draft_key] = content
    return draft_key

def load_drafts_sidebar() -> None:
    drafts = st.session_state.get('drafts', {})
    if drafts:
        st.sidebar.subheader("Your Drafts")
        for key, content in drafts.items():
            if st.sidebar.button(key):
                st.session_state.current_draft = content

def transcribe_voice(duration: int = 10) -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(f"Recording for {duration} seconds...")
        audio = recognizer.listen(source, phrase_time_limit=duration)
    try:
        return recognizer.recognize_google(audio, language="en-GB")
    except sr.UnknownValueError:
        st.error("Could not understand audio")
    except sr.RequestError as e:
        st.error(f"API error: {e}")
    return ""

def generate_pdf_from_markdown(title: str, markdown_content: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)
    for line in markdown_content.splitlines():
        pdf.multi_cell(0, 8, line)
    return pdf.output(dest='S').encode('latin-1')

def call_openai(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.5) -> str:
    openai.api_key = st.secrets["openai"]["api_key"]
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content

# --- UI Components ---
def clinical_documentation_mode():
    st.header("🏥 Clinical Documentation")
    nhs_trust = st.selectbox("NHS Trust/CCG", NHS_TRUSTS + CCG_LIST)
    nhs_number = st.text_input("NHS Number (optional)")
    specialty = st.selectbox("Specialty", list(UK_SCENARIO_TEMPLATES.keys()))
    doc_type = st.selectbox("Document Type", list(UK_SCENARIO_TEMPLATES[specialty].keys()))
    template = UK_SCENARIO_TEMPLATES[specialty][doc_type]

    if st.button("🎙️ Record Voice Note"):
        transcription = transcribe_voice()
        st.session_state.last_voice = transcription
        st.text_area("Voice Transcription", value=transcription, height=150)

    details = st.text_area("Clinical Details", value=st.session_state.get('current_draft', ''), height=200)
    if st.button("Generate Document"):
        if specialty == "Geriatrics" and not nhs_number:
            st.warning("Please include NHS Number for geriatric records.")
        else:
           prompt = f"NHS Trust / CCG: {nhs_trust}\\nTemplate: {template['prompt']}\\nDetails: {details}"

Template: {template['prompt']}
Details: {details}"
            with st.spinner("Generating document..."):
                doc = call_openai(prompt)
                key = save_draft(f"{specialty}_{doc_type}", doc)
                st.success(f"Draft saved: {key}")
                st.markdown(doc)

def patient_education_mode():
    st.header("📚 Patient Education")
    topic = st.text_input("Health Topic")
    level = st.select_slider("Reading Level", options=["Simple", "Standard", "Detailed"])
    if st.button("Generate Info Sheet"):
        age_map = {"Simple": 8, "Standard": 12, "Detailed": 16}
        reading_age = age_map[level]
        prompt = (
            f"Create NHS-style patient info about {topic} for reading age {reading_age}: "
            "include key facts, when to seek help, self-care tips, UK helplines."
        )
        with st.spinner("Generating..."):
            markdown = call_openai(prompt)
            pdf_bytes = generate_pdf_from_markdown(f"NHS Info: {topic}", markdown)
            st.markdown(markdown)
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"nhs_{topic.replace(' ', '_')}.pdf",
                mime='application/pdf'
            )

def advocacy_letters_mode():
    st.header("✉️ Advocacy & Complaints")
    category = st.selectbox("Letter Category", list(LETTER_STRUCTURE.keys()))
    issue = st.selectbox("Issue Type", list(LETTER_STRUCTURE.get(category, {})))
    answers = {}
    if issue:
        st.subheader("Provide Details:")
        for q in LETTER_STRUCTURE[category][issue]:
            answers[q] = st.text_area(q)
    user_name = st.text_input("Your Name")
    tone = st.radio("Tone", ["Standard", "Formal"])
    if st.button("Generate Letter"):
        intro = "You are an experienced care quality advocate."
        summary = "
".join(f"{q}: {a}" for q, a in answers.items())
        style = "direct, formal" if tone == "Formal" else "calm, assertive"
        prompt = f"{intro}
Category: {category}
Issue: {issue}
{summary}
Write in a {style} tone. End with Sincerely, {user_name}."
        with st.spinner("Writing letter..."):
            letter = call_openai(prompt, temperature=0.5)
            st.text_area("Letter Preview", value=letter, height=300)

# --- Main Application ---
def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        key = st.text_input("Enter License Key", type="password")
        if key and authenticate_user(key):
            st.session_state.authenticated = True
            st.success("Access granted.")
        else:
            st.warning("Invalid or missing license key.")
            return

    consent = st.sidebar.checkbox("I consent to data processing (GDPR)")
    if not consent:
        st.sidebar.warning("Consent required to proceed.")
        return

    st.sidebar.title("NHS Care Companion")
    load_drafts_sidebar()
    mode = st.sidebar.radio("Mode", [
        "Clinical Documentation",
        "Patient Education",
        "Voice Notes",
        "Advocacy Letters"
    ])

    if mode == "Clinical Documentation":
        clinical_documentation_mode()
    elif mode == "Patient Education":
        patient_education_mode()
    elif mode == "Voice Notes":
        st.header("🎙️ Voice Notes")
        if st.button("Record"):
            transcription = transcribe_voice()
            st.session_state.last_voice = transcription
            st.write(transcription)
        if st.button("Save Note"):
            save_draft("VoiceNote", st.session_state.get('last_voice', ''))
            st.success("Saved.")
    else:
        advocacy_letters_mode()

if __name__ == "__main__":
    main()
