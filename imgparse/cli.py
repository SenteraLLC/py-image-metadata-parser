"""CLI wrappers for metadata parsing functions."""

import csv
import logging
from pathlib import Path

import click

from imgparse import MetadataParser, __version__
from imgparse.types import AltitudeSource

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--log_level",
    type=click.Choice(["DEBUG", "INFO", "WARNING"]),
    default="INFO",
    help="Set logging level for both console and file",
)
@click.version_option(__version__)
def cli(log_level: str) -> None:
    """CLI wrappers for metadata parsing functions."""
    logging.basicConfig(
        level=log_level, format="%(name)s - %(levelname)s - %(message)s"
    )


@cli.command()
@click.argument("image_path", required=True)
def get_ils(image_path: str) -> None:
    """Parse ILS from metadata."""
    print("ILS:", MetadataParser(image_path).ils())


@cli.command()
@click.argument("image_path", required=True)
def get_autoexposure(image_path: str) -> None:
    """Parse autoexposure from metadata."""
    print("Autoexposure:", MetadataParser(image_path).autoexposure())


@cli.command()
@click.argument("image_path", required=True)
def get_timestamp(image_path: str) -> None:
    """Parse timestamp from metadata."""
    print("Timestamp:", MetadataParser(image_path).timestamp())


@cli.command()
@click.argument("image_path", required=True)
def get_focal_length(image_path: str) -> None:
    """Parse focal length from metadata."""
    print("Focal length (pixels):", MetadataParser(image_path).focal_length_pixels())


@cli.command()
@click.argument("image_path", required=True)
def get_principal_point(image_path: str) -> None:
    """Parse principal point from metadata."""
    print("Principal Point (x,y): ", MetadataParser(image_path).principal_point())


@cli.command()
@click.argument("image_path", required=True)
def get_distortion_parameters(image_path: str) -> None:
    """Parse radial distortion parameters from metadata."""
    print("Distortions: ", MetadataParser(image_path).distortion_parameters())


@cli.command()
@click.argument("image_path", required=True)
@click.option(
    "--source", default="default", type=click.Choice(["default", "lrf", "terrain"])
)
@click.option("--api_key")
def get_relative_altitude(image_path: str, source: str, api_key: str) -> None:
    """Parse relative altitude from metadata."""
    print(
        "Altitude (m):",
        MetadataParser(image_path).relative_altitude(
            alt_source=AltitudeSource[source], terrain_api_key=api_key
        ),
    )


@cli.command()
@click.argument("image_path", required=True)
def get_lat_lon(image_path: str) -> None:
    """Parse latitude and longitude from metadata."""
    lat, lon = MetadataParser(image_path).coordinates()
    print("Lat:", lat)
    print("Lon:", lon)


@cli.command()
@click.argument("image_path", required=True)
def get_altitude_msl(image_path: str) -> None:
    """Parse altitude msl from metadata."""
    print("Altitude MSL (m):", MetadataParser(image_path).altitude_msl())


@cli.command()
@click.argument("image_path", required=True)
@click.option("--no_standardize", is_flag=True, default=False)
def get_roll_pitch_yaw(image_path: str, no_standardize: bool) -> None:
    """Parse the roll, pitch, yaw from metadata."""
    roll, pitch, yaw = MetadataParser(image_path).rotation(
        standardize=not no_standardize
    )
    print("Roll (degrees):", roll)
    print("Pitch (degrees):", pitch)
    print("Yaw (degrees):", yaw)


@cli.command()
@click.argument("image_path", required=True)
def get_make_and_model(image_path: str) -> None:
    """Parse camera make and model from metadata."""
    make, model = MetadataParser(image_path).make_and_model()
    print("Make:", make)
    print("Model:", model)


@cli.command()
@click.argument("image_path", required=True)
def get_dimensions(image_path: str) -> None:
    """Parse image dimensions from metadata."""
    print("Dimensions:", MetadataParser(image_path).dimensions())


@cli.command()
@click.argument("image_path", required=True)
def get_gsd(image_path: str) -> None:
    """Parse gsd from metadata."""
    print("Gsd (m):", MetadataParser(image_path).gsd())


@cli.command()
@click.argument("image_path", required=True)
def get_firmware_version(image_path: str) -> None:
    """Parse firmware from metadata."""
    print(
        "Firmware version:",
        ".".join(map(str, MetadataParser(image_path).firmware_version())),
    )


@cli.command()
@click.argument("image_path", required=True)
def get_wavelength_data(image_path: str) -> None:
    """Parse wavelength data from metadata."""
    data = MetadataParser(image_path).wavelength_data()
    print("Central Wavelength:")
    for w in data[0]:
        print(f"  {w}")
    print("WavelengthFWHM:")
    for f in data[1]:
        print(f"  {f}")


@cli.command()
@click.argument("image_path", required=True)
def get_bandnames(image_path: str) -> None:
    """Parse bandnames from metadata."""
    names = MetadataParser(image_path).bandnames()
    print("Bandnames:")
    for name in names:
        print(f"  {name}")


@cli.command()
@click.argument("image_path")
def get_irradiance(image_path: str) -> None:
    """Parse irradiance from metadata."""
    print("Irradiance:", MetadataParser(image_path).irradiance())


@cli.command()
@click.argument("image_path")
def get_capture_id(image_path: str) -> None:
    """Parse capture id from metadata."""
    print("Capture ID:", MetadataParser(image_path).capture_id())


@cli.command()
@click.argument("imagery_path", required=True)
def create_metadata_csv(imagery_path: str) -> None:  # noqa: D301
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

    image_dir = Path(imagery_path)

    if not image_dir.is_dir():
        logger.error("Imagery directory doesn't exist: %s", image_dir)
        raise ValueError("Imagery directory doesn't exist")

    images = [
        file
        for file in image_dir.glob("*")
        if file.suffix.lower() in [".jpg", ".jpeg", ".tif"]
    ]

    if not images:
        logger.error("No images found in imagery dir.")
        raise ValueError("No images found in imagery dir")

    metadata_csv = image_dir / "analytics-metadata.csv"
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
            parser = MetadataParser(image_path)

            writer.writerow(
                [
                    image_path.name,
                    *parser.coordinates(),
                    parser.altitude_msl(),
                    *parser.rotation(),
                    parser.relative_altitude(),
                    parser.focal_length_pixels(),
                ]
            )

    logger.info("Metadata csv saved at: %s", metadata_csv)
