from tkinter import simpledialog, messagebox, Label, Entry, font

class TriangleSizeDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, scale_factor=1.5):
        self.triangle_size = None
        self.scale_factor = scale_factor
        super().__init__(parent, title)

    def body(self, master):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=int(default_font.cget("size") * self.scale_factor))

        Label(master, text="Max mesh triangle size:", font=default_font).grid(row=0, column=0, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))
        self.entry_x = Entry(master, font=default_font)
        self.entry_x.grid(row=0, column=1, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))

        return self.entry_x

    def validate(self):
        x = self.entry_x.get().strip()
        if not x and not isinstance(x, float):
            messagebox.showerror("Error", "Make sure the value is a decimal numbers!")
            return False

        return True

    def apply(self):
        try:
            self.triangle_size = int(self.entry_x.get())
        except ValueError:
            self.triangle_size = None
