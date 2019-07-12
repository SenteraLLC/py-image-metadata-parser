import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imgparse",
    version="0.0.0",
    description="Python image-metadata-parser utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SenteraLLC/py-image-metadata-parser",
    packages=setuptools.find_packages(),
    install_requires=[
        "exifread",
        "xmltodict"
    ],
    extras_require={
        'dev': [
            'pytest',
            'sphinx_rtd_theme',
            'pylint',
            'm2r',
            "sphinx"
        ]
    },
)
