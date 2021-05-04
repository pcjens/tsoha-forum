# Deployment

Here's guides for running a tsoha-forum server.

## With Heroku

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

## Manual setup

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
leaking sensitive information. Outside of `localhost`, login
functionality won't even work without a secure reverse proxy, because
the cookies are restricted to secure connections.
