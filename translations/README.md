# Translating tsoha-forum

This forum uses GNU gettext for its translations, and this is where
the translations reside.

## How to make a translation

Here's a short guide for making translations. Have a look at the
[fi](fi) directory as well, for a point of comparison. It contains the
Finnish translation.

1. Copy one of the existing translations, with the language code changed to your language's code:
   ```
   tsoha-forum/translations/<langcode>/LC_MESSAGES/
   ```
3. Fill out the "msgstr" entries in `tsohaforum.po`. The text after
   "msgid" is what you need to translate. If you need context, the
   line above msgid tells you the file the text is from, so you can go
   check there.
4. Run `sh compile_strings.sh`.
