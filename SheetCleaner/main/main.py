import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import re
import requests
import tempfile
import pandas as pd
import concurrent.futures
import queue

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

allowed_accents = "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß.\\-'"
allowed_chars = fr"a-zA-Z0-9\s{allowed_accents}"
special_char_pattern = re.compile(fr"[^{allowed_chars}]")
non_latin_pattern = re.compile(r"[^\u0000-\u007F]")
supported_extensions = (
    ".xls", ".xlsx", ".xlsm", ".xlsb", ".gsheet", ".ods", ".csv", ".tsv", ".numbers",
    ".123", ".wk1", ".wk3", ".wk4", ".qpw", ".wb1", ".wb2", ".wb3", ".slk", ".dif", ".xml"
)

def load_sheets(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".xls", ".xlsx", ".xlsm", ".xlsb", ".ods"):
        try:
            xls = pd.ExcelFile(file_path)
        except Exception:
            return {}
        sheets = {}
        for sheet_name in xls.sheet_names:
            try:
                sheets[sheet_name] = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            except Exception:
                continue
        return sheets
    elif ext == ".csv":
        try:
            df = pd.read_csv(file_path, dtype=str, encoding="utf-8", errors="replace")
            return {"Sheet1": df}
        except Exception:
            return {}
    elif ext == ".tsv":
        try:
            df = pd.read_csv(file_path, dtype=str, sep="\t", encoding="utf-8", errors="replace")
            return {"Sheet1": df}
        except Exception:
            return {}
    elif ext == ".xml":
        try:
            df = pd.read_xml(file_path)
            return {"Sheet1": df}
        except Exception:
            return {}
    elif ext in (".slk", ".dif"):
        try:
            df = pd.read_csv(file_path, dtype=str, encoding="utf-8", errors="replace")
            return {"Sheet1": df}
        except Exception:
            return {}
    else:
        return {}

def process_df(file_name, sheet_name, df, results, log_queue):
    emplid_column = None
    for col in df.columns:
        if "EMPLID" in col.upper():
            emplid_column = col
            break
    rows = df.head(50)
    total_rows = len(rows)
    for row_idx, row in rows.iterrows():
        emplid_value = row[emplid_column] if emplid_column in df.columns else "N/A"
        for col_idx, cell_value in enumerate(row):
            if pd.notna(cell_value):
                cell_str = str(cell_value)
                special_chars = special_char_pattern.findall(cell_str)
                non_latin_chars = non_latin_pattern.findall(cell_str)
                if special_chars or non_latin_chars:
                    log_queue.put(f"Processing: {file_name} - {sheet_name} (row {row_idx+1}, column {df.columns[col_idx]})")
                    results.append({
                        "File Name": file_name,
                        "Sheet Name": sheet_name,
                        "EMPLID": emplid_value,
                        "Row": row_idx + 1,
                        "Column": df.columns[col_idx],
                        "Original Cell Value": cell_str,
                        "Special Characters": ''.join(sorted(set(special_chars))),
                        "Non-Latin Characters": ''.join(sorted(set(non_latin_chars)))
                    })
        log_queue.put(f"STATUS: Processed row {row_idx+1} of {total_rows} in {file_name} - {sheet_name}")

def process_file(file_path, results, log_queue):
    file_name = os.path.basename(file_path)
    log_queue.put(f"Processing file: {file_name}")
    sheets = load_sheets(file_path)
    if not sheets:
        log_queue.put(f"No sheets loaded from {file_name}.")
        return
    for sheet_name, df in sheets.items():
        process_df(file_name, sheet_name, df, results, log_queue)

