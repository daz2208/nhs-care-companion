import json
import streamlit as st
from openai import OpenAI
from streamlit_extras.stylable_container import stylable_container

# --- SETUP ---
VALID_KEYS_FILE = "valid_keys.json"

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "gdpr_consent" not in st.session_state:
    st.session_state.gdpr_consent = False
if "language" not in st.session_state:
    st.session_state.language = "English"

# Language dictionaries
LANGUAGES = {
    "English": {
        "title": "Care Letter Generator",
        "auth_description": "This tool helps you create professional letters for care-related concerns, complaints, and advocacy needs. Please authenticate to continue.",
        "authenticate": "Authenticate",
        "access_granted": "✅ Access granted. Welcome.",
        "invalid_key": "⚠️ Invalid or already-used license key.",
        "gdpr_title": "Data Processing Consent",
        "gdpr_info": """
            To use this service, we need your consent to process your data in accordance with GDPR regulations:
            
            - We only process the information you provide to generate your letter
            - No personal data is stored after your session ends
            - You can withdraw consent by closing this application
        """,
        "consent_check": "I consent to data processing (GDPR)",
        "continue": "Continue",
        "consent_warning": "You must consent to GDPR processing to continue.",
        "settings": "Settings",
        "letter_tone": "Letter Tone:",
        "tone_help": "Choose the appropriate tone for your situation",
        "about": "About",
        "about_text": """
            This tool helps you create professional:
            - Care complaints
            - Advocacy letters
            - Support requests
            - Regulatory notifications
        """,
        "create_letter": "Create Your Letter",
        "letter_category": "Letter Category",
        "category_help": "Select the main purpose of your letter",
        "specific_issue": "Specific Issue",
        "issue_help": "Select the specific situation you're addressing",
        "your_details": "Your Details",
        "full_name": "Your Full Name",
        "contact_info": "Contact Information (optional)",
        "generate": "Generate Letter",
        "name_warning": "Please enter your name before generating the letter",
        "generating": "Generating your professional letter...",
        "generated_letter": "Generated Letter",
        "download_txt": "📄 Download as TXT",
        "download_doc": "📝 Download as DOC",
        "regenerate": "🔄 Generate Again",
        "error_message": "An error occurred:",
        "error_help": "Please try again or contact support if the problem persists."
    },
    "Español": {
        "title": "Generador de Cartas de Cuidado",
        "auth_description": "Esta herramienta le ayuda a crear cartas profesionales para preocupaciones, quejas y necesidades de defensa relacionadas con el cuidado. Por favor autentíquese para continuar.",
        "authenticate": "Autenticar",
        "access_granted": "✅ Acceso concedido. Bienvenido.",
        "invalid_key": "⚠️ Clave inválida o ya utilizada.",
        "gdpr_title": "Consentimiento de Procesamiento de Datos",
        "gdpr_info": """
            Para usar este servicio, necesitamos su consentimiento para procesar sus datos de acuerdo con las regulaciones GDPR:
            
            - Solo procesamos la información que usted proporciona para generar su carta
            - No almacenamos datos personales después de que finaliza su sesión
            - Puede retirar el consentimiento cerrando esta aplicación
        """,
        "consent_check": "Doy mi consentimiento para el procesamiento de datos (GDPR)",
        "continue": "Continuar",
        "consent_warning": "Debe consentir el procesamiento de datos GDPR para continuar.",
        "settings": "Configuración",
        "letter_tone": "Tono de la Carta:",
        "tone_help": "Elija el tono apropiado para su situación",
        "about": "Acerca de",
        "about_text": """
            Esta herramienta ayuda a crear:
            - Quejas sobre cuidados
            - Cartas de defensa
            - Solicitudes de apoyo
            - Notificaciones regulatorias
        """,
        "create_letter": "Crear Su Carta",
        "letter_category": "Categoría de Carta",
        "category_help": "Seleccione el propósito principal de su carta",
        "specific_issue": "Problema Específico",
        "issue_help": "Seleccione la situación específica que está abordando",
        "your_details": "Sus Datos",
        "full_name": "Su Nombre Completo",
        "contact_info": "Información de Contacto (opcional)",
        "generate": "Generar Carta",
        "name_warning": "Por favor ingrese su nombre antes de generar la carta",
        "generating": "Generando su carta profesional...",
        "generated_letter": "Carta Generada",
        "download_txt": "📄 Descargar como TXT",
        "download_doc": "📝 Descargar como DOC",
        "regenerate": "🔄 Generar Nuevamente",
        "error_message": "Ocurrió un error:",
        "error_help": "Por favor intente nuevamente o contacte al soporte si el problema persiste."
    },
    "Français": {
        "title": "Générateur de Lettres de Soins",
        "auth_description": "Cet outil vous aide à créer des lettres professionnelles pour des préoccupations, des plaintes et des besoins de plaidoyer liés aux soins. Veuillez vous authentifier pour continuer.",
        "authenticate": "S'authentifier",
        "access_granted": "✅ Accès accordé. Bienvenue.",
        "invalid_key": "⚠️ Clé invalide ou déjà utilisée.",
        "gdpr_title": "Consentement au Traitement des Données",
        "gdpr_info": """
            Pour utiliser ce service, nous avons besoin de votre consentement pour traiter vos données conformément aux réglementations GDPR:
            
            - Nous ne traitons que les informations que vous fournissez pour générer votre lettre
            - Aucune donnée personnelle n'est stockée après la fin de votre session
            - Vous pouvez retirer votre consentement en fermant cette application
        """,
        "consent_check": "Je consens au traitement des données (GDPR)",
        "continue": "Continuer",
        "consent_warning": "Vous devez consentir au traitement des données GDPR pour continuer.",
        "settings": "Paramètres",
        "letter_tone": "Ton de la Lettre:",
        "tone_help": "Choisissez le ton approprié pour votre situation",
        "about": "À propos",
        "about_text": """
            Cet outil aide à créer:
            - Plaintes concernant les soins
            - Lettres de plaidoyer
            - Demandes de soutien
            - Notifications réglementaires
        """,
        "create_letter": "Créer Votre Lettre",
        "letter_category": "Catégorie de Lettre",
        "category_help": "Sélectionnez l'objectif principal de votre lettre",
        "specific_issue": "Problème Spécifique",
        "issue_help": "Sélectionnez la situation spécifique que vous abordez",
        "your_details": "Vos Coordonnées",
        "full_name": "Votre Nom Complet",
        "contact_info": "Coordonnées (optionnel)",
        "generate": "Générer la Lettre",
        "name_warning": "Veuillez entrer votre nom avant de générer la lettre",
        "generating": "Génération de votre lettre professionnelle...",
        "generated_letter": "Lettre Générée",
        "download_txt": "📄 Télécharger en TXT",
        "download_doc": "📝 Télécharger en DOC",
        "regenerate": "🔄 Régénérer",
        "error_message": "Une erreur est survenue:",
        "error_help": "Veuillez réessayer ou contacter le support si le problème persiste."
    }
}

