# PaReco Documentation

## Introduction
`PaReco`: Patched Clones and Missed Patches among the Divergent Variants of a Software Family. This tool relies on clone detection to mine cases of missed opportunity and effort duplication from a pool of patches.

## Extending ReDebug
This tool reuses the classification method of [ReDeBug](https://github.com/dbrumley/redebug). We extend their classification method to not only identify missed security patches, but to also identify missed, duplicated and split cases in any type of patch for the programming languages `Java`, `Python`, `PHP`, `Perl`, `C`, `ShellScript` and `Ruby`. We also look deeper into a patch and classify each file and each hunk in the .diff for that file.
