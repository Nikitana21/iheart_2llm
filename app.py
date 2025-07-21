import streamlit as st
import os
import json
import difflib
from dotenv import load_dotenv
import pandas as pd
from datasets.load_data import load_tables_from_excel, generate_table_metadata, format_metadata_for_prompt
import aqxle

st.set_page_config(page_title="iHeart Demo", layout="wide")
st.title("iHeart Demo")

# Load environment variables
load_dotenv()

# Load data and metadata
@st.cache_resource
def get_data():
    all_tables = load_tables_from_excel('datasets/W48Tables_Cleaned.xlsx')
    all_metadata = generate_table_metadata(all_tables)
    formatted_metadata = format_metadata_for_prompt(all_metadata)
    return all_tables, all_metadata, formatted_metadata

all_tables, all_metadata, formatted_metadata = get_data()

# Load prompts
with open("src/prompts/table_selector.txt", "r", encoding="utf-8") as f:
    table_selector_template = f.read()
with open("src/prompts/code_generator.txt", "r", encoding="utf-8") as f:
    codegen_template = f.read()

# Suggested questions
suggested_questions = [
    "Do different Hispanic/Latinx subgroups show varying levels of interest in switching?",
    "How does radio engagement (TSL) differ among Hispanic sub-identities?",
    "How do primary decision-makers and influencers compare across genders?",
    "Which demographic groups are more likely to be decision-makers?",
    "Is being a primary decision-maker correlated with being a weekly radio listener?"
]

# Sidebar with suggested questions
st.sidebar.header("History")
st.sidebar.subheader("Suggested Questions")
for q in suggested_questions:
    if st.sidebar.button(q):
        st.session_state["suggested_input"] = q

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""
if "suggested_input" not in st.session_state:
    st.session_state["suggested_input"] = ""

# Handle suggested question
if st.session_state["suggested_input"]:
    st.session_state["user_input"] = st.session_state["suggested_input"]
    st.session_state["suggested_input"] = ""
    st.rerun()

# Chat input form
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask a question about your data:", key="user_input")
    submitted = st.form_submit_button("Submit")
    if submitted and user_input.strip():
        st.session_state["messages"].append({"role": "user", "content": user_input})

        selector_prompt = table_selector_template.replace("{{TABLE_METADATA}}", formatted_metadata).replace("{{question}}", user_input)
        aqxle.init("config.yml")
        with aqxle.params(name="table_selector", history_length=3, max_retries=2, logging=True) as selector_session:
            selector_result = selector_session.llm("table_selector_llm", message=selector_prompt)

        # Parse LLM output
        raw = selector_result.data.strip()
        if raw.startswith("```json"):
            raw = raw[len("```json"):].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
        try:
            selector_json = json.loads(raw)
        except Exception as e:
            st.error(f"Failed to parse JSON from LLM output: {e}")
            selector_json = {}

        selected_table = selector_json.get("table_name", "").strip()
        matched_table = None

        if selected_table in all_metadata:
            matched_table = selected_table
        else:
            matches = [k for k in all_metadata if selected_table.lower() in k.lower()]
            if len(matches) == 1:
                matched_table = matches[0]
            else:
                close_matches = difflib.get_close_matches(selected_table, all_metadata.keys(), n=1, cutoff=0.6)
                if close_matches:
                    matched_table = close_matches[0]
                else:
                    st.error("No relevant tables found by the Table Selector LLM. Please refine your question.")

        if matched_table:
            selected_metadata = {matched_table: all_metadata[matched_table]}
            filtered_metadata_str = format_metadata_for_prompt(selected_metadata)
            codegen_prompt = codegen_template.replace("{{TABLE_METADATA}}", filtered_metadata_str).replace("{{question}}", user_input)

            with aqxle.params(name="logicgen", history_length=5, max_retries=3, logging=True) as session:
                result = (
                    session
                    .llm("codegen_llm", message=codegen_prompt)
                    .segment(kernel="python")
                    .execute(kernel="python", function="main", df={matched_table: all_tables[matched_table]})
                )

            try:
                output = result.data.output
                st.session_state["messages"].append({"role": "assistant", "content": output})
            except Exception as e:
                st.session_state["messages"].append({"role": "assistant", "content": f"Error: {e}"})

# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        if isinstance(msg["content"], pd.DataFrame):
            st.dataframe(msg["content"])
        else:
            try:
                df = pd.read_csv(pd.compat.StringIO(msg["content"]))
                st.dataframe(df)
            except Exception:
                st.markdown(f"**Bot:** {msg['content']}")
