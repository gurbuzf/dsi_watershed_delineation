import pandas as pd
import geopandas as gpd
import os
from run_config import OUTLETS


def read_outlets(path):
    """
    Checks if all column names in df are valid.

    Args:
        df: The Pandas DataFrame.
    Returns:
        None if all column names are in col_headers, an error otherwise.
    """
    points = pd.read_csv(path, sep='\t')
    col_headers = ['id', 'name', 'long', 'lat', 'area[km2]']
    missing_cols = []
    for col in points.columns:
        if col not in col_headers:
            missing_cols.append(col)

    if missing_cols:
        raise ValueError(
            f"The following columns are missing from the DataFrame: {missing_cols}. "
            f"Please add these columns to the DataFrame or update the column headers in {OUTLETS}.")
    else:
        return gpd.GeoDataFrame(points, geometry=gpd.points_from_xy(points.long, points.lat), crs = "EPSG:4326")
    
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

    return river_vector


def clip_river_network(river_network, subbasin_polygon, max_strahler_order, line_save_path=None):
    """
    Clips a river network GeoDataFrame using a subbasin polygon and optionally saves the clipped river network as a new GeoJSON file.

    Args:
        river_network (geopandas.GeoDataFrame): Input river network GeoDataFrame.
        subbasin_polygon (geopandas.GeoDataFrame): Subbasin polygon GeoDataFrame.
        line_save_path (str, optional): Path to the output clipped river network GeoJSON file. Defaults to None.

    Returns:
        geopandas.GeoDataFrame: Clipped river network as a GeoDataFrame.

    """
    # Clip the river network to the subbasin polygon
    clipped_river_network = gpd.clip(river_network, subbasin_polygon)
    try:
        clipped_river_network = clipped_river_network[clipped_river_network["strahler"]>=max_strahler_order]
    except KeyError:
        print("A column named 'strahler' is not found in river network attribute table! MAX_STRAHLER cannot be applied!")
        pass    
    # Save the clipped river network as a new GeoJSON file, if output_file is provided
    if line_save_path is not None:
        if not line_save_path.endswith('.geojson'):
                line_save_path += '.geojson'
        clipped_river_network.to_file(line_save_path, driver='GeoJSON')
    
    return clipped_river_network