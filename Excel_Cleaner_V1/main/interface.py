import os
import json
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter import ttk

# -----------------------------
# Configuration paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = r"C:\Users\Y.CHEHBOUB\Downloads\O3_Test\Here\SheetCleaner\input"
OUTPUT_XLSX = r"C:\Users\Y.CHEHBOUB\Downloads\O3_Test\Here\SheetCleaner\output\output.xlsx"
SCRIPT_NAME = "cleaner.py"
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# -----------------------------
# Functions for file operations
# -----------------------------
def add_files():
    """
    Allows the user to select .csv, .xls, or .xlsx files.
    Copies the selected files into the designated 'input' folder.
    """
    file_paths = filedialog.askopenfilenames(
        title="Select Files",
        filetypes=[("Excel/CSV files", "*.xlsx *.xls *.csv"), ("All files", "*.*")]
    )
    if not file_paths:
        return

    files_copied = 0
    for path in file_paths:
        try:
            filename = os.path.basename(path)
            dest = os.path.join(INPUT_FOLDER, filename)
            shutil.copy(path, dest)
            files_copied += 1
        except Exception as e:
            output_text.insert(tk.END, f"Error copying {filename}: {e}\n")
    if files_copied:
        output_text.insert(tk.END, f"{files_copied} file(s) added to the input folder.\n")

def run_sheet_cleaner():
    """
    Runs the cleaning script in a separate thread.
    Displays the script output (including summary) in the log box.
    """
    run_button.config(state=tk.DISABLED)
    output_text.delete('1.0', tk.END)
    output_text.insert(tk.END, "Running Sheet Cleaner...\n\n")

    def task():
        try:
            result = subprocess.run(
                ["python", SCRIPT_NAME],
                capture_output=True,
                text=True,
                cwd=BASE_DIR
            )
            if result.stdout:
                output_text.insert(tk.END, result.stdout)
            if result.stderr:
                output_text.insert(tk.END, "\nErrors:\n" + result.stderr)
        except Exception as e:
            output_text.insert(tk.END, f"Error running {SCRIPT_NAME}: {str(e)}\n")
        finally:
            run_button.config(state=tk.NORMAL)
    threading.Thread(target=task).start()

