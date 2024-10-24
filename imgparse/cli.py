"""CLI wrappers for metadata parsing functions."""

import csv
import logging
import os

import click

from imgparse import metadata

from . import imgparse

logger = logging.getLogger(__name__)


class ClickMetadata(click.ParamType):
    """Click type that converts a passed metadata type to a Metadata instance."""

    metadata_items = {
        k: v for k, v in vars(metadata).items() if isinstance(v, metadata.Metadata)
    }

    def convert(self, value, param, ctx):
        """Attempt to parse the passed metadata string to a Metadata instance, and fail if unable."""
        try:
            return ClickMetadata.metadata_items[value.upper()]
        except KeyError:
            self.fail(
                f"Invalid metadata type '{value}'. Supported types are [{'|'.join((item for item in ClickMetadata.metadata_items))}]",
                param,
                ctx,
            )


@click.group()
@click.option(
    "--log_level",
    type=click.Choice(["DEBUG", "INFO", "WARNING"]),
    default="INFO",
    help="Set logging level for both console and file",
)
def cli(log_level):
    """CLI wrappers for metadata parsing functions."""
    logging.basicConfig(
        level=log_level, format="%(name)s - %(levelname)s - %(message)s"
    )


@cli.command()
@click.argument("image_path", required=True)
def get_ils(image_path):
    """Parse ILS from metadata."""
    print("ILS:", imgparse.get_ils(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_autoexposure(image_path):
    """Parse autoexposure from metadata."""
    print("Autoexposure:", imgparse.get_autoexposure(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_timestamp(image_path):
    """Parse timestamp from metadata."""
    print("Timestamp:", imgparse.get_timestamp(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_pixel_pitch(image_path):
    """Parse pixel pitch from metadata."""
    print("Pixel pitch (m):", imgparse.get_pixel_pitch(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_focal_length(image_path):
    """Parse focal length from metadata."""
    print("Focal length (m):", imgparse.get_focal_length(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_principal_point(image_path):
    """Parse principal point from metadata."""
    print("Principal Point (x,y): ", imgparse.get_principal_point(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_distortion_parameters(image_path):
    """Parse radial distortion parameters from metadata."""
    print("Distortions: ", imgparse.get_distortion_parameters(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_camera_params(image_path):
    """Parse pixel pitch and focal length from metadata."""
    fl, pp = imgparse.get_camera_params(image_path)
    print("Focal length (m):", fl)
    print("Pixel pitch (m):", pp)


@cli.command()
@click.argument("image_path", required=True)
@click.option(
    "--source", default="default", type=click.Choice(["default", "lrf", "terrain"])
)
@click.option("--api_key")
def get_relative_altitude(image_path, source, api_key):
    """Parse relative altitude from metadata."""
    print(
        "Altitude (m):",
        imgparse.get_relative_altitude(
            image_path, alt_source=source, terrain_api_key=api_key
        ),
    )


@cli.command()
@click.argument("image_path", required=True)
def get_lat_lon(image_path):
    """Parse latitude and longitude from metadata."""
    lat, lon = imgparse.get_lat_lon(image_path)
    print("Lat:", lat)
    print("Lon:", lon)


@cli.command()
@click.argument("image_path", required=True)
def get_altitude_msl(image_path):
    """Parse altitude msl from metadata."""
    print("Altitude MSL (m):", imgparse.get_altitude_msl(image_path))


@cli.command()
@click.argument("image_path", required=True)
@click.option("--no_standardize", is_flag=True, default=False)
def get_roll_pitch_yaw(image_path, no_standardize):
    """Parse the roll, pitch, yaw from metadata."""
    roll, pitch, yaw = imgparse.get_roll_pitch_yaw(
        image_path, standardize=not no_standardize
    )
    print("Roll (degrees):", roll)
    print("Pitch (degrees):", pitch)
    print("Yaw (degrees):", yaw)


@cli.command()
@click.argument("image_path", required=True)
def get_make_and_model(image_path):
    """Parse camera make and model from metadata."""
    make, model = imgparse.get_make_and_model(image_path)
    print("Make:", make)
    print("Model:", model)


@cli.command()
@click.argument("image_path", required=True)
def get_dimensions(image_path):
    """Parse image dimensions from metadata."""
    print("Dimensions:", imgparse.get_dimensions(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_gsd(image_path):
    """Parse gsd from metadata."""
    print("Gsd (m):", imgparse.get_gsd(image_path))


@cli.command()
@click.argument("image_path", required=True)
def get_firmware_version(image_path):
    """Parse firmware from metadata."""
    print(
        "Firmware version:",
        ".".join(map(str, imgparse.get_firmware_version(image_path))),
    )


@cli.command()
@click.argument("image_path", required=True)
def get_wavelength_data(image_path):
    """Parse wavelength data from metadata."""
    data = imgparse.get_wavelength_data(image_path)
    print("Central Wavelength:")
    for w in data[0]:
        print(f"  {w}")
    print("WavelengthFWHM:")
    for f in data[1]:
        print(f"  {f}")


@cli.command()
@click.argument("image_path", required=True)
def get_bandnames(image_path):
    """Parse bandnames from metadata."""
    names = imgparse.get_bandnames(image_path)
    print("Bandnames:")
    for name in names:
        print(f"  {name}")


@cli.command()
@click.argument("image_path", required=True)
def get_home_point(image_path):
    """Parse flight home point from metadata."""
    lat, lon = imgparse.get_home_point(image_path)
    print("Lat:", lat)
    print("Lon:", lon)


@cli.command()
@click.argument("image_path", required=True)
@click.argument("metadata", required=True, nargs=-1, type=ClickMetadata())
def get_metadata(image_path, metadata):
    """Get a variable number of supported metadata."""
    for metadata_type in metadata:
        print(f"{metadata_type.name}:", metadata_type.method(image_path))


@cli.command()
@click.argument("imagery_dir", required=True)
def create_metadata_csv(imagery_dir):  # noqa: D301
    r"""
    Construct a metadata csv file within the provided imagery directory.

    \b
    The output metadata csv contains a row for each image in the input directory specifying:
    File Name
    Lat/Lon
    Altitude MSL
    Roll/Pitch/Yaw
    Altitude AGL
    """
    logger.info("Creating metadata csv")

    if not os.path.isdir(imagery_dir):
        logger.error("Imagery directory doesn't exist: %s", imagery_dir)
        raise ValueError("Imagery directory doesn't exist")

    images = [
        os.path.join(imagery_dir, image)
        for image in os.listdir(imagery_dir)
        if os.path.splitext(image)[1].lower() in [".jpg", ".tiff", ".tif"]
    ]

    if not images:
        logger.error("No images found in imagery dir.")
        raise ValueError("No images found in imagery dir")

    metadata_csv = os.path.join(imagery_dir, "analytics-metadata.csv")
    with open(metadata_csv, "w") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(
            [
                "File Name",
                "Lat (decimal degrees)",
                "Lon (decimal degrees)",
                "Alt (meters MSL)",
                "Roll (decimal degrees)",
                "Pitch (decimal degrees)",
                "Yaw (decimal degrees)",
                "Alt (meters AGL)",
                "Focal Length (pixels)",
            ]
        )

        for image_path in images:
            logger.info("Parsing image: %s", image_path)
            exif_data = imgparse.get_exif_data(image_path)
            xmp_data = imgparse.get_xmp_data(image_path)
            fl, pp = imgparse.get_camera_params(image_path)

            writer.writerow(
                [
                    os.path.split(image_path)[1],
                    *imgparse.get_lat_lon(image_path, exif_data),
                    imgparse.get_altitude_msl(image_path, exif_data),
                    *imgparse.get_roll_pitch_yaw(image_path, exif_data, xmp_data),
                    imgparse.get_relative_altitude(image_path, exif_data, xmp_data),
                    fl / pp,
                ]
            )

    logger.info("Metadata csv saved at: %s", metadata_csv)
