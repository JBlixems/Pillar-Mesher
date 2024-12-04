import tkinter as tk
from tkinter import simpledialog, messagebox

class GridSizeDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.grid_max_x = None
        self.grid_max_y = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Enter max grid X:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_x = tk.Entry(master)
        self.entry_x.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(master, text="Enter max grid Y:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_y = tk.Entry(master)
        self.entry_y.grid(row=1, column=1, padx=5, pady=5)

        return self.entry_x  # Initial focus

    def validate(self):
        x = self.entry_x.get().strip()
        y = self.entry_y.get().strip()
        if not x and not isinstance(x, float) and not y and not isinstance(y, float):
            messagebox.showerror("Error", "Make sure both values are decimal numbers!")
            return False

        return True

    def apply(self):
        try:
            self.grid_max_x = int(self.entry_x.get())
            self.grid_max_y = int(self.entry_y.get())
        except ValueError:
            self.grid_max_x = None
            self.grid_max_y = None

