# --- MAIN FORM ---
def letter_form():
    with st.form("letter_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.user_name = st.text_input(
                t("name_label"),
                value=st.session_state.get("user_name", ""),
                placeholder="Your full name"
            )
            st.session_state.recipient = st.text_input(
                t("recipient_label"),
                value=st.session_state.get("recipient", ""),
                placeholder="Recipient organization or department"
            )
        with col2:
            st.session_state.date = st.date_input(
                t("date_label"),
                value=datetime.datetime.strptime(st.session_state.get("date"), "%Y-%m-%d")
            ).strftime("%Y-%m-%d")
            st.session_state.tone = st.selectbox(
                t("tone_label"),
                ["Standard", "Serious Formal Complaint"],
                index=0 if st.session_state.get("tone") == "Standard" else 1,
                help=t("tone_help")
            )

        category_options = list(LETTER_STRUCTURE.keys())
        selected_category = st.selectbox(
            t("category_label"),
            category_options,
            index=category_options.index(st.session_state.get("selected_category")) if st.session_state.get("selected_category") in category_options else 0
        )

        if selected_category != st.session_state.get("selected_category"):
            st.session_state.selected_category = selected_category
            st.session_state.selected_subcategory = None
            st.session_state.answers = {}

        subcategory_options = list(LETTER_STRUCTURE[selected_category]["subcategories"].keys())
        selected_subcategory = st.selectbox(
            t("subcategory_label"),
            subcategory_options,
            index=subcategory_options.index(st.session_state.get("selected_subcategory")) if st.session_state.get("selected_subcategory") in subcategory_options else 0
        )

        if selected_subcategory != st.session_state.get("selected_subcategory"):
            st.session_state.selected_subcategory = selected_subcategory
            st.session_state.answers = {}

        if selected_category and selected_subcategory:
            st.divider()
            st.subheader(t("questions_header"))
            questions = LETTER_STRUCTURE[selected_category]["subcategories"][selected_subcategory]["questions"]
            for q in questions:
                question_key = q["question"]
                prev_answer = st.session_state.answers.get(question_key, "")
                answer = st.text_area(
                    label=question_key,
                    value=prev_answer,
                    placeholder=q.get("placeholder", ""),
                    help=q.get("help_text", ""),
                    key=f"q_{hash(question_key)}"
                )
                st.session_state.answers[question_key] = answer

        col1, col2, col3 = st.columns(3)
        generate_clicked = col1.form_submit_button(t("generate_button"))
        clear_clicked = col2.form_submit_button(t("clear_button"))
        save_clicked = col3.form_submit_button(t("save_button"))

        if clear_clicked:
            clear_form()

        if save_clicked and st.session_state.generated_letter:
            save_current_letter()

        if generate_clicked:
            if not all([
                st.session_state.user_name,
                st.session_state.selected_category,
                st.session_state.selected_subcategory
            ]):
                st.error("Please complete all fields before generating.")
            else:
                with st.spinner("Generating your letter..."):
                    try:
                        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                        prompt = generate_prompt()
                        with st.expander("Debug Prompt"):
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
