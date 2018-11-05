#!/bin/bash

set -e

cd "$(dirname "$0")"

cp bash/Dotbash_profile ~/.bash_profile
cp bash/Dotbashrc ~/.bashrc
echo "Bash files installed..."

echo "source $(pwd)/vim/Dotvimrc" > ~/.vimrc
rm -rf ~/.vim
ln -s "$(pwd)/vim" ~/.vim
echo 'Vim files installed...'

