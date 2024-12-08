from tkinter import simpledialog, messagebox, Label, Entry, font

class GridSizeDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, scale_factor=1.5):
        self.grid_max_x = None
        self.grid_max_y = None
        self.scale_factor = scale_factor
        super().__init__(parent, title)

    def body(self, master):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=int(default_font.cget("size") * self.scale_factor))

        Label(master, text="Enter max grid X:", font=default_font).grid(row=0, column=0, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))
        self.entry_x = Entry(master, font=default_font)
        self.entry_x.grid(row=0, column=1, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))

        Label(master, text="Enter max grid Y:", font=default_font).grid(row=1, column=0, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))
        self.entry_y = Entry(master, font=default_font)
        self.entry_y.grid(row=1, column=1, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))

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
