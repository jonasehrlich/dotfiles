# Brewfile

The *Brewfile* lists all applications installed through `brew install` and `brew install --cask`.

Create the *Brewfile* from the current environment:

```sh
brew bundle dump --describe --no-vscode --force --file Brewfile
```

Install the dependencies from the *Brewfile*

``` sh
brew bundle install
```
