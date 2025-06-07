import json
import streamlit as st
from openai import OpenAI
from typing import Dict, List, Tuple

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

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "language" not in st.session_state:
    st.session_state.language = "English"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "gdpr_consent" not in st.session_state:
    st.session_state.gdpr_consent = False

# --- LICENSE KEY AUTHENTICATION ---
def authenticate(license_key: str) -> bool:
    """Check if license key is valid"""
    try:
        with open(VALID_KEYS_FILE, "r") as f:
            valid_keys = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        valid_keys = []
    
    return license_key in valid_keys

# --- COMPLETE LETTER STRUCTURE ---
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
        "generate_button": "Generate Letter",
        "result_label": "Generated Letter",
        "error_message": "Error generating letter:",
        "download_button": "Download Letter"
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
        "generate_button": "Generar Carta",
        "result_label": "Carta Generada",
        "error_message": "Error al generar la carta:",
        "download_button": "Descargar Carta"
    },
    # Add other languages following the same pattern
}

def t(key: str) -> str:
    """Get translation for the current language"""
    lang_code = LANGUAGES[st.session_state.language]
    return TRANSLATIONS.get(lang_code, {}).get(key, TRANSLATIONS["en"][key])

# --- PROMPT GENERATION ---
def generate_prompt(category: str, subcategory: str, answers: Dict[str, str], user_name: str, tone: str) -> str:
    """Generate the prompt for OpenAI based on user inputs"""
    base_intro = (
        f"You are an experienced care quality advocate who understands regulations in {st.session_state.language}. "
        "Your task is to generate a formal letter that addresses a care-related concern. "
        "The letter should be in the selected language and tone.\n\n"
    )

    context_block = f"Language: {st.session_state.language}\nLetter Category: {category}\nIssue Type: {subcategory}\n\n"

    summary_block = ""
    for q, a in answers.items():
        if a.strip():
            summary_block += f"{q}\n{a.strip()}\n\n"

    if tone == "Serious Formal Complaint":
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

    closing = f"\nSincerely,\n{user_name}"
    
    return base_intro + context_block + summary_block + action_block + closing

# --- MAIN APP ---
def main():
    st.set_page_config(page_title=t("title"), layout="wide")
    
    # Language selector at the top
    st.session_state.language = st.sidebar.selectbox(
        t("language_select"),
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    
    st.title(t("title"))
    
    # Authentication
    if not st.session_state.authenticated:
        license_key = st.text_input(t("license_prompt"), type="password")
        
        if st.button("Submit"):
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
    
    # Tone selection
    tone = st.radio(
        t("tone_label"),
        ("Standard", "Serious Formal Complaint"),
        help=t("tone_help")
    )
    
    # Letter category selection
    selected_category = st.selectbox(
        t("category_label"),
        list(LETTER_STRUCTURE.keys())
    )
    
    if selected_category:
        subcategories = list(LETTER_STRUCTURE[selected_category].keys())
        selected_subcategory = st.selectbox(
            t("subcategory_label"),
            subcategories
        )
        
        if selected_subcategory:
            st.markdown("---")
            st.subheader(t("questions_header"))
            
            # Store answers in session state
            if "answers" not in st.session_state:
                st.session_state.answers = {}
            
            # Create form for questions
            with st.form("letter_form"):
                for question in LETTER_STRUCTURE[selected_category][selected_subcategory]:
                    st.session_state.answers[question] = st.text_area(
                        question,
                        value=st.session_state.answers.get(question, "")
                    )
                
                st.session_state.user_name = st.text_input(
                    t("name_label"),
                    value=st.session_state.user_name
                )
                
                submitted = st.form_submit_button(t("generate_button"))
                
                if submitted:
                    with st.spinner("Generating your letter..."):
                        try:
                            client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                            
                            prompt = generate_prompt(
                                selected_category,
                                selected_subcategory,
                                st.session_state.answers,
                                st.session_state.user_name,
                                tone
                            )
                            
                            response = client.chat.completions.create(
                                model="gpt-4",
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.3 if tone == "Serious Formal Complaint" else 0.7
                            )
                            
                            generated_letter = response.choices[0].message.content
                            st.text_area(
                                t("result_label"),
                                generated_letter,
                                height=400
                            )
                            
                            # Add download button
                            st.download_button(
                                label=t("download_button"),
                                data=generated_letter,
                                file_name=f"care_letter_{selected_category.replace(' ', '_')}.txt",
                                mime="text/plain"
                            )
                            
                        except Exception as e:
                            st.error(f"{t('error_message')} {str(e)}")

if __name__ == "__main__":
    main()
