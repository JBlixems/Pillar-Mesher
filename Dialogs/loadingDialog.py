import threading
import tkinter as tk
from tkinter import ttk

class MeshLoader:
    def __init__(self, mainloop, meshing_function):
        self.mainloop = mainloop
        self.meshing_function = meshing_function
        self.stop_event = threading.Event()
        self.meshing_thread = None

        self.loading_bar_size = 200

        self.window = tk.Toplevel(self.mainloop)
        self.window.title("Generating Mesh")
        self.window.geometry("300x130")

        # Progress bar
        self.progress = ttk.Progressbar(self.window, orient="horizontal", length=250, mode="determinate")
        self.progress.pack(pady=10)

        # Label
        self.label = tk.Label(self.window, text="Meshing the area...", font=("Helvetica", 12))
        self.label.pack(pady=5)

        # Cancel button
        cancel_button = tk.Button(self.window, text="Cancel", command=self.cancel_all)
        cancel_button.pack(pady=5)

        # Close button action
        self.window.protocol("WM_DELETE_WINDOW", self.cancel_all)

    def start_meshing(self, max_area, plot_func):
        """Start the meshing process in a separate thread."""
        self.meshing_thread = threading.Thread(target=self.meshing_function, args=(self.window, self.progress, self.label, self.stop_event, max_area, plot_func))
        self.meshing_thread.start()

    def cancel_all(self):
        """Handle cancelation of all threads and close the loading screen."""
        print("Cancel button clicked. Stopping all processes.")
        self.stop_event.set()  # Signal all threads to stop
        self.cleanup()

    def cleanup(self):
        """Cleanup resources and close the loading screen."""
        if hasattr(self, 'window') and self.window.winfo_exists():
            self.window.destroy()  # Close the loading screen