"""CLI wrapper for get_relative_altitude() function."""

import argparse
import logging

import imgparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Image path to get camera params of")
    args = parser.parse_args()

    # Setup logger
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    log_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(log_format)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    altitude = imgparse.get_relative_altitude(args.image_path)
    print(f"Relative Altitude: {altitude}")
