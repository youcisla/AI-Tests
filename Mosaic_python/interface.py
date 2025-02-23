import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from shape_generator import generate_shapes, generate_preview
from api.api import get_ai_response
from PIL import ImageTk
import tkinter as tk
from tkinter import messagebox
import threading

def launch_interface():
    root = ttk.Window(themename="minty")
    root.title("Advanced Nature Mosaic Generator")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    theme_var = tk.BooleanVar(value=False)
    complexity_var = tk.IntVar(value=5)
    num_var = tk.IntVar(value=50)
    output_dir = tk.StringVar(value="shapes")
    dimension = tk.StringVar(value="2D")
    progress_var = tk.DoubleVar(value=0)
    def update_preview(*args):
        comp = complexity_var.get()
        dim = dimension.get()
        img = generate_preview(complexity=comp, dimension=dim)
        photo = ImageTk.PhotoImage(img)
        preview_label.config(image=photo)
        preview_label.image = photo
    def toggle_theme():
        if theme_var.get():
            root.style.theme_use("darkly")
        else:
            root.style.theme_use("minty")
    def show_help():
        messagebox.showinfo("Help", "Adjust the complexity and number of patterns using the sliders.\nSelect 2D or 3D, toggle dark mode, and click 'Generate Patterns' to start.\nA progress bar will show the generation progress.")
    def show_prompt():
        def run_prompt():
            prompt = get_ai_response("Generate a creative mosaic art prompt that inspires innovative mosaic patterns.")
            messagebox.showinfo("Creative Prompt", prompt)
        threading.Thread(target=run_prompt, daemon=True).start()
    def progress_callback(current, total):
        progress_var.set((current / total) * 100)
        progress_bar.update_idletasks()
    def generate():
        gen_btn.config(state="disabled")
        try:
            generate_shapes(complexity=complexity_var.get(), num_shapes=num_var.get(), output_dir=output_dir.get(), dimension=dimension.get(), progress_callback=progress_callback)
            status_label.config(text="Generation complete.")
        except Exception as e:
            status_label.config(text=f"Error: {str(e)}")
        gen_btn.config(state="normal")
    def start_generation():
        threading.Thread(target=generate, daemon=True).start()
    main_frame = ttk.Frame(root, padding=10)
    main_frame.grid(sticky="nsew")
    main_frame.rowconfigure(2, weight=1)
    main_frame.columnconfigure(0, weight=1)
    top_frame = ttk.Frame(main_frame)
    top_frame.grid(row=0, column=0, sticky="ew")
    help_btn = ttk.Button(top_frame, text="Help", bootstyle=INFO, command=show_help)
    help_btn.pack(side="right")
    prompt_btn = ttk.Button(top_frame, text="Creative Prompt", bootstyle=INFO, command=show_prompt)
    prompt_btn.pack(side="right", padx=5)
    dark_mode_chk = ttk.Checkbutton(top_frame, text="Dark Mode", variable=theme_var, command=toggle_theme)
    dark_mode_chk.pack(side="right", padx=5)
    preview_frame = ttk.Frame(main_frame)
    preview_frame.grid(row=1, column=0, sticky="ew", pady=10)
    preview_label = ttk.Label(preview_frame)
    preview_label.pack()
    controls_frame = ttk.Frame(main_frame)
    controls_frame.grid(row=2, column=0, sticky="nsew", pady=10)
    controls_frame.columnconfigure(1, weight=1)
    ttk.Label(controls_frame, text="Complexity:").grid(row=0, column=0, sticky="w")
    comp_slider = ttk.Scale(controls_frame, from_=0, to=10, variable=complexity_var, command=lambda e: update_preview())
    comp_slider.grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Label(controls_frame, text="Patterns:").grid(row=1, column=0, sticky="w")
    num_slider = ttk.Scale(controls_frame, from_=10, to=200, variable=num_var, orient="horizontal")
    num_slider.grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Label(controls_frame, text="Output Folder:").grid(row=2, column=0, sticky="w")
    output_entry = ttk.Entry(controls_frame, textvariable=output_dir)
    output_entry.grid(row=2, column=1, sticky="ew", padx=5)
    dim_frame = ttk.Frame(controls_frame)
    dim_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
    ttk.Label(dim_frame, text="Dimension:").pack(side="left")
    ttk.Radiobutton(dim_frame, text="2D", variable=dimension, value="2D", command=update_preview).pack(side="left", padx=5)
    ttk.Radiobutton(dim_frame, text="3D", variable=dimension, value="3D", command=update_preview).pack(side="left", padx=5)
    progress_bar = ttk.Progressbar(controls_frame, variable=progress_var, maximum=100)
    progress_bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
    status_label = ttk.Label(controls_frame, text="")
    status_label.grid(row=5, column=0, columnspan=2, sticky="w")
    gen_btn = ttk.Button(controls_frame, text="Generate Patterns", bootstyle=SUCCESS, command=start_generation)
    gen_btn.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
    update_preview()
    root.mainloop()
