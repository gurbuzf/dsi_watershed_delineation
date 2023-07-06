import rasterio
import numpy as np
from src.utils import haversine_distance

VERBOSE = True

def read_flow_accumulation_tif(path_flow_acc):
    """
    Reads flow accumulation data from a TIFF file and returns the data object and pixel size.

    Args:
        path_flow_acc (str): The file path for the flow accumulation data.

    Returns:
        tuple: A tuple containing the data object and pixel size (pixelSizeX, pixelSizeY).
    """
    # Verbose mode: Print the information about reading flow accumulation data.
    if VERBOSE:
        print(f"[+] Reading flow accumulation data at {path_flow_acc}...")

    try:
        data = rasterio.open(path_flow_acc)
    except FileNotFoundError:
        print(f'{path_flow_acc} is not found!\nPlease check the file path for the flow accumulation data.')

    # Get the number of rows and columns in the data and the coordinate reference system (CRS).
    rows, cols = data.shape
    crs = data.crs

    # Extract the geotransform information and pixel sizes from the data.
    gt = data.transform
    pixelSizeX = gt[0]
    pixelSizeY = gt[4]

    # Verbose mode: Print the flow accumulation data description.
    if VERBOSE:
        print(f"Flow Accumulation Data Description:\nPixel Size: ({pixelSizeX}, {pixelSizeY})\n"
              f"# of pixel in (row, col): ({rows}, {cols})\n"
              f"CRS: {crs}")

    return data, (pixelSizeX, pixelSizeY)


def resample_matrix(central_coord, n):
    """
    Creates a matrix with coordinates (row, col) based on a central point and a search-for range.

    Args:
        central_coord (list or tuple): The central point represented as a list or tuple [x, y].

        n (int): The range from the central point in number of pixel (inclusive).

    Returns:
        list: The generated matrix of coordinates.
    """
    x, y = central_coord
    matrix_row_col = [[x+i, y+j] for j in range(-n, n+1) for i in range(-n, n+1)]
    matrix_row_col = np.array(matrix_row_col)
    rows = matrix_row_col[:, 0]
    cols = matrix_row_col[:, 1]
    return rows, cols

def calculate_new_pour_point(data, pixel_size, coord, n_neighbour=1):
    """
    Processes flow accumulation data to identify the new coordinates of the pixel neighboring the 
    point located at coord. Returns the coordinate of the pixel with the highest flow accumulation.  

    Args:
        data (object): Object of flow accumulation [tif] raster data.
        pixel_size (tuple): The size of the pixel in the X and Y directions.   
        coord (tuple): The coordinate of the original pour point in the form of (X, Y).
        n_neighbour (int, optional): Number of neighboring pixels to consider. Defaults to 1.

    Returns:
        tuple: The pour point coordinates (x, y) in degrees.
    """
    # Read the flow accumulation data into a matrix
    data_matrix = data.read(1)

    # Convert the coordinate to row and column indices
    row, col = data.index(coord[0], coord[1])

    # Create a list with the central pixel row and column indices
    central_list = [row, col]

    # Resample the matrix to get the row and column indices of neighboring pixels
    search_rows, search_cols = resample_matrix(central_list, n_neighbour)

    # Get the flow accumulation values of the neighboring pixels
    temp = data_matrix[search_rows, search_cols]

    # Find the index of the pixel with the highest flow accumulation
    ind = temp.argmax()

    # Get the row and column indices of the pour point pixel
    pour_point_rc = (search_rows[ind], search_cols[ind])

    # Calculate the X and Y coordinates of the pour point pixel
    x = data.bounds.left + pixel_size[0] * pour_point_rc[1] + pixel_size[0] / 2
    y = data.bounds.top + pixel_size[1] * pour_point_rc[0] + pixel_size[1] / 2

    # Create a tuple with the snapped pour point coordinates
    snapped_pour_point_xy = (x, y)

    if VERBOSE:
        # Calculate the difference between the original coordinate and the snapped point in degrees
        dx = abs(coord[0] - x)
        dy = abs(coord[1] - y)
        snap_difference = (dx**2 + dy**2)**0.5 
        print(f"Snapped Point distance to original location (in degrees): {snap_difference}")
        
        # Calculate the distance between the snapped point and the original location in meters
        distance = haversine_distance(coord[1], coord[0], y, x)
        print(f"Snapped Point distance to original location (in meters): {distance}")

    return snapped_pour_point_xy
