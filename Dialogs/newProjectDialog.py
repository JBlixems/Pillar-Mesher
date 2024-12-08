from tkinter import simpledialog, filedialog, messagebox, Label, Button, Entry, font
import os

class NewProjectDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, scale_factor=1.5):
        self.project_name = None
        self.parent_folder = None
        self.project_path = None
        self.scale_factor = scale_factor
        super().__init__(parent, title)

    def body(self, master):
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=int(default_font.cget("size") * self.scale_factor))

        # Project name entry
        Label(master, text="Enter Project Name:", font=default_font).grid(row=0, column=0, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))
        self.project_name_entry = Entry(master, font=default_font, width=int(34 * self.scale_factor))
        self.project_name_entry.grid(row=0, column=1, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))

        # Parent folder selection
        Label(master, text="Select Parent Folder:", font=default_font).grid(row=1, column=0, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))
        self.parent_folder_label = Label(master, text="(None selected)", bg="white", anchor="w", relief="solid", width=int(30 * self.scale_factor))
        self.parent_folder_label.grid(row=1, column=1, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor), sticky="ew")
        Button(master, text="Browse...", command=self.select_folder, font=default_font).grid(row=1, column=2, padx=int(5 * self.scale_factor), pady=int(5 * self.scale_factor))

        # Make the parent folder label expand
        master.columnconfigure(1, weight=1)

        return self.project_name_entry

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Parent Folder")
        if folder:
            self.parent_folder = folder
            self.parent_folder_label.config(text=folder)

    def validate(self):
        self.project_name = self.project_name_entry.get().strip()
        if not self.project_name:
            messagebox.showerror("Error", "Project name cannot be empty!")
            return False

        if not self.parent_folder:
            messagebox.showerror("Error", "Parent folder must be selected!")
            return False

        self.project_path = os.path.join(self.parent_folder, self.project_name)
        if os.path.exists(self.project_path):
            messagebox.showerror("Error", "Project folder already exists!")
            return False

        return True

    def apply(self):
        # Create the project folder
        try:
            os.makedirs(self.project_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create project folder: {e}")
            self.project_path = None
   
