# py-image-metadata-parser

``imgparse``: Python utilities for extracting exif and xmp metadata from imagery.

## Installation 

### 1) SSH Setup

Some Python libraries depend on private Github repositories, and the setup tools use ssh to access them.  You must link 
ssh keys on your computer with your Github account when using Sentera Python
libraries, else you'll encounter installation errors.  For Windows, make sure you have downloaded the correct 
[Git Bash](https://gitforwindows.org/) to run the necessary commands.  For Linux, use a normal terminal.

Git SSH Setup Instructions: https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

Test your SSH setup with:

    ssh -T git@github.com
    
### 2) Set Up Package Manager

#### Windows (Conda)
    
1) Download [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for Python3.7
   
#### Linux (Pipenv)

1) If not installed, install pipenv.

        pip install --user pipenv
        
2) Set your PATH to point to the pipenv executable by adding the following to ~/.profile

        export PATH="$PATH:~/.local/bin"

3) Check installation:

        source ~/.profile
        pipenv -h
        
### 3) Clone and Install Package

#### Windows (Conda)

1) Open Anaconda Prompt and clone **py-image-metadata-parser** with

        git clone git@github.com:SenteraLLC/py-image-metadata-parser.git

2) Install package with

        cd py-image-metadata-parser
        start-ssh-agent
        conda env create -f environment.yml
        conda activate image-parsing
        pip install -e .
   
3) To enforce all commits to adhere to **black** and **PEP8** style conventions, within the top level 
   of the repo in the *image-parsing* environment, run

        pre-commit install
   
#### Linux (Pipenv)

1) Open terminal and clone **py-image-metadata-parser** with

        git clone git@github.com:SenteraLLC/py-image-metadata-parser.git

2) Install package with

        cd py-image-metadata-parser
        pipenv install --dev
        
3) To enforce all commits to adhere to **black** and **PEP8** style conventions, within the top level 
   of the repo, run

        pipenv run pre-commit install
        
## CLI Usage

Run ``imgparse --help`` **from any directory** to see a list of all CLI commands available.  Make sure you are in the
correct conda environment/pipenv shell.
   
## Documentation

This library is documented using Sphinx. To generate documentation, navigate to the *docs/* subfolder,
and run ``make html``.  Make sure you are in the correct conda environment/pipenv shell.  Open 
*docs/\_build/html/index.html* with a browser to get more in depth information on the various modules 
and functions within the library.
