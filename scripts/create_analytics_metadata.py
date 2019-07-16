"""
Command line wrapper for create_analytics_metadata function
"""

import argparse
import logging
import imgparse


def main(imagery_dir):
    # Setup logger
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    log_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(log_format)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    imgparse.create_analytics_metadata(imagery_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("imagery_dir", help="Imagery directory to create analytics metadata file from")
    args = parser.parse_args()

    main(args.imagery_dir)