def get_text(key):
    """Helper function to get translated text"""
    return LANGUAGES[st.session_state.language].get(key, key)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        .main {
            max-width: 900px;
            padding: 2rem;
        }
        .header {
            color: #2b5876;
            font-size: 2.5rem;
            margin-bottom: 1.5rem;
        }
        .subheader {
            color: #4e4376;
            font-size: 1.5rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        .stButton>button {
            background-color: #4e4376;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            border: none;
        }
        .stButton>button:hover {
            background-color: #2b5876;
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
            padding: 0.5rem;
        }
        .stSelectbox>div>div>select {
            border-radius: 8px;
            padding: 0.5rem;
        }
        .stRadio>div {
            flex-direction: row;
            gap: 2rem;
        }
        .stRadio>div>label {
            margin-right: 2rem;
        }
        .success-box {
            background-color: #e6f7e6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .warning-box {
            background-color: #fff3e6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .generated-letter {
            background-color: #f9f9f9;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #4e4376;
            margin: 1.5rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
if not st.session_state.authenticated:
    st.markdown(f"<div class='header'>{get_text('title')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin-bottom: 2rem;'>{get_text('auth_description')}</div>", unsafe_allow_html=True)
    
    with st.form("auth_form"):
        license_key = st.text_input("Enter your license key", type="password")
        submit_button = st.form_submit_button(get_text("authenticate"))
        
        if submit_button:
            try:
                with open(VALID_KEYS_FILE, "r") as f:
                    valid_keys = json.load(f)
            except FileNotFoundError:
                valid_keys = []

            if license_key in valid_keys:
                st.session_state.authenticated = True
                st.markdown(f"<div class='success-box'>{get_text('access_granted')}</div>", unsafe_allow_html=True)
              st.rerun()

            else:
                st.markdown(f"<div class='warning-box'>{get_text('invalid_key')}</div>", unsafe_allow_html=True)

    st.stop()

# --- MAIN APP ---
st.markdown(f"<div class='header'>{get_text('title')}</div>", unsafe_allow_html=True)

# GDPR Consent
if not st.session_state.gdpr_consent:
    st.markdown(f"<div class='subheader'>{get_text('gdpr_title')}</div>", unsafe_allow_html=True)
    with st.expander("GDPR Information", expanded=True):
        st.markdown(get_text("gdpr_info"), unsafe_allow_html=True)
    
    gdpr_consent = st.checkbox(get_text("consent_check"))
    if st.button(get_text("continue")):
        if gdpr_consent:
            st.session_state.gdpr_consent = True
            st.experimental_rerun()
        else:
            st.warning(get_text("consent_warning"))
    st.stop()

# --- OPENAI SETUP ---
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- LETTER STRUCTURE (same as before) ---
letter_structure = {
    # ... [keep the same letter structure dictionary as in your original code] ...
}

# --- IMPROVED PROMPT GENERATION WITH MULTILINGUAL SUPPORT ---
def generate_prompt(category, subcategory, answers, user_name, tone):
    language_instructions = {
        "English": {
            "tone": {
                "Standard": "Use a professional yet approachable tone that clearly communicates concerns while maintaining constructive dialogue.",
                "Serious Formal Complaint": "Use formal, assertive language with explicit references to regulatory standards and clear demands for action."
            },
            "structure": "Structure the letter in standard English business format with appropriate salutations and closings."
        },
        "Español": {
            "tone": {
                "Standard": "Utilice un tono profesional pero accesible que comunique claramente las preocupaciones manteniendo un diálogo constructivo.",
                "Serious Formal Complaint": "Utilice un lenguaje formal y asertivo con referencias explícitas a estándares regulatorios y demandas claras de acción."
            },
            "structure": "Estructura la carta en formato comercial estándar en español con saludos y cierres apropiados."
        },
        "Français": {
            "tone": {
                "Standard": "Utilisez un tono professionnel mais accessible qui communique clairement les préoccupations tout en maintenant un dialogue constructif.",
                "Serious Formal Complaint": "Utilisez un langage formel et assertif avec des références explicites aux normes réglementaires et des demandes d'action claires."
            },
            "structure": "Structurez la lettre dans un format commercial standard en français avec des salutations et des formules de politesse appropriées."
        }
    }
    
    lang = st.session_state.language
    tone_desc = language_instructions[lang]["tone"][tone]
    structure = language_instructions[lang]["structure"]
    
    prompt = f"""
    Generate a {tone.lower()} letter in {lang} regarding {subcategory} under {category}.
    
    **User Provided Information:**
    {json.dumps(answers, indent=2)}
    
    **Requirements:**
    - Language: {lang}
    - Address to appropriate recipient based on category
    - Clear subject line summarizing the issue
    - Structured in professional letter format: {structure}
    - Tone: {tone_desc}
    - Include relevant regulations/standards where appropriate
    - Specify expected response timeframe (typically 14 days)
    - Closing with "{user_name}" and contact information reminder
    
    **Special Instructions:**
    - For complaints, include escalation pathway
    - For advocacy, emphasize rights and needs
    - For praise, be specific about positive impact
    - Ensure all content is culturally appropriate for {lang} speakers
    """
    
    return prompt

# --- MAIN FORM UI ---
with st.sidebar:
    st.markdown(f"### {get_text('settings')}")
    
    # Language selector
    st.session_state.language = st.selectbox(
        "Language / Idioma / Langue",
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    tone = st.radio(
        get_text("letter_tone"),
        ("Standard", "Serious Formal Complaint"),
        help=get_text("tone_help")
    )
    
    st.markdown("---")
    st.markdown(f"### {get_text('about')}")
    st.markdown(get_text("about_text"), unsafe_allow_html=True)

# Main form
st.markdown(f"<div class='subheader'>{get_text('create_letter')}</div>", unsafe_allow_html=True)

with st.form("letter_form"):
    # Category selection
    cols = st.columns(2)
    with cols[0]:
        selected_category = st.selectbox(
            get_text("letter_category"),
            list(letter_structure.keys()),
            help=get_text("category_help")
        )
    
    # Subcategory selection
    if selected_category:
        with cols[1]:
            subcategories = list(letter_structure[selected_category].keys())
            selected_subcategory = st.selectbox(
                get_text("specific_issue"),
                subcategories,
                help=get_text("issue_help")
            )
    
    # Dynamic questions
    if selected_subcategory:
        st.markdown("---")
        st.markdown(f"### About the {selected_subcategory}")
        
        user_answers = {}
        for i, question in enumerate(letter_structure[selected_category][selected_subcategory]):
            user_answers[question] = st.text_area(
                question,
                key=f"q_{i}",
                placeholder="Provide details here..." if st.session_state.language == "English" else 
                      "Proporcione detalles aquí..." if st.session_state.language == "Español" else
                      "Fournissez des détails ici...",
                height=100 if len(question) > 50 else 80
            )
    
    # User details
    st.markdown("---")
    st.markdown(f"### {get_text('your_details')}")
    user_cols = st.columns(2)
    with user_cols[0]:
        user_name = st.text_input(get_text("full_name"), placeholder=get_text("full_name"))
    with user_cols[1]:
        user_contact = st.text_input(get_text("contact_info"), placeholder="Email/phone")
    
    # Submission
    submit_button = st.form_submit_button(get_text("generate"))

# --- LETTER GENERATION ---
if submit_button:
    if not user_name:
        st.warning(get_text("name_warning"))
    else:
        with st.spinner(get_text("generating")):
            try:
                full_prompt = generate_prompt(
                    selected_category,
                    selected_subcategory,
                    user_answers,
                    user_name,
                    tone
                )
                
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system", 
                            "content": f"You are a professional care quality advocate with expertise in health and social care regulations. Respond in {st.session_state.language}."
                        },
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.3 if tone == "Serious Formal Complaint" else 0.7
                )
                
                generated_letter = response.choices[0].message.content
                
                # Display results
                st.markdown("---")
                st.markdown(f"<div class='subheader'>{get_text('generated_letter')}</div>", unsafe_allow_html=True)
                
                with stylable_container(
                    key="generated_letter",
                    css_styles="""
                        {
                            background-color: #f8f9fa;
                            border-radius: 8px;
                            padding: 1.5rem;
                            border-left: 4px solid #4e4376;
                            white-space: pre-wrap;
                        }
                    """
                ):
                    st.markdown(generated_letter)
                
                # Download options
                st.markdown("---")
                dl_cols = st.columns(3)
                with dl_cols[0]:
                    st.download_button(
                        label=get_text("download_txt"),
                        data=generated_letter,
                        file_name=f"care_letter_{selected_subcategory.replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
                with dl_cols[1]:
                    st.download_button(
                        label=get_text("download_doc"),
                        data=generated_letter,
                        file_name=f"care_letter_{selected_subcategory.replace(' ', '_')}.doc",
                        mime="application/msword"
                    )
                with dl_cols[2]:
                    if st.button(get_text("regenerate")):
                        st.experimental_rerun()
                
            except Exception as e:
                st.error(f"{get_text('error_message')} {str(e)}")
                st.error(get_text("error_help"))
