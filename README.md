# iHeart 2LLM 

## Overview

This project enables users to ask questions about survey data stored in Excel tables. The system uses two Large Language Models (LLMs) via Aqxle: one to select the most relevant table, and another to generate Python code to answer the question using only the selected table's data. The project includes both a command-line demo (`demo.py`) and a Streamlit-based conversational chatbot (`app.py`).

---

## Workflow

1. **Configuration and Setup:**  
   Loads configuration from `config.yml`, API keys from `.env`, and initializes the environment.

2. **User Question:**  
   The user provides a question about the data via the command line or the Streamlit chatbot interface.

3. **Table Metadata Extraction:**  
   The system loads all tables from the Excel file (`datasets/W48Tables_Cleaned.xlsx`) and extracts their metadata (column names and categories).

4. **Prompt Construction:**  
   The metadata and user question are inserted into prompt templates (`src/prompts/table_selector.txt` and `src/prompts/code_generator.txt`).

5. **Table and Code Selection (LLMs):**  
   The first LLM receives the prompt and selects the most relevant table. The second LLM generates Python code to answer the question using only the selected table's data.

6. **Code Execution:**  
   The generated code is executed, and the results are displayed to the user as a DataFrame.

---

## Setup Instructions

1. **Clone the repository and navigate to the project directory.**

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure your API keys and dataset path in `config.yml` and `.env`.**

4. **Run the Streamlit chatbot app:**
   ```sh
   streamlit run app.py
   ```
   Or run the command-line demo:
   ```sh
   python demo.py
   ```

---

## File Structure

- `app.py` — Streamlit chatbot app for conversational Q&A
- `demo.py` — Command-line script for single-turn Q&A
- `datasets/load_data.py` — Helper for extracting tables and metadata from Excel
- `src/prompts/` — Prompt templates for the LLMs
- `config.yml` — Configuration file (API keys, dataset path, etc.)
- `.env` — Environment variables (not tracked in git)
- `README.md` — Project documentation
- `.gitignore` — Files and folders excluded from version control

---

## Notes

- Ensure your Excel data is formatted with clear table titles and a 'Category' column for row labels.
- If you use a virtual environment, activate it before installing dependencies.
- If `aqxle` is a private package, ensure it is installed in your environment.

---

## Example Usage

- The app or script will prompt you for a question about your data.
- The LLMs will select the most relevant table and generate code to answer your question.
- The generated code will be executed, and the answer will be displayed using only the selected table. 