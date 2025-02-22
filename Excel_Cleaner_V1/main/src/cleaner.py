import os
import sys
import re
import argparse
import concurrent.futures
import datetime
import threading
import pandas as pd
from config_manager import load_config

try:
    from ftfy import fix_text
    def fix_broken_text(text: str) -> str:
        return fix_text(text)
except ImportError:
    def fix_broken_text(text: str) -> str:
        return text

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

config = load_config()
INPUT_FOLDER = config.get("input_folder")
OUTPUT_FOLDER = config.get("output_folder")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
allowed_accents = "".join(config.get("allowed_accents", []))
allowed_chars_prefix = "".join(config.get("allowed_chars_prefix", []))
allowed_chars = allowed_chars_prefix + allowed_accents
replacement_mappings = config.get("replacement_mappings", {})
special_char_pattern = re.compile(fr"[^{allowed_chars}]")
non_latin_pattern = re.compile(r"[^\u0000-\u007F]")

def clean_text(text):
    fixed = fix_broken_text(text)
    for k, v in replacement_mappings.items():
        fixed = fixed.replace(k, v)
    cleaned = re.sub(special_char_pattern, '', fixed)
    return cleaned

def is_date(text):
    date_formats = ["%d/%m/%Y", "%Y/%d/%m", "%Y/%m/%d", "%m/%d/%Y"]
    for fmt in date_formats:
        try:
            datetime.datetime.strptime(text, fmt)
            return True
        except ValueError:
            continue
    return False

def contains_parenthesized_name(text):
    return bool(re.search(r'\([A-Za-z\s]+\)', text))

def process_file(file_path, auto_fix, dry_run):
    results = []
    summary = {"total_cells": 0, "flagged": 0, "fixed": 0}
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()
    if ext in [".xlsx", ".xls"]:
        try:
            xls = pd.ExcelFile(file_path)
        except Exception as e:
            print(f"{datetime.datetime.now()} - Error opening {file_name}: {e}")
            return (results, summary)
        sheets = {}
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            except Exception as e:
                print(f"{datetime.datetime.now()} - Error reading sheet {sheet_name} in {file_name}: {e}")
                continue
            if df.empty:
                continue
            emplid_column = None
            for col in df.columns:
                if "EMPLID" in str(col).upper():
                    emplid_column = col
                    break
            for row_idx, row in df.iterrows():
                emplid_value = row[emplid_column] if emplid_column in df.columns else "N/A"
                for col_idx, cell_value in enumerate(row):
                    summary["total_cells"] += 1
                    if pd.notna(cell_value):
                        cell_str = str(cell_value)
                        if is_date(cell_str) or contains_parenthesized_name(cell_str):
                            cleaned = cell_str
                        else:
                            cleaned = clean_text(cell_str)
                        special_chars = ''.join(sorted(set(special_char_pattern.findall(cell_str))))
                        non_latin_chars = ''.join(sorted(set(non_latin_pattern.findall(cell_str))))
                        if cell_str != cleaned:
                            summary["flagged"] += 1
                            if auto_fix and not dry_run:
                                df.iat[row_idx, col_idx] = cleaned
                                summary["fixed"] += 1
                            results.append([file_name, sheet_name, emplid_value, row_idx+1, df.columns[col_idx],
                                            cell_str, cleaned, special_chars, non_latin_chars])
            sheets[sheet_name] = df
        if auto_fix and not dry_run:
            output_file = os.path.join(OUTPUT_FOLDER, os.path.splitext(file_name)[0] + "_cleaned" + ext)
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                for sheet_name, df in sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"{datetime.datetime.now()} - Cleaned file saved: {output_file}")
    elif ext == ".csv":
        try:
            df = pd.read_csv(file_path, dtype=str)
        except Exception as e:
            print(f"{datetime.datetime.now()} - Error reading CSV {file_name}: {e}")
            return (results, summary)
        emplid_column = None
        for col in df.columns:
            if "EMPLID" in str(col).upper():
                emplid_column = col
                break
        for row_idx, row in df.iterrows():
            emplid_value = row[emplid_column] if emplid_column in df.columns else "N/A"
            for col_idx, cell_value in enumerate(row):
                summary["total_cells"] += 1
                if pd.notna(cell_value):
                    cell_str = str(cell_value)
                    if is_date(cell_str) or contains_parenthesized_name(cell_str):
                        cleaned = cell_str
                    else:
                        cleaned = clean_text(cell_str)
                    special_chars = ''.join(sorted(set(special_char_pattern.findall(cell_str))))
                    non_latin_chars = ''.join(sorted(set(non_latin_pattern.findall(cell_str))))
                    if cell_str != cleaned:
                        summary["flagged"] += 1
                        if auto_fix and not dry_run:
                            df.iat[row_idx, col_idx] = cleaned
                            summary["fixed"] += 1
                        results.append([file_name, "Sheet1", emplid_value, row_idx+1, df.columns[col_idx],
                                        cell_str, cleaned, special_chars, non_latin_chars])
        if auto_fix and not dry_run:
            output_file = os.path.join(OUTPUT_FOLDER, os.path.splitext(file_name)[0] + "_cleaned.csv")
            df.to_csv(output_file, index=False)
            print(f"{datetime.datetime.now()} - Cleaned file saved: {output_file}")
    else:
        print(f"{datetime.datetime.now()} - Unsupported file type: {file_name}")
    return (results, summary)

