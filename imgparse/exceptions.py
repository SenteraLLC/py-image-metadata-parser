"""Custom exceptions for image metadata parsing."""


class ParsingError(Exception):
    """Custom exception for when information can't be parsed from metadata."""

    pass


class TerrainAPIError(Exception):
    """Custom exception for when the call to the google terrain api fails."""

    pass
