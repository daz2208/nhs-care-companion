import json
import streamlit as st
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import datetime
import os
import logging
from enum import Enum

# --- Setup logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONSTANTS ---
VALID_KEYS_FILE = "valid_keys.json"
LETTERS_HISTORY_FILE = "letters_history.json"
USER_SETTINGS_FILE = "user_settings.json"

class LetterTone(Enum):
    STANDARD = "Standard"
    SERIOUS = "Serious Formal Complaint"

# --- Language and Translation Management ---
class TranslationManager:
    def __init__(self):
        self.languages = {
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
        
        self.translations = {
            "en": self._load_english_translations(),
            "es": self._load_spanish_translations(),
            # Other languages would be loaded here
        }
    
    def _load_english_translations(self):
        return {
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
            "load_button": "Load Letter",
            "format_options": "Formatting Options",
            "font_style": "Font Style",
            "font_size": "Font Size",
            "line_spacing": "Line Spacing",
            "letter_stats": "Letter Statistics",
            "word_count": "Word Count",
            "char_count": "Character Count",
            "generation_time": "Generation Time",
            "last_updated": "Last Updated"
        }
    
    def _load_spanish_translations(self):
        return {
            "title": "Generador de Cartas de Defensa de la Calidad del Cuidado",
            # ... other Spanish translations
        }
    
    def get_languages(self):
        return self.languages
    
    def get_translation(self, key: str, language: str = "en") -> str:
        """Get translation for a specific key and language"""
        lang_code = self.languages.get(language, "en")
        return self.translations.get(lang_code, {}).get(key, self.translations["en"].get(key, key))

# Initialize translation manager
translation_manager = TranslationManager()

# --- Letter Structure ---
class LetterStructure:
    def __init__(self):
        self.structure = self._load_structure()
    
    def _load_structure(self) -> Dict:
        return {
            "Care Complaint Letter": {
                "Neglect or injury": [
                    "Who was harmed?",
                    "Where did it happen?",
                    "What happened?",
                    "What was the result?",
                    "Have you raised this already?"
                ],
                # ... other categories and subcategories
            }
        }
    
    def get_categories(self) -> List[str]:
        return list(self.structure.keys())
    
    def get_subcategories(self, category: str) -> List[str]:
        return list(self.structure.get(category, {}).keys())
    
    def get_questions(self, category: str, subcategory: str) -> List[str]:
        return self.structure.get(category, {}).get(subcategory, [])

letter_structure = LetterStructure()

# --- Session State Management ---
class SessionStateManager:
    def __init__(self):
        self.default_state = {
            "authenticated": False,
            "language": "English",
            "user_name": "",
            "gdpr_consent": False,
            "answers": {},
            "generated_letter": "",
            "selected_category": None,
            "selected_subcategory": None,
            "tone": LetterTone.STANDARD.value,
            "recipient": "",
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "saved_letters": {},
            "letter_stats": {},
            "font_style": "Arial",
            "font_size": 12,
            "line_spacing": 1.5
        }
        
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize all session state variables"""
        for key, value in self.default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def reset_form(self):
        """Reset form inputs while preserving settings"""
        st.session_state.answers = {}
        st.session_state.generated_letter = ""
        st.session_state.letter_stats = {}
    
    def clear_all(self):
        """Clear all session state except authentication"""
        auth_state = st.session_state.authenticated
        for key in self.default_state.keys():
            if key != "authenticated":
                st.session_state[key] = self.default_state[key]
        st.session_state.authenticated = auth_state

state_manager = SessionStateManager()

# --- Authentication and License Management ---
class AuthManager:
    def __init__(self):
        self.valid_keys_file = VALID_KEYS_FILE
        self._initialize_keys_file()
    
    def _initialize_keys_file(self):
        """Create valid keys file if it doesn't exist"""
        if not os.path.exists(self.valid_keys_file):
            with open(self.valid_keys_file, "w") as f:
                json.dump([], f)
    
    def authenticate(self, license_key: str) -> Tuple[bool, str]:
        """Check if license key is valid"""
        try:
            with open(self.valid_keys_file, "r") as f:
                valid_keys = json.load(f)
            
            if license_key.strip() in valid_keys:
                return True, "Authentication successful"
            return False, "Invalid license key"
        
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading valid keys: {str(e)}")
            return False, "Error validating license key"
        
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            return False, "System error during authentication"

auth_manager = AuthManager()

# --- Letter Generation ---
class LetterGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        self.last_generation_time = None
    
    def generate_prompt(self) -> str:
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
            f"Date: {st.session_state.date}\n"
            f"Tone: {st.session_state.tone}\n\n"
        )

        summary_block = ""
        for q, a in st.session_state.answers.items():
            if a.strip():
                summary_block += f"{q}\n{a.strip()}\n\n"

        if st.session_state.tone == LetterTone.SERIOUS.value:
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
    
    def generate_letter(self) -> Tuple[str, Dict]:
        """Generate the letter using OpenAI API"""
        start_time = datetime.datetime.now()
        
        try:
            prompt = self.generate_prompt()
            if not prompt:
                return "", {"error": "Incomplete input data"}
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3 if st.session_state.tone == LetterTone.SERIOUS.value else 0.7
            )
            
            content = response.choices[0].message.content
            end_time = datetime.datetime.now()
            
            # Calculate statistics
            word_count = len(content.split())
            char_count = len(content)
            generation_time = (end_time - start_time).total_seconds()
            
            stats = {
                "word_count": word_count,
                "char_count": char_count,
                "generation_time": f"{generation_time:.2f} seconds",
                "last_updated": end_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.last_generation_time = generation_time
            return content, stats
            
        except Exception as e:
            logger.error(f"Error generating letter: {str(e)}")
            return "", {"error": str(e)}

letter_generator = LetterGenerator()

# --- UI Components ---
class UIComponents:
    def __init__(self):
        self.t = translation_manager.get_translation
    
    def display_auth_form(self):
        """Display authentication form"""
        with st.form("auth_form"):
            license_key = st.text_input(self.t("license_prompt"), type="password")
            
            if st.form_submit_button("Submit"):
                authenticated, message = auth_manager.authenticate(license_key)
                if authenticated:
                    st.session_state.authenticated = True
                    st.success(self.t("access_granted"))
                else:
                    st.error(message)
    
    def display_letter(self):
        """Display the generated letter and related options"""
        st.subheader(self.t("result_label"))
        
        # Display letter with formatting options
        formatted_letter = self._apply_formatting(st.session_state.generated_letter)
        st.text_area(
            "Letter Content",
            formatted_letter,
            height=400,
            label_visibility="collapsed"
        )
        
        # Display statistics
        if st.session_state.letter_stats:
            self._display_stats()
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label=self.t("download_button"),
                data=st.session_state.generated_letter,
                file_name=self._generate_filename(),
                mime="text/plain"
            )
        with col2:
            if st.button(self.t("save_button")):
                self._save_current_letter()
        with col3:
            if st.button(self.t("clear_button")):
                state_manager.reset_form()
                st.rerun()
    
    def _apply_formatting(self, text: str) -> str:
        """Apply formatting options to the letter"""
        # In a real app, this would apply the selected font, size, etc.
        return text
    
    def _generate_filename(self) -> str:
        """Generate a filename for the downloaded letter"""
        category = st.session_state.selected_category or "letter"
        date = datetime.datetime.now().strftime("%Y%m%d")
        return f"{category.replace(' ', '_')}_{date}.txt"
    
    def _display_stats(self):
        """Display letter statistics"""
        with st.expander(self.t("letter_stats")):
            cols = st.columns(2)
            with cols[0]:
                st.metric(self.t("word_count"), st.session_state.letter_stats.get("word_count", 0))
                st.metric(self.t("char_count"), st.session_state.letter_stats.get("char_count", 0))
            with cols[1]:
                st.metric(self.t("generation_time"), st.session_state.letter_stats.get("generation_time", "N/A"))
                st.metric(self.t("last_updated"), st.session_state.letter_stats.get("last_updated", "N/A"))
    
    def _save_current_letter(self):
        """Save the current letter to session state"""
        if not st.session_state.generated_letter:
            st.warning("No letter to save")
            return
        
        letter_title = f"{st.session_state.selected_category} - {st.session_state.selected_subcategory}"
        st.session_state.saved_letters[letter_title] = {
            "content": st.session_state.generated_letter,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": st.session_state.selected_category,
            "subcategory": st.session_state.selected_subcategory,
            "answers": st.session_state.answers.copy(),
            "stats": st.session_state.letter_stats.copy()
        }
        st.success("Letter saved successfully!")
    
    def display_main_form(self):
        """Display the main letter generation form"""
        with st.form("main_form"):
            # Header section
            self._display_form_header()
            
            # Letter details section
            self._display_letter_details()
            
            # Category selection
            self._display_category_selection()
            
            # Questions section
            if st.session_state.selected_subcategory:
                self._display_questions_section()
            
            # Formatting options
            self._display_formatting_options()
            
            # Form actions
            self._display_form_actions()
    
    def _display_form_header(self):
        """Display the form header section"""
        st.subheader("Letter Details")
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.user_name = st.text_input(
                self.t("name_label"),
                value=st.session_state.user_name,
                help="Your name as it will appear in the letter signature"
            )
            
            st.session_state.recipient = st.text_input(
                self.t("recipient_label"),
                value=st.session_state.recipient,
                help="The organization or person you're addressing"
            )
            
        with col2:
            st.session_state.date = st.date_input(
                self.t("date_label"),
                value=datetime.datetime.strptime(st.session_state.date, "%Y-%m-%d").date() 
                if isinstance(st.session_state.date, str) else datetime.date.today()
            ).strftime("%Y-%m-%d")
            
            st.session_state.tone = st.radio(
                self.t("tone_label"),
                [tone.value for tone in LetterTone],
                index=0 if st.session_state.tone == LetterTone.STANDARD.value else 1,
                help=self.t("tone_help")
            )
    
    def _display_letter_details(self):
        """Display letter details section"""
        pass  # Additional details could go here
    
    def _display_category_selection(self):
        """Display category selection section"""
        st.divider()
        st.subheader("Letter Content")
        
        # Letter category selection
        st.session_state.selected_category = st.selectbox(
            self.t("category_label"),
            letter_structure.get_categories(),
            index=letter_structure.get_categories().index(st.session_state.selected_category) 
            if st.session_state.selected_category in letter_structure.get_categories() else 0,
            help="Select the most relevant category for your concern"
        )
        
        if st.session_state.selected_category:
            subcategories = letter_structure.get_subcategories(st.session_state.selected_category)
            st.session_state.selected_subcategory = st.selectbox(
                self.t("subcategory_label"),
                subcategories,
                index=subcategories.index(st.session_state.selected_subcategory) 
                if st.session_state.selected_subcategory in subcategories else 0,
                help="Select the specific issue type"
            )
    
    def _display_questions_section(self):
        """Display the questions section"""
        st.divider()
        st.subheader(self.t("questions_header"))
        
        # Create form for questions
        for question in letter_structure.get_questions(
            st.session_state.selected_category, 
            st.session_state.selected_subcategory
        ):
            st.session_state.answers[question] = st.text_area(
                question,
                value=st.session_state.answers.get(question, ""),
                key=f"q_{hash(question)}",  # Unique key for each question
                help="Provide as much detail as possible"
            )
    
    def _display_formatting_options(self):
        """Display formatting options"""
        st.divider()
        with st.expander(self.t("format_options")):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state.font_style = st.selectbox(
                    self.t("font_style"),
                    ["Arial", "Times New Roman", "Courier New"],
                    index=["Arial", "Times New Roman", "Courier New"].index(st.session_state.font_style)
                )
            with col2:
                st.session_state.font_size = st.slider(
                    self.t("font_size"),
                    min_value=10,
                    max_value=16,
                    value=st.session_state.font_size
                )
            with col3:
                st.session_state.line_spacing = st.select_slider(
                    self.t("line_spacing"),
                    options=[1.0, 1.15, 1.5, 2.0],
                    value=st.session_state.line_spacing
                )
    
    def _display_form_actions(self):
        """Display form action buttons"""
        st.divider()
        generate_clicked = st.form_submit_button(
            self.t("generate_button"),
            help="Generate the letter based on your inputs"
        )
        
        if generate_clicked:
            self._handle_generation()
    
    def _handle_generation(self):
        """Handle letter generation"""
        if not all([st.session_state.user_name, st.session_state.selected_category, 
                   st.session_state.selected_subcategory]):
            st.error("Please fill in all required fields")
            return
        
        with st.spinner("Generating your letter..."):
            try:
                letter_content, stats = letter_generator.generate_letter()
                if stats.get("error"):
                    st.error(f"{self.t('error_message')} {stats['error']}")
                else:
                    st.session_state.generated_letter = letter_content
                    st.session_state.letter_stats = stats
                    st.rerun()
            except Exception as e:
                st.error(f"{self.t('error_message')} {str(e)}")

