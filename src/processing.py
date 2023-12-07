import os
import csv
import warnings

import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio

from src.snap_pour_point import calculate_new_pour_point
from src.delineator import calculate_upstream_arcgis, calculate_upstream_grass
from src.polygonize import raster_to_polygon, rasterize_array
from src.utils import geopandas2KML


def read_outlets(path):
    """
    Checks if all column names in df are valid.

    Args:
        df: The Pandas DataFrame.
    Returns:
        None if all column names are in col_headers, an error otherwise.
    """
    with open(path, "rb") as f:
        _first_row = f.readlines(1)
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(_first_row[0].decode("utf-8"))
    except UnicodeDecodeError:
        dialect = sniffer.sniff(_first_row[0].decode("windows-1254"))

    try:
        points = pd.read_csv(path, encoding="utf-8-sig", sep=dialect.delimiter)
    except UnicodeDecodeError:
        points = pd.read_csv(path, encoding="windows-1254",
                             sep=dialect.delimiter)

    points.columns = [col.strip() for col in points.columns]

    col_headers = ['id', 'name', 'long', 'lat', 'area[km2]']
    missing_cols = [col for col in col_headers if col not in points.columns]

    if missing_cols:
        raise ValueError(
            f"The following columns are missing from the DataFrame: {missing_cols}. "
            f"Please add these columns to the DataFrame or update the column headers in {path}.")
    else:
        return gpd.GeoDataFrame(points, geometry=gpd.points_from_xy(points.long, points.lat), crs="EPSG:4326")


def join_watersheds2points(points, path2watershed):
    """
    Joins watershed information to points based on spatial relationship and returns the resulting GeoPandas DataFrame.

    Args:
        points (geopandas.GeoDataFrame): GeoPandas DataFrame containing the points.
        path2watershed (str): Path to the watershed GeoJSON file.

    Returns:
        pandas.DataFrame: DataFrame with the joined watershed information. Columns ['geometry', 'index_right', 'OBJECTID', 'Havza_Adı', 'Havza_Alan']
        are removed.

    """

    # Read watershed polygons from GeoJSON file
    watersheds = gpd.read_file(path2watershed)

    # Perform left join between points and watersheds
    joined = gpd.sjoin(points, watersheds, how='left', predicate='within')

    # Remove unnecessary columns
    columns_to_remove = ['geometry']
    joined.drop(columns=columns_to_remove, inplace=True)

    # Return the final pandas object
    return joined


def load_river_network(path2rivernetwork):
    """
    Loads a river network GeoDataFrame for a specific watershed.

    Args:
        path2rivernetwork (str): Path to the directory containing river network data.

    Returns:
        geopandas.GeoDataFrame: River network GeoDataFrame for the specified watershed.

    Notes:
        - The river network data is expected to be in GeoJSON format.
        - The function uses geopandas library to read the GeoJSON file.
        - The river network GeoDataFrame contains information about the river network's geometry, 
          attributes, and other spatial properties.
        - The path2rivernetwork should point to the directory containing the river network data file.
    """
    if path2rivernetwork in ['', None, False]:
        return None
    else:
        # Load the river network data as a GeoDataFrame
        river_vector = gpd.read_file(path2rivernetwork)
        river_vector.crs = 'epsg:4326'
        return river_vector


def clip_river_network(river_network, subbasin_polygon, min_strahler_order, line_save_path=None, file_extension=None):
    """
    Clips a GeoDataFrame representing a river network using a subbasin polygon and optionally saves the clipped river network as a new GeoJSON or KML file.

    Args:
        river_network (geopandas.GeoDataFrame): Input GeoDataFrame representing the river network.
        subbasin_polygon (geopandas.GeoDataFrame): GeoDataFrame representing the subbasin polygon.
        min_strahler_order (int): Minimum Strahler order for filtering the river network.
        line_save_path (str, optional): Path to save the clipped river network file. Defaults to None.
        file_extension (str, optional): File extension for saving the clipped river network file ('geojson', 'kml'). Defaults to None.

    Returns:
        tuple: A tuple containing the clipped GeoDataFrame representing the river network and a feedback dictionary.

    Warns:
        UserWarning: If the 'strahler' column is not found in the river network attribute table, a warning is issued, and MIN_STRAHLER cannot be applied.

    Notes:
        - The function clips the river network to the provided subbasin polygon and filters by the minimum Strahler order.
        - The clipped river network can be optionally saved as a GeoJSON or KML file.

    Example:
        # Clip river network and save as GeoJSON
        clipped_river, feedback = clip_river_network(river_network, subbasin_polygon, min_strahler_order=3,
                                                     line_save_path="path/to/clipped_river", file_extension="geojson")
    """
    # Clip the river network to the subbasin polygon
    clipped_river_network = gpd.clip(river_network, subbasin_polygon)

    if 'strahler' in clipped_river_network:
        # Filter the clipped river network by minimum Strahler order
        clipped_river_network = clipped_river_network[clipped_river_network["strahler"]
                                                      >= min_strahler_order]
    else:
        warnings.warn(
            "The 'strahler' column is not found in river_network data. MIN_STRAHLER cannot be applied!", UserWarning)

    feedback = {
        "river_status": "No rivers clipped within the given basin." if clipped_river_network.shape[0] == 0 else ""
    }

    # Save the clipped river network as a new GeoJSON or KML file, if line_save_path is provided

    if line_save_path is not None:
        if not line_save_path.endswith(f'.{file_extension}'):
            line_save_path += f'.{file_extension}'

        if file_extension == "kml":
            geopandas2KML(clipped_river_network,
                          line_save_path, vector_type="linestring")
        elif file_extension == "geojson":
            clipped_river_network.to_file(line_save_path, driver="GeoJSON")

    return clipped_river_network, feedback


