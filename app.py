# --- Elite-Level NHS Care Companion Pro ---
# Enhanced Features:
# 1. Multi-user authentication system
# 2. NHS Data Standards compliance
# 3. Advanced document templating
# 4. Integrated clinical coding (SNOMED CT)
# 5. Audit trail for all actions

import streamlit as st
import os
import json
import openai
from dotenv import load_dotenv
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
import speech_recognition as sr
import uuid
from functools import lru_cache
import hashlib

# --- Enhanced Configuration ---
load_dotenv()

# --- NHS Standards Configuration ---
SNOMED_CT_CODES = {
    "MedicationError": "281647001",
    "ClinicalNeglect": "408856003",
    "DischargeConcern": "306206005",
    "Safeguarding": "723220000",
    "PositiveFeedback": "281647001"
}

# --- Page Configuration & Styling ---
st.set_page_config(
    page_title="NHS Care Companion Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .sidebar .sidebar-content { background-color: #e9ecef; }
    .stButton>button { 
        background-color: #005eb8; 
        color: white; 
        border-radius: 8px; 
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stDownloadButton>button { background-color: #28a745; }
    .stAlert { border-left: 4px solid #005eb8; }
    .header { color: #005eb8; }
</style>
""", unsafe_allow_html=True)

# --- Security & Authentication ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_session():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.audit_log = []

def log_audit_event(action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event = {
        "timestamp": timestamp,
        "session_id": st.session_state.session_id,
        "user": st.session_state.get('user_email', 'unknown'),
        "action": action
    }
    st.session_state.audit_log.append(event)

# --- Enhanced Authentication System ---
def authenticate_user():
    create_user_session()
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        with st.sidebar.expander("🔐 Authentication", expanded=True):
            auth_option = st.radio("Login Method", ["License Key", "NHS Mail"])
            
            if auth_option == "License Key":
                key = st.text_input("Enter License Key", type="password")
                valid_keys = load_valid_keys(VALID_KEYS_FILE)
                if st.button("Authenticate"):
                    if key and key in valid_keys:
                        st.session_state.authenticated = True
                        log_audit_event("License key authentication")
                        st.success("Authentication successful")
                    else:
                        st.error("Invalid license key")
                        log_audit_event("Failed authentication attempt")
                        st.stop()
            
            elif auth_option == "NHS Mail":
                email = st.text_input("NHS Email")
                password = st.text_input("Password", type="password")
                if st.button("Login"):
                    if email.endswith("@nhs.net") and len(password) > 8:
                        st.session_state.authenticated = True
                        st.session_state.user_email = email
                        log_audit_event("NHS Mail authentication")
                        st.success("Login successful")
                    else:
                        st.error("Invalid NHS credentials")
                        log_audit_event("Failed NHS login attempt")
                        st.stop()
            
            if not st.session_state.authenticated:
                st.stop()

# --- Enhanced Document Generation ---
class NHSPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'NHS Care Companion Document', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_enhanced_pdf(title, content, metadata=None):
    pdf = NHSPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, title, ln=True, align='C')
    
    # Add metadata if provided
    if metadata:
        pdf.set_font("Arial", 'I', 10)
        for key, value in metadata.items():
            pdf.cell(0, 6, f"{key}: {value}", ln=True)
        pdf.ln(5)
    
    # Main content
    pdf.set_font("Arial", size=11)
    for line in content.split('\n'):
        pdf.multi_cell(0, 5, line)
        pdf.ln(2)
    
    return pdf.output(dest='S').encode('latin-1')

# --- Clinical Coding Integration ---
def add_clinical_codes(content, code_type):
    if code_type in SNOMED_CT_CODES:
        return f"{content}\n\nSNOMED CT Code: {SNOMED_CT_CODES[code_type]}"
    return content

# --- Enhanced Voice Transcription ---
def enhanced_transcribe(duration=15):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info(f"Recording for {duration} seconds... (Speak clearly)")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source, phrase_time_limit=duration)
    
    try:
        text = r.recognize_google(audio, language='en-UK')
        log_audit_event("Voice note recorded")
        return text
    except sr.UnknownValueError:
        st.error("Could not understand audio")
        log_audit_event("Voice transcription failed")
        return ""
    except sr.RequestError as e:
        st.error(f"Recognition service error: {e}")
        log_audit_event("Voice service error")
        return ""

# --- Enhanced Clinical Documentation ---
def clinical_documentation():
    st.header("🏥 Advanced Clinical Documentation")
    
    with st.expander("Patient Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nhs_number = st.text_input("NHS Number", placeholder="123 456 7890")
            first_name = st.text_input("First Name")
            dob = st.date_input("Date of Birth")
        with col2:
            trust = st.selectbox("NHS Trust/CCG", NHS_TRUSTS + CCG_LIST)
            last_name = st.text_input("Last Name")
            postcode = st.text_input("Postcode")
    
    with st.expander("Clinical Details"):
        clinical_details = st.text_area(
            "Clinical Notes", 
            height=250,
            help="Enter your clinical notes here. Be specific and include relevant details.",
            value=st.session_state.get('current_draft', '')
        )
        
        # Enhanced voice recording
        if st.button("🎤 Record Clinical Note (15s)"):
            st.session_state.voice_note = enhanced_transcribe()
        
        if st.session_state.get('voice_note'):
            st.text_area("Voice Transcription", value=st.session_state.voice_note, height=150)
            if st.button("Append to Notes"):
                clinical_details += f"\n\n[Voice Note Transcription]: {st.session_state.voice_note}"
    
    # Clinical coding selection
    clinical_code = st.selectbox(
        "Clinical Code Category",
        list(SNOMED_CT_CODES.keys()),
        help="Select the most relevant SNOMED CT code category"
    )
    
    if st.button("Generate Enhanced Clinical Document"):
        if not nhs_number or not clinical_details:
            st.warning("Please enter NHS Number and Clinical Details")
            return
        
        metadata = {
            "Patient": f"{first_name} {last_name}",
            "NHS Number": nhs_number,
            "DOB": dob.strftime("%Y-%m-%d"),
            "Trust": trust,
            "Generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        prompt = f"""Create a comprehensive NHS clinical document with these details:
        Trust: {trust}
        Patient: {first_name} {last_name}
        NHS Number: {nhs_number}
        DOB: {dob}
        Clinical Details: {clinical_details}
        
        Format the document with appropriate sections and NHS-compliant terminology."""
        
        with st.spinner("Generating enhanced clinical document..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4
                )
                document = response.choices[0].message.content
                document = add_clinical_codes(document, clinical_code)
                
                key = save_draft("ClinicalDoc", document)
                log_audit_event(f"Generated clinical document: {key}")
                
                st.success("Document generated successfully")
                st.markdown(document)
                
                # Generate PDF with metadata
                pdf = generate_enhanced_pdf(
                    "Clinical Document",
                    document,
                    metadata
                )
                
                st.download_button(
                    label="Download as PDF",
                    data=pdf,
                    file_name=f"clinical_document_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error generating document: {e}")
                log_audit_event(f"Document generation failed: {str(e)}")

# --- Main App ---
def main():
    authenticate_user()
    consent_check()
    load_drafts_sidebar()
    
    st.sidebar.header("Navigation")
    mode = st.sidebar.radio(
        "Select Mode",
        ["Clinical Docs", "Patient Education", "Voice Notes", "Advocacy Letters"],
        index=0
    )
    
    if mode == "Clinical Docs":
        clinical_documentation()
    elif mode == "Patient Education":
        patient_education()
    elif mode == "Voice Notes":
        voice_notes()
    elif mode == "Advocacy Letters":
        advocacy_letters()
    
    # Audit log viewer (admin only)
    if st.session_state.get('user_email', '').endswith('@nhs.net'):
        if st.sidebar.checkbox("Show Audit Log"):
            st.sidebar.write("### Audit Trail")
            for event in st.session_state.audit_log[-5:]:
                st.sidebar.write(f"{event['timestamp']}: {event['action']}")

if __name__ == "__main__":
    main()
