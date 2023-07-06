import rasterio 
import numpy as np
from numba import njit

def read_drainage_direction(drainage_direction_path, pour_point_coord):
    """
    Reads the drainage direction data from a TIFF file.

    Parameters:
        drainage_direction_path (str): File path of the drainage direction TIFF.
        pour_point_coord (tuple): Coordinates of the pour point in the format (x, y).

    Returns:
        tuple: A tuple containing the drainage direction data as a NumPy array,
               the pour point coordinates in the TIFF, and the metadata profile of the TIFF.

    Notes:
        - The function uses the rasterio library to read the TIFF file.
        - The drainage direction data is typically represented as an array where each
          cell represents the direction of flow.
        - The pour point coordinates are used to locate the specific cell in the TIFF.
        - The metadata profile contains information about the TIFF such as its spatial
          reference system, resolution, and other properties.

    """

    with rasterio.open(drainage_direction_path) as src:
        drainage_direction = src.read(1)
        pour_point_xy = src.index(pour_point_coord[0], pour_point_coord[1])
        profile = src.profile

    return drainage_direction, pour_point_xy, profile

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