# --- Main App ---
def main():
    # Configure page
    st.set_page_config(
        page_title=translation_manager.get_translation("title"), 
        layout="wide",
        page_icon="✉️"
    )
    
    # Initialize UI components
    ui = UIComponents()
    
    # Sidebar
    with st.sidebar:
        # Language selection
        st.session_state.language = st.selectbox(
            ui.t("language_select"),
            list(translation_manager.get_languages().keys()),
            index=list(translation_manager.get_languages().keys()).index(st.session_state.language)
        )
        
        # Saved letters
        if st.session_state.authenticated and st.session_state.saved_letters:
            st.subheader(ui.t("saved_letters"))
            for title in st.session_state.saved_letters.keys():
                if st.button(title):
                    ui._load_letter(title)
    
    # Main content
    st.title(ui.t("title"))
    
    # Authentication
    if not st.session_state.authenticated:
        ui.display_auth_form()
        return
    
    # GDPR Consent
    st.session_state.gdpr_consent = st.checkbox(ui.t("gdpr_label"))
    if not st.session_state.gdpr_consent:
        st.warning(ui.t("gdpr_warning"))
        return
    
    # Main form
    ui.display_main_form()
    
    # Display generated letter
    if st.session_state.generated_letter:
        ui.display_letter()

if __name__ == "__main__":
    main()
