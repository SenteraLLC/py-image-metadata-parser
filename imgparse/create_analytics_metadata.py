"""
Deprecated function to create an analytics metadata file needed by the old version of ape
"""

import os
import random
import logging
import pandas
from . import imgparse

logger = logging.getLogger(__name__)


def create_analytics_metadata(imagery_dir, sample_size=-1):
    """
    Constructs an *analytics-metadata.csv* file within the imagery directory provided.  This file is needed by the
    old version of ape in order to process a directory of images.  This function is deprecated and will be removed
    with creation of a new version of ape that no longer needs this *analytics-metadata.csv* file.

    :param imagery_dir: directory of images to create analytics metadata file from
    :param sample_size: (optional) samples metadata from provided number of images in the directory
    :return: **True/False** - indicating success
    """
    logger.info("Creating analytics-metadata file")

    if not os.path.isdir(imagery_dir):
        logger.error("Input imagery directory doesn't exist.  Couldn't construct analytics metadata file")
        raise ValueError("Input imagery directory doesn't exist.  Couldn't construct analytics metadata file")

    images = [os.path.join(imagery_dir, image) for image in os.listdir(imagery_dir) if os.path.splitext(image)[1].lower() == ".jpg"]
    if not images:
        logger.error("No jpegs found in imagery dir. Couldn't construct analytics metadata file")
        raise ValueError("No jpegs found in imagery dir. Couldn't construct analytics metadata file")

    if 0 < sample_size < len(images):
        images = random.sample(images, k=sample_size)

    data_frame = pandas.DataFrame(columns=['File Name',
                                           'Lat (decimal degrees)',
                                           'Lon (decimal degrees)',
                                           'Alt (meters MSL)',
                                           'Roll (decimal degrees)',
                                           'Pitch (decimal degrees)',
                                           'Yaw (decimal degrees)',
                                           'Relative Altitude'])

    for image_path in images:
        image = os.path.split(image_path)[1]
        exif_data = imgparse.get_exif_data(image_path)
        xmp_data = imgparse.get_xmp_data(image_path)

        lat, lon = imgparse.get_lat_lon(image_path, exif_data)
        if not lat:
            logger.error("Couldn't extract lat and lon from image: %s", image_path)
            logger.error("Couldn't construct analytics metadata file")
            raise ValueError("Couldn't extract lat and lon from image")

        abs_alt = imgparse.get_altitude_msl(image_path, exif_data)
        if not abs_alt:
            logger.error("Couldn't extract msl altitude for image: %s", image_path)
            logger.error("Couldn't construct analytics metadata file")
            raise ValueError("Couldn't extract msl altitude from image")

        roll, pitch, yaw = imgparse.get_roll_pitch_yaw(image_path, exif_data, xmp_data)

        relative_alt = imgparse.get_relative_altitude(image_path, exif_data, xmp_data)

        if not relative_alt:
            logger.error("Couldn't extract relative altitude for image: %s", image_path)
            logger.error("Couldn't construct analytics metadata file")
            raise ValueError("Couldn't extract relative altitude from image")

        data_frame.loc[len(data_frame)] = [image, lat, lon, abs_alt, roll, pitch, yaw, relative_alt]

    analytics_path = os.path.join(imagery_dir, "analytics-metadata.csv")
    data_frame.to_csv(analytics_path, index=False)

    logger.info("Analytics metadata file saved at: %s", analytics_path)
