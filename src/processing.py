import pandas as pd
import geopandas as gpd
import fiona
import os
import csv
from src.snap_pour_point import calculate_new_pour_point
from src.delineator import calculate_upstream_v2
from src.polygonize import raster_to_polygon, rasterize_array
from src.utils import geopandas2KML
from configuration import OUTLETS,  PIXEL2SEARCH, VECTOR_EXTENSION


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
            f"Please add these columns to the DataFrame or update the column headers in {OUTLETS}.")
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
    # Load the river network data as a GeoDataFrame
    river_vector = gpd.read_file(path2rivernetwork)
    river_vector.crs = 'epsg:4326'
    return river_vector


def clip_river_network(
        river_network: gpd.GeoDataFrame,
        subbasin_polygon: gpd.GeoDataFrame,
        max_strahler_order: int,
        line_save_path: str = None):
    """
    Clips a river network GeoDataFrame using a subbasin polygon and optionally saves the clipped river network as a new GeoJSON file.

    Args:
        river_network (geopandas.GeoDataFrame): Input river network GeoDataFrame.
        subbasin_polygon (geopandas.GeoDataFrame): Subbasin polygon GeoDataFrame.
        max_strahler_order (int): Maximum strahler order for filtering.
        line_save_path (str, optional): Path to the output clipped river network GeoJSON file. Defaults to None.

    Returns:
        tuple: A tuple containing the clipped river network GeoDataFrame and feedback dictionary.
    """
    # Clip the river network to the subbasin polygon
    clipped_river_network = gpd.clip(river_network, subbasin_polygon)

    try:
        clipped_river_network = clipped_river_network[clipped_river_network["strahler"]
                                                      >= max_strahler_order]
    except KeyError:
        raise KeyError(
            "A column named 'strahler' is not found in river network attribute table! MAX_STRAHLER cannot be applied!")

    feedback = {
        "status": "success" if clipped_river_network.shape[0] > 0 else "fail",
        "message": "no rivers clipped within the given basin." if clipped_river_network.shape[0] == 0 else ""
    }

    # Save the clipped river network as a new GeoJSON file, if output_file is provided
    if line_save_path is not None:
        if not line_save_path.endswith(f'.{VECTOR_EXTENSION}'):
            line_save_path += f'.{VECTOR_EXTENSION}'
        if feedback["status"] == "success":

            if VECTOR_EXTENSION == "kml":
                geopandas2KML(clipped_river_network,
                              line_save_path, vector_type="linestring")

            elif VECTOR_EXTENSION == "geojson":
                clipped_river_network.to_file(line_save_path, driver="GeoJSON")
        else:
            pass

    return clipped_river_network, feedback


def insert_watershed_info(points_copy, row, new_pour_point, area, feedback):
    """
    Inserts watershed delineation information into the points table.

    Args:
        points_copy (pandas.DataFrame): DataFrame containing points information.
        row (pandas.Series): Row of the DataFrame for which information is to be inserted.
        new_pour_point (tuple): Coordinates of the new pour point in the format (x, y).
        area (float): Area in square kilometers.
        feedback (dict): Feedback dictionary containing status and message.

    Returns:
        pandas.DataFrame: Updated DataFrame with watershed information.

    """

    points_copy.loc[points_copy["id"] ==
                    row.id, "snap_long"] = new_pour_point[0]
    points_copy.loc[points_copy["id"] ==
                    row.id, "snap_lat"] = new_pour_point[1]
    points_copy.loc[points_copy["id"] == row.id, "CalculatedArea[km2]"] = area
    points_copy.loc[points_copy["id"] == row.id, "status"] = feedback["status"]
    points_copy.loc[points_copy["id"] ==
                    row.id, "comment"] = feedback["message"]

    return points_copy


def process_watershed_points(points, accum, drainage_direction, dr_dir_src,
                             tif_profile, river_vector, MAX_STRAHLER, RESULTS):
    """
    Process watershed points and update points_copy with watershed information.

    Args:
        points (pandas.DataFrame): DataFrame containing points information.
        accum: (numpy.ndarray): Array containing flow accumulation data.
        drainage_direction (numpy.ndarray): Array containing drainage direction data.
        dr_dir_src (rasterio.io.DatasetReader): ....
        tif_profile (rasterio.profiles.Profile): Profile of the TIFF file.
        river_vector (geopandas.GeoDataFrame): GeoDataFrame containing river network data.
        MAX_STRAHLER (int): Maximum Strahler order.
        RESULTS (str): Path to the directory for saving results.

    Returns:
        pandas.DataFrame: Updated DataFrame with watershed information.

    """
    points_copy = points.copy()
    # Extract the geotransform information and pixel sizes from the data.
    gt = dr_dir_src.transform
    pixelSizeX = gt[0]
    pixelSizeY = gt[4]
    pixel_size = (pixelSizeX, pixelSizeY)

    for index, row in points.iterrows():
        print(f"[+] Processing {row.id}.")

        # Calculate new pour point
        new_pour_point = calculate_new_pour_point(
            accum, pixel_size, (row.long, row.lat), PIXEL2SEARCH)
        new_pour_point_xy = dr_dir_src.index(
            new_pour_point[0], new_pour_point[1])

        # Extract watersheds
        upstream_area = calculate_upstream_v2(
            drainage_direction, new_pour_point_xy)
        rasterized_array = rasterize_array(upstream_area, tif_profile)

        # Save polygon and line as JSON
        subbasin = raster_to_polygon(rasterized_array, save_polygon=True,
                                     polygon_save_path=os.path.join(RESULTS, "watershed", str(row.id) + "_havza"))

        # Clip rivers
        clipped_river_network, feedback = clip_river_network(river_vector, subbasin,
                                                             max_strahler_order=MAX_STRAHLER,
                                                             line_save_path=os.path.join(RESULTS, "river", str(row.id) + "_akarsu"))

        # Insert watershed delineation information into the points table
        points_copy = insert_watershed_info(points_copy, row, new_pour_point,
                                            subbasin["CalculatedArea[km2]"][0], feedback)

    return points_copy
