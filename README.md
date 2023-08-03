# PaReco

## Introduction
`PaReco`: Patched Clones and Missed Patches among the Divergent Variants of a Software Family. This tool relies on clone detection to mine cases of missed opportunity and effort duplication from a pool of patches.

The complete [documentation](https://unlv-evol.github.io/pareco) of `PaReco` is available [here](https://unlv-evol.github.io/pareco)

## Extending ReDebug
This tool reuses the classification method of [ReDeBug](https://github.com/dbrumley/redebug). We extend their classification method to not only identify missed security patches, but to also identify missed, duplicated and split cases in any type of patch for the programming languages `Java`, `Python`, `PHP`, `Perl`, `C`, `ShellScript` and `Ruby`. We also look deeper into a patch and classify each file and each hunk in the .diff for that file.

## Directory Structure
```
.
├── LICENSE
├── README.md
├── docs
├── mkdocs.yml
├── requirements.txt
├── PaReco.py
├── src
│   ├── bin
│   ├── constants
│   ├── core
│   ├── utils
│   ├── legacy
│   ├── notebooks
│   └── tests
└── 
```
The **initial version** of `PaReco` is available[here](https://github.com/danielogen/patchesandmissedmatches) or in the `legacy` directory of this repository `/src/legacy`.

## Setting up PaReco
To setup and test `PaReco` tool on your local computer, following the steps below:
### Get the code
The easiest way is using the `git clone` command:
```
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

## Publications
`PaReco` is completely open and free to be used and extended by researchers and developers. Incase you use this tool in your publication, kindly cite the following papers:

1. Ramkisoen, P. K., Businge, J., van Bladel, B., Decan, A., Demeyer, S., De Roover, C., & Khomh, F. (2022, November). [PaReco: patched clones and missed patches among the divergent variants of a software family](https://dl.acm.org/doi/abs/10.1145/3540250.3549112). In _Proceedings of the 30th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (pp. 646-658)_.

## Contributing
Join us in building this tool. Contribution is encouraged from OSS community. If interested, take a look at our [contribution guidelines](https://)
## Issues 
Before reporting any issues, please visit the [issue reporting guidelines](https://) page.
