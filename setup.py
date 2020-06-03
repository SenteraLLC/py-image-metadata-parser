"""imgparse parses metadata from imagery needed for image processing."""

import re

import setuptools

VERSIONFILE = "imgparse/_version.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imgparse",
    version=verstr,
    description="Python image-metadata-parser utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SenteraLLC/py-image-metadata-parser",
    packages=setuptools.find_packages(),
    install_requires=["exifread", "pandas", "parsec"],
    extras_require={
        "dev": ["pytest", "sphinx_rtd_theme", "m2r", "sphinx", "pre_commit"]
    },
)
