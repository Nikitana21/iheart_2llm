import pandas as pd
import re


def load_tables_from_excel(file_path):
    df = pd.read_excel(file_path, header=None)
    tables = {}

    # Identify all table start indices and their names
    table_indices = []
    for i, row in df.iterrows():
        for cell in row:
            if isinstance(cell, str) and re.match(r"Table \d+:", cell.strip()):
                table_indices.append((i, cell.strip()))
                break

    # Add end boundary for last table
    table_indices.append((len(df), None))

    # Extract and clean each table
    for idx in range(len(table_indices) - 1):
        start_idx, table_name = table_indices[idx]
        end_idx, _ = table_indices[idx + 1]

        # Get raw table slice
        table_raw = df.iloc[start_idx + 1:end_idx].copy()

        # First row is header
        header = table_raw.iloc[0].astype(str).str.strip()
        data = table_raw.iloc[1:].copy()
        data.columns = header

        # Drop rows that are completely empty
        data.dropna(how='all', inplace=True)

        # Reset index
        data.reset_index(drop=True, inplace=True)

        # Ensure 'Category' column exists
        if 'Category' not in data.columns:
            first_col = data.columns[0]
            data.rename(columns={first_col: 'Category'}, inplace=True)

        # Strip whitespace from all column names
        data.columns = data.columns.astype(str).str.strip()

        tables[table_name] = data

    return tables


def generate_table_metadata(tables):
    """
    Extracts metadata from each table, including column headers and all category labels.
    """
    metadata = {}
    for table_name, df in tables.items():
        columns = df.columns.tolist()
        categories = df['Category'].dropna().astype(str).tolist() if 'Category' in df.columns else []
        metadata[table_name] = {
            "columns": columns,
            "categories": categories
        }
    return metadata


def format_metadata_for_prompt(metadata_dict):
    """
    Converts the metadata dictionary into a readable text block suitable for insertion into a prompt.
    """
    lines = []
    for table_name, meta in metadata_dict.items():
        lines.append(f"{table_name}")
        lines.append(f"  Columns: {', '.join(meta['columns'])}")
        if meta['categories']:
            lines.append(f"  Categories: {', '.join(meta['categories'])}")
        lines.append("")  # spacer between tables
    return "\n".join(lines)
