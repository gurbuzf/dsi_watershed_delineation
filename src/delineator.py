
import numpy as np
import rasterio
from numba import njit
import pandas as pd
import geopandas as gpd

import rasterio

import rasterio

def read_drainage_direction(drainage_direction_path):
    """
    Read drainage direction data from a TIFF file.

    Args:
        drainage_direction_path (str): File path of the drainage direction TIFF.

    Returns:
        tuple: A tuple containing the drainage direction data as a NumPy array, the TIFF profile, and the rasterio dataset object.

    Raises:
        FileNotFoundError: If the TIFF file is not found or cannot be opened.
        ValueError: If the TIFF file does not contain the expected drainage direction data.

    Notes:
        - The function uses the rasterio library to read the TIFF file.
        - The drainage direction data is typically represented as a 2D array where each cell represents the direction of flow.
        - The function reads the first band of the TIFF file (band index 1) to extract the drainage direction data.
        - The rasterio dataset object (rasterio.io.DatasetReader) is also returned to allow further manipulation of the data if needed.

    Example:
        # Read drainage direction data from a TIFF file
        drainage_direction_path = "path/to/drainage_direction.tif"
        drainage_direction, tiff_profile, dr_dir_source = read_drainage_direction(drainage_direction_path)

        # Perform further operations with the drainage_direction data, tiff_profile, or the dr_dir_source object

    """
    try:
        with rasterio.open(drainage_direction_path) as src:
            # Check if the dataset has exactly one band
            if src.count != 1:
                raise ValueError("The TIFF file should have exactly one band containing the drainage direction data.")
            
            drainage_direction = src.read(1)

            tiff_profile = src.profile
            return drainage_direction, tiff_profile, src
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{drainage_direction_path}' is not found or cannot be opened.")
    except rasterio.RasterioIOError:
        raise ValueError(f"The file '{drainage_direction_path}' does not contain the expected drainage direction data.")




def calculate_upstream_v1(drainage_direction, pour_point_coords):
    """
    Calculate the upstream area based on the given drainage direction and pour point coordinates.

    Parameters:
    - drainage_direction: numpy.ndarray
        A 2D array representing the drainage direction. Each pixel indicates the direction in which water flows.
    - pour_point_coords: tuple (row, column)
        The row and column indices of the pour point, which is the starting point for calculating the upstream area.

    Returns:
    - upstream_area: numpy.ndarray
        A boolean array indicating the pixels that belong to the upstream area.

    The function uses a recursive algorithm to traverse upstream from the pour point, following the drainage direction.
    It marks the pixels that contribute flow to the pour point as part of the upstream area.

    Note:
    - The drainage direction values should follow the D8 convention (values 1 to 8 representing the eight directions).
    - The pour point coordinates should be within the boundaries of the drainage direction array.
    """

    # Create an empty array with the same shape as the drainage direction
    upstream_area = np.zeros_like(drainage_direction, dtype=bool)

    # Get the row and column indices of the pour point
    row, col = pour_point_coords

    # Define the D8 offsets for the eight directions
    offsets = [(0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1)]

    # Recursive function to calculate upstream area
    def traverse_upstream(r, c):
        # Check if the current pixel is within the boundaries of the array
        if r < 0 or r >= drainage_direction.shape[0] or c < 0 or c >= drainage_direction.shape[1]:
            return

        # Check if the current pixel is already marked as part of the upstream area
        if upstream_area[r, c]:
            return

        # Mark the current pixel as part of the upstream area
        upstream_area[r, c] = True

        # Iterate over the eight directions
        for direction in range(8):
            # Get the offset for the corresponding direction
            offset = offsets[direction]

            # Move to the next pixel based on the offset
            next_r = r + offset[0]
            next_c = c + offset[1]

            # Check if the next pixel drains into the current pixel
            if next_r >= 0 and next_r < drainage_direction.shape[0] and next_c >= 0 and next_c < drainage_direction.shape[1]:
                if (drainage_direction[next_r, next_c] - 1) % 8 == (7 + direction - 4) % 8:
                    # Recursively traverse upstream from the next pixel
                    traverse_upstream(next_r, next_c)

    # Start traversing upstream from the pour point
    traverse_upstream(row, col)

    return upstream_area.astype(int)

@njit
def calculate_upstream_v2(drainage_direction, pour_point_coords):
    """
    Calculate the upstream area based on the given drainage direction and pour point coordinates.

    Parameters:
    - drainage_direction: numpy.ndarray
        A 2D array representing the drainage direction. Each pixel indicates the direction in which water flows.
    - pour_point_coords: tuple (row, column)
        The row and column indices of the pour point, which is the starting point fo r calculating the upstream area.

    Returns:
    - upstream_area: numpy.ndarray
        A binary array indicating the pixels that belong to the upstream area (1 for upstream, 0 for other pixels).

    The function uses a stack-based iterative algorithm to traverse upstream from the pour point, following the
    drainage direction. It marks the pixels that contribute flow to the pour point as part of the upstream area.

    Note:
    - The drainage direction values should follow the D8 convention (values 1 to 8 representing the eight directions).
    - The pour point coordinates should be within the boundaries of the drainage direction array.
    - The function utilizes the `numba` library's `njit` decorator for improved performance.
    """

    # Create an empty array with the same shape as the drainage direction
    upstream_area = np.zeros_like(drainage_direction, dtype=np.int8)

    # Get the row and column indices of the pour point
    row, col = pour_point_coords

    # Define the D8 offsets for the eight directions
    offsets = [(0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1)]

    # Create a stack to store the pixel coordinates
    stack = [(row, col)]

    # Mark the pour point as part of the upstream area
    upstream_area[row, col] = 1

    # Iterate until the stack is empty
    while stack:
        r, c = stack.pop()

        # Iterate over the eight directions
        for direction in range(8):
            offset = offsets[direction]
            next_r = r + offset[0]
            next_c = c + offset[1]

            # Check if the next pixel is within the array boundaries
            if 0 <= next_r < drainage_direction.shape[0] and 0 <= next_c < drainage_direction.shape[1]:
                # Check if the next pixel drains into the current pixel

                if (drainage_direction[next_r, next_c] - 1) % 8 == (7 + direction - 4) % 8:
                    # Mark the next pixel as part of the upstream area
                    upstream_area[next_r, next_c] = 1
                    stack.append((next_r, next_c))

    return upstream_area