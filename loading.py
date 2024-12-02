import threading
import tkinter as tk
from tkinter import ttk

class MeshLoader:
    def __init__(self, mainloop, meshing_function):
        self.mainloop = mainloop
        self.meshing_function = meshing_function
        self.stop_event = threading.Event()
        self.loading_thread = None
        self.meshing_thread = None

        self.loading_bar_size = 200

        self.window = tk.Toplevel(self.mainloop)
        self.window.title("Generating Mesh")
        self.window.geometry("300x150")

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

    def show_loading_screen(self):
        """Show the loading screen with a progress bar and cancel button."""
        self.window.mainloop()

    def start_meshing(self, max_area):
        """Start the meshing process in a separate thread."""
        self.meshing_thread = threading.Thread(target=self.meshing_function, args=(self.window, self.progress, self.label, self.stop_event, max_area))
        self.meshing_thread.start()

    def start_loading(self):
        self.loading_thread = threading.Thread(target=self.show_loading_screen)
        self.loading_thread.start()

    def cancel_all(self):
        """Handle cancelation of all threads and close the loading screen."""
        print("Cancel button clicked. Stopping all processes.")
        # self.stop_event.set()  # Signal all threads to stop
        self.cleanup()

    def cleanup(self):
        """Cleanup resources and close the loading screen."""
        if hasattr(self, 'window') and self.window.winfo_exists():
            self.window.destroy()  # Close the loading screen
        if self.loading_thread and self.loading_thread.is_alive():
            self.loading_thread.join()  # Wait for the loading thread to exit
        # if self.meshing_thread and self.meshing_thread.is_alive():
        #     self.meshing_thread.join()  # Wait for the meshing thread to exit