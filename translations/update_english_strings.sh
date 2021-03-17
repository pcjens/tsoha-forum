#!/bin/sh

# This script uses the xgettext tool to extract translatable strings
# from the templates, for use in translating the website to new
# languages.
set -e

if [ ! -e "update_english_strings.sh" ]; then
    echo "Please run this script in the translations/ directory."
    exit 1
fi

rm -f tsohaforum.po
# Note: xgettext doesn't support HTML, but it seems to work ok with
# the language set to Python. It crashes if it's set to Javascript.
xgettext --language=python --omit-header --default-domain=tsohaforum --output-dir=./ ../forum/templates/*

# Add an ending bit that declares that the po file is utf-8, to avoid
# encoding issues.
echo '' >> tsohaforum.po
echo '# leave this as is, it is for utf-8 support' >> tsohaforum.po
echo 'msgid ""' >> tsohaforum.po
echo 'msgstr "Content-Type: text/plain; charset=utf-8\n"' >> tsohaforum.po
