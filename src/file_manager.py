import os
import warnings
import configparser


def check_config_file_validity(config_file_path):
    """
    Validate the configuration file for the selected mode.

    This function checks the validity of the configuration file, raising ValueErrors for invalid configurations,
    such as incorrect file/folder paths or unsupported parameter values. Additionally, it raises a UserWarning if the
    value of PIXEL2SEARCH is set higher than 6, which may lead to unexpected results.

    Args:
        config_file_path (str): Path to the configuration file.

    Raises:
        ValueError: If the configuration file is invalid for the selected mode.
        ValueError: If the MODE parameter is not set to 'single' or 'partial'.
        ValueError: If the VERBOSE parameter is not set to either True, False, 1, or 0.

    Warns:
        UserWarning: If the value of PIXEL2SEARCH is set higher than 6, which may lead to unexpected results.
        UserWarning: If the RESULTS directory does not exist, it will be generated.

    """

    config = read_config(config_file_path)
    MODE = config.get('MODE')
    OUTLETS = config.get('OUTLETS')
    DRAINAGE_DIRECTION = config.get('DRAINAGE_DIRECTION')
    DRAINAGE_DIRECTION_TYPE = config.get('DRAINAGE_DIRECTION_TYPE')

    try:
        WATERSHEDS = eval(config.get('WATERSHEDS'))
    except NameError:
        WATERSHEDS = config.get('WATERSHEDS')

    try: 
        RIVERS = eval(config.get('RIVERS'))
    except NameError:
        RIVERS = config.get('RIVERS')

    try:
        FLOW_ACCUMULATION = eval(config.get('FLOW_ACCUMULATION'))
    except NameError:
        FLOW_ACCUMULATION = config.get('FLOW_ACCUMULATION')

    VERBOSE = eval(config.get('VERBOSE'))
    PIXEL2SEARCH = int(config.get('PIXEL2SEARCH'))
    RESULTS = config.get('RESULTS')
    MIN_STRAHLER = eval(config.get('MIN_STRAHLER'))
    VECTOR_EXTENSION = config.get('VECTOR_EXTENSION')

    if MODE == "single":
        if not RIVERS in ['', None, False]:
            if not os.path.isfile(RIVERS):
                raise ValueError("In Single Mode, Rivers Vector Path must be a file not a folder. "
                                 f"Please check RIVERS = {RIVERS}")
        if not FLOW_ACCUMULATION in ['', None, False]:
            if not os.path.isfile(FLOW_ACCUMULATION):
                raise ValueError("In Single Mode, Flow Accumulation Path must be a file not a folder. "
                                 f"Please check FLOW_ACCUMULATION = {FLOW_ACCUMULATION}")

        if not os.path.isfile(DRAINAGE_DIRECTION):
            raise ValueError("In Single Mode, Drainage Direction Path must be a file not a folder. "
                             f"Please check DRAINAGE_DIRECTION = {DRAINAGE_DIRECTION}")

    elif MODE == "partial":
        if not RIVERS in ['', None, False]:
            if not os.path.isdir(RIVERS):
                raise ValueError("In Partial Mode, Rivers Vector Path must be a folder not a file. "
                                 f"Please check RIVERS = {RIVERS}")
        if not FLOW_ACCUMULATION in ['', None, False]:
            if not os.path.isdir(FLOW_ACCUMULATION):
                raise ValueError("In Partial Mode, Flow Accumulation Path must be a folder not a file. "
                                 f"Please check FLOW_ACCUMULATION = {FLOW_ACCUMULATION}")

        if not os.path.isdir(DRAINAGE_DIRECTION):
            raise ValueError("In Partial Mode, Drainage Direction Path must be a folder not a file. "
                             f"Please check DRAINAGE_DIRECTION = {DRAINAGE_DIRECTION}")
    else:
        raise ValueError("MODE can only be either 'single' or 'partial'! "
                         "Please check the configuration.py file and arrange the MODE parameter accordingly.")

    if DRAINAGE_DIRECTION_TYPE not in ["arcgis", "grass"]:
        raise ValueError("DRAINAGE_DIRECTION_TYPE can only be 'arcgis' or 'grass'."
                         "Please check the DRAINAGE_DIRECTION_TYPE parameter in configuration file.")
    if not FLOW_ACCUMULATION in ['', None, False]:
        if PIXEL2SEARCH >= 6:
            warnings.warn(f"PIXEL2SEARCH is set to {PIXEL2SEARCH}! This value seems high. "
                          "Unexpected results may occur!", UserWarning)

    if VERBOSE not in [True, False]:
        raise ValueError("VERBOSE can only be True, False, 1, or 0. "
                         "Please check the VERBOSE parameter in in configuration file.")

    if not os.path.isdir(RESULTS):
        warnings.warn(
            f"{RESULTS} directory/folder does not exist! It will be generated!")

    if VECTOR_EXTENSION not in ["kml", "geojson"]:
        raise ValueError('VECTOR_EXTENSION should be kml (default), geojson.')


def create_results_directory(path, verbose=False):
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
    # web_dir = os.path.join(path, "web")

    os.makedirs(watershed_dir, exist_ok=True)
    os.makedirs(river_dir, exist_ok=True)
    # os.makedirs(web_dir, exist_ok=True)

    if verbose:
        print(f"[+] {path} folder is created! The results will be stored in this folder.\n")


def read_config(config_file_path):
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f"Config file not found: {config_file_path}")

    config = configparser.ConfigParser()
    config.read(config_file_path)

    if 'Settings' not in config:
        raise ValueError("Settings section not found in the config file.")

    return config['Settings']
