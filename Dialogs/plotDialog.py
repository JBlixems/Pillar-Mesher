import os
import numpy as np
import matplotlib.pyplot as plt
from threading import Thread
from constants import MINED_OUTPUT_FILENAME_START, ELEMENT_FILE_EXT

class Plotter:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def read_file(self, file_path):
        """Reads a single .tri file and extracts vertex and triangle data."""
        vertices = []
        triangles = []
        with open(file_path, "r") as file:
            for line in file:
                if line.startswith("E_LT:"):
                    parts = line.split(";")[-1].strip().split()
                    coords = list(map(float, parts))
                    # Ensure we are appending triplets of points (x1, y1, x2, y2, x3, y3)
                    vertices.append([coords[0], coords[1]])  # x1, y1
                    vertices.append([coords[2], coords[3]])  # x2, y2
                    vertices.append([coords[4], coords[5]])  # x3, y3
                    idx = len(vertices)
                    triangles.append([idx - 3, idx - 2, idx - 1])

        vertices = np.array(vertices)

        # Check the shape of the vertices array
        if vertices.ndim == 1:
            vertices = vertices.reshape(-1, 2)  # Reshape to ensure it's a 2D array

        return {"vertices": vertices, "triangles": np.array(triangles)}

    def read_mesh_data(self):
        """Reads all .tri files in the folder and organizes them by color."""
        mesh_data = []
        if not os.path.exists(self.folder_path):
            return mesh_data
        
        for filename in os.listdir(self.folder_path):
            if filename.endswith(f".{ELEMENT_FILE_EXT}"):
                file_path = os.path.join(self.folder_path, filename)
                mesh = self.read_file(file_path)
                color = "gray" if filename.startswith(MINED_OUTPUT_FILENAME_START) else "blue"
                mesh_data.append((mesh, color))
        return mesh_data

    def plot_mesh(self, mesh_data):
        """Plots mesh data using matplotlib."""
        plt.figure(figsize=(10, 8))
        for mesh, color in mesh_data:
            plt.triplot(
                mesh["vertices"][:, 0],  # x-coordinates
                mesh["vertices"][:, 1],  # y-coordinates
                mesh["triangles"],       # triangle connectivity
                color=color,
            )

        plt.gcf().canvas.manager.set_window_title('PolyMesh - Mesh Plot') 
        plt.title("Mesh Plot")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.axis("equal")
        plt.show(block=True)

    def run_plotter(self):
        """Runs the plotting function in a separate thread."""
        mesh_data = self.read_mesh_data()
        plot_thread = Thread(target=self.plot_mesh, args=(mesh_data,))
        plot_thread.start()
