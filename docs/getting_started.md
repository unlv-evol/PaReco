# Getting Started

## Setting up PaReco
To setup and test `PaReco` tool on your local computer, following the steps below:
## Directory Structure

```bash
.
├── LICENSE # MIT license
├── README.md
├── docs # documentaion files as markdowns
├── mkdocs.yml # mkdocs configuration file
├── requirements.txt # python development packages
├── tokens-example.txt # GitHub API tokens file, renamed to `tokens.txt` in production 
├── PaReco.py # main application entrypoint
├── src
│   ├── bin # contains shell script for install of OS dependencies
│   ├── constants # application wide global and constant variable 
│   ├── core # contains the files that are at the heart of the tool for classification 
│   ├── utils # helpers function used in the main files 
│   ├── legacy # backup of the original version of PaReco
│   ├── notebooks # experiments and analysis 
│   └── tests # Test cases
└── 
```
### Get the code
The easiest way is using the `git clone` command:

```bash
git clone https://github.com/unlv-evol/PaReco.git
```
### Dependencies
`PaReco` consist of two categories of depencies i.e. (i) OS specific dependencies and (ii) development dependencies. The OS specific dependency is `libmagic`. To install this dependency on `Ubuntu/Debian` or `MacOS X`, run the shell script in the `bin` directory.

```bash
cd bin/
chmod +x script.sh
./script.sh
```
The above code will automatically detect the OS (Linux or MacOS X) and install the libraries.
Before installing development specific dependencies, let's set python virtual environment;

```bash
cd PaReco/

python3 -m venv venv
```
Activate the virtual environment 

```bash
source venv/bin/activate
```

Now, let us install the dependencies

```bash
pip install -r requirements.txt
```
Note: `PaReco` has been tested on `python >= 3.7`

## Testing PaReco

### GitHub Tokens
To access private repositories, and to have a higher rate limit, GitHub tokens are needed.

They can be set in the `tokens.txt` file or by directly inserting it in the token_list in the notebooks. **GitHub tokens are a MUST** to run the code, because of the high number of requests done to the GitHub API. Every token in the `tokens.txt` file is seperated by only a comma. The user can add as many tokens as needed. **A minimal of 5 tokens** can be used to safely execute code and to make sure that the rate limit is not reached for a token.

### Using Notebooks
There are 3 notebooks that are at the heart of this tool: `/legacy/src/getData.ipynb`, `/legacy/src/classify.ipynb` and `/legac/src/analysis.ipynb`: 
* `getData.ipynb` extracts the pull request data from the GitHub API and stores it in Repos_prs
* After which `classify.ipynb` extracts the files from for each pull request, the `diffs` for each **modified/added/removed** file and classifies the `hunk` and `files`.
* Then `analysis.ipynb` does the last classification for the `patch` and calcualtes the total classification per repository and plots the results
* Finally, `timeLag.ipynb` calcualtes the techinical lag for each `patch`.

#### Examples
The folder `/legacy/Examples` contains a Jupyter notebook that can be used to quickly run the tool and classify one or more pull requests for two variant repositories. A simple class `PaReco` exists that does the classification. Running the notebook for source and target variant `mrbrdo/rack-webconsole -> codegram/rack-webconsole` and pull request 2 will give an output as:

```
mrbrdo/rack-webconsole -> codegram/rack-webconsole
Pull request nr ==> 2
File classifications ==>
	 lib/rack/webconsole/assets.rb
		 Operation - MODIFIED
		 Class - ED
Patch classification ==> ED
```

Additionally, the classification distribution will also be plotted.
To use this notebook for classification, you need to have:
*  The `source` and `target` repository names, 
*  The `list of pull requests`
*  The `cut off date`.

**NB:** Create the `Repos_files` and `Repos_results` directories before running the examples.