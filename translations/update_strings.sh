#!/bin/sh

# This script uses the xgettext tool to extract translatable strings
# from the templates, for use in translating the website to new
# languages.
set -e

if [ ! -e "update_strings.sh" ]; then
    echo "Please run this script in the translations/ directory."
    exit 1
fi

# Note: xgettext doesn't support HTML, but it seems to work ok with
# the language set to Python. It crashes if it's set to Javascript.
SRC_FILES="../forum/routes.py "../forum/templates/*
xgettext --language=python --omit-header --default-domain=tsohaforum --join-existing --output-dir=./fi/LC_MESSAGES/ $SRC_FILES
xgettext --language=python --omit-header --default-domain=tsohaforum --join-existing --output-dir=./en/LC_MESSAGES/ $SRC_FILES
