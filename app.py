import json
import streamlit as st
from openai import OpenAI
from streamlit_extras.stylable_container import stylable_container

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Care Letter Generator",
    page_icon="💌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "gdpr_consent" not in st.session_state:
    st.session_state.gdpr_consent = False
if "language" not in st.session_state:
    st.session_state.language = "English"
if "tone" not in st.session_state:
    st.session_state.tone = "Standard"

# --- THEME OVERRIDES ---
st.markdown("""
<style>
html, body { background-color: #F4F7FA; }
.main .block-container { padding: 2rem; background: #FFFFFF; border-radius: 12px; }
.stButton>button, .stDownloadButton>button { border-radius: 8px; margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("⚙️ Settings & Info")
tab = st.sidebar.radio("Navigate", ["Generate", "About"])

# --- AUTHENTICATION ---
VALID_KEYS_FILE = "valid_keys.json"
if not st.session_state.authenticated:
    st.sidebar.subheader("🔑 License Authentication")
    key = st.sidebar.text_input("Enter license key", type="password", help="Your unique access key.")
    if st.sidebar.button("Submit Key"):
        try:
            valid_keys = json.load(open(VALID_KEYS_FILE))
        except FileNotFoundError:
            valid_keys = []
        if key in valid_keys:
            st.session_state.authenticated = True
            st.sidebar.success("✅ Access granted")
            st.experimental_rerun()
        else:
            st.sidebar.error("⛔ Invalid key")
    st.stop()

# --- OPENAI CLIENT ---
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- LANGUAGE DICTIONARIES ---
LANGUAGES = {
    "English": {
        "title": "Care Letter Generator",
        "gdpr_title": "GDPR Consent Required",
        "gdpr_info": "We require your consent to process data in line with GDPR guidelines before proceeding.",
        "consent_check": "I consent to data processing under GDPR",
        "consent_warning": "Please consent to GDPR to continue.",
        "settings": "Settings",
        "letter_tone": "Select Tone",
        "tone_help": "Choose a calm or formal complaint tone.",
        "about": "About This Tool",
        "about_text": "Generate professional care-related letters with ease.",
        "letter_category": "Select Letter Category",
        "category_help": "Choose your issue category.",
        "specific_issue": "Select Specific Issue",
        "issue_help": "Choose the detailed issue.",
        "your_details": "Your Details",
        "full_name": "Full Name",
        "contact_info": "Contact Information",
        "generate": "Generate Letter",
        "name_warning": "Please enter your name.",
        "generating": "Generating your letter...",
        "generated_letter": "Generated Letter",
        "download_txt": "Download as .txt",
        "download_doc": "Download as .doc",
        "error_message": "Error:",
        "error_help": "Check your inputs or connection."
    },
    "Español": {
        "title": "Generador de Cartas de Cuidado",
        "gdpr_title": "Consentimiento GDPR Requerido",
        "gdpr_info": "Requerimos su consentimiento para procesar datos de acuerdo con el GDPR antes de continuar.",
        "consent_check": "Consiento el procesamiento de datos bajo GDPR",
        "consent_warning": "Por favor, otorgue su consentimiento GDPR para continuar.",
        "settings": "Configuración",
        "letter_tone": "Seleccione el tono",
        "tone_help": "Elija un tono tranquilo o de queja formal.",
        "about": "Acerca de esta herramienta",
        "about_text": "Genere cartas profesionales relacionadas con el cuidado con facilidad.",
        "letter_category": "Seleccione la categoría de carta",
        "category_help": "Elija la categoría de su problema.",
        "specific_issue": "Seleccione el problema específico",
        "issue_help": "Elija el problema detallado.",
        "your_details": "Sus datos",
        "full_name": "Nombre completo",
        "contact_info": "Información de contacto",
        "generate": "Generar carta",
        "name_warning": "Por favor ingrese su nombre.",
        "generating": "Generando su carta...",
        "generated_letter": "Carta generada",
        "download_txt": "Descargar como .txt",
        "download_doc": "Descargar como .doc",
        "error_message": "Error:",
        "error_help": "Verifique sus entradas o conexión."
    },
    "Français": {
        "title": "Générateur de Lettres de Soins",
        "gdpr_title": "Consentement GDPR Requis",
        "gdpr_info": "Nous nécessitons votre consentement pour traiter les données conformément au RGPD avant de continuer.",
        "consent_check": "Je consens au traitement des données selon le RGPD",
        "consent_warning": "Veuillez fournir votre consentement RGPD pour continuer.",
        "settings": "Paramètres",
        "letter_tone": "Choisir le ton",
        "tone_help": "Choisissez un ton calme ou de plainte formelle.",
        "about": "À propos de cet outil",
        "about_text": "Générez facilement des lettres professionnelles liées aux soins.",
        "letter_category": "Sélectionnez la catégorie de lettre",
        "category_help": "Choisissez la catégorie de votre problème.",
        "specific_issue": "Sélectionnez le problème spécifique",
        "issue_help": "Choisissez le problème détaillé.",
        "your_details": "Vos coordonnées",
        "full_name": "Nom complet",
        "contact_info": "Informations de contact",
        "generate": "Générer la lettre",
        "name_warning": "Veuillez saisir votre nom.",
        "generating": "Génération de votre lettre...",
        "generated_letter": "Lettre générée",
        "download_txt": "Télécharger en .txt",
        "download_doc": "Télécharger en .doc",
        "error_message": "Erreur:",
        "error_help": "Vérifiez vos entrées ou votre connexion."
    }
}

def get_text(key):
    return LANGUAGES[st.session_state.language].get(key, key)

# --- GDPR CONSENT ---
if not st.session_state.gdpr_consent:
    st.sidebar.subheader(get_text("gdpr_title"))
    with st.sidebar.expander("GDPR Info", expanded=True):
        st.write(get_text("gdpr_info"))
    if st.sidebar.checkbox(get_text("consent_check")):
        st.session_state.gdpr_consent = True
        st.experimental_rerun()
    else:
        st.sidebar.warning(get_text("consent_warning"))
    st.stop()

# --- ABOUT PAGE ---
if tab == "About":
    st.title(get_text("about"))
    st.write(get_text("about_text"))
    st.info("Supports English, Español & Français — 2025 UI")
    st.stop()

# --- GENERATE PAGE HEADER ---
st.title("💌 " + get_text("title"))
st.caption("Modern Care Letter Generator — 2025 Edition")

# --- SIDEBAR OPTIONS ---
st.sidebar.selectbox("🌐 Language", list(LANGUAGES.keys()), key="language")
st.sidebar.radio(get_text("letter_tone"), ("Standard", "Serious Formal Complaint"), key="tone")

# --- LETTER TEMPLATES ---
letter_structure = {
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
            "What is your loved one’s diagnosis?",
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
            "What has changed in the person’s condition?",
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
            "What is the person’s current care situation?",
            "Why do you believe the refusal is unfair?",
            "Have you received a written explanation?"
        ],
        "Request carer support plan": [
            "Are you a family carer?",
            "What support are you struggling to provide?",
            "Has a carer’s assessment ever been done?",
            "What help would make a difference?"
        ]
    }
}

# --- PROMPT GENERATION ---
def generate_prompt(cat, sub, answers, user, tone):
    intro = f"Category: {cat}\nIssue: {sub}\n\n"
    details = "".join(f"{q}: {a}\n" for q,a in answers.items() if a)
    tone_instr = (
        "Use a calm, empathetic tone." if tone=="Standard"
        else "Use a formal, assertive tone referencing regulations."
    )
    return intro + details + "\n" + tone_instr + f"\n\nSincerely,\n{user}"

# --- FORM LAYOUT ---
col1, col2 = st.columns([2,1])
with col1:
    category = st.selectbox(get_text("letter_category"), list(letter_structure.keys()), help=get_text("category_help"))
    if category:
        subcats = list(letter_structure[category].keys())
        issue = st.selectbox(get_text("specific_issue"), subcats, help=get_text("issue_help"))
        if issue:
            st.markdown("---")
            st.header(f"📝 {issue}")
            answers = {}
            for q in letter_structure[category][issue]:
                answers[q] = st.text_area(q, height=120)
            st.markdown("---")
            st.subheader(get_text("your_details"))
            user_name = st.text_input(get_text("full_name"))
            contact = st.text_input(get_text("contact_info"))
            if st.button(get_text("generate"), use_container_width=True):
                if not user_name:
                    st.warning(get_text("name_warning"))
                else:
                    with st.spinner(get_text("generating")):
                        prompt = generate_prompt(category, issue, answers, user_name, st.session_state.tone)
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role":"user","content":prompt}],
                            temperature=0.5
                        )
                        letter = response.choices[0].message.content
                    st.success("Done!")
                    with stylable_container(css_styles="{background:#FFF;padding:1rem;border-radius:8px;}"):
                        st.write(letter)
                    d1, d2 = st.columns(2)
                    d1.download_button(get_text("download_txt"), letter, file_name="care_letter.txt")
                    d2.download_button(get_text("download_doc"), letter, file_name="care_letter.doc")
with col2:
    st.metric(label="Version", value="2025.2")
    st.metric(label="Model", value="GPT-4o-Mini")
    st.metric(label="Locale", value=st.session_state.language)

    
