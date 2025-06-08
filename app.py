import streamlit as st
import json
import openai
from datetime import datetime
import pytz
from typing import Dict, List, Optional, Any
import uuid
import pyperclip

# Constants
VALID_KEYS_FILE = "valid_keys.json"
LETTER_STRUCTURE_FILE = "letter_structure_meta.json"
DATE_FORMAT = "%d %B %Y"
TIMEZONE = "Europe/London"

# Translations
TRANSLATIONS = {
    "en": {
        "app_title": "NHS Care Companion Letter Generator",
        "welcome": "Welcome to the NHS Care Companion Letter Generator",
        "license_prompt": "Please enter your license key to continue",
        "invalid_key": "Invalid license key. Please try again.",
        "gdpr_title": "GDPR Compliance",
        "gdpr_text": "I confirm that I will handle patient data in accordance with GDPR requirements.",
        "gdpr_accept": "I Accept",
        "language_select": "Select Language",
        "category_select": "Select Letter Category",
        "subcategory_select": "Select Subcategory/Issue",
        "tone_select": "Select Tone",
        "tone_standard": "Standard",
        "tone_complaint": "Serious Formal Complaint",
        "generate_button": "Generate Letter",
        "letter_subject": "Subject",
        "letter_date": "Date",
        "letter_recipient": "Recipient",
        "letter_body": "Body",
        "save_button": "Save Letter",
        "load_button": "Load Letter",
        "delete_button": "Delete Letter",
        "download_button": "Download as .txt",
        "copy_button": "Copy to Clipboard",
        "saved_letters": "Saved Letters",
        "debug_prompt": "Debug: Prompt Used",
        "no_saved_letters": "No saved letters found.",
        "letter_saved": "Letter saved successfully!",
        "letter_loaded": "Letter loaded successfully!",
        "letter_deleted": "Letter deleted successfully!",
        "letter_copied": "Letter copied to clipboard!",
        "required_field": "This field is required",
        "patient_ref": "Patient Reference",
        "recipient_name": "Recipient Name",
        "your_name": "Your Name",
        "your_position": "Your Position",
        "your_contact": "Your Contact Information"
    },
    "es": {
        "app_title": "Generador de Cartas de Acompañamiento del NHS",
        "welcome": "Bienvenido al Generador de Cartas de Acompañamiento del NHS",
        "license_prompt": "Por favor, introduzca su clave de licencia para continuar",
        "invalid_key": "Clave de licencia no válida. Por favor, inténtelo de nuevo.",
        "gdpr_title": "Cumplimiento del GDPR",
        "gdpr_text": "Confirmo que manejaré los datos del paciente de acuerdo con los requisitos del GDPR.",
        "gdpr_accept": "Acepto",
        "language_select": "Seleccionar Idioma",
        "category_select": "Seleccionar Categoría de Carta",
        "subcategory_select": "Seleccionar Subcategoría/Problema",
        "tone_select": "Seleccionar Tono",
        "tone_standard": "Estándar",
        "tone_complaint": "Queja Formal Grave",
        "generate_button": "Generar Carta",
        "letter_subject": "Asunto",
        "letter_date": "Fecha",
        "letter_recipient": "Destinatario",
        "letter_body": "Cuerpo",
        "save_button": "Guardar Carta",
        "load_button": "Cargar Carta",
        "delete_button": "Eliminar Carta",
        "download_button": "Descargar como .txt",
        "copy_button": "Copiar al Portapapeles",
        "saved_letters": "Cartas Guardadas",
        "debug_prompt": "Depuración: Prompt Utilizado",
        "no_saved_letters": "No se encontraron cartas guardadas.",
        "letter_saved": "¡Carta guardada con éxito!",
        "letter_loaded": "¡Carta cargada con éxito!",
        "letter_deleted": "¡Carta eliminada con éxito!",
        "letter_copied": "¡Carta copiada al portapapeles!",
        "required_field": "Este campo es obligatorio",
        "patient_ref": "Referencia del Paciente",
        "recipient_name": "Nombre del Destinatario",
        "your_name": "Su Nombre",
        "your_position": "Su Cargo",
        "your_contact": "Su Información de Contacto"
    },
    "fr": {
        "app_title": "Générateur de Lettres d'Accompagnement NHS",
        "welcome": "Bienvenue dans le Générateur de Lettres d'Accompagnement NHS",
        "license_prompt": "Veuillez entrer votre clé de licence pour continuer",
        "invalid_key": "Clé de licence invalide. Veuillez réessayer.",
        "gdpr_title": "Conformité GDPR",
        "gdpr_text": "Je confirme que je traiterai les données des patients conformément aux exigences du GDPR.",
        "gdpr_accept": "J'accepte",
        "language_select": "Sélectionner la Langue",
        "category_select": "Sélectionner la Catégorie de Lettre",
        "subcategory_select": "Sélectionner la Sous-catégorie/Problème",
        "tone_select": "Sélectionner le Ton",
        "tone_standard": "Standard",
        "tone_complaint": "Plainte Formelle Sérieuse",
        "generate_button": "Générer la Lettre",
        "letter_subject": "Sujet",
        "letter_date": "Date",
        "letter_recipient": "Destinataire",
        "letter_body": "Corps",
        "save_button": "Enregistrer la Lettre",
        "load_button": "Charger la Lettre",
        "delete_button": "Supprimer la Lettre",
        "download_button": "Télécharger en .txt",
        "copy_button": "Copier dans le Presse-papiers",
        "saved_letters": "Lettres Enregistrées",
        "debug_prompt": "Débogage: Prompt Utilisé",
        "no_saved_letters": "Aucune lettre enregistrée trouvée.",
        "letter_saved": "Lettre enregistrée avec succès !",
        "letter_loaded": "Lettre chargée avec succès !",
        "letter_deleted": "Lettre supprimée avec succès !",
        "letter_copied": "Lettre copiée dans le presse-papiers !",
        "required_field": "Ce champ est obligatoire",
        "patient_ref": "Référence du Patient",
        "recipient_name": "Nom du Destinataire",
        "your_name": "Votre Nom",
        "your_position": "Votre Poste",
        "your_contact": "Vos Coordonnées"
    }
}

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "gdpr_accepted" not in st.session_state:
    st.session_state.gdpr_accepted = False