def process_web_link(url, results, log_queue):
    try:
        log_queue.put(f"Downloading file from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        suffix = os.path.splitext(url)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(response.content)
            temp_file_path = tmp_file.name
        log_queue.put(f"Downloaded file to {temp_file_path}")
        process_file(temp_file_path, results, log_queue)
        os.remove(temp_file_path)
    except Exception as e:
        log_queue.put(f"Error processing web link {url}: {e}")

def process_folder(folder_path, results, log_queue):
    for root, _, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                file_path = os.path.join(root, file)
                process_file(file_path, results, log_queue)

class SheetScannerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sheet Scanner and Cleaner")
        self.geometry("700x500")
        self.resizable(True, True)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.log_queue = queue.Queue()
        self.create_widgets()
        self.after(100, self.process_log_queue)

    def create_widgets(self):
        self.input_type_var = tk.StringVar(value="file")
        frame_top = tk.Frame(self)
        frame_top.pack(pady=10, fill=tk.X, padx=10)
        tk.Label(frame_top, text="Select Input Type:").grid(row=0, column=0, sticky="w")
        tk.Radiobutton(frame_top, text="File", variable=self.input_type_var, value="file", command=self.update_input_frame).grid(row=0, column=1)
        tk.Radiobutton(frame_top, text="Folder", variable=self.input_type_var, value="folder", command=self.update_input_frame).grid(row=0, column=2)
        tk.Radiobutton(frame_top, text="Web Link", variable=self.input_type_var, value="web", command=self.update_input_frame).grid(row=0, column=3)
        self.frame_input = tk.Frame(self)
        self.frame_input.pack(pady=5, fill=tk.X, padx=10)
        self.entry_input = tk.Entry(self.frame_input, width=50)
        self.entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_browse = tk.Button(self.frame_input, text="Browse", command=self.browse_input)
        self.btn_browse.pack(side=tk.LEFT, padx=5)
        self.btn_process = tk.Button(self, text="Process", command=self.start_processing)
        self.btn_process.pack(pady=10)
        self.text_log = tk.Text(self, height=10)
        self.text_log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.status_label = tk.Label(self, text="Status: Idle")
        self.status_label.pack(padx=10, pady=5, fill=tk.X)
        self.update_input_frame()

    def update_input_frame(self):
        if self.input_type_var.get() in ("file", "folder"):
            self.btn_browse.config(state=tk.NORMAL)
            self.entry_input.delete(0, tk.END)
        else:
            self.btn_browse.config(state=tk.DISABLED)
            self.entry_input.delete(0, tk.END)

    def browse_input(self):
        if self.input_type_var.get() == "file":
            file_path = filedialog.askopenfilename(title="Select a sheet file", filetypes=[("All Supported", "*.xls *.xlsx *.xlsm *.xlsb *.ods *.csv *.tsv *.xml *.slk *.dif *.gsheet *.numbers *.123 *.wk1 *.wk3 *.wk4 *.qpw *.wb1 *.wb2 *.wb3"), ("All files", "*.*")])
            if file_path:
                self.entry_input.delete(0, tk.END)
                self.entry_input.insert(0, file_path)
        elif self.input_type_var.get() == "folder":
            folder_path = filedialog.askdirectory(title="Select a folder")
            if folder_path:
                self.entry_input.delete(0, tk.END)
                self.entry_input.insert(0, folder_path)

    def log(self, message):
        self.log_queue.put(message)

    def process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            if message.startswith("STATUS:"):
                self.status_label.config(text=message.replace("STATUS:", "").strip())
            else:
                self.text_log.insert(tk.END, message + "\n")
                self.text_log.see(tk.END)
        self.after(100, self.process_log_queue)

    def start_processing(self):
        self.btn_process.config(state=tk.DISABLED)
        self.text_log.delete(1.0, tk.END)
        self.status_label.config(text="Status: Processing...")
        user_input = self.entry_input.get().strip()
        input_type = self.input_type_var.get()
        results = []
        def processing_task():
            if input_type == "web":
                process_web_link(user_input, results, self.log)
            elif input_type == "file":
                if os.path.isfile(user_input):
                    process_file(user_input, results, self.log)
                else:
                    self.log("Invalid file path.")
            elif input_type == "folder":
                if os.path.isdir(user_input):
                    process_folder(user_input, results, self.log)
                else:
                    self.log("Invalid folder path.")
            if results:
                output_file = os.path.join(os.getcwd(), "scanned_report.csv")
                df_output = pd.DataFrame(results)
                df_output.to_csv(output_file, index=False, encoding="utf-8")
                self.log(f"Scan report saved: {output_file}")
                self.after(0, lambda: messagebox.showinfo("Process Complete", f"Scan report saved:\n{output_file}"))
            else:
                self.log("No unwanted special characters found.")
                self.after(0, lambda: messagebox.showinfo("Process Complete", "No unwanted special characters found."))
            self.after(0, lambda: self.btn_process.config(state=tk.NORMAL))
            self.after(0, lambda: self.status_label.config(text="Status: Idle"))
        self.executor.submit(processing_task)

    def on_closing(self):
        self.executor.shutdown(wait=False)
        self.destroy()

if __name__ == "__main__":
    app = SheetScannerGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
