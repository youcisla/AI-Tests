import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import pandas as pd
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import logging
from config_manager import load_config, save_config

# ----------------- Logging Configuration -----------------
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SheetCleanerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Sheet Cleaner Tool")
        self.master.geometry("1000x800")
        # Set a greenish background for the entire window.
        self.master.configure(background="#f1f8e9")  # light green
        
        # Load configuration once.
        self.config = load_config()
        
        # Create the notebook (tabs)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill="both", expand=True)
        
        # Build tabs in a user-friendly order.
        self.build_main_tab()
        self.build_excel_viewer_tab()
        self.build_config_tab()
        self.build_help_tab()
        
        # Set exception handler.
        master.report_callback_exception = self.tk_report_callback_exception

    # ----------------- Main Tab -----------------
    def build_main_tab(self):
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Main")
        
        # Title label with Excel-green color.
        title_label = ttk.Label(
            self.main_frame, 
            text="Sheet Cleaner Tool", 
            font=("Helvetica", 22, "bold"),
            foreground="#2e7d32",  # dark green
            background="#f1f8e9"
        )
        title_label.pack(pady=10)
        
        instr = (
            "Instructions:\n"
            "1. Add Files: Copy files to the input folder.\n"
            "2. Run Sheet Cleaner: Process files (choose Auto-Fix or Dry Run as needed).\n"
            "3. View Report: Open the cleaned report in the Excel Viewer tab.\n"
            "4. Check Configuration for settings."
        )
        instr_label = ttk.Label(
            self.main_frame, 
            text=instr, 
            font=("Helvetica", 11),
            wraplength=900, 
            justify="left",
            foreground="#388e3c",  # medium green
            background="#f1f8e9"
        )
        instr_label.pack(pady=5)
        
        action_frame = ttk.Frame(self.main_frame, padding=10)
        action_frame.pack(pady=10, fill="x", padx=20)
        
        add_btn = ttk.Button(action_frame, text="Add Files", command=self.add_files)
        add_btn.grid(row=0, column=0, padx=5)
        self.create_tooltip(add_btn, "Select files to copy into the input folder.")
        
        self.auto_fix_var = tk.BooleanVar()
        self.dry_run_var = tk.BooleanVar()
        auto_fix_check = ttk.Checkbutton(action_frame, text="Auto-Fix", variable=self.auto_fix_var)
        auto_fix_check.grid(row=0, column=1, padx=5)
        dry_run_check = ttk.Checkbutton(action_frame, text="Dry Run", variable=self.dry_run_var)
        dry_run_check.grid(row=0, column=2, padx=5)
        
        self.run_button = ttk.Button(action_frame, text="Run Sheet Cleaner", command=self.run_sheet_cleaner)
        self.run_button.grid(row=0, column=3, padx=5)
        self.create_tooltip(self.run_button, "Start cleaning the sheets.")
        
        view_button = ttk.Button(action_frame, text="View Report", command=self.view_report)
        view_button.grid(row=0, column=4, padx=5)
        self.create_tooltip(view_button, "Switch to Excel Viewer tab to see the report.")
        
        # Folder entries.
        folder_frame = ttk.Frame(self.main_frame, padding=10)
        folder_frame.pack(pady=5)
        ttk.Label(folder_frame, text="Input Folder:", foreground="#1b5e20").grid(row=0, column=0, sticky="e")
        self.input_folder_entry = ttk.Entry(folder_frame, width=50)
        self.input_folder_entry.insert(0, self.config.get("input_folder"))
        self.input_folder_entry.grid(row=0, column=1, padx=5)
        ttk.Button(folder_frame, text="Browse", command=lambda: self.browse_folder(self.input_folder_entry)).grid(row=0, column=2, padx=5)
        
        ttk.Label(folder_frame, text="Output Folder:", foreground="#1b5e20").grid(row=1, column=0, sticky="e")
        self.output_folder_entry = ttk.Entry(folder_frame, width=50)
        self.output_folder_entry.insert(0, self.config.get("output_folder"))
        self.output_folder_entry.grid(row=1, column=1, padx=5)
        ttk.Button(folder_frame, text="Browse", command=lambda: self.browse_folder(self.output_folder_entry)).grid(row=1, column=2, padx=5)
        
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        
        output_frame = ttk.Frame(self.main_frame, padding=10)
        output_frame.pack(fill="both", expand=True, padx=20, pady=10)
        ttk.Label(output_frame, text="Log / Output:", font=("Helvetica", 12, "bold"), foreground="#2e7d32").pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(output_frame, width=110, height=10)
        self.log_text.pack(fill="both", expand=True)
    
    # ----------------- Configuration Tab -----------------
    def build_config_tab(self):
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        
        ttk.Label(self.config_frame, text="Allowed Accents (space-separated):", foreground="#6a1b9a").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.accents_entry = ttk.Entry(self.config_frame, width=80)
        self.accents_entry.insert(0, " ".join(self.config.get("allowed_accents", [])))
        self.accents_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.config_frame, text="Allowed Chars Prefix (space-separated):", foreground="#6a1b9a").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.prefix_entry = ttk.Entry(self.config_frame, width=80)
        self.prefix_entry.insert(0, " ".join(self.config.get("allowed_chars_prefix", [])))
        self.prefix_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.config_frame, text="Replacement Mappings (key -> value per line):", foreground="#6a1b9a").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.mapping_text = scrolledtext.ScrolledText(self.config_frame, width=60, height=4)
        if self.config.get("replacement_mappings"):
            mappings_str = "\n".join([f"{k} -> {v}" for k, v in self.config["replacement_mappings"].items()])
            self.mapping_text.insert(tk.END, mappings_str)
        self.mapping_text.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.config_frame, text="Input Folder Path:", foreground="#6a1b9a").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.conf_input_folder_entry = ttk.Entry(self.config_frame, width=80)
        self.conf_input_folder_entry.insert(0, self.config.get("input_folder"))
        self.conf_input_folder_entry.grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(self.config_frame, text="Browse", command=lambda: self.browse_folder(self.conf_input_folder_entry)).grid(row=3, column=2, padx=5, pady=5)
        
        ttk.Label(self.config_frame, text="Output Folder Path:", foreground="#6a1b9a").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.conf_output_folder_entry = ttk.Entry(self.config_frame, width=80)
        self.conf_output_folder_entry.insert(0, self.config.get("output_folder"))
        self.conf_output_folder_entry.grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(self.config_frame, text="Browse", command=lambda: self.browse_folder(self.conf_output_folder_entry)).grid(row=4, column=2, padx=5, pady=5)
        
        ttk.Button(self.config_frame, text="Save Config", command=self.save_current_config).grid(row=5, column=1, pady=10)
    
    # ----------------- Excel Viewer Tab -----------------
    def build_excel_viewer_tab(self):
        self.excel_viewer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.excel_viewer_frame, text="Excel Viewer")
        self.excel_tree = ttk.Treeview(self.excel_viewer_frame)
        self.excel_tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    # ----------------- Help Tab -----------------
    def build_help_tab(self):
        self.help_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.help_frame, text="Help")
        self.help_text_box = scrolledtext.ScrolledText(self.help_frame, width=100, height=20, wrap=tk.WORD)
        self.help_text_box.pack(padx=10, pady=10)
        self.load_help_text()
    
    # ----------------- Methods for Buttons -----------------
    def browse_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)
    
    def add_files(self):
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
                dest = os.path.join(self.config["input_folder"], filename)
                shutil.copy(path, dest)
                files_copied += 1
            except Exception as e:
                self.log_text.insert(tk.END, f"Error copying {filename}: {e}\n")
                logging.exception(f"Error copying file: {filename}")
        if files_copied:
            self.log_text.insert(tk.END, f"{files_copied} file(s) added to the input folder.\n")
    
    def run_sheet_cleaner(self):
        self.save_current_config()
        self.run_button.config(state="disabled")
        self.log_text.delete('1.0', tk.END)
        self.log_text.insert(tk.END, "Running Sheet Cleaner...\n\n")
        args = ["python", os.path.join("..", "src", "cleaner.py")]
        if self.auto_fix_var.get():
            args.append("--auto_fix")
        if self.dry_run_var.get():
            args.append("--dry_run")
        def task():
            try:
                proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                while True:
                    line = proc.stdout.readline()
                    if line:
                        self.log_text.insert(tk.END, line)
                        self.log_text.see(tk.END)
                    elif proc.poll() is not None:
                        break
                err = proc.stderr.read()
                if err:
                    self.log_text.insert(tk.END, "\nErrors:\n" + err)
                    logging.error("Error output from cleaner.py:\n" + err)
            except Exception as e:
                self.log_text.insert(tk.END, f"Error running cleaner.py: {e}\n")
                logging.exception("Error running cleaner.py")
            finally:
                self.run_button.config(state="normal")
        threading.Thread(target=task).start()
    
    def view_report(self):
        self.refresh_excel_viewer()
        self.notebook.select(self.excel_viewer_frame)
    
    def refresh_excel_viewer(self):
        report_path = os.path.join(self.config["output_folder"], "output_report.xlsx")
        for row in self.excel_tree.get_children():
            self.excel_tree.delete(row)
        if os.path.exists(report_path):
            try:
                report = pd.read_excel(report_path, sheet_name="Details")
                self.excel_tree["columns"] = list(report.columns)
                self.excel_tree["show"] = "headings"
                for col in report.columns:
                    self.excel_tree.heading(col, text=col)
                    self.excel_tree.column(col, width=120)
                for _, row in report.iterrows():
                    self.excel_tree.insert("", tk.END, values=list(row))
            except Exception as e:
                messagebox.showerror("Error", f"Unable to load report:\n{e}")
                logging.exception("Error loading Excel report")
        else:
            # If no report exists, clear the view.
            pass
    
    def refresh_debug_log(self):
        # Debug Log tab has been removed.
        pass
    
    def load_help_text(self):
        help_message = (
            "Sheet Cleaner Tool - Feature Overview:\n\n"
            "1. Allowed Dates: Cells containing dates (dd/mm/yyyy, yyyy/dd/mm, yyyy/mm/dd, mm/dd/yyyy) will not be modified.\n\n"
            "2. Allowed Parenthesized Names: Names within parentheses (e.g. (John Doe)) are preserved.\n\n"
            "3. Allowed Apostrophes: Names with apostrophes (e.g. O'Connor) remain unchanged.\n\n"
            "4. Auto-Fix: When enabled, cells flagged during cleaning are automatically corrected.\n\n"
            "5. Dry Run: Simulates cleaning without modifying files.\n\n"
            "6. Excel Viewer: The cleaned report is displayed in the 'Excel Viewer' tab.\n\n"
            "7. Configuration: In the 'Configuration' tab, you can update settings. (Click 'Save Config' after changes.)"
        )
        self.help_text_box.config(state="normal")
        self.help_text_box.delete("1.0", tk.END)
        self.help_text_box.insert(tk.END, help_message)
        self.help_text_box.config(state="disabled")
    
    def save_current_config(self):
        self.config["allowed_accents"] = self.accents_entry.get().split()
        self.config["allowed_chars_prefix"] = self.prefix_entry.get().split()
        mapping_lines = self.mapping_text.get("1.0", tk.END).strip().splitlines()
        mappings = {}
        for line in mapping_lines:
            if "->" in line:
                key, value = line.split("->", 1)
                mappings[key.strip()] = value.strip()
        self.config["replacement_mappings"] = mappings
        self.config["input_folder"] = self.conf_input_folder_entry.get() if hasattr(self, 'conf_input_folder_entry') else self.input_folder_entry.get()
        self.config["output_folder"] = self.conf_output_folder_entry.get() if hasattr(self, 'conf_output_folder_entry') else self.output_folder_entry.get()
        try:
            save_config(self.config)
            messagebox.showinfo("Config Saved", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save config:\n{e}")
    
    def tk_report_callback_exception(self, exc, val, tb):
        logging.exception("Unhandled Tkinter exception", exc_info=(exc, val, tb))
        messagebox.showerror("Unhandled Exception", f"An error occurred:\n{val}\nSee debug.log for details.")

    # Simple tooltip method
    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry("0x0+0+0")
        tooltip.withdraw()
        label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1, font=("Helvetica", 10))
        label.pack()
        def enter(event):
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()
        def leave(event):
            tooltip.withdraw()
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)


if __name__ == "__main__":
    root = ttkb.Window(themename="minty")  # using minty as a base; colors overridden below.
    # Override styles to match our Excel-greenish color scheme.
    style = ttkb.Style("minty")
    style.configure("TButton", font=("Helvetica", 12, "bold"), padding=6, background="#388e3c", foreground="white")
    style.map("TButton",
              foreground=[('pressed', 'white'), ('active', 'white')],
              background=[('pressed', '!disabled', '#2e7d32'), ('active', '#2e7d32')])
    # Optionally, override label styles if needed.
    app = SheetCleanerApp(root)
    root.mainloop()
