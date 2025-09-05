"""
Tkinter-based mockup for the main Dashboard GUI of WaveTap.

This is a static mockup for documentation and screenshot purposes only.
NOTE: GitHub CoPilot was used to assist in writing the code for this mockup.

TODO: this is currently based on the mockup, and being used as a placeholder.
"""

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

        # Canvas placeholder (created on demand)
        self._map_canvas = None

        def _on_map_frame_configure(event):
            w, h = max(1, event.width), max(1, event.height)

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
