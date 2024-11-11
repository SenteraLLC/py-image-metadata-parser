"""Defines package version."""

import importlib.metadata
import os

if os.environ.get("VERSION"):
    __version__ = os.environ.get("VERSION")
else:
    __version__ = importlib.metadata.version("imgparse")
