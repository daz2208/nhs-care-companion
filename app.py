import streamlit as st
import json
import datetime
import uuid
from openai import OpenAI

# ----- PAGE CONFIG -----
st.set_page_config(
    page_title="NHS Care Companion Letter Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "## NHS Care Companion by Care Clarity\nGenerate formal letters for elderly care-related concerns, complaints, and advocacy."
    }
)

# ----- CUSTOM CSS -----
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stButton button { 
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.02);
    }
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        border-radius: 5px;
        border: 1px solid #ccc;
    }
    .response-box {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        background-color: #fff;
        margin-top: 1rem;
        min-height: 400px;
    }
    .letter-meta {
        color: #555;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ----- TRANSLATIONS & LANGUAGES -----
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

TRANSLATIONS = {
    "en": {
        "language": "Language",
        "license_prompt": "Enter your license key:",
        "gdpr_consent": "I consent to data processing in accordance with GDPR.",
        "category": "Letter Category",
        "subcategory": "Issue",
        "tone": "Tone",
        "standard": "Standard",
        "serious": "Serious Formal Complaint",
        "generate": "Generate Letter",
        "save_letter": "Save Letter",
        "load_letter": "Load Saved Letter",
        "delete_letter": "Delete Saved Letter",
        "select_letter": "Select a saved letter",
        "generated_letter": "Generated Letter",
        "copy": "Copy to Clipboard",
        "download": "Download as .txt",
        "debug_prompt": "Show Generation Prompt (Debug)",
        "recipient": "To: Care Provider / Local Authority",
        "date": "Date",
        "subject": "Subject",
        "gdpr_required": "GDPR consent is required to proceed.",
        "invalid_key": "Invalid license key.",
        "question_missing": "Missing required input.",
        "name_label": "Your Full Name",
        "recipient_label": "Recipient Organization",
        "tone_help": "Select 'Serious Formal Complaint' for legal matters"
    }
}

def t(key: str) -> str:
    """Get translation for the current language"""
    lang_code = LANGUAGES.get(st.session_state.get("language", "English"), "en")
    return TRANSLATIONS.get(lang_code, TRANSLATIONS["en"]).get(key, key)

# ----- LOAD JSON FILES -----
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.error(f"Failed to load {path}")
        return {}

VALID_KEYS = load_json("valid_keys.json")
LETTER_STRUCTURE = load_json("letter_structure_meta.json")

# ----- INITIALIZE SESSION STATE -----
DEFAULT_STATE = {
    "authenticated": False,
    "language": "English",
    "gdpr_ok": False,
    "license_key": "",
    "user_name": "",
    "recipient": "",
    "date": datetime.date.today().strftime("%Y-%m-%d"),
    "category": None,
    "subcategory": None,
    "tone": "Standard",
    "answers": {},
    "generated_letter": "",
    "last_prompt": "",
    "saved_letters": {},
    "meta": {
        "version": "2.1",
        "letter_count": 0,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ----- LETTER GENERATION -----
def generate_prompt() -> str:
    """Generate the AI prompt with context"""
    context = f"""**Context:**
- Language: {st.session_state.language}
- Category: {st.session_state.category}
- Issue: {st.session_state.subcategory}
- Tone: {st.session_state.tone}
- Sender: {st.session_state.user_name}
- Recipient: {st.session_state.recipient}
- Date: {st.session_state.date}

**Details:**
"""
    for q, a in st.session_state.answers.items():
        context += f"- {q}: {a}\n"

    context += f"""
**Instructions:**
Write a {'very formal complaint letter' if st.session_state.tone == "Serious Formal Complaint" else 'professional letter'} with:
- Proper business letter format
- Clear structure with introduction, body, and conclusion
- {"Strong but polite language with potential legal references" if st.session_state.tone == "Serious Formal Complaint" else "Professional yet accessible tone"}
- Specific references to provided details
- Appropriate closing

**Format:**
[Date]
[Recipient Address]
[Subject Line]

[Salutation],

[Body paragraphs]

[Closing],
{st.session_state.user_name}
"""
    return context

# ----- SAVE/LOAD LETTERS -----
def save_current_letter():
    """Save letter with metadata"""
    if not st.session_state.generated_letter:
        return
        
    letter_id = str(uuid.uuid4())[:8]
    save_name = f"{st.session_state.category} - {st.session_state.subcategory} - {letter_id}"
    
    st.session_state.saved_letters[save_name] = {
        "content": st.session_state.generated_letter,
        "date": datetime.datetime.now().isoformat(),
        "category": st.session_state.category,
        "subcategory": st.session_state.subcategory,
        "answers": st.session_state.answers.copy(),
        "recipient": st.session_state.recipient,
        "user_name": st.session_state.user_name,
        "tone": st.session_state.tone,
        "prompt": st.session_state.last_prompt
    }
    
    st.session_state.meta["letter_count"] = len(st.session_state.saved_letters)
    st.session_state.meta["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.toast(f"Letter saved as: {save_name}", icon="💾")

def load_letter(letter_title: str):
    """Load a saved letter"""
    if letter_title in st.session_state.saved_letters:
        data = st.session_state.saved_letters[letter_title]
        st.session_state.update({
            "category": data["category"],
            "subcategory": data["subcategory"],
            "answers": data.get("answers", {}),
            "recipient": data.get("recipient", ""),
            "user_name": data.get("user_name", ""),
            "tone": data.get("tone", "Standard"),
            "generated_letter": data["content"],
            "last_prompt": data.get("prompt", "")
        })
        st.toast(f"Loaded: {letter_title}", icon="📄")
        st.rerun()

# ----- AUTHENTICATION -----
with st.sidebar:
    st.session_state.language = st.selectbox(
        t("language"),
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(st.session_state.language)
    )
    
    if not st.session_state.authenticated:
        with st.form("auth_form"):
            st.text_input(t("license_prompt"), type="password", key="license_key")
            st.checkbox(t("gdpr_consent"), key="gdpr_ok")
            if st.form_submit_button("Submit"):
                if st.session_state.license_key in VALID_KEYS and st.session_state.gdpr_ok:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error(t("invalid_key") if not st.session_state.license_key in VALID_KEYS else t("gdpr_required")

if not st.session_state.authenticated:
    st.stop()

# ----- MAIN APP -----
st.title("📝 NHS Care Companion Letter Generator")

# User Information
col1, col2 = st.columns(2)
with col1:
    st.session_state.user_name = st.text_input(t("name_label"), st.session_state.user_name)
with col2:
    st.session_state.recipient = st.text_input(t("recipient_label"), st.session_state.recipient)

# Letter Details
st.session_state.category = st.selectbox(
    t("category"),
    list(LETTER_STRUCTURE.keys()),
    index=list(LETTER_STRUCTURE.keys()).index(st.session_state.category) 
    if st.session_state.category in LETTER_STRUCTURE else 0
)

if st.session_state.category:
    st.session_state.subcategory = st.selectbox(
        t("subcategory"),
        list(LETTER_STRUCTURE[st.session_state.category].keys()),
        index=list(LETTER_STRUCTURE[st.session_state.category].keys()).index(st.session_state.subcategory)
        if st.session_state.subcategory in LETTER_STRUCTURE[st.session_state.category] else 0
    )

# Questions
if st.session_state.subcategory:
    questions = LETTER_STRUCTURE[st.session_state.category][st.session_state.subcategory]["questions"]
    for q in questions:
        answer = st.text_area(q["question"], 
                            value=st.session_state.answers.get(q["question"], ""),
                            placeholder=q.get("placeholder", ""))
        st.session_state.answers[q["question"]] = answer

# Tone Selection
st.session_state.tone = st.radio(
    t("tone"),
    [t("standard"), t("serious")],
    index=0 if st.session_state.tone == t("standard") else 1,
    help=t("tone_help")
)

# Generate Button
if st.button(t("generate"), type="primary"):
    if not all([st.session_state.user_name, st.session_state.category, st.session_state.subcategory]):
        st.error("Please complete all required fields")
    else:
        with st.spinner("Generating professional letter..."):
            try:
                client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                prompt = generate_prompt()
                st.session_state.last_prompt = prompt
                
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3 if st.session_state.tone == t("serious") else 0.7
                )
                st.session_state.generated_letter = response.choices[0].message.content
                st.session_state.meta["letter_count"] += 1
                st.rerun()
            except Exception as e:
                st.error(f"Generation error: {str(e)}")

# Display Generated Letter
if st.session_state.generated_letter:
    st.subheader(t("generated_letter"))
    with st.container():
        st.markdown(f"""<div class='response-box'>
            <div class='letter-meta'>
                <b>{t('recipient')}:</b> {st.session_state.recipient}<br>
                <b>{t('date')}:</b> {st.session_state.date}<br>
                <b>{t('subject')}:</b> {st.session_state.subcategory}
            </div>
            {st.session_state.generated_letter.replace('\n', '<br>')}
        </div>""", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(t("download"), 
                          st.session_state.generated_letter,
                          file_name=f"care_letter_{datetime.datetime.now().strftime('%Y%m%d')}.txt")
    with col2:
        if st.button(t("copy")):
            st.session_state.clipboard = st.session_state.generated_letter
            st.toast("Copied to clipboard!", icon="📋")
    with col3:
        if st.button(t("save_letter")):
            save_current_letter()

# Saved Letters Panel
with st.sidebar:
    if st.session_state.saved_letters:
        st.markdown("### 💾 Saved Letters")
        for title in st.session_state.saved_letters:
            cols = st.columns([4,1])
            with cols[0]:
                if st.button(title, key=f"load_{title}", use_container_width=True):
                    load_letter(title)
            with cols[1]:
                if st.button("🗑️", key=f"del_{title}"):
                    del st.session_state.saved_letters[title]
                    st.rerun()

# Debug View
with st.expander(t("debug_prompt")):
    if "last_prompt" in st.session_state:
        st.code(st.session_state.last_prompt)

                   
