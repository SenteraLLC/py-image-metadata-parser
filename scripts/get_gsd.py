"""CLI wrapper for get_gsd() function."""

import argparse
import logging

import imgparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Image path to get gsd of")
    parser.add_argument(
        "--altitude",
        help="(optional) Relative altitude of the image above ground",
        type=float,
    )
    args = parser.parse_args()

    # Setup logger
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    log_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(log_format)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    gsd = imgparse.get_gsd(args.image_path, corrected_alt=args.altitude)
    print(f"GSD: {gsd}")