def insert_watershed_info(points_copy, row, new_pour_point, area, feedback):
    """
    Inserts watershed delineation information into the points table.

    Args:
        points_copy (pandas.DataFrame): DataFrame containing points information.
        row (pandas.Series): Row of the DataFrame for which information is to be inserted.
        new_pour_point (tuple): Coordinates of the new pour point in the format (x, y).
        area (float): Area in square kilometers.
        feedback (dict): Feedback dictionary containing river_status.

    Returns:
        pandas.DataFrame: Updated DataFrame with watershed information.

    """

    points_copy.loc[points_copy["id"] ==
                    row.id, "snap_long"] = new_pour_point[0]
    points_copy.loc[points_copy["id"] ==
                    row.id, "snap_lat"] = new_pour_point[1]
    points_copy.loc[points_copy["id"] == row.id, "CalculatedArea[km2]"] = area
    points_copy.loc[points_copy["id"] ==
                    row.id, "river_status"] = feedback["river_status"]

    return points_copy


def process_watershed_points(points: pd.DataFrame,
                             accum: np.ndarray,
                             drainage_direction: np.ndarray,
                             direction_type: str,
                             dr_dir_src: rasterio.io.DatasetReader,
                             tif_profile: rasterio.profiles.Profile,
                             river_vector: gpd.GeoDataFrame,
                             results_path: str,
                             vector_extension: str,
                             verbose: bool = False,
                             n_neighbour: int = 1,
                             min_strahler_order: int = 1) -> pd.DataFrame:
    """
    Process watershed points and update points_copy with watershed information.

    Args:
        points (pd.DataFrame): DataFrame containing points information.
        accum (np.ndarray): Array containing flow accumulation data.
        drainage_direction (np.ndarray): Array containing drainage direction data.
        direction_type (str): Type of drainage direction calculation ('arcgis' or 'grass').
        dr_dir_src (rasterio.io.DatasetReader): DatasetReader object for the drainage direction data.
        tif_profile (rasterio.profiles.Profile): Profile of the TIFF file.
        river_vector (gpd.GeoDataFrame): GeoDataFrame containing river network data.
        results_path (str): Path to the directory where results will be saved.
        vector_extension (str): File extension for saving vector files (e.g., 'geojson', 'kml').
        verbose (bool): If True, print information about the processing. Defaults to False.
        n_neighbour (int): Number of neighboring cells to consider when recalculating coordinates based on flow accumulation.
        min_strahler_order (int, optional): Minimum Strahler order for river network filtering. Defaults to 1.

    Returns:
        pd.DataFrame: Updated DataFrame with watershed information.
    """

    # Define the appropriate calculate_upstream function based on direction_type
    if direction_type == 'arcgis':
        calculate_upstream = calculate_upstream_arcgis
    elif direction_type == 'grass':
        calculate_upstream = calculate_upstream_grass

    # Create a copy of the points DataFrame
    points_copy = points.copy()

    # Extract pixel size information from the drainage direction data
    pixelSizeX, pixelSizeY = dr_dir_src.transform[0], dr_dir_src.transform[4]
    pixel_size = (pixelSizeX, pixelSizeY)

    for _, row in points.iterrows():
        if verbose:
            print(f"[+] Processing point {row.id}.")

        # Recalculate coordinates based on flow accumulation
        if accum is None:
            new_pour_point = (row.long, row.lat)
            new_pour_point_xy = dr_dir_src.index(
                new_pour_point[0], new_pour_point[1])
            if verbose:
                print("No changes has been made in pour point XY:",
                      new_pour_point_xy)
        else:
            new_pour_point = calculate_new_pour_point(
                accum, pixel_size, (row.long, row.lat), n_neighbour, verbose)
            new_pour_point_xy = dr_dir_src.index(
                new_pour_point[0], new_pour_point[1])
            if verbose:
                print("New pour point XY:", new_pour_point_xy)

        # Extract watersheds
        upstream_area = calculate_upstream(
            drainage_direction, new_pour_point_xy)
        rasterized_array = rasterize_array(upstream_area, tif_profile)

        # Save watershed polygon and river network as JSON
        subbasin = raster_to_polygon(rasterized_array, save_polygon=True,
                                     polygon_save_path=os.path.join(
                                         results_path, "watershed", f"{row.id}_catchment"),
                                     file_extension=vector_extension)
        if river_vector is not None:
            # Clip rivers
            clipped_river_network, feedback = clip_river_network(river_vector, subbasin,
                                                                 min_strahler_order=min_strahler_order,
                                                                 line_save_path=os.path.join(
                                                                     results_path, "river", f"{row.id}_river"),
                                                                 file_extension=vector_extension)
        else:
            feedback = {
                "river_status": "-"
            }
        # Insert watershed delineation information into the points table
        points_copy = insert_watershed_info(points_copy, row, new_pour_point,
                                            subbasin["CalculatedArea[km2]"][0], feedback)

    return points_copy
