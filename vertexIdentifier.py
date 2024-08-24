import numpy as np
import cv2
from tkinter import Tk, filedialog, simpledialog
from mesher import mesh_area
import os

# Function to find polygons based on the provided thresholds and epsilon factor
def find_polygons(image, canny_threshold1=50, canny_threshold2=150, epsilon_factor=0.01):
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
        polygons.append(approx)
    
    return polygons

# Callback function to update the image based on slider values
def update_image(*args):
    global image1, polygons
    epsilon_factor = cv2.getTrackbarPos('Epsilon', 'Polygons') / 100000.0

    image_copy = image1.copy()
    
    polygons = find_polygons(image_copy, epsilon_factor=epsilon_factor)
    num_polygons = len(polygons)
    num_vertices = sum(len(polygon) for polygon in polygons)

    for i, polygon in enumerate(polygons):
        avg_x = int(np.mean(polygon[:, 0, 0]))
        avg_y = int(np.mean(polygon[:, 0, 1]))
        for point in polygon:
            x, y = point[0]
            cv2.circle(image_copy, (x, y), 6, (19, 69, 139), -1)
        cv2.putText(image_copy, str(i + 1), (avg_x - 3, avg_y - 3), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
    
    # Display number of polygons and vertices identified
    cv2.putText(image_copy, f'Polygons: {num_polygons}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(image_copy, f'Vertices: {num_vertices}', (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Display tooltips
    cv2.putText(image_copy, 'Press "u" to Change Image', (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(image_copy, 'Press "p" to Save Pillars', (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(image_copy, 'Press "b" to Save Border', (30, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(image_copy, 'Press "m" to Mesh Image', (30, 230), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    cv2.imshow('Polygons', image_copy)

# Function to upload a new image
def upload_image():
    global image1
    Tk().withdraw()  
    file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if file_path:
        image1 = cv2.imread(file_path)
        update_image()

# Function to save polygons to a text file
def save_polygons(pillars=True):
    global polygons
    grid_max_x = simpledialog.askinteger("Input", "Enter max grid X:")
    grid_max_y = simpledialog.askinteger("Input", "Enter max grid Y:")
    
    if grid_max_x is None or grid_max_y is None:
        return 
    
    # Create Data directory if it doesn't exist
    if not os.path.exists("Data"):
        os.makedirs("Data")

    height, width = image1.shape[:2]
    
    if pillars:
        with open("Data/pillars.txt", "w") as f:
            for i, polygon in enumerate(polygons):
                f.write(f"P{i+1}\n")
                for point in polygon:
                    x, y = point[0]
                    actual_x = (x / width) * grid_max_x
                    actual_y = grid_max_y - (y / height) * grid_max_y
                    f.write(f"{actual_x:.4f} {actual_y:.4f}\n")
    else:
        with open("Data/border.txt", "w") as f:
            for i, polygon in enumerate(polygons):
                f.write(f"M{i+1}\n")
                for point in polygon:
                    x, y = point[0]
                    actual_x = (x / width) * grid_max_x
                    actual_y = grid_max_y - (y / height) * grid_max_y
                    f.write(f"{actual_x:.4f} {actual_y:.4f}\n")

# Load the initial image
image1 = cv2.imread("Example/layout.png")

# Create a window to display the results
cv2.namedWindow('Polygons', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Polygons', 1920, 1080)

# Create trackbars (sliders)
cv2.createTrackbar('Epsilon', 'Polygons', 100, 1000, update_image)

while True:
    key = cv2.waitKey(1)
    
    if cv2.getWindowProperty('Polygons', cv2.WND_PROP_VISIBLE) < 1:
        cv2.destroyAllWindows()
        break
        
    if key == ord('u'):
        upload_image()
    elif key == ord('p'):
        save_polygons(pillars=True)
    elif key == ord('b'):
        save_polygons(pillars=False)
    elif key == ord('m'):
        max_area = simpledialog.askfloat("Input", "Enter triangle max area:", initialvalue=0.5)
        if max_area is not None:
            mesh_area(max_area)
