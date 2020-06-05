"""CLI wrappers for metadata parsing functions."""

import logging

import click

from . import imgparse


@click.group()
@click.option(
    "--log_level",
    type=click.Choice(["DEBUG", "INFO", "WARNING"]),
    default="INFO",
    help="Set logging level for both console and file",
)
def cli(log_level):
    """CLI wrappers for metadata parsing functions."""
    logging.basicConfig(level=log_level)


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
def get_camera_params(image_path):
    """Parse pixel pitch and focal length from metadata."""
    fl, pp = imgparse.get_camera_params(image_path)
    print("Focal length (m):", fl)
    print("Pixel pitch (m):", pp)


@cli.command()
@click.argument("image_path", required=True)
def get_relative_altitude(image_path):
    """Parse relative altitude from metadata."""
    print("Altitude (m):", imgparse.get_relative_altitude(image_path))


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
def get_roll_pitch_yaw(image_path):
    """Parse the roll, pitch, yaw from metadata."""
    roll, pitch, yaw = imgparse.get_roll_pitch_yaw(image_path)
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
