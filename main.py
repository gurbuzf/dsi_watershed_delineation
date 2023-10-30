"""
Main script for processing hydrological data and delineating watersheds.
"""

# Add the parent directory of the current script to the system path
# to enable importing modules from that directory or its subdirectories.
from configuration import OUTLETS, WATERSHEDS, MODE, FLOW_ACCUMULATION, DRAINAGE_DIRECTION, PIXEL2SEARCH, RIVERS, RESULTS, MAX_STRAHLER, VERBOSE
from src.file_manager import check_config_file_validity, \
    create_results_directory
from src.polygonize import raster_to_polygon, \
    rasterize_array
from src.delineator import read_drainage_direction, \
    calculate_upstream_v2
from src.snap_pour_point import read_flow_accumulation_tif, \
    calculate_new_pour_point
from src.processing import read_outlets, \
    join_watersheds2points, \
    load_river_network, \
    clip_river_network, \
    insert_watershed_info, \
    process_watershed_points
import geopandas as gpd
import pandas as pd
import rasterio
import numpy as np
from datetime import datetime
import os
import sys

module_path = os.path.abspath(os.path.join('../'))

if module_path not in sys.path:
    sys.path.append(module_path)

# Import necessary modules and functions

# Add other necessary imports


def main():
    """
    Main function for processing hydrological data given the instructions in configuration.py.
    """
    check_config_file_validity()

    create_results_directory(RESULTS)

    points = read_outlets(OUTLETS)
    # points["status"] = None
    # points["comment"] = None

    if MODE == "single":

        accum, pixel_size = read_flow_accumulation_tif(FLOW_ACCUMULATION)

        drainage_direction, tif_profile, dr_dir_src = read_drainage_direction(
            DRAINAGE_DIRECTION)

        river_vector = load_river_network(RIVERS)

        points_new = process_watershed_points(points, accum, pixel_size, drainage_direction, dr_dir_src,
                                              tif_profile, river_vector, MAX_STRAHLER, RESULTS)
        points_new["change_rate[%]"] = 100 * \
            (points_new["CalculatedArea[km2]"] -
             points_new["area[km2]"]) / points_new["area[km2]"]

    elif MODE == "partial":
        points_labelled = join_watersheds2points(points, WATERSHEDS)

        unique_watershed_ids = points_labelled["Watershed_ID"].unique()

        points_new = pd.DataFrame()

        for watershed in unique_watershed_ids:
            print(
                f"Delineating the upstream area of the points in {watershed}...")

            filtered_points_labelled = points_labelled[points_labelled["Watershed_ID"] == watershed]

            accum, pixel_size = read_flow_accumulation_tif(
                os.path.join(FLOW_ACCUMULATION, watershed + '.tif'))

            drainage_direction, tif_profile, dr_dir_src = read_drainage_direction(
                os.path.join(DRAINAGE_DIRECTION, watershed + '.tif'))

            river_vector = load_river_network(
                os.path.join(RIVERS, watershed + '.geojson'))

            points_watershed = process_watershed_points(filtered_points_labelled, accum, pixel_size, drainage_direction, dr_dir_src,
                                                        tif_profile, river_vector, MAX_STRAHLER, RESULTS)

            points_new = pd.concat(
                [points_new, points_watershed], ignore_index=True)
        points_new["change_rate[%]"] = 100 * \
            (points_new["CalculatedArea[km2]"] -
             points_new["area[km2]"]) / points_new["area[km2]"]

    # Get current date and time
    date_time = datetime.now().strftime("%d%m%Y_%H%M")
    try:
        points_new.to_csv(os.path.join(
            RESULTS, f'report_{date_time}.csv'), encoding="windows-1254")
    except UnicodeEncodeError:
        points_new.to_csv(os.path.join(
            RESULTS, f'report_{date_time}.csv'), encoding="utf-8-sig")


if __name__ == "__main__":
    main()
