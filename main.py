"""
Main script for processing hydrological data and delineating watersheds.
"""

# Importing necessary libraries
import geopandas as gpd
import pandas as pd
import rasterio
import numpy as np
from datetime import datetime
import os
import sys

# Adding the parent directory of the current script to the system path
# to enable importing modules from that directory or its subdirectories.
module_path = os.path.abspath(os.path.join('../'))
if module_path not in sys.path:
    sys.path.append(module_path)

# Importing functions from custom modules
from configuration import OUTLETS, WATERSHEDS, MODE, FLOW_ACCUMULATION, DRAINAGE_DIRECTION, PIXEL2SEARCH, RIVERS, RESULTS, MAX_STRAHLER, VERBOSE
from src.file_manager import check_config_file_validity, create_results_directory
from src.delineator import read_drainage_direction
from src.snap_pour_point import read_flow_accumulation_tif
from src.processing import read_outlets, join_watersheds2points, load_river_network, process_watershed_points


def main():
    """
    Main function for processing hydrological data given the instructions in configuration.py.
    """
    check_config_file_validity()  # Check if the configuration file is valid

    create_results_directory(RESULTS)  # Create the results directory if it doesn't exist

    points = read_outlets(OUTLETS)  # Read outlet points from the specified file

    if MODE == "single":  # If processing mode is 'single'
        accum, pixel_size = read_flow_accumulation_tif(FLOW_ACCUMULATION)  # Read flow accumulation data

        # Read drainage direction data
        drainage_direction, tif_profile, dr_dir_src = read_drainage_direction(DRAINAGE_DIRECTION)

        river_vector = load_river_network(RIVERS)  # Load river network data

        # Process the watershed points
        points_new = process_watershed_points(points, accum, pixel_size, drainage_direction, dr_dir_src,
                                              tif_profile, river_vector, MAX_STRAHLER, RESULTS)
        
        # Calculate and add change rate to the DataFrame
        points_new["change_rate[%]"] = 100 * \
            (points_new["CalculatedArea[km2]"] -
             points_new["area[km2]"]) / points_new["area[km2]"]

    elif MODE == "partial":  # If processing mode is 'partial'
        points_labelled = join_watersheds2points(points, WATERSHEDS)  # Join watersheds to points

        unique_watershed_ids = points_labelled["Watershed_ID"].unique()  # Get unique watershed IDs

        points_new = pd.DataFrame()

        for watershed in unique_watershed_ids:
            print(
                f"Delineating the upstream area of the points in {watershed}...")

            filtered_points_labelled = points_labelled[points_labelled["Watershed_ID"] == watershed]

            accum = read_flow_accumulation_tif(
                os.path.join(FLOW_ACCUMULATION, watershed + '.tif'))  # Read flow accumulation data

            drainage_direction, tif_profile, dr_dir_src = read_drainage_direction(
                os.path.join(DRAINAGE_DIRECTION, watershed + '.tif'))  # Read drainage direction data

            river_vector = load_river_network(
                os.path.join(RIVERS, watershed + '.geojson'))  # Load river network data

            points_watershed = process_watershed_points(filtered_points_labelled, accum, drainage_direction, dr_dir_src,
                                                        tif_profile, river_vector, MAX_STRAHLER, RESULTS)  # Process watershed points

            points_new = pd.concat(
                [points_new, points_watershed], ignore_index=True)  # Concatenate DataFrames for different watersheds
        
        # Calculate and add change rate to the DataFrame
        points_new["change_rate[%]"] = 100 * (points_new["CalculatedArea[km2]"] - points_new["area[km2]"]) / points_new["area[km2]"]

    # Get current date and time
    date_time = datetime.now().strftime("%d%m%Y_%H%M")
    # try:
    points_new.to_csv(os.path.join(
        RESULTS, f'report_{date_time}.csv'), encoding="utf-8-sig")  # Save the results to a CSV file
    # except UnicodeEncodeError:
    #     points_new.to_csv(os.path.join(
    #         RESULTS, f'report_{date_time}.csv'), encoding="utf-8-sig")  # Handle encoding error


if __name__ == "__main__":
    main()  # Call the main function if the script is run directly
