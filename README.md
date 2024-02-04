# dotfiles

These are my dotfiles. There are many like it, but these are mine

## Installation

To install the dotfiles in your environment use the interactive `./install` script.
The install script will do the following steps:

1. Create a `~/.gitconfig` file based on the template in [.gitconfig](.gitconfig)
2. Symlink the available [`.gitignore`](.gitignore) file to `~/.gitignore`
3. Symlink the  [`.tmux.conf`](.tmux.conf) to `~/.tmux.conf`
3. Symlink the  [`.pythonstartup`](.pythonstartup) to `~/.pythonstartup`
4. If requested, install [oh-my-zsh](https://github.com/ohmyzsh/ohmyzsh/) (**required for included [`.zshrc`](.zshrc)**)
5. If requested, install [fzf](https://github.com/junegunn/fzf) (**required for included [`.zshrc`](.zshrc)**)
6. If requested, install [pyenv](https://github.com/pyenv/pyenv) (**required for included [`.zshrc`](.zshrc)**)
7. If requested, install VSCode extensions listed in [`vscode-extensions.txt`](vscode-extensions.txt)
8. If requested, add the default included [`.zshrc`](.zshrc)

This installation process tries to achieve that the repository is always the single source of truth.
