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
    "Arabic": "ar",
    "Hindi": "hi",
    "Urdu": "ur"
}

# Initialize valid keys file if it doesn't exist
if not os.path.exists(VALID_KEYS_FILE):
    with open(VALID_KEYS_FILE, "w") as f:
        json.dump([], f)

# --- LETTER STRUCTURE ---
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
        ],
        "Cleanliness or environment": [
            "What hygiene issue or risk occurred?",
            "Who did it affect?",
            "What date/time was this?",
            "Has it been addressed?",
            "Are you seeking specific action?"
        ],
        "General standards of care": [
            "What care concerns do you have?",
            "Is this recent or long-standing?",
            "Any dates/incidents worth noting?",
            "What changes are you requesting?"
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
        ],
        "Challenge capacity assessment": [
            "What is your loved one's diagnosis?",
            "Why do you believe the assessment is flawed?",
            "What outcome are you seeking?",
            "Have you discussed this with professionals already?"
        ],
        "Request second opinion": [
            "What was the first opinion or assessment?",
            "Why do you feel a second opinion is necessary?",
            "What changes in care would this affect?",
            "Have you made a formal request before?"
        ],
        "Follow-up after safeguarding": [
            "What was the original concern?",
            "What outcome are you checking on?",
            "Any dates/people involved?",
            "Has there been any communication since?"
        ]
    },
    "Referral Support Letter": {
        "Request community support": [
            "What support do you believe is needed?",
            "Who is the individual needing it?",
            "Have they had this support before?",
            "Why now?"
        ],
        "Request MDT review": [
            "What is the reason for requesting an MDT?",
            "Who is involved in the care?",
            "Are there conflicting opinions?",
            "What is the ideal next step?"
        ],
        "Referral to CHC/NHS Continuing Care": [
            "Why do you think CHC is appropriate?",
            "What needs are you highlighting?",
            "Have assessments already started?",
            "Are you requesting a Fast Track?"
        ],
        "Referral for reassessment": [
            "What has changed in the person's condition?",
            "When was the last assessment?",
            "What result are you hoping for?"
        ]
    },
    "Thank You & Positive Feedback": {
        "Praise for a staff member": [
            "What did they do well?",
            "When and where?",
            "What impact did it have?",
            "Do you want management to be notified?"
        ],
        "Thank a team or home": [
            "What overall praise would you like to give?",
            "Is there a specific moment worth mentioning?",
            "Would you like to stay in contact?"
        ],
        "Positive discharge feedback": [
            "What made the discharge go well?",
            "Who was involved?",
            "Any specific comments you'd like to share?"
        ],
        "Support during end-of-life care": [
            "Who provided support?",
            "What actions stood out?",
            "Would you like this shared with leadership?"
        ]
    },
    "Hospital & Discharge": {
        "Discharge objection": [
            "What discharge is being planned?",
            "Why is it not safe/suitable?",
            "Have you communicated with the ward?",
            "What would be a better plan?"
        ],
        "Hospital complaint": [
            "What happened?",
            "Where (ward/hospital)?",
            "What impact did this have?",
            "Have you already raised this?"
        ],
        "Request delayed discharge support": [
            "Who is awaiting discharge?",
            "What barriers exist?",
            "Have you asked for social worker input?"
        ],
        "Hospital to home unsafe discharge": [
            "Who was discharged unsafely?",
            "What went wrong?",
            "What was the result?",
            "What are you requesting now?"
        ]
    },
    "Other Letters": {
        "Safeguarding concern": [
            "What concern do you want to report?",
            "Who is at risk?",
            "When and where did this happen?",
            "Have you contacted the safeguarding team?"
        ],
        "LPA/Deputy involvement letter": [
            "What role do you hold (LPA/Deputy)?",
            "What decisions are being challenged?",
            "What outcome are you requesting?"
        ],
        "Request for care review": [
            "Why is a review needed?",
            "What has changed?",
            "What result are you hoping for?",
            "Who needs to be involved?"
        ],
        "GP concern": [
            "Who is the GP or practice?",
            "What is the concern?",
            "What impact is this having?",
            "Are you requesting referral or action?"
        ],
        "CQC notification (family use)": [
            "What is the setting?",
            "What concern are you reporting?",
            "Is this ongoing or resolved?",
            "Do you want a callback or acknowledgment?"
        ]
    },
    "Escalation & Regulatory": {
        "Notify safeguarding board": [
            "What incident or risk are you reporting?",
            "Who is affected?",
            "Have you reported it to the care provider?",
            "Why are you escalating it externally now?"
        ],
        "Raise formal concern with CQC": [
            "What concern do you want CQC to investigate?",
            "Where is the setting and who is affected?",
            "Is this a single incident or ongoing pattern?",
            "Have you tried resolving this locally first?"
        ],
        "Escalate to Integrated Care Board (ICB)": [
            "What issue are you escalating?",
            "What support or funding is being denied?",
            "Have you followed the correct steps so far?",
            "Why is ICB intervention needed now?"
        ]
    },
    "Advocate Support Requests": {
        "Seek mental capacity advocate (IMCA)": [
            "What decision is being made?",
            "Does the person lack capacity for it?",
            "Are they unbefriended (no close family/friends)?",
            "What outcome are you hoping for?"
        ],
        "Request independent advocate (IMHA)": [
            "What mental health issue is involved?",
            "Is the person detained or sectioned?",
            "What kind of support is needed from advocacy?",
            "Have they had an advocate before?"
        ],
        "Challenge under Human Rights Act": [
            "What decision or treatment is breaching rights?",
            "Whose rights are affected?",
            "Which right (Article 8, 5, etc.) is relevant?",
            "What action are you requesting?"
        ]
    },
    "Delays & Practical Barriers": {
        "Chase delayed referral or appointment": [
            "Who is waiting for what (referral/test/support)?",
            "How long has the delay been?",
            "What impact is the delay having?",
            "Have you contacted the provider already?"
        ],
        "Dispute funding refusal (LA/NHS)": [
            "What funding was denied?",
            "What is the person's current care situation?",
            "Why do you believe the refusal is unfair?",
            "Have you received a written explanation?"
        ],
        "Request carer support plan": [
            "Are you a family carer?",
            "What support are you struggling to provide?",
            "Has a carer's assessment ever been done?",
            "What help would make a difference?"
        ]
    },
    "Care Home Specific": {
        "Request care plan review": [
            "What aspects of the care plan need review?",
            "What changes are you requesting?",
            "Have you discussed this with staff already?",
            "What is your preferred timeline?"
        ],
        "Complaint about food/nutrition": [
            "What specific issues have you observed?",
            "How long has this been going on?",
            "What impact is this having?",
            "Have you raised this with staff before?"
        ],
        "Activities and engagement": [
            "What activities are lacking?",
            "How does this affect residents?",
            "What suggestions do you have?",
            "Have you discussed this with the activities coordinator?"
        ],
        "Visitation rights concern": [
            "What visitation issues are occurring?",
            "How is this affecting the resident?",
            "Have you seen the home's visitation policy?",
            "What resolution are you seeking?"
        ]
    },
    "Mental Health Advocacy": {
        "Challenge section or treatment": [
            "What decision are you challenging?",
            "What are your specific concerns?",
            "What alternative approaches would you suggest?",
            "Have you discussed this with the care team?"
        ],
        "Request care coordinator meeting": [
            "What issues need discussion?",
            "Who should be present?",
            "What are your desired outcomes?",
            "Have you tried informal resolution first?"
        ],
        "Medication side effects": [
            "What medication is causing issues?",
            "What side effects are occurring?",
            "How is this affecting daily life?",
            "Have you reported this to the prescribing doctor?"
        ],
        "Aftercare planning": [
            "What aftercare is being proposed?",
            "What support is missing?",
            "What risks concern you?",
            "Have you seen the written aftercare plan?"
        ]
    },
    "Children's Services": {
        "EHCP concerns": [
            "What specific parts of the EHCP aren't being met?",
            "How is this affecting the child?",
            "Have you raised this with the school/local authority?",
            "What outcome are you seeking?"
        ],
        "Social services involvement": [
            "What decisions are you concerned about?",
            "How is this affecting the family?",
            "Have you had a chance to share your views?",
            "What support do you feel is needed?"
        ],
        "CAMHS waiting times": [
            "How long has the child been waiting?",
            "What impact is the delay having?",
            "Have you contacted the service about prioritization?",
            "What interim support is needed?"
        ],
        "Education provision complaint": [
            "What specific issues are occurring at school?",
            "How is this affecting the child's education?",
            "Have you followed the school's complaints policy?",
            "What resolution would you like to see?"
        ]
    }
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
        "title": "Generador de Cartas de Defensa de la Calidad del Cuidado",
        "language_select": "Seleccionar Idioma",
        "license_prompt": "Ingrese su clave de licencia",
        "invalid_key": "Clave de licencia inválida o ya utilizada.",
        "access_granted": "Acceso concedido. Bienvenido.",
        "gdpr_label": "Doy mi consentimiento para el procesamiento de datos (GDPR)",
        "gdpr_warning": "Debe consentir el procesamiento de datos GDPR para continuar.",
        "tone_label": "Seleccione el tono para su carta:",
        "tone_help": "Elija 'Queja Formal Grave' si desea lenguaje regulatorio y redacción de escalamiento fuerte.",
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
    "fr": {
        "title": "Générateur de Lettres pour la Qualité des Soins",
        "language_select": "Sélectionner la Langue",
        "license_prompt": "Entrez votre clé de licence",
        "invalid_key": "Clé de licence invalide ou déjà utilisée.",
        "access_granted": "Accès accordé. Bienvenue.",
        "gdpr_label": "Je consens au traitement des données (GDPR)",
        "gdpr_warning": "Vous devez consentir au traitement des données GDPR pour continuer.",
        "tone_label": "Sélectionnez le ton de votre lettre:",
        "tone_help": "Choisissez 'Plainte Formelle Sérieuse' si vous voulez un langage réglementaire et une formulation d'escalade forte.",
        "category_label": "Choisissez la catégorie de votre lettre:",
        "subcategory_label": "Sélectionnez le type de problème:",
        "questions_header": "📝 Veuillez répondre aux questions suivantes:",
        "name_label": "Votre Nom",
        "recipient_label": "Nom/Organisation du Destinataire",
        "date_label": "Date",
        "generate_button": "Générer la Lettre",
        "result_label": "Lettre Générée",
        "error_message": "Erreur lors de la génération de la lettre:",
        "download_button": "Télécharger la Lettre",
        "clear_button": "Effacer le Formulaire",
        "saved_letters": "Lettres Sauvegardées",
        "save_button": "Sauvegarder la Lettre",
        "load_button": "Charger la Lettre"
    },
    "de": {
        "title": "Generator für Beschwerdebriefe zur Pflegequalität",
        "language_select": "Sprache auswählen",
        "license_prompt": "Geben Sie Ihren Lizenzschlüssel ein",
        "invalid_key": "Ungültiger oder bereits verwendeter Lizenzschlüssel.",
        "access_granted": "Zugang gewährt. Willkommen.",
        "gdpr_label": "Ich stimme der Datenverarbeitung zu (GDPR)",
        "gdpr_warning": "Sie müssen der GDPR-Datenverarbeitung zustimmen, um fortzufahren.",
        "tone_label": "Wählen Sie den Ton für Ihren Brief:",
        "tone_help": "Wählen Sie 'Ernste Formelle Beschwerde', wenn Sie regulatorische Sprache und starke Eskalationsformulierungen wünschen.",
        "category_label": "Wählen Sie Ihre Briefkategorie:",
        "subcategory_label": "Wählen Sie den Problemtyp:",
        "questions_header": "📝 Bitte beantworten Sie Folgendes:",
        "name_label": "Ihr Name",
        "recipient_label": "Name/Organisation des Empfängers",
        "date_label": "Datum",
        "generate_button": "Brief generieren",
        "result_label": "Generierter Brief",
        "error_message": "Fehler beim Generieren des Briefes:",
        "download_button": "Brief herunterladen",
        "clear_button": "Formular zurücksetzen",
        "saved_letters": "Gespeicherte Briefe",
        "save_button": "Brief speichern",
        "load_button": "Brief laden"
    },
    "hi": {
        "title": "स्वास्थ्य देखभाल गुणवत्ता पत्र जनरेटर",
        "language_select": "भाषा चुनें",
        "license_prompt": "अपना लाइसेंस कुंजी दर्ज करें",
        "invalid_key": "अमान्य या पहले से उपयोग की गई लाइसेंस कुंजी।",
        "access_granted": "पहुंच प्रदान की गई। स्वागत है।",
        "gdpr_label": "मैं डेटा प्रसंस्करण के लिए सहमति देता हूं (GDPR)",
        "gdpr_warning": "जारी रखने के लिए आपको GDPR प्रसंस्करण के लिए सहमति देनी होगी।",
        "tone_label": "अपने पत्र के लिए स्वर चुनें:",
        "tone_help": "'गंभीर औपचारिक शिकायत' चुनें यदि आप नियामक भाषा और मजबूत एस्केलेशन शब्दावली चाहते हैं।",
        "category_label": "अपना पत्र श्रेणी चुनें:",
        "subcategory_label": "मुद्दे का प्रकार चुनें:",
        "questions_header": "📝 कृपया निम्नलिखित प्रश्नों का उत्तर दें:",
        "name_label": "आपका नाम",
        "recipient_label": "प्राप्तकर्ता का नाम/संगठन",
        "date_label": "तारीख",
        "generate_button": "पत्र जनरेट करें",
        "result_label": "जनरेट किया गया पत्र",
        "error_message": "पत्र जनरेट करने में त्रुटि:",
        "download_button": "पत्र डाउनलोड करें",
        "clear_button": "फॉर्म साफ करें",
        "saved_letters": "सहेजे गए पत्र",
        "save_button": "पत्र सहेजें",
        "load_button": "पत्र लोड करें"
    },
    "ur": {
        "title": "دیکھ بھال معیار کی وکالت خط جنریٹر",
        "language_select": "زبان منتخب کریں",
        "license_prompt": "اپنی لائسنس کی کلید درج کریں",
        "invalid_key": "غلط یا پہلے سے استعمال شدہ لائسنس کلید۔",
        "access_granted": "رسائی دی گئی۔ خوش آمدید۔",
        "gdpr_label": "میں ڈیٹا پروسیسنگ کی اجازت دیتا ہوں (GDPR)",
        "gdpr_warning": "جاری رکھنے کے لیے آپ کو GDPR پروسیسنگ کی اجازت دینی ہوگی۔",
        "tone_label": "اپنے خط کا انداز منتخب کریں:",
        "tone_help": "'سنجیدہ رسمی شکایت' منتخب کریں اگر آپ کو ریگولیٹری زبان اور مضبوط اسکیلیشن الفاظ چاہیے۔",
        "category_label": "اپنی خط کی قسم منتخب کریں:",
        "subcategory_label": "مسئلے کی قسم منتخب کریں:",
        "questions_header": "📝 براہ کرم درج ذیل سوالات کے جوابات دیں:",
        "name_label": "آپ کا نام",
        "recipient_label": "وصول کنندہ کا نام/ادارہ",
        "date_label": "تاریخ",
        "generate_button": "خط جنریٹ کریں",
        "result_label": "تیار کردہ خط",
        "error_message": "خط جنریٹ کرنے میں خرابی:",
        "download_button": "خط ڈاؤن لوڈ کریں",
        "clear_button": "فارم صاف کریں",
        "saved_letters": "محفوظ شدہ خطوط",
        "save_button": "خط محفوظ کریں",
        "load_button": "خط لوڈ کریں"
    }
}

