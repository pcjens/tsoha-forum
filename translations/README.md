# Translating tsoha-forum

This forum uses GNU gettext for its translations, and this is where
the translations reside.

## How to make a translation

Here's a short guide for making translations. Have a look at the
[fi](fi) directory as well, for a point of comparison. It contains the
Finnish translation.

1. Make a directory for your language in the following format:
   ```
   tsoha-forum/translations/<langcode>/LC_MESSAGES/
   ```
2. Copy [`tsohaforum.po`](tsohaforum.po) to the directory you just
   made.
3. Fill out the "msgstr" entries. The text after "msgid" is what you
   need to translate. If you need context, the line above msgid tells
   you the file the text is from, so you can go check there.
4. Move to the directory where the new .po file is, and run `msgfmt -o
   tsohaforum.mo tsohaforum.po`.
