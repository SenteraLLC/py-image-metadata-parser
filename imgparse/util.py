"""Utility functions for parsing metadata."""

from typing import Any, Callable

from exifread.classes import IfdTag


def convert_to_degrees(tag: IfdTag) -> float:
    """Convert the `exifread` GPS coordinate IfdTag object to degrees in float format."""
    degrees = convert_to_float(tag, 0)
    minutes = convert_to_float(tag, 1)
    seconds = convert_to_float(tag, 2)

    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def convert_to_float(tag: IfdTag, index: int = 0) -> float:
    """Convert `exifread` IfdTag object to float."""
    return float(tag.values[index].num) / float(tag.values[index].den)


def parse_seq(
    tag: dict[str, dict[str, list[str] | str]],
    type_cast_func: Callable[[str], Any] | None = None,
) -> list[Any]:
    """Parse an XML sequence."""
    seq = tag["rdf:Seq"]["rdf:li"]
    if not isinstance(seq, list):
        seq = [seq]
    if type_cast_func is not None:
        seq = [type_cast_func(item) for item in seq]

    return seq