# --- SESSION STATE MANAGEMENT ---
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
        "tone": "Standard",
        "recipient": "",
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "saved_letters": {}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- UTILITY FUNCTIONS ---
def t(key: str) -> str:
    """Get translation for the current language"""
    lang_code = LANGUAGES.get(st.session_state.language, "en")
    return TRANSLATIONS.get(lang_code, {}).get(key, TRANSLATIONS["en"][key])

def authenticate(license_key: str) -> bool:
    """Check if license key is valid"""
    try:
        with open(VALID_KEYS_FILE, "r") as f:
            valid_keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        valid_keys = []
    
    return license_key.strip() in valid_keys

def clear_form():
    """Clear the form inputs"""
    st.session_state.answers = {}
    st.session_state.generated_letter = ""

def save_current_letter():
    """Save the current letter to session state"""
    if not st.session_state.generated_letter:
        return
    
    letter_title = f"{st.session_state.selected_category} - {st.session_state.selected_subcategory}"
    st.session_state.saved_letters[letter_title] = {
        "content": st.session_state.generated_letter,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": st.session_state.selected_category,
        "subcategory": st.session_state.selected_subcategory,
        "answers": st.session_state.answers.copy()
    }
    st.success("Letter saved successfully!")

def load_letter(letter_title: str):
    """Load a saved letter"""
    letter_data = st.session_state.saved_letters.get(letter_title)
    if letter_data:
        st.session_state.generated_letter = letter_data["content"]
        st.session_state.selected_category = letter_data["category"]
        st.session_state.selected_subcategory = letter_data["subcategory"]
        st.session_state.answers = letter_data.get("answers", {})

