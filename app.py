# NHS Care Companion Letter Generator (Full UI Version)

import streamlit as st
import json
import datetime
import uuid
import os
from openai import OpenAI

# --- FILE PATHS ---
VALID_KEYS_FILE = "valid_keys.json"
LETTER_STRUCTURE_FILE = "letter_structure_meta.json"

# --- TRANSLATIONS ---
TRANSLATIONS = {
    "en": {
        "title": "NHS Care Companion Letter Generator",
        "license_prompt": "Enter your license key",
        "access_granted": "Access granted!",
        "invalid_key": "Invalid license key.",
        "gdpr_label": "I agree to the GDPR terms.",
        "gdpr_warning": "Please provide GDPR consent to continue.",
        "name_label": "Your Name",
        "recipient_label": "Recipient",
        "date_label": "Date",
        "tone_label": "Tone of Letter",
        "tone_help": "Choose a standard tone or a serious formal complaint tone.",
        "category_label": "Letter Category",
        "subcategory_label": "Issue Type",
        "questions_header": "Please answer the following:",
        "generate_button": "Generate Letter",
        "clear_button": "Clear",
        "save_button": "Save",
        "download_button": "Download",
        "result_label": "Generated Letter",
        "language_select": "Language",
        "error_message": "Error generating letter:",
    }
}

LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr"
}

# --- LOAD JSON ---
def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

VALID_KEYS = load_json(VALID_KEYS_FILE)
LETTER_STRUCTURE = load_json(LETTER_STRUCTURE_FILE)

