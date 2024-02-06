# Set PATH, MANPATH, etc., for Homebrew.' >> /Users/jehrlich/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

cpath+=( $(brew --prefix graphviz)/include/ )
library_path+=( $(brew --prefix graphviz)/lib/ )

source $(brew --prefix chruby)/share/chruby/chruby.sh
source $(brew --prefix chruby)/share/chruby/auto.sh
chruby ruby-3.1.3
