# directory_reporter.py
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from api import get_ai_response  # Ensure your api.py is set up as before

def choose_directory():
    dir_path = filedialog.askdirectory(title="Select Directory to Scan")
    if dir_path:
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, dir_path)

def scan_directory():
    directory = directory_entry.get()
    if not directory or not os.path.isdir(directory):
        messagebox.showerror("Error", "Please select a valid directory.")
        return

    report_text.delete("1.0", tk.END)
    overall_report = ""
    
    # Walk through the directory recursively.
    for root_dir, sub_dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root_dir, file)
            ext = os.path.splitext(file)[1]
            header = f"\n--- Report for: {file_path} ---\n"
            overall_report += header

            # Try reading the file as text.
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                is_text = True
            except Exception:
                is_text = False

            # Build a concise AI prompt based on file type.
            if is_text:
                # Use only a snippet if file is large.
                snippet = content if len(content) <= 500 else content[:500] + "..."
                prompt = (
                    f"File Name: {file}\n"
                    f"File Path: {file_path}\n"
                    f"Extension: {ext}\n"
                    f"Snippet of Content (max 500 characters):\n{snippet}\n\n"
                    "Instructions: Analyze the file content and identify any issues, errors, or areas for improvement. "
                    "Then, provide a brief, step-by-step guide (using bullet points) on how to fix the problems. "
                    "Use very simple, non-technical language and keep your answer very short."
                )
            else:
                size = os.path.getsize(file_path)
                prompt = (
                    f"File Name: {file}\n"
                    f"File Path: {file_path}\n"
                    f"Extension: {ext}\n"
                    f"Size: {size} bytes\n\n"
                    "Instructions: This is a binary file. Provide a very brief, bullet-point troubleshooting guide on "
                    "common issues that might occur with files of this type and simple steps to fix them. "
                    "Keep the explanation non-technical and minimal."
                )

            # Update status so the user knows which file is processing.
            status_var.set(f"Processing: {file_path}")
            root_window.update()

            try:
                file_report = get_ai_response(prompt)
            except Exception as e:
                file_report = f"Error processing file: {e}"

            overall_report += file_report + "\n"
            report_text.insert(tk.END, header + file_report + "\n")
    
    status_var.set("Scan complete!")
    overall_report_global.set(overall_report)

def save_report():
    report = overall_report_global.get()
    if not report:
        messagebox.showerror("Error", "No report to save.")
        return
    file_path = filedialog.asksaveasfilename(
        title="Save Report", defaultextension=".txt", 
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            messagebox.showinfo("Success", "Report saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report:\n{e}")

# ------------------- Set up the Tkinter UI -------------------
root_window = tk.Tk()
root_window.title("Directory Scanner & Report Generator")

# Directory selection row.
tk.Label(root_window, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
directory_entry = tk.Entry(root_window, width=50)
directory_entry.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root_window, text="Browse...", command=choose_directory).grid(row=0, column=2, padx=5, pady=5)

# Scan button.
tk.Button(root_window, text="Scan Directory", command=scan_directory).grid(row=1, column=1, padx=5, pady=5)

# Status label.
status_var = tk.StringVar(value="")
tk.Label(root_window, textvariable=status_var).grid(row=2, column=1, padx=5, pady=5)

# Report display (scrollable).
report_text = scrolledtext.ScrolledText(root_window, width=80, height=20)
report_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

# Save report button.
tk.Button(root_window, text="Save Report", command=save_report).grid(row=4, column=1, padx=5, pady=5)

# Global variable to hold overall report.
overall_report_global = tk.StringVar(value="")

root_window.mainloop()
