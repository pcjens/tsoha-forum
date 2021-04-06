# tsoha-forum
Written for the database project course (abbreviated *tsoha*) at the
University of Helsinki.

## Features

The core idea of this project is to create a forum along the lines of
[phpBB](https://www.phpbb.com/community/), though smaller in scope. A
list of concrete features to be filled out as the project develops:

- [x] Users can register, login, and logout.
- [ ] The front page has of a list of boards. Each board should
      display the amount of topics and messages, and the date of the
      latest message on the board.
- [ ] Users can create new topics.
- [ ] Users can post new messages in existing topics.
- [ ] Users can modify their own topics and messages.
- [ ] Users can search for messages containing a word.
- [ ] Administrators can add and remove boards.
- [ ] Administrators can create secret boards, and specify which users
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
      ensuring that the entire code base is type-safe (within reason,
      some library interfaces require `Any` usage) and does not have
      obvious, pylint-recognized issues. This is implemented in the
      [static-analysis](https://github.com/pcjens/tsoha-forum/actions/workflows/static-analysis.yml)
      workflow, using pylint (general lints) and mypy (typechecking).

Additional fun features as time allows (I don't necessarily expect to
do any of these, let alone all of them):

- [ ] Optional Markdown in messages, and message preview.
- [ ] Polls attached to messages.
- [ ] Users can upload avatars that will display next to their
      messages.
- [ ] Users can have titles associated with their profile, assignable
      by administrators manually, or based on how many posts they have
      contributed to the forum.
- [ ] Users can follow and unfollow boards and topics, which will
      cause the interface to highlight boards and topics which have
      messages posted after the user previously visited said board or
      topic.
- [ ] Administrators can configure registration to be closed,
      invite-only, open with email confirmations, or completely open.
- [ ] Rules and Privacy Policy pages, and the agreement to those
      during registration.
- [ ] Moderation tools, you can never have enough of those:
  - [ ] Ability to remove and modify any user's posts.
  - [ ] Ability to lock topics.
  - [ ] Ability to remove avatars.
  - [ ] Ability to silence users for a duration.
  - [ ] Ability to ban users.
  - [ ] Ability to configure rate-limits for posting frequency.
  - [ ] A moderator group or per-user-permissions, to enable the
        creation of moderator accounts without administration rights.

## Running

### With Heroku

The repository is configured to work out-of-the-box with Heroku.

1. Create a new Heroku app, using this repository as the code for
   deployment. The `release` branch is recommended for this, and is
   the one deployed at
   [tsoha-pcjens-forum.herokuapp.com](https://tsoha-pcjens-forum.herokuapp.com/).
2. Add the Heroku Postgres addon.
3. Define `SECRET_KEY` in the Config Vars to some long string of
   secret characters. Can be generated with e.g.:
   ```sh
   openssl rand -hex 20
   ```
4. Deploy!

### Manually

Requirements: Python 3, pip, and PostgreSQL.

Run the following to install the prerequisites onto your machine:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# or: pip install flask flask-sqlalchemy jinja2 mypy pylint psycopg2-binary gunicorn python-dotenv
cp .env.sample .env
```

Configure `.env` to fit your system and needs. The user and database
specified in `DATABASE_URL` should exist before running the server.

Example: say your username is `foo`. Set DATABASE_URL to
`postgresql://foo@localhost/tsohadb`, and then create the role
("database user") and database as follows:

```sql
CREATE ROLE foo WITH LOGIN;
CREATE DATABASE tsohadb WITH OWNER foo;
```

Authentication by matching username might not work on all PostgreSQL
installs, in which case I recommend getting familiar with your
distribution's PostgreSQL setup beforehand.

After you have configured `.env` and your database, start the server
with:

```sh
FLASK_APP=forum flask run
```

After this initial setup, you only need to run `source
venv/bin/activate` before `flask run` to run the server again if you
log out (or close the terminal) in between sessions.

When deploying for production usage, there should be a reverse proxy
that accepts HTTPS connections in front of this server, to avoid
leaking sensitive information.

## License
This server software is distributed under the terms of the [GNU
AGPLv3](LICENSE) license.