# --- PROMPT GENERATION ---
def generate_prompt() -> str:
    """Generate the prompt for OpenAI based on user inputs"""
    if not all([st.session_state.user_name, 
               st.session_state.selected_category, 
               st.session_state.selected_subcategory]):
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
        f"Recipient: {st.session_state.recipient}\n"
        f"Date: {st.session_state.date}\n\n"
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

# --- MAIN APP COMPONENTS ---
def auth_form():
    """Display authentication form"""
    with st.form("auth_form"):
        license_key = st.text_input(t("license_prompt"), type="password")
        
        if st.form_submit_button("Submit"):
            if authenticate(license_key):
                st.session_state.authenticated = True
                st.success(t("access_granted"))
            else:
                st.error(t("invalid_key"))

def display_letter():
    """Display the generated letter and download option"""
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

def main_form():
    """Display the main letter generation form"""
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.user_name = st.text_input(
                t("name_label"),
                value=st.session_state.user_name
            )
            
            st.session_state.recipient = st.text_input(
                t("recipient_label"),
                value=st.session_state.recipient
            )
            
        with col2:
            st.session_state.date = st.date_input(
                t("date_label"),
                value=datetime.datetime.strptime(st.session_state.date, "%Y-%m-%d").date() if isinstance(st.session_state.date, str) else datetime.date.today()
            ).strftime("%Y-%m-%d")
            
            st.session_state.tone = st.radio(
                t("tone_label"),
                ("Standard", "Serious Formal Complaint"),
                index=0 if st.session_state.tone == "Standard" else 1,
                help=t("tone_help")
            )
        
        # Letter category selection
        category_options = list(LETTER_STRUCTURE.keys())
        selected_category = st.selectbox(
            t("category_label"),
            category_options,
            index=category_options.index(st.session_state.selected_category) 
            if st.session_state.selected_category in category_options else 0,
            key="category_select"
        )
        
        # Reset subcategory if category changes
        if selected_category != st.session_state.selected_category:
            st.session_state.selected_category = selected_category
            st.session_state.selected_subcategory = None
            st.session_state.answers = {}
        
        if st.session_state.selected_category:
            subcategory_options = list(LETTER_STRUCTURE[st.session_state.selected_category].keys())
            selected_subcategory = st.selectbox(
                t("subcategory_label"),
                subcategory_options,
                index=subcategory_options.index(st.session_state.selected_subcategory) 
                if st.session_state.selected_subcategory in subcategory_options else 0,
                key="subcategory_select"
            )
            
            # Reset answers if subcategory changes
            if selected_subcategory != st.session_state.selected_subcategory:
                st.session_state.selected_subcategory = selected_subcategory
                st.session_state.answers = {}
            
            if st.session_state.selected_subcategory:
                st.markdown("---")
                st.subheader(t("questions_header"))
                
                # Create form for questions
                questions = LETTER_STRUCTURE[st.session_state.selected_category][st.session_state.selected_subcategory]
                for question in questions:
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
            if st.session_state.generated_letter:
                save_clicked = st.form_submit_button(t("save_button"))
            else:
                save_clicked = False

        # Handle form actions
        if clear_clicked:
            clear_form()
        
        if save_clicked and st.session_state.generated_letter:
            save_current_letter()
        
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
                    except Exception as e:
                        st.error(f"{t('error_message')} {str(e)}")

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
        
        if st.session_state.authenticated and st.session_state.saved_letters:
            st.subheader(t("saved_letters"))
            for title in st.session_state.saved_letters.keys():
                if st.button(title):
                    load_letter(title)
    
    st.title(t("title"))
    
    # Authentication
    if not st.session_state.authenticated:
        auth_form()
        return
    
    # GDPR Consent
    st.session_state.gdpr_consent = st.checkbox(t("gdpr_label"))
    if not st.session_state.gdpr_consent:
        st.warning(t("gdpr_warning"))
        return
    
    # Main form
    main_form()
    
    # Display generated letter
    if st.session_state.generated_letter:
        display_letter()

if __name__ == "__main__":
    main()
