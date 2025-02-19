import os
import pandas as pd
import re

folder_path = r"C:\\Users\\Y.CHEHBOUB\\Downloads\\SheetCleaner\\input"
output_file = os.path.join(folder_path, "output\\output.csv")
allowed_accents = "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß.\-'"
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

if results:
    report_df = pd.DataFrame(results, columns=[
        "File Name", "Sheet Name", "EMPLID", "Row", "Column", "Cell Value", "Special Characters", "Non-Latin Characters"
    ])
    report_df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"✅ Report saved: {output_file}")
else:
    print("✅ No unwanted special characters found.")
