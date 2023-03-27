# py-image-metadata-parser

``imgparse``: Python utilities for extracting exif and xmp metadata from imagery.

## Installation 

### Windows 

1) [Set up SSH](https://github.com/SenteraLLC/install-instructions/blob/master/ssh_setup.md)
2) Install [conda](https://github.com/SenteraLLC/install-instructions/blob/master/conda.md)
3) Install package

        git clone git@github.com:SenteraLLC/py-image-metadata-parser.git
        cd py-image-metadata-parser
        conda env create -f environment.yml
        conda activate image-parsing
        pip install .
   
4) Set up ``pre-commit`` to ensure all commits to adhere to **black** and **PEP8** style conventions.

        pre-commit install
   
### Linux

1) [Set up SSH](https://github.com/SenteraLLC/install-instructions/blob/master/ssh_setup.md)
2) Install [pyenv](https://github.com/SenteraLLC/install-instructions/blob/master/pyenv.md) and [poetry](https://python-poetry.org/docs/#installation)
3) Install package

        git clone git@github.com:SenteraLLC/py-image-metadata-parser.git
        cd py-image-metadata-parser
        pyenv install $(cat .python-version)
        poetry install -E dji_timestamps
        
4) Set up ``pre-commit`` to ensure all commits to adhere to **black** and **PEP8** style conventions.

        poetry run pre-commit install
        
## CLI Usage

Run ``imgparse --help`` to see a list of all CLI commands available.  Make sure you are in the correct conda 
environment/poetry shell.
