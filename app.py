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
    # ... [rest of your existing LETTER_STRUCTURE content]
    # Make sure to include all your original categories and subcategories
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
        # ... [your Spanish translations]
    },
    # ... [other language translations]
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
        st.session_state.selected_category = st.selectbox(
            t("category_label"),
            list(LETTER_STRUCTURE.keys()),
            index=list(LETTER_STRUCTURE.keys()).index(st.session_state.selected_category) 
            if st.session_state.selected_category in LETTER_STRUCTURE else 0
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
            if st.session_state.generated_letter:
                save_clicked = st.form_submit_button(t("save_button"))
            else:
                save_clicked = False

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
    
    # Handle form actions
    if st.session_state.get("clear_clicked", False):
        clear_form()
    
    if st.session_state.get("save_clicked", False) and st.session_state.generated_letter:
        save_current_letter()
    
    # Generate letter if requested
    if st.session_state.get("generate_clicked", False):
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
    
    # Display generated letter
    if st.session_state.generated_letter:
        display_letter()

if __name__ == "__main__":
    main()
