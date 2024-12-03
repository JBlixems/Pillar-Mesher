import numpy as np
import cv2
import os
from tkinter import Tk, Scale, HORIZONTAL, Canvas, filedialog, simpledialog, Menu, ttk
from PIL import Image, ImageTk
from loadingDialog import MeshLoader
from mesher import Mesher
from plotDialog import Plotter
from inputDialog import GridSizeDialog
from constants import *

class Window:
    def __init__(self):
        self.project_path = os.getcwd()
        print("Project path:", self.project_path)
        self.image1 = cv2.imread(os.path.join("Example", "layout.png"))
        self.polygons = []
        self.epsilon_factor = 0.01
        self.canvas_image = None

        # Create the main Tkinter window
        self.root = Tk()
        self.root.title("Image Processing with Polygons")
        self.root.state('zoomed')
        self.root.bind("<Configure>", self.on_window_resize)

        # Create a menu bar
        menu_bar = Menu()

        # File Menu
        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Upload Image", command=self.upload_image)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Save Menu
        save_menu = Menu(menu_bar, tearoff=0)
        save_menu.add_command(label="Save Outline", command=self.save_outline)
        save_menu.add_command(label="Save Pillars", command=self.save_pillars)
        menu_bar.add_cascade(label="Save", menu=save_menu)

        # Mesh Menu
        mesh_menu = Menu(menu_bar, tearoff=0)
        mesh_menu.add_command(label="Mesh Files", command=self.mesh_files)
        mesh_menu.add_command(label="Plot Files", command=self.plot_files)
        menu_bar.add_cascade(label="Mesh", menu=mesh_menu)

        # Attach the menu bar to the root window
        self.root.config(menu=menu_bar)

        # Add a slider for epsilon factor
        self.epsilon_slider = Scale(self.root, from_=1, to=1000, orient=HORIZONTAL, label="Vertex Sensitivity Factor", command=lambda x: self.update_image(), length=400, showvalue=0)
        self.epsilon_slider.pack(side="top")

        # Create a canvas to display the image
        self.canvas = Canvas(self.root)
        self.canvas.pack(fill="both", expand=True)

        self.initialize_canvas()
        self.update_image()

        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        # Start the Tkinter main loop
        self.root.mainloop()

    def on_window_resize(self, event):
        """Handle window resize events."""
        if hasattr(self, '_last_size'):
            # Avoid redundant updates if the size hasn't changed
            if self._last_size == (event.width, event.height):
                return
        self._last_size = (event.width, event.height)
        
        # Update the canvas and the image
        self.canvas.size = (event.width, event.height)
        self.update_image()

    def find_polygons(self, image, canny_threshold1=50, canny_threshold2=150, epsilon_factor=0.01):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)

        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        edges = cv2.erode(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        polygons = []
        min_vertex_distance = 10
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
        image_copy = self.image1.copy()
        
        # Find polygons
        self.polygons = self.find_polygons(image_copy, epsilon_factor=epsilon_factor)
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
        canvas_height = self.root.winfo_height()
        image_rgb = cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB)
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
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image1 = cv2.imread(file_path)
            self.update_image()

    def _get_data_folder_path(self):
        return os.path.join(self.project_path, DATA_FOLDER_NAME)
    
    def _get_mesh_folder_path(self):
        return os.path.join(self.project_path, DATA_FOLDER_NAME, MESH_FOLDER_NAME)
    
    def _get_plot_folder_path(self):
        return os.path.join(self.project_path, DATA_FOLDER_NAME, PLOT_FOLDER_NAME)

    # Function to save polygons to a text file
    def save_polygons(self, pillars=True):
        dialog = GridSizeDialog(self.root, title="Grid Size Input")
        grid_max_x = dialog.grid_max_x
        grid_max_y = dialog.grid_max_y
        
        if grid_max_x is None or grid_max_y is None:
            print("Failed to get x and y grid values")
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

    def new_project(self):
        print("New Project selected")
        # Your new project functionality here

    def open_project(self):
        folder_path = filedialog.askdirectory(title="Open Project Folder")
        if folder_path:
            self.project_path = folder_path
            print(f"Opening project from {folder_path}")
            # Add logic to open the project

    def save_outline(self):
        self.save_polygons(pillars=False)

    def save_pillars(self):
        self.save_polygons(pillars=True)

    def mesh_files(self):
        mesher = Mesher(self.project_path)
        max_area = simpledialog.askfloat("Input", "Enter triangle max area:", initialvalue=0.5)
        if max_area is not None:
            mesh_loader = MeshLoader(self.root, mesher.mesh_area)

            mesh_loader.start_meshing(max_area)

    def plot_files(self):
        folder_path = self._get_mesh_folder_path()
        plotter = Plotter(folder_path)
        plotter.run_plotter()

    def initialize_canvas(self):
        # Update the Tkinter window to ensure dimensions are available
        self.root.update_idletasks()

        # Get the fullscreen dimensions
        canvas_width = self.root.winfo_width()
        canvas_height = self.root.winfo_height()

        print(f"Fullscreen size: {canvas_width}x{canvas_height}")

        # Configure the canvas to match fullscreen dimensions
        self.canvas.config(width=canvas_width, height=canvas_height)

        # Resize the image to fit the fullscreen canvas
        image_rgb = cv2.cvtColor(self.image1, cv2.COLOR_BGR2RGB)
        resized_image = self.resize_image_to_fit_canvas(image_rgb, canvas_width, canvas_height)

        # Convert to Tkinter-compatible image
        image_pil = Image.fromarray(resized_image)
        image_tk = ImageTk.PhotoImage(image_pil)

        # Calculate offsets to center the image on the canvas
        image_width, image_height = resized_image.shape[1], resized_image.shape[0]
        x_offset = (canvas_width - image_width) // 2
        y_offset = (canvas_height - image_height) // 2

        # Display the image on the canvas, centered
        self.canvas_image = self.canvas.create_image(x_offset, y_offset, anchor="nw", image=image_tk)
        self.canvas.image = image_tk  # Store reference to avoid garbage collection



if __name__ == "__main__":
    Window()