import sys
import os
import json
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
load_dotenv()

import aqxle
from datasets.load_data import load_tables_from_excel, generate_table_metadata, format_metadata_for_prompt

all_tables = load_tables_from_excel('datasets/W48Tables_Cleaned.xlsx')
all_metadata = generate_table_metadata(all_tables)
formatted_metadata = format_metadata_for_prompt(all_metadata)

table_selector_prompt_path = "src/prompts/table_selector.txt"
codegen_prompt_path = "src/prompts/code_generator.txt"

with open(table_selector_prompt_path, "r", encoding="utf-8") as f:
    table_selector_template = f.read()
with open(codegen_prompt_path, "r", encoding="utf-8") as f:
    codegen_template = f.read()

question = input("Ask a question about your data: ")

selector_prompt = table_selector_template.replace("{{TABLE_METADATA}}", formatted_metadata).replace("{{question}}", question)

print("\n--- Table Selector Prompt ---\n")
print(selector_prompt)
print("\n----------------------------\n")

aqxle.init("config.yml")

with aqxle.params(name="table_selector", history_length=3, max_retries=2, logging=True) as selector_session:
    selector_result = (
        selector_session
        .llm("table_selector_llm", message=selector_prompt)
    )

# Print raw output for debugging
print("LLM raw output:", repr(selector_result.data))

# Try to extract JSON block from LLM output
try:
    # Try direct JSON parse first
    selector_json = json.loads(selector_result.data)
except json.JSONDecodeError:
    # Try to extract JSON block using regex
    match = re.search(r'\{.*\}', selector_result.data, re.DOTALL)
    if match:
        try:
            selector_json = json.loads(match.group(0))
        except Exception as e:
            print("Failed to parse extracted JSON:", e)
            selector_json = {}
    else:
        print("No JSON found in LLM output.")
        selector_json = {}

selected_table = selector_json.get("table_name", "").strip()

# Try exact match first
if selected_table in all_metadata:
    matched_table = selected_table
else:
    # Try to find a table whose name contains the LLM's output (case-insensitive)
    matches = [k for k in all_metadata if selected_table.lower() in k.lower()]
    if len(matches) == 1:
        matched_table = matches[0]
    elif len(matches) > 1:
        print("Multiple tables matched. Please refine your question or improve the prompt.")
        print("Matches:", matches)
        exit(1)
    else:
        # Try fuzzy matching (best effort)
        import difflib
        close_matches = difflib.get_close_matches(selected_table, all_metadata.keys(), n=1, cutoff=0.6)
        if close_matches:
            matched_table = close_matches[0]
        else:
            print("No relevant tables found by the Table Selector LLM. Please refine your question.")
            exit(1)

# Use matched_table for the rest of your code
selected_metadata = {matched_table: all_metadata[matched_table]}
filtered_metadata_str = format_metadata_for_prompt(selected_metadata)

codegen_prompt = codegen_template.replace("{{TABLE_METADATA}}", filtered_metadata_str).replace("{{question}}", question)

print("\n--- Codegen Prompt ---\n")
print(codegen_prompt)
print("\n---------------------\n")

with aqxle.params(name="logicgen", history_length=5, max_retries=3, logging=True) as session:
    result = (
        session
        .llm("codegen_llm", message=codegen_prompt)
        .segment(kernel="python")
        .execute(kernel="python", function="main", df={matched_table: all_tables[matched_table]})
    )

print(result.data.output)
print(result.data.error)
