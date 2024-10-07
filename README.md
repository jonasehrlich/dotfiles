# dotfiles

This repository contains dotfiles, templates for dotfiles and a Python installer package.

## Requirements

Running the installer has a few expectations at the

The following executables are required:

* *python3* (3.10+) - required to run the install script
* *curl* - used by the install script to download / install tools
* *git* - used by the install script to download / install
* *sh* - used by the install script to execute installer scripts
* *zsh* - required to install oh-my-zsh

Automated installation of these basic packages is not supported at this point in time. Please use your OS package
manager to install them manually.

## Installation

Install the dotfiles in your environment using the interactive [`./install`](install) script.

``` sh
./install
```
