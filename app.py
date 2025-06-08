import json
import streamlit as st
from openai import OpenAI
from typing import Dict, List, Optional
import datetime
import os

# --- CONSTANTS ---
VALID_KEYS_FILE = "valid_keys.json"
LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Russian": "ru",
    "Chinese (Simplified)": "zh",
    "Japanese": "ja",
    "Arabic": "ar"
}

# Initialize valid keys file if it doesn't exist
if not os.path.exists(VALID_KEYS_FILE):
    with open(VALID_KEYS_FILE, "w") as f:
        json.dump([], f)

# --- SESSION STATE INITIALIZATION ---
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "authenticated": False,
        "language": "English",
        "user_name": "",
        "gdpr_consent": False,
        "answers": {},
        "generated_letter": "",
        "selected_category": None,
        "selected_subcategory": None,
        "tone": "Standard"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- LICENSE KEY AUTHENTICATION ---
def authenticate(license_key: str) -> bool:
    """Check if license key is valid"""
    try:
        with open(VALID_KEYS_FILE, "r") as f:
            valid_keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        valid_keys = []
    
    return license_key.strip() in valid_keys

# --- LETTER STRUCTURE ---
LETTER_STRUCTURE = {
    # [Previous structure remains exactly the same]
    # ... (keeping all the existing letter structure content)
}

# --- TRANSLATION DICTIONARY ---
TRANSLATIONS = {
    "en": {
        "title": "Care Quality Advocacy Letter Generator",
        "language_select": "Select Language",
        "license_prompt": "Enter your license key",
        "invalid_key": "Invalid or already-used license key.",
        "access_granted": "Access granted. Welcome.",
        "gdpr_label": "I consent to data processing (GDPR)",
        "gdpr_warning": "You must consent to GDPR processing to continue.",
        "tone_label": "Select the tone for your letter:",
        "tone_help": "Choose 'Serious Formal Complaint' if you want regulatory language and strong escalation wording.",
        "category_label": "Choose your letter category:",
        "subcategory_label": "Select the issue type:",
        "questions_header": "📝 Please answer the following:",
        "name_label": "Your Name",
        "recipient_label": "Recipient Name/Organization",
        "date_label": "Date",
        "generate_button": "Generate Letter",
        "result_label": "Generated Letter",
        "error_message": "Error generating letter:",
        "download_button": "Download Letter",
        "clear_button": "Clear Form",
        "saved_letters": "Saved Letters",
        "save_button": "Save Letter",
        "load_button": "Load Letter"
    },
    "es": {
        "title": "Generador de Cartas de Defensa de la Calidad de la Atención",
        "language_select": "Seleccionar idioma",
        "license_prompt": "Ingrese su clave de licencia",
        "invalid_key": "Clave de licencia inválida o ya utilizada.",
        "access_granted": "Acceso concedido. Bienvenido.",
        "gdpr_label": "Doy mi consentimiento para el procesamiento de datos (GDPR)",
        "gdpr_warning": "Debe dar su consentimiento para el procesamiento de datos GDPR para continuar.",
        "tone_label": "Seleccione el tono para su carta:",
        "tone_help": "Elija 'Queja Formal Grave' si desea un lenguaje regulatorio y redacción de escalamiento fuerte.",
        "category_label": "Elija la categoría de su carta:",
        "subcategory_label": "Seleccione el tipo de problema:",
        "questions_header": "📝 Por favor responda lo siguiente:",
        "name_label": "Su Nombre",
        "recipient_label": "Nombre/Organización del Destinatario",
        "date_label": "Fecha",
        "generate_button": "Generar Carta",
        "result_label": "Carta Generada",
        "error_message": "Error al generar la carta:",
        "download_button": "Descargar Carta",
        "clear_button": "Limpiar Formulario",
        "saved_letters": "Cartas Guardadas",
        "save_button": "Guardar Carta",
        "load_button": "Cargar Carta"
    },
    # Add other languages following the same pattern
}

def t(key: str) -> str:
    """Get translation for the current language"""
    lang_code = LANGUAGES.get(st.session_state.language, "en")
    return TRANSLATIONS.get(lang_code, {}).get(key, TRANSLATIONS["en"][key])

# --- PROMPT GENERATION ---
def generate_prompt() -> str:
    """Generate the prompt for OpenAI based on user inputs"""
    if not all([st.session_state.selected_category, 
               st.session_state.selected_subcategory,
               st.session_state.user_name]):
        return ""
    
    base_intro = (
        f"You are an experienced care quality advocate who understands regulations in {st.session_state.language}. "
        "Your task is to generate a formal letter that addresses a care-related concern. "
        "The letter should be in the selected language and tone.\n\n"
    )

    context_block = (
        f"Language: {st.session_state.language}\n"
        f"Letter Category: {st.session_state.selected_category}\n"
        f"Issue Type: {st.session_state.selected_subcategory}\n"
        f"Recipient: {st.session_state.get('recipient', '')}\n"
        f"Date: {st.session_state.get('date', '')}\n\n"
    )

    summary_block = ""
    for q, a in st.session_state.answers.items():
        if a.strip():
            summary_block += f"{q}\n{a.strip()}\n\n"

    if st.session_state.tone == "Serious Formal Complaint":
        action_block = (
            "Please write this letter in a direct, formal, and legally aware tone. The letter should:\n"
            "- Be factual and to the point\n"
            "- Reflect concern for well-being\n"
            "- State concern for care standards explicitly\n"
            "- Use respectful yet assertive language\n"
            "- Reference relevant regulations where appropriate\n"
            "- Mention escalation options professionally\n\n"
        )
    else:
        action_block = (
            "Please write this letter in a calm, assertive tone. The letter should:\n"
            "- Clearly explain the concern\n"
            "- Highlight any risks\n"
            "- Request investigation and response\n"
            "- Mention any reports already made\n"
            "- Specify expected response timeframe\n"
            "- Close with readiness to escalate if needed\n\n"
        )

    closing = f"\nSincerely,\n{st.session_state.user_name}"
    
    return base_intro + context_block + summary_block + action_block + closing

