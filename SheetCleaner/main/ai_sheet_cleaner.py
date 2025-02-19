import os
import sys
import pandas as pd
import re
import concurrent.futures

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from api.api import get_ai_response

def get_ai_response_with_timeout(prompt, timeout=30):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(get_ai_response, prompt)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return "Error: Timeout waiting for AI response."

folder_path = r"C:\Users\Y.CHEHBOUB\Downloads\O3_Test\Here\SheetCleaner\input"
output_file = os.path.join(folder_path, "output", "ai_output.csv")

allowed_accents = "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß.\\-'"
allowed_chars = fr"a-zA-Z0-9\s{allowed_accents}"
special_char_pattern = re.compile(fr"[^{allowed_chars}]")
non_latin_pattern = re.compile(r"[^\u0000-\u007F]")

results = []

for file_name in os.listdir(folder_path):
    if file_name.endswith(".xlsx"):
        file_path = os.path.join(folder_path, file_name)
        try:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
                emplid_column = None
                for col in df.columns:
                    if "EMPLID" in col.upper():
                        emplid_column = col
                        break
                for row_idx, row in df.iterrows():
                    emplid_value = row[emplid_column] if emplid_column in df.columns else "N/A"
                    for col_idx, cell_value in enumerate(row):
                        if pd.notna(cell_value):
                            cell_str = str(cell_value)
                            special_chars = special_char_pattern.findall(cell_str)
                            non_latin_chars = non_latin_pattern.findall(cell_str)
                            if special_chars or non_latin_chars:
                                # Optional: truncate the cell text if it's too long
                                truncated_text = cell_str if len(cell_str) < 1000 else cell_str[:1000] + "..."
                                prompt = (
                                    "Clean the following text by removing any characters that are not letters "
                                    "(including accented letters), digits, whitespace, or the following punctuation: . - '\n"
                                    f"Original text: {truncated_text}\n"
                                    "Return only the cleaned text."
                                )
                                print(f"Processing: {file_name}, {sheet_name}, row {row_idx + 1}, column {df.columns[col_idx]}")
                                try:
                                    ai_cleaned = get_ai_response_with_timeout(prompt)
                                except Exception as e:
                                    ai_cleaned = f"Error: {e}"
                                results.append([
                                    file_name,
                                    sheet_name,
                                    emplid_value,
                                    row_idx + 1,
                                    df.columns[col_idx],
                                    cell_str,
                                    ''.join(sorted(set(special_chars))),
                                    ''.join(sorted(set(non_latin_chars))),
                                    ai_cleaned
                                ])
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

if results:
    report_df = pd.DataFrame(results, columns=[
        "File Name", "Sheet Name", "EMPLID", "Row", "Column", "Original Cell Value",
        "Special Characters", "Non-Latin Characters", "AI Cleaned Value"
    ])
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    report_df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"✅ AI Cleaned Report saved: {output_file}")
else:
    print("✅ No unwanted special characters found.")
