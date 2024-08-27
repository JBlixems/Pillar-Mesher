import triangle
import matplotlib.pyplot as plt
import numpy as np
import os

# Function to read vertices from a file
def read_vertices_from_file(filename):
    vertices = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.strip().startswith('M') or line.strip().startswith('P'):
                continue
            parts = line.strip().split()
            if len(parts) == 2:
                x, y = map(float, parts)
                vertices.append([x, y])
    return np.array(vertices)

# Function to check if a point is inside a given polygon
def is_point_in_polygon(point, polygon):
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

def mesh_area(max_area):
    # Read the border vertices
    border_vertices = read_vertices_from_file('Data/border.txt')

    # Read the pillar (hole) vertices
    holes = []
    hole_segments = []
    current_hole = []
    current_segments = []

    with open('Data/pillars.txt', 'r') as file:
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
    mesh = triangle.triangulate(polygon, 'pqa{}'.format(max_area))

    # Plot the mesh
    plt.figure()

    # Plot all triangles with default color (black)
    plt.triplot(
        mesh['vertices'][:, 0], mesh['vertices'][:, 1], mesh['triangles'], color='black'
    )

    # Create Data directory if it doesn't exist
    mesh_dir = "Data/Mesh"

    if os.path.exists(mesh_dir):
        with os.scandir(mesh_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    os.remove(entry.path)
    else:
        os.makedirs(mesh_dir)

    # Create text files for each hole
    hole_files = [open(f"Data/Mesh/P{i+1}.txt", "a") for i in range(len(holes))]

    # Identify and fill triangles inside each hole with transparent red color
    i = 0
    print("Triangles: " + str(len(mesh['triangles'])))
    for triangle_indices in mesh['triangles']:
        if(i % 1000 == 0):
            print(i)

        i += 1
        # Get the triangle's vertices
        triangle_points = mesh['vertices'][triangle_indices]
        
        # Calculate the centroid of the triangle
        centroid = np.mean(triangle_points, axis=0)
        
       # Check if the centroid is inside any of the holes
        inside_hole = False
        for j, hole in enumerate(holes):
            if is_point_in_polygon(centroid, hole):
                inside_hole = True
                hole_files[j].write(
                    f"{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f} "
                    f"{triangle_points[1][0]:.4f} {triangle_points[1][1]:.4f} "
                    f"{triangle_points[2][0]:.4f} {triangle_points[2][1]:.4f}\n"
                )
                plt.fill(triangle_points[:, 0], triangle_points[:, 1], color='red', alpha=0.5)
                break

        if not inside_hole:
            with open("Data/Mesh/M1.txt", "a") as f:
                f.write(
                    f"{triangle_points[0][0]:.4f} {triangle_points[0][1]:.4f} "
                    f"{triangle_points[1][0]:.4f} {triangle_points[1][1]:.4f} "
                    f"{triangle_points[2][0]:.4f} {triangle_points[2][1]:.4f}\n"
                )

    plt.gca().set_aspect('equal')
    plt.ion()
    plt.show(block=True)
