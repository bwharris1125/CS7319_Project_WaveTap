"""
Tkinter-based mockup for the main Dashboard GUI of WaveTap.

This is a static mockup for documentation and screenshot purposes only.
NOTE: GitHub CoPilot was used to assist in writing the code for this mockup.
"""

import os
import tkinter as tk
from tkinter import ttk


class DashboardMockup(tk.Tk):
    """
    A mockup dashboard UI for the WaveTap application, built using Tkinter.
    """  # noqa: D200

    def __init__(self):
        """
        Initialize the DashboardMockup window.

        Sets up the main window properties (title, size, background) and
        constructs all UI widgets, including the header, status panel, map
        view, controls, and footer.
        """
        super().__init__()
        self.title("WaveTap Dashboard Mockup")
        self.geometry("800x500")
        self.configure(bg="#f4f4f4")
        self._create_widgets()

    def _create_widgets(self):
        # Header
        header = tk.Label(
            self,
            text="WaveTap Dashboard",
            font=("Arial", 22, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=16,
        )
        header.pack(fill=tk.X)

        # Main content frame
        main_frame = tk.Frame(self, bg="#f4f4f4")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        # Left panel: Status
        status_frame = tk.LabelFrame(
            main_frame,
            text="System Status",
            font=("Arial", 12, "bold"),
            padx=12,
            pady=12,
            bg="#f4f4f4",
        )
        status_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16), pady=0)
        tk.Label(
            status_frame,
            text="SDR Connected: Yes",
            font=("Arial", 11),
            bg="#f4f4f4",
        ).pack(anchor="w")
        tk.Label(
            status_frame,
            text="ADS-B Feed: Active",
            font=("Arial", 11),
            bg="#f4f4f4",
        ).pack(anchor="w")
        tk.Label(
            status_frame,
            text="Last Sync: 2025-09-03 14:22",
            font=("Arial", 11),
            bg="#f4f4f4",
        ).pack(anchor="w")

        # Center panel: Map placeholder (display example_map.png if present)
        map_frame = tk.LabelFrame(
            main_frame,
            text="Live Map View",
            font=("Arial", 12, "bold"),
            padx=12,
            pady=12,
            bg="#e9ecef",
        )

        # Display the static example map image (if present) and scale it to
        # the map_frame when the frame resizes. Pillow is used for high-quality
        # resizing if available. If Pillow isn't available, the image will be
        # shown at native size (Tk PhotoImage).
        img_path = os.path.join(os.path.dirname(__file__), "example_map.png")

        # Label that will hold the PhotoImage (if any)
        self._map_label = tk.Label(map_frame, bg="#e9ecef")
        self._map_label.pack(fill=tk.BOTH, expand=True)

        # Prepare image sources
        self._pil_available = False
        self._orig_pil_img = None
        self._orig_photo = None

        if os.path.exists(img_path):
            try:
                from PIL import Image

                self._pil_available = True
                self._orig_pil_img = Image.open(img_path)
            except Exception:
                # Pillow not available; try Tkinter.PhotoImage (may not resize)
                try:
                    self._orig_photo = tk.PhotoImage(file=img_path)
                except Exception:
                    self._orig_photo = None

        # Canvas placeholder (created on demand)
        self._map_canvas = None

        def _on_map_frame_configure(event):
            w, h = max(1, event.width), max(1, event.height)

            if self._pil_available and self._orig_pil_img is not None:
                # Resize PIL image to fit while preserving aspect ratio
                orig_w, orig_h = self._orig_pil_img.size
                scale = min(w / orig_w, h / orig_h)
                new_w = max(1, int(orig_w * scale))
                new_h = max(1, int(orig_h * scale))
                try:
                    from PIL import ImageTk

                    resized = self._orig_pil_img.resize(
                        (new_w, new_h), Image.LANCZOS
                    )
                    self._map_photo = ImageTk.PhotoImage(resized)
                    self._map_label.configure(image=self._map_photo)
                    # if canvas was visible before, hide it
                    if self._map_canvas is not None:
                        self._map_canvas.pack_forget()
                        self._map_canvas = None
                except Exception:
                    pass
            elif self._orig_photo is not None:
                # No Pillow: show native image (no smooth scaling available)
                self._map_label.configure(image=self._orig_photo)
                if self._map_canvas is not None:
                    self._map_canvas.pack_forget()
                    self._map_canvas = None
            else:
                # No image available: show a canvas placeholder and center text
                if self._map_canvas is None:
                    # remove label image if any
                    self._map_label.configure(image="")
                    self._map_canvas = tk.Canvas(map_frame, bg="#b2bec3")
                    self._map_canvas.pack(fill=tk.BOTH, expand=True)

                self._map_canvas.delete("_ph")
                self._map_canvas.create_text(
                    w // 2,
                    h // 2,
                    text="[Map View Placeholder]",
                    font=("Arial", 13, "italic"),
                    fill="#636e72",
                    tags=("_ph",),
                )

        # Bind resize events so the image follows the frame size
        map_frame.bind("<Configure>", _on_map_frame_configure)

        # Right panel: Controls
        control_frame = tk.LabelFrame(
            main_frame,
            text="Controls",
            font=("Arial", 12, "bold"),
            padx=12,
            pady=12,
            bg="#f4f4f4",
        )
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0), pady=0)
        ttk.Button(control_frame, text="Start Capture").pack(fill=tk.X, pady=4)
        ttk.Button(control_frame, text="Stop Capture").pack(fill=tk.X, pady=4)
        ttk.Button(control_frame, text="Export Data").pack(fill=tk.X, pady=4)
        ttk.Button(control_frame, text="Settings").pack(fill=tk.X, pady=4)

        # Now pack the map frame so it expands into the remaining space
        map_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 16), pady=0
        )

        # Footer
        footer = tk.Label(
            self,
            text="WaveTap v1.0 | For demonstration only",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="white",
            pady=6,
        )
        footer.pack(fill=tk.X, side=tk.BOTTOM)


if __name__ == "__main__":
    app = DashboardMockup()
    app.mainloop()