def view_output():
    """
    Force-open the generated 'output.xlsx' in Excel.
    If Excel is not in PATH, specify a full path to EXCEL.EXE if needed.
    """
    if os.path.exists(OUTPUT_XLSX):
        try:
            subprocess.run(["cmd", "/c", "start", "excel", OUTPUT_XLSX], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to open output file in Excel.\n{e}")
    else:
        messagebox.showinfo("No Output File", "No output file found. Please run the cleaner first.")

# -----------------------------
# Functions for Config management
# -----------------------------
def load_config():
    """Load config.json if exists; otherwise return defaults."""
    defaults = {
        "allowed_accents": list("àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß.\\-'"),
        "allowed_chars_prefix": ["a-zA-Z0-9", "\\s"]
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            # Ensure keys exist
            for key in defaults:
                if key not in config:
                    config[key] = defaults[key]
            return config
        except Exception as e:
            messagebox.showerror("Config Error", f"Error reading config file:\n{e}")
            return defaults
    else:
        return defaults

def save_config():
    """Save the config based on the current listbox values."""
    allowed_accents = list(listbox_accents.get(0, tk.END))
    allowed_chars_prefix = list(listbox_chars.get(0, tk.END))

    config = {
        "allowed_accents": allowed_accents,
        "allowed_chars_prefix": allowed_chars_prefix
    }
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Config Saved", "Configuration saved successfully.")
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not save config:\n{e}")

def add_item(listbox, entry):
    item = entry.get().strip()
    if item:
        listbox.insert(tk.END, item)
        entry.delete(0, tk.END)

def remove_item(listbox):
    selected = listbox.curselection()
    if selected:
        listbox.delete(selected[0])

def replace_item(listbox, entry):
    selected = listbox.curselection()
    if selected:
        item = entry.get().strip()
        if item:
            listbox.delete(selected[0])
            listbox.insert(selected[0], item)
            entry.delete(0, tk.END)

def load_config_to_ui():
    config = load_config()
    listbox_accents.delete(0, tk.END)
    for item in config.get("allowed_accents", []):
        listbox_accents.insert(tk.END, item)
    listbox_chars.delete(0, tk.END)
    for item in config.get("allowed_chars_prefix", []):
        listbox_chars.insert(tk.END, item)

# -----------------------------
# GUI SETUP with Notebook
# -----------------------------
root = tk.Tk()
root.title("Sheet Cleaner Tool")
root.geometry("900x700")
root.configure(bg="#f0f0f0")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ----- Main Tab -----
main_frame = ttk.Frame(notebook)
notebook.add(main_frame, text="Main")

title_label = tk.Label(main_frame, text="Sheet Cleaner Tool", font=("Arial", 18, "bold"), fg="#333", bg="#f0f0f0")
title_label.pack(pady=10)

desc = (
    "This tool cleans unwanted special characters from Excel/CSV files.\n"
    "1. Add your .csv, .xls, or .xlsx files to the 'input' folder.\n"
    "2. Click 'Run Sheet Cleaner' to process them.\n"
    "3. Click 'View Output' to open the generated Excel report in columns."
)
desc_label = tk.Label(main_frame, text=desc, font=("Arial", 11), justify="left", bg="#f0f0f0")
desc_label.pack(pady=5, padx=20, anchor="w")

button_frame = tk.Frame(main_frame, bg="#f0f0f0")
button_frame.pack(pady=10)
add_button = ttk.Button(button_frame, text="Add Files", command=add_files)
add_button.grid(row=0, column=0, padx=5, pady=5)
run_button = ttk.Button(button_frame, text="Run Sheet Cleaner", command=run_sheet_cleaner)
run_button.grid(row=0, column=1, padx=5, pady=5)
view_button = ttk.Button(button_frame, text="View Output", command=view_output)
view_button.grid(row=0, column=2, padx=5, pady=5)

output_frame = tk.Frame(main_frame, bg="#f0f0f0")
output_frame.pack(fill="both", expand=True, padx=20, pady=10)
output_label = tk.Label(output_frame, text="Log / Output:", font=("Arial", 12, "bold"), bg="#f0f0f0")
output_label.pack(anchor="w")
output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Consolas", 10))
output_text.pack(fill="both", expand=True)

footer_label = tk.Label(main_frame, text="© 2025 Your Company Name", font=("Arial", 8), bg="#f0f0f0", fg="#666")
footer_label.pack(side="bottom", pady=5)

# ----- Configuration Tab -----
config_frame = ttk.Frame(notebook)
notebook.add(config_frame, text="Configuration")

accents_frame = tk.LabelFrame(config_frame, text="Allowed Accents", font=("Arial", 11))
accents_frame.pack(fill="both", padx=15, pady=10, expand=True)

listbox_accents = tk.Listbox(accents_frame, height=8, font=("Consolas", 10))
listbox_accents.pack(side="left", fill="both", expand=True, padx=5, pady=5)
accents_scroll = ttk.Scrollbar(accents_frame, orient=tk.VERTICAL, command=listbox_accents.yview)
accents_scroll.pack(side="left", fill="y")
listbox_accents.config(yscrollcommand=accents_scroll.set)

accents_control = tk.Frame(accents_frame)
accents_control.pack(side="left", fill="y", padx=5)
accents_entry = ttk.Entry(accents_control, width=10)
accents_entry.pack(pady=2)
ttk.Button(accents_control, text="Add", command=lambda: add_item(listbox_accents, accents_entry)).pack(pady=2)
ttk.Button(accents_control, text="Remove", command=lambda: remove_item(listbox_accents)).pack(pady=2)
ttk.Button(accents_control, text="Replace", command=lambda: replace_item(listbox_accents, accents_entry)).pack(pady=2)

chars_frame = tk.LabelFrame(config_frame, text="Allowed Chars Prefix", font=("Arial", 11))
chars_frame.pack(fill="both", padx=15, pady=10, expand=True)

listbox_chars = tk.Listbox(chars_frame, height=6, font=("Consolas", 10))
listbox_chars.pack(side="left", fill="both", expand=True, padx=5, pady=5)
chars_scroll = ttk.Scrollbar(chars_frame, orient=tk.VERTICAL, command=listbox_chars.yview)
chars_scroll.pack(side="left", fill="y")
listbox_chars.config(yscrollcommand=chars_scroll.set)

chars_control = tk.Frame(chars_frame)
chars_control.pack(side="left", fill="y", padx=5)
chars_entry = ttk.Entry(chars_control, width=15)
chars_entry.pack(pady=2)
ttk.Button(chars_control, text="Add", command=lambda: add_item(listbox_chars, chars_entry)).pack(pady=2)
ttk.Button(chars_control, text="Remove", command=lambda: remove_item(listbox_chars)).pack(pady=2)
ttk.Button(chars_control, text="Replace", command=lambda: replace_item(listbox_chars, chars_entry)).pack(pady=2)

save_button = ttk.Button(config_frame, text="Save Config", command=save_config)
save_button.pack(pady=10)

# Load config on startup
load_config_to_ui()

root.mainloop()
