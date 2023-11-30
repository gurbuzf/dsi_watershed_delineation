"""
Main script for processing hydrological data and delineating watersheds.
"""
import os
from datetime import datetime

import pandas as pd

# Importing necessary libraries
from src.processing import read_outlets, join_watersheds2points, load_river_network, process_watershed_points
from src.snap_pour_point import read_flow_accumulation_tif
from src.delineator import read_drainage_direction
from src.file_manager import read_config, check_config_file_validity, create_results_directory


def delineate_upstream(config_file_path):
    """
    Main function for processing hydrological data given the instructions in configuration.py.
    """
    check_config_file_validity(config_file_path)  # Check if the configuration file is valid
    config = read_config(config_file_path)
    MODE = config.get('MODE')
    OUTLETS = config.get('OUTLETS')
    WATERSHEDS = config.get('WATERSHEDS')
    RIVERS = config.get('RIVERS')
    FLOW_ACCUMULATION = config.get('FLOW_ACCUMULATION')
    DRAINAGE_DIRECTION = config.get('DRAINAGE_DIRECTION')
    DRAINAGE_DIRECTION_TYPE = config.get('DRAINAGE_DIRECTION_TYPE')
    VERBOSE = bool(eval(config.get('VERBOSE')))
    PIXEL2SEARCH = int(config.get('PIXEL2SEARCH'))
    RESULTS = config.get('RESULTS')
    MIN_STRAHLER = int(config.get('MIN_STRAHLER'))
    VECTOR_EXTENSION = config.get('VECTOR_EXTENSION')

    # Create the results directory if it doesn't exist
    create_results_directory(RESULTS, verbose=VERBOSE)

    # Read outlet points from the specified file
    points = read_outlets(OUTLETS)

    if MODE == "single":  # If processing mode is 'single'
        # Read flow accumulation data
        accum = read_flow_accumulation_tif(FLOW_ACCUMULATION, verbose=VERBOSE)

        # Read drainage direction data
        drainage_direction, tif_profile, dr_dir_src = read_drainage_direction(
            DRAINAGE_DIRECTION, verbose=VERBOSE)

        river_vector = load_river_network(RIVERS)  # Load river network data

        # Process the watershed points
        points_new = process_watershed_points(points,
                                              accum,
                                              drainage_direction,
                                              DRAINAGE_DIRECTION_TYPE,
                                              dr_dir_src,
                                              tif_profile,
                                              river_vector,
                                              results_path=RESULTS,
                                              vector_extension=VECTOR_EXTENSION,
                                              n_neighbour=PIXEL2SEARCH,
                                              verbose=VERBOSE,
                                              min_strahler_order=MIN_STRAHLER)

        # Calculate and add change rate to the DataFrame
        points_new["change_rate[%]"] = 100 * \
            (points_new["CalculatedArea[km2]"] -
             points_new["area[km2]"]) / points_new["area[km2]"]

    elif MODE == "partial":  # If processing mode is 'partial'
        points_labelled = join_watersheds2points(
            points, WATERSHEDS)  # Join watersheds to points

        # Get unique watershed IDs
        unique_watershed_ids = points_labelled["Watershed_ID"].unique()

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
            # Process watershed points
            points_watershed = process_watershed_points(filtered_points_labelled,
                                                        accum,
                                                        drainage_direction,
                                                        DRAINAGE_DIRECTION_TYPE,
                                                        dr_dir_src,
                                                        tif_profile,
                                                        river_vector,
                                                        results_path=RESULTS,
                                                        vector_extension=VECTOR_EXTENSION,
                                                        n_neighbour=PIXEL2SEARCH,
                                                        verbose=VERBOSE,
                                                        min_strahler_order=MIN_STRAHLER)

            points_new = pd.concat(
                [points_new, points_watershed], ignore_index=True)  # Concatenate DataFrames for different watersheds

        # Calculate and add change rate to the DataFrame
        points_new["change_rate[%]"] = 100 * \
            (points_new["CalculatedArea[km2]"] -
             points_new["area[km2]"]) / points_new["area[km2]"]

    # Get current date and time
    date_time = datetime.now().strftime("%d%m%Y_%H%M")
    points_new.to_csv(os.path.join(
        RESULTS, f'report_{date_time}.csv'), encoding="utf-8-sig")  # Save the results to a CSV file
if __name__ == "__main__":
    delineate_upstream('configuration.ini')