import triangle
import numpy as np
import os
from constants import *

class Mesher:
    def __init__(self, project_path):
        self.triangles = 0
        self.stop_thread = False
        self.project_path = project_path

    # Function to read vertices from a file
    def read_vertices_from_file(self, filename):
        vertices = []
        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if line.strip().startswith(MINED_OUTPUT_FILENAME_START) or line.strip().startswith(PILLAR_OUTPUT_FILENAME_START):
                    continue
                parts = line.strip().split()
                if len(parts) == 2:
                    x, y = map(float, parts)
                    vertices.append([x, y])
        return np.array(vertices)

    # Function to check if a point is inside a given polygon
    def is_point_in_polygon(self, point, polygon):
        x, y = point
        inside = False
        n = len(polygon)
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
  
    def enforce_edge_constraint(self, mesh, max_edges=9):
        # Create adjacency list to count edges per vertex
        vertex_edges = {i: set() for i in range(len(mesh['vertices']))}
        for triangle_indices in mesh['triangles']:
            for i, j in zip(triangle_indices, np.roll(triangle_indices, -1)):
                vertex_edges[i].add(j)
                vertex_edges[j].add(i)

        # Identify vertices exceeding the max_edges limit
        excess_vertices = {v for v, edges in vertex_edges.items() if len(edges) > max_edges}

        if not excess_vertices:
            return mesh  # No changes needed

        # Remove triangles involving excess vertices
        new_triangles = []
        for triangle_indices in mesh['triangles']:
            if not any(v in excess_vertices for v in triangle_indices):
                new_triangles.append(triangle_indices)

        mesh['triangles'] = np.array(new_triangles)

        # Optionally, retriangulate locally to fill gaps (not shown here for simplicity)
        return mesh

    def mesh_area(self, window, progress, label, stop_event, max_area):
        # Read the pillar (hole) vertices
        holes = []
        hole_segments = []
        current_hole = []
        current_segments = []

        hole_files = []
        hole_plot_files = []        
        try:
            border_file = os.path.join(self.project_path, DATA_FOLDER_NAME, BORDER_VERTEX_FILE_NAME)
            pillar_file = os.path.join(self.project_path, DATA_FOLDER_NAME, PILLAR_VERTEX_FILE_NAME)

            # Read the border vertices
            border_vertices = self.read_vertices_from_file(border_file)

            with open(pillar_file, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if line.strip().startswith('P'):
                        if current_hole:
                            # Connect last segment to first for closed loop
                            current_segments.append([len(current_hole) - 1, 0])

                            holes.append(np.array(current_hole))
                            hole_segments.append(np.array(current_segments))
                            current_hole = []
                            current_segments = []
                    else:
                        parts = line.strip().split()
                        if len(parts) == 2:
                            x, y = map(float, parts)
                            current_hole.append([x, y])
                            if len(current_hole) > 1:
                                current_segments.append([len(current_hole) - 2, len(current_hole) - 1])
                if current_hole:
                    holes.append(np.array(current_hole))
                    hole_segments.append(np.array(current_segments))

            # Define segments for the border
            num_border_vertices = len(border_vertices)
            border_segments = np.array([[i, (i + 1) % num_border_vertices] for i in range(num_border_vertices)])

            # Combine all vertices and segments
            all_vertices = border_vertices.copy()
            all_segments = border_segments.copy()
            offset = len(border_vertices)

            for hole, segments in zip(holes, hole_segments):
                all_vertices = np.vstack([all_vertices, hole])
                segments = segments + offset
                all_segments = np.vstack([all_segments, segments])
                offset += len(hole)

            # Define the polygon dictionary
            polygon = {
                'vertices': all_vertices,
                'segments': all_segments
            }

            # Generate the mesh using the triangulate function with a max_area constraint
            mesh = triangle.triangulate(polygon, f"pqa{max_area}")
            mesh = self.enforce_edge_constraint(mesh)

            # Create Data directory if it doesn't exist
            mesh_dir = os.path.join(self.project_path, DATA_FOLDER_NAME, MESH_FOLDER_NAME)
            plot_dir = os.path.join(self.project_path, DATA_FOLDER_NAME, PLOT_FOLDER_NAME)

            if os.path.exists(mesh_dir):
                with os.scandir(mesh_dir) as entries:
                    for entry in entries:
                        if entry.is_file():
                            os.remove(entry.path)
            else:
                os.makedirs(mesh_dir)

            if os.path.exists(plot_dir):
                with os.scandir(plot_dir) as entries:
                    for entry in entries:
                        if entry.is_file():
                            os.remove(entry.path)
            else:
                os.makedirs(plot_dir)

            # Create text files for each hole
            hole_files = [open(os.path.join(mesh_dir, f"{PILLAR_OUTPUT_FILENAME_START}{i+1}.{ELEMENT_FILE_EXT}"), "a") for i in range(len(holes))]
            hole_plot_files = [open(os.path.join(plot_dir, f"{PILLAR_OUTPUT_FILENAME_START}{i+1}.{PLOT_FILE_EXT}"), "a") for i in range(len(holes))]
            mined_file = open(os.path.join(mesh_dir, f"{MINED_OUTPUT_FILENAME_START}1.{ELEMENT_FILE_EXT}"), "a")
            mined_plot_file = open(os.path.join(plot_dir, f"{MINED_OUTPUT_FILENAME_START}1.{PLOT_FILE_EXT}"), "a")
            hole_counter = [1] * (len(holes) + 1)
            m_counter = 1

            # Identify and fill triangles inside each hole with transparent red color
            i = 0
            self.triangles = len(mesh['triangles'])
            label["text"] = f"Meshing in progress... ({self.triangles} triangles)"
            print("Triangles: " + str(self.triangles))
            for triangle_indices in mesh['triangles']:
                if stop_event.is_set():
                    return

                i += 1
                # Get the triangle's vertices
                triangle_points = mesh['vertices'][triangle_indices]
                
                # Calculate the centroid of the triangle
                centroid = np.mean(triangle_points, axis=0)
                
                # Check if the centroid is inside any of the holes
                inside_hole = False
                for j, hole in enumerate(holes):
                    if self.is_point_in_polygon(centroid, hole):
                        inside_hole = True
                        el_name = f"{(j + 1):02}" + f"{hole_counter[j]:05}"
                        hole_counter[j] += 1
                        hole_files[j].write(
                            f"{PILLAR_TEXT.replace('XXXXXXX', el_name)}{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f} "
                            f"{triangle_points[1][0]:.4f} {triangle_points[1][1]:.4f} "
                            f"{triangle_points[2][0]:.4f} {triangle_points[2][1]:.4f}\n"
                        )

                        hole_plot_files[j].write(
                            f"{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f}\n"
                            f"{triangle_points[1][0]:.4f} {triangle_points[1][1]:.4f}\n"
                            f"{triangle_points[2][0]:.4f} {triangle_points[2][1]:.4f}\n"
                            f"{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f}\n\n"
                        )

                        break

                if not inside_hole:
                    el_name = "01" + f"{m_counter:05}"
                    m_counter += 1
                    mined_file.write(
                        f"{MINED_TEXT.replace('XXXXXXX', el_name)}{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f} "
                        f"{triangle_points[1][0]:.4f} {triangle_points[1][1]:.4f} "
                        f"{triangle_points[2][0]:.4f} {triangle_points[2][1]:.4f}\n"
                    )
                
                    mined_plot_file.write(
                        f"{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f}\n"
                        f"{triangle_points[1][0]:.4f} {triangle_points[1][1]:.4f}\n"
                        f"{triangle_points[2][0]:.4f} {triangle_points[2][1]:.4f}\n"
                        f"{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f}\n\n"
                    )   

                if(i % 100 == 0):
                    print(i, f"{i/self.triangles:.2%}")
                    progress['value'] = (i/self.triangles)*100  # Update progress bar
            
            for f in hole_files:
                f.close()
            for f in hole_plot_files:
                f.close()  

        except Exception as e:
            print(e)
            return
        
        finally:
            window.destroy()
            mined_file.close()
            mined_plot_file.close()
            for f in hole_files:
                f.close()
            for f in hole_plot_files:
                f.close()  
            
            print("Exited the mesh generator and closed all files")
        