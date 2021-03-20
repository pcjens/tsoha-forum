# tsoha-forum
A forum, written for tsoha.

## Features

- [ ] Users can register, login, and logout.
- [ ] The front page has of a list of boards, showing the amount of
      topics and messages in each, as well as the date of the latest
      message in said board.
- [ ] Users can create new topics.
- [ ] Users can post new messages in existing topics.
- [ ] Users can modify their own topics and messages.
- [ ] Users can search for messages containing a word.
- [ ] Administrators can add and remove boards.
- [ ] Administrators can create secret boards, and specify which users
      have access to it.

## Running

Requirements: Python 3, pip, and postgresql.

Run the following to install the prerequisites onto your machine:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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