if "language" not in st.session_state:
    st.session_state.language = "en"
if "generated_letters" not in st.session_state:
    st.session_state.generated_letters = {}
if "current_letter" not in st.session_state:
    st.session_state.current_letter = None
if "form_data" not in st.session_state:
    st.session_state.form_data = {}

# Helper functions
def get_text(key: str) -> str:
    """Get translated text for the current language"""
    lang = st.session_state.get("language", "en")
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["en"].get(key, key))

def load_json_file(filename: str) -> Dict:
    """Load JSON file with error handling"""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: {filename} not found.")
        st.stop()
    except json.JSONDecodeError:
        st.error(f"Error: {filename} contains invalid JSON.")
        st.stop()

def validate_license_key(key: str) -> bool:
    """Validate the provided license key"""
    valid_keys = load_json_file(VALID_KEYS_FILE)
    return key in valid_keys.get("keys", [])

def get_current_date() -> str:
    """Get current date in the specified format and timezone"""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).strftime(DATE_FORMAT)

def generate_prompt(category: str, subcategory: str, questions: Dict, tone: str, form_data: Dict) -> str:
    """Generate the prompt for OpenAI"""
    base_prompt = f"Write a professional {tone.lower()} letter in {st.session_state.language} regarding {category} - {subcategory}.\n\n"
    base_prompt += f"Recipient: {form_data.get('recipient_name', '')}\n"
    base_prompt += f"Patient Reference: {form_data.get('patient_ref', '')}\n"
    base_prompt += f"Your Name: {form_data.get('your_name', '')}\n"
    base_prompt += f"Your Position: {form_data.get('your_position', '')}\n"
    base_prompt += f"Your Contact: {form_data.get('your_contact', '')}\n\n"
    
    if tone == get_text("tone_complaint"):
        base_prompt += "This is a serious formal complaint. The tone should reflect the gravity of the situation while remaining professional.\n\n"
    
    for q_id, question in questions.items():
        answer = form_data.get(q_id, "")
        base_prompt += f"{question}: {answer}\n"
    
    return base_prompt

def generate_letter(prompt: str) -> str:
    """Generate letter using OpenAI API"""
    try:
        openai.api_key = st.secrets["openai"]["api_key"]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes professional healthcare letters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating letter: {str(e)}")
        return ""

def save_current_letter() -> None:
    """Save the current letter to session state"""
    if st.session_state.current_letter:
        letter_id = str(uuid.uuid4())
        st.session_state.generated_letters[letter_id] = st.session_state.current_letter
        st.session_state.form_data["last_saved_id"] = letter_id
        st.success(get_text("letter_saved"))

def load_letter(letter_id: str) -> None:
    """Load a letter from session state"""
    if letter_id in st.session_state.generated_letters:
        st.session_state.current_letter = st.session_state.generated_letters[letter_id]
        st.success(get_text("letter_loaded"))

def delete_letter(letter_id: str) -> None:
    """Delete a letter from session state"""
    if letter_id in st.session_state.generated_letters:
        del st.session_state.generated_letters[letter_id]
        if st.session_state.current_letter and st.session_state.current_letter.get("id") == letter_id:
            st.session_state.current_letter = None
        st.success(get_text("letter_deleted"))

def copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard"""
    try:
        pyperclip.copy(text)
        st.success(get_text("letter_copied"))
    except Exception as e:
        st.error(f"Failed to copy to clipboard: {str(e)}")

# Page config
st.set_page_config(
    page_title=get_text("app_title"),
    page_icon="🏥",
    layout="centered",
    menu_items={
        "About": f"## {get_text('app_title')}\n\nProfessional letter generator for healthcare communications."
    }
)

# Custom CSS
st.markdown("""
    <style>
        .stTextInput, .stSelectbox, .stTextArea {
            margin-bottom: 1rem;
        }
        .stButton button {
            width: 100%;
        }
        .letter-container {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 1.5rem;
            margin-top: 1rem;
            background-color: #f9f9f9;
        }
        .letter-header {
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
        }
        .debug-prompt {
            font-family: monospace;
            white-space: pre-wrap;
            background-color: #f5f5f5;
            padding: 1rem;
            border-radius: 5px;
            margin-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Authentication
if not st.session_state.authenticated:
    st.title(get_text("welcome"))
    license_key = st.text_input(get_text("license_prompt"), type="password")
    
    if st.button("Submit"):
        if validate_license_key(license_key):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error(get_text("invalid_key"))
    st.stop()

# GDPR Consent
if not st.session_state.gdpr_accepted:
    st.title(get_text("gdpr_title"))
    st.markdown(f"### {get_text('gdpr_text')}")
    
    if st.button(get_text("gdpr_accept")):
        st.session_state.gdpr_accepted = True
        st.rerun()
    st.stop()

# Main App
st.title(get_text("app_title"))

# Language selection
st.session_state.language = st.selectbox(
    get_text("language_select"),
    options=list(TRANSLATIONS.keys()),
    format_func=lambda x: {"en": "English", "es": "Español", "fr": "Français"}.get(x, x)
)

# Load letter structure
letter_structure = load_json_file(LETTER_STRUCTURE_FILE)
categories = list(letter_structure.keys())

# Category selection
category = st.selectbox(get_text("category_select"), categories)
subcategories = list(letter_structure[category].keys())

# Subcategory selection
subcategory = st.selectbox(get_text("subcategory_select"), subcategories)
questions = letter_structure[category][subcategory].get("questions", {})

# Tone selection
tone = st.selectbox(
    get_text("tone_select"),
    options=[get_text("tone_standard"), get_text("tone_complaint")]
)

# Dynamic form for questions
form_data = {}
st.subheader("Letter Details")

required_fields = {
    "recipient_name": get_text("recipient_name"),
    "patient_ref": get_text("patient_ref"),
    "your_name": get_text("your_name"),
    "your_position": get_text("your_position"),
    "your_contact": get_text("your_contact")
}

for field_id, label in required_fields.items():
    form_data[field_id] = st.text_input(f"{label} *", key=field_id)

for q_id, question in questions.items():
    form_data[q_id] = st.text_area(question, key=q_id)

st.session_state.form_data = form_data

# Generate letter
if st.button(get_text("generate_button")):
    # Validate required fields
    missing_fields = [label for field_id, label in required_fields.items() if not form_data.get(field_id)]
    if missing_fields:
        st.error(f"{get_text('required_field')}: {', '.join(missing_fields)}")
    else:
        with st.spinner("Generating letter..."):
            prompt = generate_prompt(category, subcategory, questions, tone, form_data)
            letter_content = generate_letter(prompt)
            
            if letter_content:
                st.session_state.current_letter = {
                    "id": str(uuid.uuid4()),
                    "subject": f"{category} - {subcategory}",
                    "date": get_current_date(),
                    "recipient": form_data.get("recipient_name", ""),
                    "content": letter_content,
                    "prompt": prompt
                }

# Display generated letter
if st.session_state.current_letter:
    letter = st.session_state.current_letter
    st.subheader("Generated Letter")
    
    with st.container():
        st.markdown(f"<div class='letter-container'>", unsafe_allow_html=True)
        st.markdown(f"<div class='letter-header'><strong>{get_text('letter_subject')}:</strong> {letter['subject']}</div>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>{get_text('letter_date')}:</strong> {letter['date']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>{get_text('letter_recipient')}:</strong> {letter['recipient']}</p>", unsafe_allow_html=True)
        st.markdown(f"<div><strong>{get_text('letter_body')}:</strong></div>", unsafe_allow_html=True)
        st.markdown(letter["content"], unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(get_text("save_button")):
                save_current_letter()
        with col2:
            st.download_button(
                label=get_text("download_button"),
                data=letter["content"],
                file_name=f"NHS_Letter_{letter['date']}.txt",
                mime="text/plain"
            )
        with col3:
            if st.button(get_text("copy_button")):
                copy_to_clipboard(letter["content"])
        
        # Debug expander
        with st.expander(get_text("debug_prompt")):
            st.code(letter["prompt"], language="text")

# Saved letters section
if st.session_state.generated_letters:
    st.subheader(get_text("saved_letters"))
    for letter_id, letter in st.session_state.generated_letters.items():
        with st.container():
            st.markdown(f"**{letter['subject']}** - {letter['date']}")
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                if st.button(f"View {letter_id[:8]}", key=f"view_{letter_id}"):
                    load_letter(letter_id)
                    st.rerun()
            with col2:
                if st.button(f"Delete {letter_id[:8]}", key=f"delete_{letter_id}"):
                    delete_letter(letter_id)
                    st.rerun()
else:
    st.info(get_text("no_saved_letters"))
