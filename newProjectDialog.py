import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import os

class NewProjectDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None):
        self.project_name = None
        self.parent_folder = None
        self.project_path = None
        super().__init__(parent, title)

    def body(self, master):
        # Project name entry
        tk.Label(master, text="Enter Project Name:").grid(row=0, column=0, padx=5, pady=5)
        self.project_name_entry = tk.Entry(master)
        self.project_name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Parent folder selection
        tk.Label(master, text="Select Parent Folder:").grid(row=1, column=0, padx=5, pady=5)
        self.parent_folder_label = tk.Label(master, text="(None selected)", bg="white", anchor="w", relief="solid")
        self.parent_folder_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(master, text="Browse...", command=self.select_folder).grid(row=1, column=2, padx=5, pady=5)

        # Make the parent folder label expand
        master.columnconfigure(1, weight=1)

        return self.project_name_entry  # Initial focus

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
   
