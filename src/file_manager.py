import os
import warnings
from run_config import *

def check_config_file_validity():
    """
    Checks the validity of the configuration file for running a specific mode.

    This function validates the configuration file based on the selected mode and parameter values. It raises
    ValueErrors if the configuration is invalid, such as incorrect file/folder paths or unsupported parameter values.
    Additionally, it raises a UserWarning if the value of PIXEL2SEARCH is set higher than 6, which may lead to
    unexpected results.

    Raises:
        ValueError: If the configuration file is invalid for the selected mode.
        ValueError: If the MODE parameter is not set to 'single' or 'partial'.
        ValueError: If the VERBOSE parameter is not set to either True, False, 1, or 0.

    Warns:
        UserWarning: If the value of PIXEL2SEARCH is set higher than 6, which may lead to unexpected results.
        UserWarning: If the RESULTS directory does not exist, it will be generated.

    """
    if MODE == "single":
        if not os.path.isfile(RIVERS):
            raise ValueError("In Single Mode, Rivers Vector Path must be a file not a folder. "
                             f"Please check RIVERS = {RIVERS}")
        if not os.path.isfile(FLOW_ACCUMULATION):
            raise ValueError("In Single Mode, Flow Accumulation Path must be a file not a folder. "
                             f"Please check FLOW_ACCUMULATION = {FLOW_ACCUMULATION}")
        if not os.path.isfile(DRAINAGE_DIRECTION):
            raise ValueError("In Single Mode, Drainage Direction Path must be a file not a folder. "
                             f"Please check DRAINAGE_DIRECTION = {DRAINAGE_DIRECTION}")
    elif MODE == "partial":
        if not os.path.isdir(RIVERS):
            raise ValueError("In Partial Mode, Rivers Vector Path must be a folder not a file. "
                             f"Please check RIVERS = {RIVERS}")
        if not os.path.isdir(FLOW_ACCUMULATION):
            raise ValueError("In Partial Mode, Flow Accumulation Path must be a folder not a file. "
                             f"Please check FLOW_ACCUMULATION = {FLOW_ACCUMULATION}")
        if not os.path.isdir(DRAINAGE_DIRECTION):
            raise ValueError("In Partial Mode, Drainage Direction Path must be a folder not a file. "
                             f"Please check DRAINAGE_DIRECTION = {DRAINAGE_DIRECTION}")
    else:
        raise ValueError("MODE can only be either 'single' or 'partial'! "
                         "Please check the run_config.py file and arrange the MODE parameter accordingly.")

    if PIXEL2SEARCH >= 6:
        warnings.warn(f"PIXEL2SEARCH is set to {PIXEL2SEARCH}! This value seems high. "
                      "Unexpected results may occur!", UserWarning)

    if VERBOSE not in [True, False]:
        raise ValueError("VERBOSE can only be True, False, 1, or 0. "
                         "Please check the VERBOSE parameter in run_config.py.")
    
    if not os.path.isdir(RESULTS):
        warnings.warn(f"{RESULTS} directory/folder does not exist! It will be generated!")




def create_results_directory(path):
    """
    Check if the given path is a directory and create necessary subdirectories.

    This function checks if the provided path exists. If it does not exist, it creates the directory.
    If the path exists, it verifies if it's a directory. If it's not a directory, a NotADirectoryError is raised to notify the user.
    If the path is a directory, it creates three subdirectories inside it: 'watershed', 'river', and 'web'.
    If any of these subdirectories already exist, the function does not raise an error and continues execution.

    Args:
        path (str): The path of the directory to check and create subdirectories in.

    Raises:
        NotADirectoryError: If the provided path exists but is not a directory.

    """
    if not os.path.exists(path):
        os.makedirs(path)

    if not os.path.isdir(path):
        raise NotADirectoryError(f"The path '{path}' is not a directory.")

    watershed_dir = os.path.join(path, "watershed")
    river_dir = os.path.join(path, "river")
    web_dir = os.path.join(path, "web")

    os.makedirs(watershed_dir, exist_ok=True)
    os.makedirs(river_dir, exist_ok=True)
    os.makedirs(web_dir, exist_ok=True)

    if VERBOSE:
        print(f"{RESULTS} folder is created! The results will be stored in this folder.")
