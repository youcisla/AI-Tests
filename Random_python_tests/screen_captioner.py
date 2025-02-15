import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pyautogui
import requests  # <-- for calling local LLM server

from transformers import BlipProcessor, BlipForConditionalGeneration

# Load BLIP model and processor.
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

class ScreenCaptionerApp:
    def __init__(self, root, capture_interval=5, api_url="http://127.0.0.1:8000/v1/chat/completions"):
        self.root = root
        self.root.title("Screen Captioner + Local LLM")
        self.capture_interval = capture_interval  # seconds between captures
        self.running = False
        self.thread = None

        # URL of your locally running "OpenAI-style" server (openai_api.py)
        self.api_url = api_url

        # Frame to display screenshot and captions.
        self.image_label = tk.Label(root)
        self.image_label.pack(padx=10, pady=10)

        # BLIP caption text
        self.caption_label = tk.Label(root, text="BLIP Caption will appear here.", wraplength=500, justify="center", font=("Arial", 14))
        self.caption_label.pack(padx=10, pady=10)

        # LLM expanded text
        self.llm_label = tk.Label(root, text="Local LLM Output will appear here.", wraplength=500, justify="center", font=("Arial", 12), fg="blue")
        self.llm_label.pack(padx=10, pady=10)

        # Controls frame.
        controls = tk.Frame(root)
        controls.pack(pady=5)
        self.start_button = tk.Button(controls, text="Start", command=self.start)
        self.start_button.grid(row=0, column=0, padx=5)
        self.stop_button = tk.Button(controls, text="Stop", command=self.stop, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)
        self.capture_button = tk.Button(controls, text="Capture Now", command=self.capture_once)
        self.capture_button.grid(row=0, column=2, padx=5)

        # Handle window close event.
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start(self):
        """Start the continuous screen captioning."""
        if not self.running:
            self.running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            # Create a non-daemon thread and start it.
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def stop(self):
        """Stop the continuous screen captioning."""
        self.running = False
        # If a thread is running, join it to clean up.
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def capture_once(self):
        """Capture the screen, generate caption, and update UI."""
        screenshot = pyautogui.screenshot()
        # Resize screenshot (PIL Image) for display.
        display_image = screenshot.resize((500, int(500 * screenshot.height / screenshot.width)))
        imgtk = ImageTk.PhotoImage(display_image)
        self.image_label.imgtk = imgtk
        self.image_label.configure(image=imgtk)

        # Generate caption using the BLIP model.
        blip_caption = self.generate_caption(screenshot)
        self.caption_label.config(text=f"BLIP Caption:\n{blip_caption}")

        # Call local LLM to expand on the BLIP caption.
        # For example, ask: "What else can you say about this image?"
        llm_text = self.call_local_llm(blip_caption)
        self.llm_label.config(text=f"LLM Output:\n{llm_text}")

    def generate_caption(self, image):
        """Generate a caption for the given PIL image using BLIP."""
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True)
        return caption

    def call_local_llm(self, caption):
        """
        Send the BLIP caption to the locally running openai_api.py server
        to get a more detailed or alternative description.
        """
        # You can craft the prompt any way you like.
        # Here we simply ask the model to elaborate on the BLIP caption.
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "gpt-3.5-turbo",  # must match the ID used in openai_api.py
            "messages": [
                {"role": "user", "content": f"Based on the caption '{caption}', please describe in more detail what might be happening or what the image contains."}
            ],
            "stream": False
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            response_json = response.json()

            # The local server returns a structure with .choices[0].message.content
            llm_output = response_json["choices"][0]["message"]["content"]
            return llm_output.strip()
        except Exception as e:
            return f"[Error calling local LLM: {e}]"

    def run(self):
        """Continuously capture screen and update the caption."""
        while self.running:
            self.capture_once()
            time.sleep(self.capture_interval)

    def on_closing(self):
        """Ensure we stop thread if running and close the application."""
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    # For demonstration, capture the screen every 5 seconds
    # and call the local LLM at http://127.0.0.1:8000
    app = ScreenCaptionerApp(root, capture_interval=5, api_url="http://127.0.0.1:8000/v1/chat/completions")
    root.mainloop()