# --- LETTER MANAGEMENT ---
def save_letter(title: str, content: str):
    """Save a letter to session state"""
    if "saved_letters" not in st.session_state:
        st.session_state.saved_letters = {}
    
    st.session_state.saved_letters[title] = {
        "content": content,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": st.session_state.selected_category,
        "subcategory": st.session_state.selected_subcategory
    }

def clear_form():
    """Clear the form inputs"""
    st.session_state.answers = {}
    st.session_state.generated_letter = ""
    st.session_state.user_name = st.session_state.get("user_name", "")
    st.session_state.recipient = st.session_state.get("recipient", "")
    st.session_state.date = st.session_state.get("date", "")

# --- MAIN APP ---
def main():
    st.set_page_config(
        page_title=t("title"), 
        layout="wide",
        page_icon="✉️"
    )
    
    # Sidebar for language and saved letters
    with st.sidebar:
        st.session_state.language = st.selectbox(
            t("language_select"),
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.language)
        )
        
        if st.session_state.authenticated and "saved_letters" in st.session_state:
            st.subheader(t("saved_letters"))
            for title, letter_data in st.session_state.saved_letters.items():
                if st.button(f"{title} ({letter_data['date']})"):
                    st.session_state.generated_letter = letter_data["content"]
                    st.session_state.selected_category = letter_data["category"]
                    st.session_state.selected_subcategory = letter_data["subcategory"]
                    st.experimental_rerun()
    
    st.title(t("title"))
    
    # Authentication
    if not st.session_state.authenticated:
        with st.form("auth_form"):
            license_key = st.text_input(t("license_prompt"), type="password")
            
            if st.form_submit_button("Submit"):
                if authenticate(license_key):
                    st.session_state.authenticated = True
                    st.success(t("access_granted"))
                    st.experimental_rerun()
                else:
                    st.error(t("invalid_key"))
        return
    
    # GDPR Consent
    st.session_state.gdpr_consent = st.checkbox(t("gdpr_label"))
    if not st.session_state.gdpr_consent:
        st.warning(t("gdpr_warning"))
        return
    
    # Main form
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.user_name = st.text_input(
                t("name_label"),
                value=st.session_state.user_name
            )
            
            st.session_state.recipient = st.text_input(
                t("recipient_label"),
                value=st.session_state.get("recipient", "")
            )
            
        with col2:
            st.session_state.date = st.date_input(
                t("date_label"),
                value=datetime.date.today()
            ).strftime("%Y-%m-%d")
            
            st.session_state.tone = st.radio(
                t("tone_label"),
                ("Standard", "Serious Formal Complaint"),
                index=0 if st.session_state.tone == "Standard" else 1,
                help=t("tone_help")
            )
        
        # Letter category selection
        st.session_state.selected_category = st.selectbox(
            t("category_label"),
            list(LETTER_STRUCTURE.keys()),
            index=list(LETTER_STRUCTURE.keys()).index(st.session_state.selected_category) 
            if st.session_state.selected_category else 0
        )
        
        if st.session_state.selected_category:
            subcategories = list(LETTER_STRUCTURE[st.session_state.selected_category].keys())
            st.session_state.selected_subcategory = st.selectbox(
                t("subcategory_label"),
                subcategories,
                index=subcategories.index(st.session_state.selected_subcategory) 
                if st.session_state.selected_subcategory in subcategories else 0
            )
            
            if st.session_state.selected_subcategory:
                st.markdown("---")
                st.subheader(t("questions_header"))
                
                # Create form for questions
                for question in LETTER_STRUCTURE[st.session_state.selected_category][st.session_state.selected_subcategory]:
                    st.session_state.answers[question] = st.text_area(
                        question,
                        value=st.session_state.answers.get(question, ""),
                        key=f"q_{hash(question)}"  # Unique key for each question
                    )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            generate_clicked = st.form_submit_button(t("generate_button"))
        with col2:
            clear_clicked = st.form_submit_button(t("clear_button"))
        with col3:
            save_clicked = st.form_submit_button(t("save_button")) if st.session_state.generated_letter else st.empty()
        
        if clear_clicked:
            clear_form()
            st.experimental_rerun()
        
        if save_clicked and st.session_state.generated_letter:
            letter_title = f"{st.session_state.selected_category} - {st.session_state.selected_subcategory}"
            save_letter(letter_title, st.session_state.generated_letter)
            st.success("Letter saved!")
    
    # Generate letter if requested
    if generate_clicked:
        if not all([st.session_state.user_name, st.session_state.selected_category, 
                   st.session_state.selected_subcategory]):
            st.error("Please fill in all required fields")
        else:
            with st.spinner("Generating your letter..."):
                try:
                    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                    
                    prompt = generate_prompt()
                    
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3 if st.session_state.tone == "Serious Formal Complaint" else 0.7
                    )
                    
                    st.session_state.generated_letter = response.choices[0].message.content
                    st.experimental_rerun()
                
                except Exception as e:
                    st.error(f"{t('error_message')} {str(e)}")
    
    # Display generated letter
    if st.session_state.generated_letter:
        st.subheader(t("result_label"))
        st.text_area(
            "Letter Content",
            st.session_state.generated_letter,
            height=400,
            label_visibility="collapsed"
        )
        
        # Add download button
        st.download_button(
            label=t("download_button"),
            data=st.session_state.generated_letter,
            file_name=f"care_letter_{st.session_state.selected_category.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
