import json
import streamlit as st
from openai import OpenAI
from typing import Dict, List, Optional
import datetime
import os
import uuid
from pathlib import Path

# --- CONSTANTS ---
VALID_KEYS_FILE = "valid_keys.json"
LETTER_STRUCTURE_FILE = "letter_structure_meta.json"
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

# Load letter structure from JSON file
def load_letter_structure():
    try:
        with open(LETTER_STRUCTURE_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Failed to load letter structure: {str(e)}")
        return {}

LETTER_STRUCTURE = load_letter_structure()

# Initialize valid keys file if it doesn't exist
if not os.path.exists(VALID_KEYS_FILE):
    with open(VALID_KEYS_FILE, "w") as f:
        json.dump([], f)

# --- TRANSLATION DICTIONARY ---
# (Same as original)

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
        "saved_letters": {},
        "meta": {
            "version": "2.1",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d"),
            "letter_count": 0
        }
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
    st.session_state.selected_subcategory = None
    st.rerun()

def save_current_letter():
    """Save the current letter to session state"""
    if not st.session_state.generated_letter:
        st.warning("No letter to save")
        return
    
    if not st.session_state.selected_category or not st.session_state.selected_subcategory:
        st.error("Cannot save - missing category or subcategory")
        return
    
    letter_id = str(uuid.uuid4())[:8]
    subject_template = LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"][st.session_state.selected_subcategory]["subject_template"]
    letter_title = subject_template.format(date=datetime.datetime.now().strftime("%Y-%m-%d"))
    
    st.session_state.saved_letters[letter_title] = {
        "content": st.session_state.generated_letter,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": st.session_state.selected_category,
        "subcategory": st.session_state.selected_subcategory,
        "answers": st.session_state.answers.copy(),
        "recipient": st.session_state.recipient,
        "user_name": st.session_state.user_name,
        "tone": st.session_state.tone,
        "title": letter_title
    }
    
    # Update metadata
    st.session_state.meta["letter_count"] = len(st.session_state.saved_letters)
    st.session_state.meta["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    st.toast(f"Letter saved as: {letter_title}", icon="✅")

def load_letter(letter_title: str):
    """Load a saved letter"""
    letter_data = st.session_state.saved_letters.get(letter_title)
    if letter_data:
        st.session_state.generated_letter = letter_data["content"]
        st.session_state.selected_category = letter_data["category"]
        st.session_state.selected_subcategory = letter_data["subcategory"]
        st.session_state.answers = letter_data.get("answers", {})
        st.session_state.recipient = letter_data.get("recipient", "")
        st.session_state.user_name = letter_data.get("user_name", "")
        st.session_state.tone = letter_data.get("tone", "Standard")
        st.toast(f"Loaded letter: {letter_title}", icon="📄")
        st.rerun()

def delete_letter(letter_title: str):
    """Delete a saved letter"""
    if letter_title in st.session_state.saved_letters:
        del st.session_state.saved_letters[letter_title]
        st.session_state.meta["letter_count"] = len(st.session_state.saved_letters)
        st.toast(f"Deleted letter: {letter_title}", icon="🗑️")
        st.rerun()

# --- PROMPT GENERATION ---
def generate_prompt() -> str:
    """Generate the prompt for OpenAI based on user inputs"""
    if not all([st.session_state.user_name, 
               st.session_state.selected_category, 
               st.session_state.selected_subcategory]):
        return ""
    
    # Get the subcategory metadata
    subcategory_meta = LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"][st.session_state.selected_subcategory]
    
    # Create context block with metadata
    context_block = (
        f"**Context:**\n"
        f"- Language: {st.session_state.language}\n"
        f"- Letter Category: {st.session_state.selected_category}\n"
        f"- Issue Type: {st.session_state.selected_subcategory}\n"
        f"- Subject: {subcategory_meta['subject_template'].format(date=st.session_state.date)}\n"
        f"- Sender: {st.session_state.user_name}\n"
        f"- Recipient: {st.session_state.recipient}\n"
        f"- Date: {st.session_state.date}\n"
        f"- Tone: {st.session_state.tone}\n\n"
    )

    # Create detailed content block from answers
    content_block = "**Details Provided:**\n"
    for q_data in subcategory_meta["questions"]:
        question = q_data["question"]
        answer = st.session_state.answers.get(question, "")
        if answer.strip():
            content_block += f"- {question}: {answer.strip()}\n"
    content_block += "\n"

    # Tone-specific instructions
    if st.session_state.tone == "Serious Formal Complaint":
        instruction_block = (
            "**Instructions:**\n"
            "Write a formal complaint letter with these characteristics:\n"
            "- Professional and legally precise tone\n"
            "- Clear statement of facts without emotion\n"
            "- Reference to relevant regulations and standards\n"
            "- Specific requests for investigation and response\n"
            "- Mention of potential escalation pathways\n"
            "- Polite but firm language\n\n"
        )
    else:
        instruction_block = (
            "**Instructions:**\n"
            "Write a professional advocacy letter with these characteristics:\n"
            "- Clear and concise communication\n"
            "- Respectful tone while being assertive\n"
            "- Specific details about the concern\n"
            "- Reasonable requests for action\n"
            "- Openness to dialogue and resolution\n\n"
        )

    # Formatting requirements
    format_block = (
        "**Format Requirements:**\n"
        "- Use proper business letter format\n"
        "- Include date, recipient address, salutation\n"
        "- Structured paragraphs with clear purpose\n"
        "- Appropriate closing and signature\n"
        f"- Sign off with: Sincerely, {st.session_state.user_name}\n\n"
    )
    
    return context_block + content_block + instruction_block + format_block

# --- UI COMPONENTS ---
def auth_form():
    """Display authentication form"""
    with st.container(border=True):
        st.subheader("License Verification")
        with st.form("auth_form"):
            license_key = st.text_input(t("license_prompt"), type="password")
            
            if st.form_submit_button("Submit", use_container_width=True):
                if authenticate(license_key):
                    st.session_state.authenticated = True
                    st.success(t("access_granted"))
                    st.rerun()
                else:
                    st.error(t("invalid_key"))

def render_question_input(question_data):
    """Render the appropriate input field based on question type"""
    question = question_data["question"]
    default_value = st.session_state.answers.get(question, "")
    
    if question_data["type"] == "text":
        return st.text_area(
            question,
            value=default_value,
            placeholder=question_data.get("placeholder", ""),
            help=question_data.get("help_text", ""),
            key=f"q_{hash(question)}"
        )
    # Add other input types as needed (e.g., select, date, etc.)
    else:
        return st.text_input(
            question,
            value=default_value,
            placeholder=question_data.get("placeholder", ""),
            help=question_data.get("help_text", ""),
            key=f"q_{hash(question)}"
        )

def letter_form():
    """Main letter generation form"""
    with st.form("main_form"):
        # Header section
        st.subheader("Letter Details")
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.user_name = st.text_input(
                t("name_label"),
                value=st.session_state.user_name,
                placeholder="Your full name"
            )
            
            st.session_state.recipient = st.text_input(
                t("recipient_label"),
                value=st.session_state.recipient,
                placeholder="Recipient organization or department"
            )
            
        with col2:
            st.session_state.date = st.date_input(
                t("date_label"),
                value=datetime.datetime.strptime(st.session_state.date, "%Y-%m-%d").date() if isinstance(st.session_state.date, str) else datetime.date.today()
            ).strftime("%Y-%m-%d")
            
            st.session_state.tone = st.selectbox(
                t("tone_label"),
                ("Standard", "Serious Formal Complaint"),
                index=0 if st.session_state.tone == "Standard" else 1,
                help=t("tone_help")
            )
        
        # Category selection
        st.divider()
        st.subheader("Letter Type")
        
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
        
        # Subcategory selection
        if st.session_state.selected_category:
            subcategory_options = list(LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"].keys())
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
            
            # Questions section
            if st.session_state.selected_subcategory:
                st.divider()
                st.subheader(t("questions_header"))
                
                questions = LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"][st.session_state.selected_subcategory]["questions"]
                for question_data in questions:
                    answer = render_question_input(question_data)
                    if answer:
                        st.session_state.answers[question_data["question"]] = answer
        
        # Form actions
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            generate_clicked = st.form_submit_button(
                t("generate_button"), 
                use_container_width=True,
                type="primary"
            )
        with col2:
            clear_clicked = st.form_submit_button(
                t("clear_button"),
                use_container_width=True
            )
        with col3:
            if st.session_state.generated_letter:
                save_clicked = st.form_submit_button(
                    t("save_button"),
                    use_container_width=True
                )
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
                with st.spinner("Generating your professional letter..."):
                    try:
                        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                        prompt = generate_prompt()
                        
                        # Debug: Show prompt in expander
                        with st.expander("Debug: View Prompt Sent to AI"):
                            st.text(prompt)
                        
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.3 if st.session_state.tone == "Serious Formal Complaint" else 0.7
                        )
                        st.session_state.generated_letter = response.choices[0].message.content
                        st.session_state.meta["letter_count"] += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_message')} {str(e)}")
                        st.exception(e)

def letter_display():
    """Display the generated letter"""
    if not st.session_state.generated_letter:
        return
    
    st.subheader(t("result_label"))
    
    # Letter display with copy button
    with st.container(border=True):
        st.markdown(f"**To:** {st.session_state.recipient}")
        st.markdown(f"**Date:** {st.session_state.date}")
        
        if st.session_state.selected_category and st.session_state.selected_subcategory:
            subject_template = LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"][st.session_state.selected_subcategory]["subject_template"]
            st.markdown(f"**Subject:** {subject_template.format(date=st.session_state.date)}")
        
        st.divider()
        
        st.text_area(
            "Letter Content",
            st.session_state.generated_letter,
            height=400,
            label_visibility="collapsed",
            key="letter_display"
        )
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label=t("download_button"),
                data=st.session_state.generated_letter,
                file_name=f"care_letter_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            if st.button("Copy to Clipboard", use_container_width=True):
                st.session_state.clipboard = st.session_state.generated_letter
                st.toast("Copied to clipboard!", icon="📋")
        with col3:
            if st.button("Save Letter", use_container_width=True):
                save_current_letter()

def saved_letters_panel():
    """Display saved letters in sidebar"""
    if not st.session_state.saved_letters:
        return
    
    with st.sidebar.expander("📂 Saved Letters", expanded=True):
        for title, letter_data in st.session_state.saved_letters.items():
            cols = st.columns([4,1])
            with cols[0]:
                if st.button(title, key=f"load_{title}", use_container_width=True):
                    load_letter(title)
            with cols[1]:
                if st.button("🗑️", key=f"del_{title}", help="Delete this letter"):
                    delete_letter(title)

# --- MAIN APP ---
def main():
    # Page configuration with metadata
    st.set_page_config(
        page_title=t("title"),
        layout="wide",
        page_icon="✉️",
        menu_items={
            'Get Help': 'https://example.com/help',
            'Report a bug': "https://example.com/bug",
            'About': f"""
            ## Care Quality Advocacy Letter Generator
            
            Version: {st.session_state.meta['version']}  
            Letters Generated: {st.session_state.meta['letter_count']}  
            Last Updated: {st.session_state.meta['last_updated']}  
            
            This tool helps create professional letters for care quality concerns.
            """
        }
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .stTextArea textarea {
            min-height: 100px;
        }
        .stButton button {
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            transform: scale(1.02);
        }
        div[data-testid="stExpander"] details {
            background: #f0f2f6;
            border-radius: 8px;
            padding: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar components
    with st.sidebar:
        # Language selector
        st.session_state.language = st.selectbox(
            t("language_select"),
            list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.language),
            key="lang_select"
        )
        
        # GDPR consent
        st.session_state.gdpr_consent = st.checkbox(
            t("gdpr_label"),
            value=st.session_state.gdpr_consent
        )
        
        # Saved letters panel
        saved_letters_panel()
        
        # App metadata
        with st.expander("ℹ️ About This App"):
            st.markdown(f"""
            **Version:** {st.session_state.meta['version']}  
            **Letters Generated:** {st.session_state.meta['letter_count']}  
            **Last Updated:** {st.session_state.meta['last_updated']}  
            
            This tool helps create professional letters for care quality concerns.
            """)
    
    # Main content area
    st.title(t("title"))
    
    # Authentication check
    if not st.session_state.authenticated:
        auth_form()
        return
    
    # GDPR consent check
    if not st.session_state.gdpr_consent:
        st.warning(t("gdpr_warning"))
        return
    
    # Main form and letter display
    letter_form()
    letter_display()

if __name__ == "__main__":
    main()
