## py-image-metadata-parser

**``imgparse``**: Python utilities for extracting exif and xmp data from imagery.

### Installation 
    
#### 1) Set Up Package Manager

##### Windows (Conda)
    
1) Download [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for Python3.7
   
##### Linux (Pipenv)

1) If not installed, install pipenv.

        >> pip install --user pipenv
        
2) Set your PATH to point to the pipenv executable by adding the following to ~/.profile

        export PATH="$PATH:~/.local/bin"

3) Check installation:

        >> source ~/.profile
        >> pipenv -h
        
#### 2) Clone and Install Package

##### Windows (Conda)

1) Open Anaconda Prompt and clone **py-image-metadata-parser** with

        >> git clone git@github.com:SenteraLLC/py-image-metadata-parser.git

2) Install package with

        >> cd py-image-metadata-parser
        >> start-ssh-agent
        >> conda env create -f environment.yml
        >> conda activate image-parsing
        >> pip install -e .
        
3) This creates a *image-parsing* environment that all scripts should be run in and installs the ``imgparse``
   library for the scripts to reference.
   
4) To enforce all commits to adhere to **black** and **PEP8** style conventions, within the top level 
   of the repo in the *image-parsing* environment, run

        >> pre-commit install
   
##### Linux (Pipenv)

1) Open terminal and clone **py-image-metadata-parser** with

        >> git clone git@github.com:SenteraLLC/py-image-metadata-parser.git

2) Install package with

        >> cd py-image-metadata-parser
        >> pipenv install --dev
        
4) To enforce all commits to adhere to **black** and **PEP8** style conventions, within the top level 
   of the repo, run

        >> pipenv run pre-commit install
        
3) Run all scripts with:

        >> pipenv run python scripts/<script.py> [--args]
   
### Documentation

This library is documented using Sphinx. To generate documentation, navigate to the *doc/* subfolder,
and run

#### Windows

    >> conda activate image-parsing
    >> make html
    
#### Linux

    >> pipenv run make html

The documentation will be generated as an html file located at *py-image-metadata-parser/doc/\_build/html/index.html*. 
Open with a browser to get more in depth information on the various modules and functions within the library.
