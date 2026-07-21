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
        poetry install -E s3

4) Set up ``pre-commit`` to ensure all commits to adhere to **black** and **PEP8** style conventions.

        poetry run pre-commit install

### uv (alternative to poetry)

The project is also compatible with [uv](https://docs.astral.sh/uv/). Poetry remains the
primary tool (``poetry.lock`` is the committed lockfile), but uv can be used as a drop-in
dev environment manager. ``poetry.toml`` isolates poetry's virtualenv in ``.venv-poetry`` so
it doesn't collide with uv's ``.venv``.

1) Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2) Install package (creates ``.venv`` and resolves ``uv.lock``)

        git clone git@github.com:SenteraLLC/py-image-metadata-parser.git
        cd py-image-metadata-parser
        uv sync --all-extras

3) Set up ``pre-commit`` (the mypy hook auto-detects uv vs poetry).

        uv run pre-commit install

Run commands with ``uv run`` in place of ``poetry run`` (e.g. ``uv run pytest``,
``uv run imgparse --help``).

## CLI Usage

Run ``imgparse --help`` to see a list of all CLI commands available.  Make sure you are in the correct conda 
environment/poetry shell.
