# tsoha-forum

[![static-analysis](https://github.com/pcjens/tsoha-forum/actions/workflows/static-analysis.yml/badge.svg?branch=main)](https://github.com/pcjens/tsoha-forum/actions/workflows/static-analysis.yml)

Written for the database project course (abbreviated *tsoha*) at the
University of Helsinki.

See [DEPLOYMENT.md](DEPLOYMENT.md) for server installation / setup, as
well as administration instructions. For general information about the
forum, read on.

## Usage and testing

Register an account at: https://tsoha-pcjens-forum.herokuapp.com/

Once logged in, you can:
- Read messages and topics posted on the boards.
- Start a new topic on one of the boards.
- Post replies to the topics.
- Delete your own posts.
- Edit your topics and replies.
- Search for posts.

## Features

The core idea of this project is to create a forum along the lines of
[phpBB](https://www.phpbb.com/community/), though smaller in scope. A
list of concrete features to be filled out as the project develops:

- [x] Users can register, login, and logout.
- [x] The front page has of a list of boards. Each board should
      display the amount of topics and messages.
- [x] The board and topic listings show the title and date
      of the latest post on the board or topic.
- [x] Users can create new topics.
- [x] Users can post new messages in existing topics.
- [x] Users can modify their own topics and messages.
- [x] Messages are written in Markdown, and sanitized with
      [bleach](https://pypi.org/project/bleach/).
- [x] Users can search for messages powered by [PostgreSQL's full text
      search](https://www.postgresql.org/docs/9.5/textsearch.html).
  - The search uses the correct dictionary for the user's language,
    improving search results for non-English forums.
- [x] Users can have roles associated with their profile, assignable
      by administrators.
- [x] Administrators can add, remove, and edit boards.
- [x] Administrators can create secret boards, and specify which roles
      can access them.

Technical features / highlights:

- [x] The site is translatable to (most) other languages with
      gettext-style translations, and has an example translation for
      Finnish. This is achieved with Jinja2's support for
      gettext-based translations.
- [x] The forum is backwards-compatible database-wise, older versions
      of the database are automatically migrated to new versions. This
      functionality does not come from a library, it is implemented in
      [forum.database.run_migrations()](https://github.com/pcjens/tsoha-forum/blob/main/forum/database.py).
- [x] All of the code is typechecked and linted with GitHub Actions,
      ensuring that the entire codebase is type-safe (within reason,
      some library interfaces require `Any` usage) and does not have
      obvious, pylint-recognized issues. This is implemented in the
      [static-analysis](https://github.com/pcjens/tsoha-forum/actions/workflows/static-analysis.yml)
      workflow, using pylint (general lints) and mypy (typechecking).
- [x] User input is sanitized to avoid XSS attacks.
- [x] Forms are protected against CSRF attacks with the [Synchronizer
      Token
      Pattern](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#synchronizer-token-pattern).
      The synchronizer tokens are stored in the database, per-session.
- [x] A strict Content-Security-Policy as a last-ditch effort against
      XSS and similar security issues.

## License
This server software is distributed under the terms of the [GNU
AGPLv3](LICENSE) license.
