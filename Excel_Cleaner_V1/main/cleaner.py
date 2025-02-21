import os
import json
import pandas as pd
import re
import sys

# OPTIONAL: only if you want to fix "ValÃ©rie" -> "Valérie"
try:
    from ftfy import fix_text
    def fix_broken_text(text: str) -> str:
        return fix_text(text)
except ImportError:
    # If ftfy isn't installed, just return the text as-is
    def fix_broken_text(text: str) -> str:
        return text

# Ensure we can print Unicode characters on Windows
sys.stdout.reconfigure(encoding='utf-8')

# ----------------------------------------------------------------
# 1) Paths & Config
# ----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = r"C:\Users\Y.CHEHBOUB\Downloads\O3_Test\Here\SheetCleaner\input"
OUTPUT_XLSX = os.path.join(INPUT_FOLDER, r"C:\Users\Y.CHEHBOUB\Downloads\O3_Test\Here\SheetCleaner\output\output.xlsx")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def load_config():
    """
    Loads a JSON file (config.json) with two keys:
      - allowed_accents: list of individual accented/punctuation characters
      - allowed_chars_prefix: list of strings (like 'a-zA-Z0-9', '\\s', etc.)
    If config.json doesn't exist or is incomplete, defaults are used.
    """
    defaults = {
        "allowed_accents": list("àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß.\\-'"),
        "allowed_chars_prefix": ["a-zA-Z0-9", "\\s"]
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            # Ensure required keys exist
            for key in defaults:
                if key not in config:
                    config[key] = defaults[key]
            return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            return defaults
    else:
        return defaults

config = load_config()

# Build the allowed characters pattern
allowed_accents = "".join(config.get("allowed_accents", []))
allowed_chars_prefix = "".join(config.get("allowed_chars_prefix", []))
allowed_chars = allowed_chars_prefix + allowed_accents

# Compile regex patterns
special_char_pattern = re.compile(fr"[^{allowed_chars}]")
non_latin_pattern = re.compile(r"[^\u0000-\u007F]")

results = []

# ----------------------------------------------------------------
# 2) Main Logic: Scan .xlsx files in the input folder
# ----------------------------------------------------------------
for file_name in os.listdir(INPUT_FOLDER):
    if file_name.lower().endswith(".xlsx"):
        file_path = os.path.join(INPUT_FOLDER, file_name)
        try:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)

                # Look for an "EMPLID" column (case-insensitive)
                emplid_column = None
                for col in df.columns:
                    if "EMPLID" in col.upper():
                        emplid_column = col
                        break

                for row_idx, row in df.iterrows():
                    emplid_value = row[emplid_column] if emplid_column in df.columns else "N/A"
                    for col_idx, cell_value in enumerate(row):
                        if pd.notna(cell_value):
                            # Convert to string & fix broken text
                            cell_str = str(cell_value)
                            cell_str = fix_broken_text(cell_str)

                            # Check for special or non-latin characters
                            special_chars = special_char_pattern.findall(cell_str)
                            non_latin_chars = non_latin_pattern.findall(cell_str)
                            if special_chars or non_latin_chars:
                                results.append([
                                    file_name,
                                    sheet_name,
                                    emplid_value,
                                    row_idx + 1,
                                    df.columns[col_idx],
                                    cell_str,
                                    ''.join(sorted(set(special_chars))),
                                    ''.join(sorted(set(non_latin_chars)))
                                ])
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

# ----------------------------------------------------------------
# 3) Write Results as XLSX
# ----------------------------------------------------------------
if results:
    report_df = pd.DataFrame(
        results,
        columns=[
            "File Name",
            "Sheet Name",
            "EMPLID",
            "Row",
            "Column",
            "Cell Value",
            "Special Characters",
            "Non-Latin Characters"
        ]
    )
    os.makedirs(os.path.dirname(OUTPUT_XLSX), exist_ok=True)

    # Write an actual Excel file so columns are aligned in Excel
    report_df.to_excel(OUTPUT_XLSX, index=False, engine="openpyxl")

    print(f"✅ Excel report saved: {OUTPUT_XLSX}")
else:
    print("✅ No unwanted special characters found.")
