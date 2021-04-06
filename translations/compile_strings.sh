#!/bin/sh

# This script uses the msgfmt tool to compile the translated strings
# for the server to use.
set -e

if [ ! -e "compile_strings.sh" ]; then
    echo "Please run this script in the translations/ directory."
    exit 1
fi

msgfmt -o fi/LC_MESSAGES/tsohaforum.mo fi/LC_MESSAGES/tsohaforum.po