def process_all_files(auto_fix, dry_run):
    all_results = []
    total_summary = {"total_cells": 0, "flagged": 0, "fixed": 0}
    files = [os.path.join(INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER)
             if os.path.splitext(f)[1].lower() in [".xlsx", ".xls", ".csv"]]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_file, f, auto_fix, dry_run): f for f in files}
        for future in concurrent.futures.as_completed(futures):
            res, summ = future.result()
            all_results.extend(res)
            total_summary["total_cells"] += summ["total_cells"]
            total_summary["flagged"] += summ["flagged"]
            total_summary["fixed"] += summ["fixed"]
    return all_results, total_summary

def write_report(results, summary):
    if results:
        report_df = pd.DataFrame(results, columns=["File Name", "Sheet Name", "EMPLID", "Row", "Column",
                                                    "Original Value", "Cleaned Value",
                                                    "Special Characters", "Non-Latin Characters"])
    else:
        report_df = pd.DataFrame(columns=["File Name", "Sheet Name", "EMPLID", "Row", "Column",
                                          "Original Value", "Cleaned Value",
                                          "Special Characters", "Non-Latin Characters"])
    summary_df = pd.DataFrame([summary])
    output_report = os.path.join(OUTPUT_FOLDER, "output_report.xlsx")
    with pd.ExcelWriter(output_report, engine="openpyxl") as writer:
        report_df.to_excel(writer, sheet_name="Details", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    print(f"{datetime.datetime.now()} - Report saved: {output_report}")

def run_watcher(auto_fix, dry_run):
    if not WATCHDOG_AVAILABLE:
        print(f"{datetime.datetime.now()} - Watchdog not available.")
        return
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                ext = os.path.splitext(event.src_path)[1].lower()
                if ext in [".xlsx", ".xls", ".csv"]:
                    print(f"{datetime.datetime.now()} - Detected new file: {event.src_path}")
                    res, summ = process_file(event.src_path, auto_fix, dry_run)
                    if res:
                        write_report(res, summ)
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=False)
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto_fix", action="store_true")
    parser.add_argument("--dry_run", action="store_true")
    parser.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    if args.watch:
        run_watcher(args.auto_fix, args.dry_run)
    else:
        results, summary = process_all_files(args.auto_fix, args.dry_run)
        write_report(results, summary)
        print(f"{datetime.datetime.now()} - Total cells processed: {summary['total_cells']}, Flagged: {summary['flagged']}, Fixed: {summary['fixed']}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    main()
