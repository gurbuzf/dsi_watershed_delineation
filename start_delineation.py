"""
Console tool for running the hydrological data processing script.
"""

import argparse
import subprocess


def run_script(config_file):
    """
    Run the hydrological data processing script with the provided config file.

    Args:
        config_file (str): Path to the config file.
    """
    command = f"python main.py {config_file}"
    subprocess.run(command, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run script with config file.")
    parser.add_argument("config_file", help="Path to the config file")

    args = parser.parse_args()
    run_script(args.config_file)
