import numpy as np
import cv2
import os
import customtkinter
import subprocess

from CTkMenuBar import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from Dialogs.loadingDialog import MeshLoader
from mesher import Mesher
from Dialogs.plotDialog import Plotter
from Dialogs.gridSizeDialog import GridSizeDialog
from Dialogs.triangleSizeDialog import TriangleSizeDialog
from Dialogs.newProjectDialog import NewProjectDialog
from constants import *

# Pyinstaller command to create an executable
# pyinstaller --onefile --windowed --add-data "Assets;Assets" --icon=Assets/Logo.ico PolyMesh.py

class PolyMesh:
    def __init__(self):
        self.path_to_logo_image = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Assets', 'Logo.png'))
        self.path_to_select_image = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Assets', 'Select Image.png'))
        self.project_path = os.getcwd()

        self.dialog_scale_factor = 1.5
        self.current_image_path = self.path_to_select_image
        self.image1 = cv2.imread(self.current_image_path)
        self.polygons = []
        self.canvas_image = None
        self.pillar_image = None

        # Create the main Tkinter window
        customtkinter.set_appearance_mode("light")

        self.root = customtkinter.CTk()
        self.root.title("PolyMesh - Polygon Mesh Generator")
        self.root.after(0, lambda: self.root.wm_state('zoomed'))
        self.root.focus = True
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

        icon_photo = ImageTk.PhotoImage(Image.open(self.path_to_logo_image))
        self.root.iconphoto(True, icon_photo)

        self.init_menu()
        self.init_toolbar()
        self.init_canvas()

        self.root.mainloop()

    def init_menu(self):
        self.menu_bar = CTkMenuBar(self.root)
        self.menu_bar._corner_radius = 0
        self.menu_bar.pack(side="top", fill="x")

        file_menu = self.menu_bar.add_cascade("File")
        file_menu._corner_radius = 0
        save_menu = self.menu_bar.add_cascade("Save")
        save_menu._corner_radius = 0
        self.image_menu = self.menu_bar.add_cascade("Image")
        self.image_menu._corner_radius = 0
        mesh_menu = self.menu_bar.add_cascade("Mesh")
        mesh_menu._corner_radius = 0

        # File Menu
        file_menu_drop = CustomDropdownMenu(file_menu)
        file_menu_drop.corner_radius = 0
        file_menu_drop._corner_radius = 0
        file_menu_drop.add_option(option="New Project", command=self.new_project)
        file_menu_drop.add_option(option="Open Project", command=self.open_project)
        file_menu_drop.add_separator()
        file_menu_drop.add_option(option="Upload Image", command=self.upload_image)

        # Save Menu
        save_menu_drop = CustomDropdownMenu(save_menu)
        save_menu_drop.corner_radius = 0
        save_menu_drop._corner_radius = 0
        save_menu_drop.add_option(option="Save Border", command=self.save_outline)
        save_menu_drop.add_option(option="Save Pillars", command=self.save_pillars)

        # # Mesh Menu
        mesh_menu_drop = CustomDropdownMenu(mesh_menu)
        mesh_menu_drop.corner_radius = 0
        mesh_menu_drop._corner_radius = 0
        mesh_menu_drop.add_option(option="Mesh Files", command=self.mesh_files)
        mesh_menu_drop.add_option(option="Plot Mesh", command=self.plot_files)

        self.populate_select_menu()

    def init_toolbar(self):
        # Create a frame for the toolbar
        self.toolbar = customtkinter.CTkFrame(self.root)
        self.toolbar.pack(side="top", fill="x", anchor="n")

        # Display the current working directory
        self.current_directory_label = customtkinter.CTkLabel(
            self.toolbar, 
            text=f"Project: {os.path.split(self.project_path)[-1]}",
            anchor="w",
            cursor="hand2",
            font=("Arial", 14, "bold"),
        )
        self.current_directory_label.bind("<Button-1>", self.open_project_path)
        self.current_directory_label.pack(side="right", padx=5, anchor="ne")

        # Create a frame inside the toolbar for sliders (to center them)
        self.sliders_frame = customtkinter.CTkFrame(self.toolbar)
        self.sliders_frame.pack(side="top", padx=10)

        # Add the epsilon slider
        customtkinter.CTkLabel(self.sliders_frame, text="Vertex Sensitivity Factor").pack(side="left", padx=5)

        self.epsilon_slider = customtkinter.CTkSlider(
            self.sliders_frame,
            from_=1,
            to=1000,
            command=lambda x: self.update_image(),
        )
        self.epsilon_slider.set(100)
        self.epsilon_slider.pack(side="left", padx=15)

        # Add the pixel distance slider
        customtkinter.CTkLabel(self.sliders_frame, text="Minimum Vertex Distance").pack(side="left", padx=5)

        self.min_distance_slider = customtkinter.CTkSlider(
            self.sliders_frame,
            from_=0,
            to=1000,
            command=lambda x: self.update_image(),
        )
        self.min_distance_slider.set(0)
        self.min_distance_slider.pack(side="left", padx=15)

    def init_canvas(self):
        # Create a ttk.Frame to hold the canvas
        self.canvas_frame = customtkinter.CTkFrame(self.root)
        self.canvas_frame.pack(fill="both", expand=True)
        
        # Create a canvas to display the image
        self.canvas = customtkinter.CTkCanvas(self.canvas_frame)
        self.canvas.pack(fill="both", expand=True)

        # Update the Tkinter window to ensure dimensions are available
        self.root.update_idletasks()

        # Get the fullscreen dimensions
        canvas_width = self.root.winfo_width()
        canvas_height = self.root.winfo_height() - self.toolbar.winfo_height() - self.menu_bar.winfo_height()

        print(f"Fullscreen size: {canvas_width}x{canvas_height}")

        # Configure the canvas to match fullscreen dimensions
        self.canvas.config(width=canvas_width, height=canvas_height)

        # Resize the image to fit the fullscreen canvas
        image_rgb = cv2.cvtColor(self.image1, cv2.COLOR_BGR2RGB)
        resized_image = self.resize_image_to_fit_canvas(image_rgb, canvas_width, canvas_height)

        # Convert to Tkinter-compatible image
        image_pil = Image.fromarray(resized_image)
        self.image_tk = ImageTk.PhotoImage(image_pil)

        # Calculate offsets to center the image on the canvas
        image_width, image_height = self.image_tk.width(), self.image_tk.height()
        x_offset = (canvas_width - image_width) // 2
        y_offset = (canvas_height - image_height) // 2

        # Display the image on the canvas, centered
        self.canvas_image = self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.image_tk)

        self.update_image()

    # Populate the "Select" submenu with image files
    def populate_select_menu(self):
        """Dynamically populates the 'Select' menu with image files."""

        # Add "Select" menu to the Image Menu
        self.image_menu_drop = CustomDropdownMenu(self.image_menu)
        self.image_menu_drop.corner_radius = 0
        self.image_menu_drop._corner_radius = 0

        image_files = [
            os.path.join(self.project_path, f)
            for f in os.listdir(self.project_path)
            if f.lower().endswith(('.png', '.jpg'))
        ]
        if not image_files:
            self.image_menu_drop.add_option(option="No images found")
        else:
            for image_path in image_files:
                image_name = os.path.basename(image_path)
                self.image_menu_drop.add_option(
                    option=image_name,
                    command=lambda path=image_path: self.select_image(path)
                )

    # Bind a click event to open the file explorer
    def open_project_path(self, event):
        print("Opening project path", self.project_path)
        if os.path.exists(self.project_path):
            # Open the directory in the file explorer
            subprocess.Popen(f'explorer "{self.project_path}"')

    def on_window_resize(self, event):
        """Handle window resize events."""
        if hasattr(self, '_last_size'):
            # Avoid redundant updates if the size hasn't changed
            if self._last_size == (event.width, event.height):
                return
        self._last_size = (event.width, event.height)
        
        # Update the canvas and the image
        self.update_image()

    def find_polygons(self, image, canny_threshold1=50, canny_threshold2=150, epsilon_factor=0.01, min_vertex_distance=0):
        if self.current_image_path == self.path_to_select_image:
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)

        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        edges = cv2.erode(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        polygons = []
        for contour in contours:
            epsilon = epsilon_factor * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            # polygons.append(approx)

            # Filter vertices based on minimum distance
            filtered_approx = []
            for i, vertex in enumerate(approx):
                if i == 0 or np.linalg.norm(vertex[0] - filtered_approx[-1][0]) > min_vertex_distance:
                    filtered_approx.append(vertex)

            polygons.append(np.array(filtered_approx))
        
        return polygons

    def resize_image_to_fit_canvas(self, image, canvas_width, canvas_height):
        """Resize the image to fit within the canvas while preserving its aspect ratio."""
        h, w = image.shape[:2]
        scale = min(canvas_width / w, canvas_height / h)
        new_width = int(w * scale)
        new_height = int(h * scale)
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        return resized_image

    def quit_application(self):
        self.root.destroy()

    # Function to update the displayed image
    def update_image(self):
        epsilon_factor = self.epsilon_slider.get() / 100000.0
        min_vertex_distance = self.min_distance_slider.get() / 10.0
        image_copy = self.image1.copy()
        
        # Find polygons
        self.polygons = self.find_polygons(image_copy, epsilon_factor=epsilon_factor, min_vertex_distance=min_vertex_distance)
        num_polygons = len(self.polygons)
        num_vertices = sum(len(polygon) for polygon in self.polygons)

        for i, polygon in enumerate(self.polygons):
            avg_x = int(np.mean(polygon[:, 0, 0]))
            avg_y = int(np.mean(polygon[:, 0, 1]))
            for point in polygon:
                x, y = point[0]
                cv2.circle(image_copy, (x, y), 6, (19, 69, 139), -1)
            cv2.putText(image_copy, str(i + 1), (avg_x - 3, avg_y - 3), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)

        # Display number of polygons and vertices identified
        cv2.putText(image_copy, f'Polygons: {num_polygons}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(image_copy, f'Vertices: {num_vertices}', (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Resize image to fit canvas
        canvas_width = self.root.winfo_width() 
        canvas_height = self.root.winfo_height() - self.toolbar.winfo_height() - self.menu_bar.winfo_height()
        image_rgb = cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB)
        self.pillar_image = image_rgb
        resized_image = self.resize_image_to_fit_canvas(image_rgb, canvas_width, canvas_height)

        # Convert to Tkinter image
        image_pil = Image.fromarray(resized_image)
        image_tk = ImageTk.PhotoImage(image_pil)

        # Calculate offsets to center the image on the canvas
        image_width, image_height = resized_image.shape[1], resized_image.shape[0]
        x_offset = (canvas_width - image_width) // 2
        y_offset = (canvas_height - image_height) // 2

        # Update the canvas
        self.canvas.itemconfig(self.canvas_image, image=image_tk)
        self.canvas.coords(self.canvas_image, x_offset, y_offset)
        self.canvas.image = image_tk  # Store reference to avoid garbage collection

    # Function to upload a new image
    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
        if file_path:
            # Copy the image to the project folder give it a unique file name
            new_image_path = os.path.join(self.project_path, os.path.basename(file_path))
            cv2.imwrite(new_image_path, cv2.imread(file_path))          

            self.select_image(new_image_path)

            self.populate_select_menu()

    def select_image(self, path):
        if os.path.exists(path):
            self.current_image_path = path
            self.image1 = cv2.imread(path)
            self.update_image()

    def _get_data_folder_path(self):
        return os.path.join(self.project_path, DATA_FOLDER_NAME)
    
    def _get_mesh_folder_path(self):
        return os.path.join(self.project_path, DATA_FOLDER_NAME, MESH_FOLDER_NAME)
    
    def _get_plot_folder_path(self):
        return os.path.join(self.project_path, DATA_FOLDER_NAME, PLOT_FOLDER_NAME)

    # Function to save polygons to a text file
    def save_polygons(self, pillars=True):
        dialog = GridSizeDialog(self.root, title="Grid Size Input", scale_factor=self.dialog_scale_factor)
        grid_max_x = dialog.grid_max_x
        grid_max_y = dialog.grid_max_y
        
        if grid_max_x is None or grid_max_y is None:
            return 
        
        if not os.path.exists(self._get_data_folder_path()):
            os.makedirs(self._get_data_folder_path())

        height, width = self.image1.shape[:2]
        filename = os.path.join(self._get_data_folder_path(), PILLAR_VERTEX_FILE_NAME) if pillars else os.path.join(self._get_data_folder_path(), BORDER_VERTEX_FILE_NAME)
        with open(filename, "w") as f:
            for i, polygon in enumerate(self.polygons):
                f.write(f"{PILLAR_OUTPUT_FILENAME_START if pillars else MINED_OUTPUT_FILENAME_START}{i+1}\n")
                for point in polygon:
                    x, y = point[0]
                    actual_x = (x / width) * grid_max_x
                    actual_y = grid_max_y - (y / height) * grid_max_y
                    f.write(f"{actual_x:.4f} {actual_y:.4f}\n")

        # Save current image to the data folder
        if pillars and self.pillar_image is not None:
            cv2.imwrite(os.path.join(self._get_data_folder_path(), PILLAR_NUMBERS_IMAGE), self.pillar_image)

    def new_project(self):
        dialog = NewProjectDialog(self.root, title="Create New Project", scale_factor=self.dialog_scale_factor)
        if dialog.project_path:
            dialog.project_path.replace("/", "\\")
            self.project_path = dialog.project_path
            print(f"New project created at: {dialog.project_path}")
            self.current_directory_label.configure(text=f"Project: {os.path.split(self.project_path)[-1]}")

            self.populate_select_menu()

            self.image1 = cv2.imread(self.current_image_path)


    def open_project(self):
        folder_path = filedialog.askdirectory(title="Open Project Folder")

        # Change project path to valid os path
        folder_path = folder_path.replace("/", "\\")

        if folder_path:
            self.project_path = folder_path
            self.current_directory_label.configure(text=f"Project: {os.path.split(self.project_path)[-1]}")

            image_files = [
                os.path.join(self.project_path, f)
                for f in os.listdir(self.project_path)
                if f.lower().endswith(('.png', '.jpg'))
            ]
            if image_files:
                self.current_image_path = image_files[0]
                self.image1 = cv2.imread(image_files[0])
                self.update_image()
            
            self.populate_select_menu()
        else:
            self.image1 = cv2.imread(self.current_image_path)

    def save_outline(self):
        self.save_polygons(pillars=False)

    def save_pillars(self):
        self.save_polygons(pillars=True)

    def mesh_files(self):
        # Check if the data folder exists with border.dat and pillars.dat
        data_folder_path = self._get_data_folder_path()
        if not os.path.exists(data_folder_path):
            messagebox.showerror("Error", "No vertices found. Please save the border and pillars first.")
            return
        
        pillar_file = os.path.join(data_folder_path, PILLAR_VERTEX_FILE_NAME)
        border_file = os.path.join(data_folder_path, BORDER_VERTEX_FILE_NAME)

        if not os.path.exists(pillar_file):
            messagebox.showerror("Error", "No pillars found. Please save the pillars first.")
            return
        
        if not os.path.exists(border_file):
            messagebox.showerror("Error", "No border found. Please save the border first.")
            return

        mesher = Mesher(self.project_path)
        dialog = TriangleSizeDialog(self.root, title="Mesh Triangle Size Input", scale_factor=self.dialog_scale_factor)
        max_area = dialog.triangle_size
        if max_area is not None:
            mesh_loader = MeshLoader(self.root, mesher.mesh_area)
            mesh_loader.start_meshing(max_area, self.plot_files)

    def plot_files(self):
        folder_path = self._get_mesh_folder_path()
        plotter = Plotter(folder_path)
        plotter.plot_mesh(plotter.read_mesh_data())

if __name__ == "__main__":
    try:
        PolyMesh()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while running the application.\n{e}")