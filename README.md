## py-image-metadata-parser

Python utilities for extracting exif and xmp data from imagery.

### Installation

This library has only been built and used on Windows 10 and Ubuntu 18 operating systems, and so those are the
environments assumed by these installation instructions.  However installing and using this library on a different OS 
should be a simple extension of these instructions.

#### Windows (Conda)

1) If not installed, install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for Python 3.6

2) Open Anaconda Prompt and clone **py-image-metadata-parser** with

        >> git clone https://github.com/SenteraLLC/py-image-metadata-parser.git

3) Open Anaconda Prompt and navigate to **py-image-metadata-parser**.  Run

        >> conda env create -f environment.yml
        >> conda activate image-parsing
        >> pip install -e .
        
4) This creates the *image-parsing* environment that all scripts should be run in and installs
   the **imgparse** library for the scripts to reference.
   
5) Within the top level of the repo in the *image-parsing* environment, run

        >> pre-commit install
        
   This will enforce all commits to adhere to **black** and **PEP8** style conventions.
   
6) To check it is properly installed, open a new Anaconda shell, navigate to **py-image-metadata-parser**, and run

        >> activate image-parsing
        >> pytest tests

If no errors appear, the **imgparse** library should be installed correctly.

#### Linux (Pipenv)

1) If not installed, install **pipenv** with the command

        >> pip install pipenv
        
2) Open a terminal and clone **py-image-metadata-parser** with

        >> git clone https://github.com/SenteraLLC/py-image-metadata-parser.git        
        
3) Navigate to **py-image-metadata-parser** and run

        >> pipenv install --dev
        
5) Within the top level of the repo, run

        >> pipenv run pre-commit install
        
   This will enforce all commits to adhere to **black** and **PEP8** style conventions.
   
4) Everything should be properly installed within a pipenv environment.  To check it is, run

        >> pipenv run pytest tests
        
If no errors appear, the **imgparse** library should be installed correctly

### Documentation

This library is documented using sphinx. Generate the documentation with the following commands

    >> cd py-image-metadata-parser\doc\
    >> make html

The documentation will be generated as an html file located at *py-image-metadata-parser/doc/\_build/html/index.html*.  
Open with a browser to get more in depth information on the various modules and functions within the 
**imgparse** library.