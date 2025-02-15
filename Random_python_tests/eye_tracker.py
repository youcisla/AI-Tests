import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import time

# Initialize MediaPipe Face Mesh with refined landmarks (includes iris landmarks)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Landmark indices for various regions (these are approximations based on MediaPipe's face mesh):
LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]

# Use a subset of face contour landmarks for skin overlay.
FACE_CONTOUR = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152]

# Outer lips indices.
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308]

# Eyebrow indices (combining approximate left and right eyebrows).
EYEBROWS = [70, 63, 105, 66, 107, 336, 296, 334, 293, 300]

def get_gaze_color(iris_points, mode="Normal"):
    """
    Compute the iris center relative to its bounding box and return an overlay color
    based on the gaze direction.
    Modes:
      - "Normal": Subtle overlay.
      - "Mood": Blended with a neutral tone.
      - "Dramatic": Bold color.
    Returns a BGR tuple (e.g. (255, 0, 0)) or None if the iris appears centered.
    """
    iris_np = np.array(iris_points, dtype=np.int32)
    center = np.mean(iris_np, axis=0)
    min_x = np.min(iris_np[:, 0])
    max_x = np.max(iris_np[:, 0])
    min_y = np.min(iris_np[:, 1])
    max_y = np.max(iris_np[:, 1])
    
    if max_x - min_x == 0 or max_y - min_y == 0:
        return None

    ratio_x = (center[0] - min_x) / (max_x - min_x)
    ratio_y = (center[1] - min_y) / (max_y - min_y)

    # Determine base color based on iris position.
    if ratio_x < 0.4:
        base_color = (255, 0, 0)      # Blue: looking left
    elif ratio_x > 0.6:
        base_color = (0, 255, 0)      # Green: looking right
    elif ratio_y < 0.4:
        base_color = (0, 0, 255)      # Red: looking up
    elif ratio_y > 0.6:
        base_color = (255, 0, 255)    # Purple: looking down
    else:
        return None  # Centered gaze: no overlay

    # Modify intensity based on mode.
    if mode == "Normal":
        return tuple(int(c * 0.6) for c in base_color)
    elif mode == "Mood":
        neutral = np.array([100, 100, 100])
        color = np.array(base_color, dtype=np.float32)
        blended = 0.5 * color + 0.5 * neutral
        return tuple(int(x) for x in blended)
    elif mode == "Dramatic":
        return base_color
    else:
        return base_color

def get_region_color(region, mode):
    """
    Return a predetermined overlay color (BGR) for a facial region, based on the chosen mode.
    """
    if region == "skin":
        if mode == "Normal":
            return (200, 180, 160)  # Subtle warm tone.
        elif mode == "Mood":
            return (180, 160, 140)
        elif mode == "Dramatic":
            return (0, 165, 255)    # Bright orange.
    elif region == "lips":
        if mode == "Normal":
            return (180, 105, 255)  # Subtle pink.
        elif mode == "Mood":
            return (150, 80, 200)
        elif mode == "Dramatic":
            return (0, 0, 255)      # Vivid red.
    elif region == "eyebrows":
        if mode == "Normal":
            return (50, 50, 50)     # Dark gray.
        elif mode == "Mood":
            return (30, 30, 30)
        elif mode == "Dramatic":
            return (0, 0, 0)        # Black.
    return None

class EyeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Dynamic Gaze-Triggered Facial Color Changer")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Video display area.
        self.video_label = tk.Label(root)
        self.video_label.pack()

        # Controls frame.
        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack(fill="x", pady=5)

        # Start/Stop buttons.
        self.start_button = tk.Button(self.controls_frame, text="Start", command=self.start)
        self.start_button.grid(row=0, column=0, padx=5)
        self.stop_button = tk.Button(self.controls_frame, text="Stop", command=self.stop, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)

        # Snapshot button.
        self.snapshot_button = tk.Button(self.controls_frame, text="Snapshot", command=self.save_snapshot, state="disabled")
        self.snapshot_button.grid(row=0, column=2, padx=5)

        # Mode selection.
        tk.Label(self.controls_frame, text="Mode:").grid(row=0, column=3, padx=5)
        self.mode_var = tk.StringVar(value="Normal")
        self.mode_option = ttk.Combobox(self.controls_frame, textvariable=self.mode_var, values=["Normal", "Mood", "Dramatic"], state="readonly", width=10)
        self.mode_option.grid(row=0, column=4, padx=5)

        # Overlay intensity slider.
        tk.Label(self.controls_frame, text="Overlay Intensity:").grid(row=0, column=5, padx=5)
        self.intensity_var = tk.DoubleVar(value=0.4)
        self.intensity_slider = tk.Scale(self.controls_frame, variable=self.intensity_var, from_=0.0, to=1.0, resolution=0.05, orient="horizontal", length=150)
        self.intensity_slider.grid(row=0, column=6, padx=5)

        # Checkboxes for region overlays.
        self.eye_overlay_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.controls_frame, text="Eye Overlay", variable=self.eye_overlay_var).grid(row=1, column=0, padx=5)
        self.skin_overlay_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.controls_frame, text="Skin Overlay", variable=self.skin_overlay_var).grid(row=1, column=1, padx=5)
        self.lips_overlay_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.controls_frame, text="Lips Overlay", variable=self.lips_overlay_var).grid(row=1, column=2, padx=5)
        self.eyebrows_overlay_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.controls_frame, text="Eyebrows Overlay", variable=self.eyebrows_overlay_var).grid(row=1, column=3, padx=5)
        self.landmarks_checkbox = tk.Checkbutton(self.controls_frame, text="Show Outlines", variable=tk.BooleanVar(value=True))
        self.landmarks_checkbox.grid(row=1, column=4, padx=5)

        # Info label.
        self.info_label = tk.Label(root, text="Press 'Start' to begin video feed.", fg="blue")
        self.info_label.pack(pady=5)

        self.cap = None
        self.running = False
        self.current_frame = None
        self.face_landmarks = None

    def start(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.info_label.config(text="Error: Unable to access the webcam.", fg="red")
            return
        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.snapshot_button.config(state="normal")
        self.info_label.config(text="Video feed running. Adjust controls as desired.", fg="green")
        self.update_frame()

    def stop(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.snapshot_button.config(state="disabled")
        self.info_label.config(text="Video feed stopped. Press 'Start' to resume.", fg="blue")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.video_label.config(image="")

    def save_snapshot(self):
        if self.current_frame is not None:
            filename = f"snapshot_{int(time.time())}.png"
            cv2.imwrite(filename, self.current_frame)
            messagebox.showinfo("Snapshot Saved", f"Snapshot saved as {filename}")

    def process_region(self, frame, landmark_indices, overlay_color, intensity, show_outline):
        height, width, _ = frame.shape
        points = []
        for idx in landmark_indices:
            lm = self.face_landmarks.landmark[idx]
            points.append((int(lm.x * width), int(lm.y * height)))
        if len(points) < 3:
            return frame
        mask = np.zeros((height, width), dtype=np.uint8)
        pts = np.array(points, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        overlay = np.full(frame.shape, overlay_color, dtype=np.uint8)
        colored_region = cv2.addWeighted(frame, 1 - intensity, overlay, intensity, 0)
        frame = np.where(mask[:, :, np.newaxis] == 255, colored_region, frame)
        if show_outline:
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=1)
        return frame

    def process_eye(self, frame, width, height, iris_indices, mode, intensity, show_outline):
        iris_points = []
        for idx in iris_indices:
            lm = self.face_landmarks.landmark[idx]
            iris_points.append((int(lm.x * width), int(lm.y * height)))
        if len(iris_points) != len(iris_indices):
            return frame
        overlay_color = get_gaze_color(iris_points, mode=mode)
        if overlay_color is None:
            return frame
        mask = np.zeros((height, width), dtype=np.uint8)
        pts = np.array(iris_points, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
        overlay = np.full(frame.shape, overlay_color, dtype=np.uint8)
        colored_eye = cv2.addWeighted(frame, 1 - intensity, overlay, intensity, 0)
        frame = np.where(mask[:, :, np.newaxis] == 255, colored_eye, frame)
        if show_outline:
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 255), thickness=1)
        return frame

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.info_label.config(text="Error: Could not grab frame.", fg="red")
            self.stop()
            return

        self.current_frame = frame.copy()
        height, width, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)

        self.face_landmarks = None
        if results.multi_face_landmarks:
            self.face_landmarks = results.multi_face_landmarks[0]
            mode = self.mode_var.get()
            intensity = self.intensity_var.get()
            show_outline = True  # You could tie this to the "Show Outlines" checkbox if desired.
            # Process eyes if enabled.
            if self.eye_overlay_var.get():
                frame = self.process_eye(frame, width, height, LEFT_IRIS_INDICES, mode, intensity, show_outline)
                frame = self.process_eye(frame, width, height, RIGHT_IRIS_INDICES, mode, intensity, show_outline)
            # Process skin overlay if enabled.
            if self.skin_overlay_var.get():
                skin_color = get_region_color("skin", mode)
                frame = self.process_region(frame, FACE_CONTOUR, skin_color, intensity, show_outline)
            # Process lips overlay if enabled.
            if self.lips_overlay_var.get():
                lips_color = get_region_color("lips", mode)
                frame = self.process_region(frame, LIPS, lips_color, intensity, show_outline)
            # Process eyebrows overlay if enabled.
            if self.eyebrows_overlay_var.get():
                eyebrows_color = get_region_color("eyebrows", mode)
                frame = self.process_region(frame, EYEBROWS, eyebrows_color, intensity, show_outline)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)
        self.root.after(10, self.update_frame)

    def on_closing(self):
        self.stop()
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = EyeTrackerApp(root)
    root.mainloop()
