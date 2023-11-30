# run.py
import argparse
from src.delineate_upstream import delineate_upstream

def main():
    parser = argparse.ArgumentParser(description="Run script with config file.")
    parser.add_argument("--config_path", required=True, help="Path to the config file")

    args = parser.parse_args()
    delineate_upstream(args.config_path)

if __name__ == "__main__":
    main()