# --- TRANSLATION ---
def t(key):
    lang = LANGUAGES.get(st.session_state.language, "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

# --- SESSION STATE INIT ---
def init_state():
    defaults = {
        "authenticated": False,
        "language": "English",
        "gdpr_consent": False,
        "user_name": "",
        "recipient": "",
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "tone": "Standard",
        "selected_category": None,
        "selected_subcategory": None,
        "answers": {},
        "generated_letter": "",
        "saved_letters": {},
        "meta": {
            "version": "2.0",
            "letter_count": 0,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- AUTHENTICATION ---
def authenticate_form():
    with st.form("auth"):
        key = st.text_input(t("license_prompt"), type="password")
        if st.form_submit_button("Submit"):
            if key.strip() in VALID_KEYS:
                st.session_state.authenticated = True
                st.success(t("access_granted"))
                st.rerun()
            else:
                st.error(t("invalid_key"))

# --- PROMPT GENERATION ---
def generate_prompt():
    meta = LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"][st.session_state.selected_subcategory]
    subject = meta["subject_template"].format(date=st.session_state.date)
    q_block = "\n".join([
        f"- {q['question']}: {st.session_state.answers.get(q['question'], '')}"
        for q in meta["questions"] if st.session_state.answers.get(q['question'], '').strip()
    ])
    instruction = (
        "Write a formal complaint letter with legal tone, reference regulations, request investigation."
        if st.session_state.tone == "Serious Formal Complaint" else
        "Write a professional advocacy letter that is respectful, assertive, and clear."
    )
    return f"""
**Context:**
- Language: {st.session_state.language}
- Category: {st.session_state.selected_category}
- Issue: {st.session_state.selected_subcategory}
- Subject: {subject}
- From: {st.session_state.user_name}
- To: {st.session_state.recipient}
- Date: {st.session_state.date}
- Tone: {st.session_state.tone}

**Details Provided:**
{q_block}

**Instructions:**
{instruction}

**Format:**
- Business letter format
- Include subject, recipient, date
- Paragraphs, closing, sign: Sincerely, {st.session_state.user_name}
"""

# --- LETTER STATE ---
def clear_form():
    st.session_state.answers = {}
    st.session_state.generated_letter = ""
    st.session_state.selected_subcategory = None
    st.rerun()

def save_current_letter():
    if not st.session_state.generated_letter:
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
    st.session_state.meta["letter_count"] = len(st.session_state.saved_letters)
    st.session_state.meta["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.toast(f"Saved letter: {letter_title}", icon="✅")

def load_letter(title):
    d = st.session_state.saved_letters.get(title)
    if d:
        st.session_state.generated_letter = d["content"]
        st.session_state.selected_category = d["category"]
        st.session_state.selected_subcategory = d["subcategory"]
        st.session_state.answers = d.get("answers", {})
        st.session_state.recipient = d.get("recipient", "")
        st.session_state.user_name = d.get("user_name", "")
        st.session_state.tone = d.get("tone", "Standard")
        st.toast(f"Loaded letter: {title}", icon="📄")
        st.rerun()

def delete_letter(title):
    if title in st.session_state.saved_letters:
        del st.session_state.saved_letters[title]
        st.session_state.meta["letter_count"] = len(st.session_state.saved_letters)
        st.toast(f"Deleted letter: {title}", icon="🗑️")
        st.rerun()

# --- UI COMPONENTS ---
def sidebar():
    st.sidebar.selectbox(t("language_select"), list(LANGUAGES.keys()), key="language")
    st.sidebar.checkbox(t("gdpr_label"), value=st.session_state.gdpr_consent, key="gdpr_consent")
    if st.session_state.saved_letters:
        with st.sidebar.expander("📂 Saved Letters", expanded=True):
            for title in st.session_state.saved_letters:
                cols = st.columns([4, 1])
                with cols[0]:
                    if st.button(title, key=f"load_{title}"):
                        load_letter(title)
                with cols[1]:
                    if st.button("🗑️", key=f"del_{title}", help="Delete this letter"):
                        delete_letter(title)
    with st.sidebar.expander("ℹ️ About This App"):
        st.markdown(f"**Version:** {st.session_state.meta['version']}")
        st.markdown(f"**Letters Generated:** {st.session_state.meta['letter_count']}")
        st.markdown(f"**Last Updated:** {st.session_state.meta['last_updated']}")

# --- MAIN FORM ---
def letter_form():
    with st.form("letter_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(t("name_label"), value=st.session_state.user_name, key="user_name")
            st.text_input(t("recipient_label"), value=st.session_state.recipient, key="recipient")
        with col2:
            st.date_input(t("date_label"), value=datetime.datetime.strptime(st.session_state.date, "%Y-%m-%d"), key="date")
            st.selectbox(t("tone_label"), ["Standard", "Serious Formal Complaint"], index=0 if st.session_state.tone=="Standard" else 1, key="tone", help=t("tone_help"))
        st.selectbox(t("category_label"), list(LETTER_STRUCTURE.keys()), key="selected_category")
        if st.session_state.selected_category:
            subs = LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"]
            st.selectbox(t("subcategory_label"), list(subs.keys()), key="selected_subcategory")
            if st.session_state.selected_subcategory:
                st.subheader(t("questions_header"))
                for q in subs[st.session_state.selected_subcategory]["questions"]:
                    st.text_area(q["question"], key=f"q_{q['question']}")
        col1, col2, col3 = st.columns(3)
        if col1.form_submit_button(t("generate_button")):
            st.session_state.answers = {k[2:]: v for k, v in st.session_state.items() if k.startswith("q_")}
            prompt = generate_prompt()
            with st.expander("Debug Prompt"):
                st.text(prompt)
            try:
                client = OpenAI(api_key=st.secrets["openai"]["api_key"])
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
        if col2.form_submit_button(t("clear_button")):
            clear_form()
        if col3.form_submit_button(t("save_button")):
            save_current_letter()

# --- LETTER OUTPUT ---
def show_letter():
    if not st.session_state.generated_letter:
        return
    st.subheader(t("result_label"))
    st.markdown(f"**To:** {st.session_state.recipient}")
    st.markdown(f"**Date:** {st.session_state.date}")
    subject_template = LETTER_STRUCTURE[st.session_state.selected_category]["subcategories"][st.session_state.selected_subcategory]["subject_template"]
    st.markdown(f"**Subject:** {subject_template.format(date=st.session_state.date)}")
    st.text_area("Letter Content", st.session_state.generated_letter, height=400)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(t("download_button"), st.session_state.generated_letter, file_name="care_letter.txt")
    with col2:
        if st.button("📋 Copy to Clipboard"):
            st.session_state.clipboard = st.session_state.generated_letter
            st.toast("Copied to clipboard!", icon="📋")

# --- MAIN ---
def main():
    st.set_page_config(page_title=t("title"), layout="wide")
    st.markdown("""
        <style>
        .stTextArea textarea { min-height: 100px; }
        .stButton button:hover { transform: scale(1.02); }
        </style>
    """, unsafe_allow_html=True)
    sidebar()
    st.title(t("title"))
    if not st.session_state.authenticated:
        authenticate_form()
        return
    if not st.session_state.gdpr_consent:
        st.warning(t("gdpr_warning"))
        return
    letter_form()
    show_letter()

if __name__ == "__main__":
    main()
