# PaReco Documentation

## Introduction
`PaReco`: Patched Clones and Missed Patches among the Divergent Variants of a Software Family. This tool relies on clone detection to mine cases of missed opportunity and effort duplication from a pool of patches.

## Extending ReDebug
This tool reuses the classification method of [ReDeBug](https://github.com/dbrumley/redebug). We extend their classification method to not only identify missed security patches, but to also identify missed, duplicated and split cases in any type of patch for the programming languages `Java`, `Python`, `PHP`, `Perl`, `C`, `ShellScript` and `Ruby`. We also look deeper into a patch and classify each file and each hunk in the .diff for that file.

## Publications
`PaReco` is complete open and free to be used and extended by researchers and developers. Incase you this tool in your publication, kindly cite the following papers:

1. Ramkisoen, P. K., Businge, J., van Bladel, B., Decan, A., Demeyer, S., De Roover, C., & Khomh, F. (2022, November). [PaReco: patched clones and missed patches among the divergent variants of a software family](https://dl.acm.org/doi/abs/10.1145/3540250.3549112). In Proceedings of the 30th ACM Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering (pp. 646-658).

## Contributing
