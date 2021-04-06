"""Database access and maintenance functionality."""

from typing import Any, Optional, Callable, cast, List
from os import getenv
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash

class ForumDatabase:
    """Holder of database access, provider of persistent data."""

    def __init__(self, database: Any) -> None:
        self.database = database

    def logged_in(self, user_id: Optional[int]) -> bool:
        """Returns true if the given user id is not None, and is an actual user's user id."""
        if user_id is None:
            return False
        sql = "select * from users where user_id = :user_id"
        result = self.database.session.execute(sql, { "user_id": user_id }).fetchone()
        return result is not None

    def register(self, username: str, password: str) -> bool:
        """Creates a new user with the given username and password,
        if the username has not been taken. If it has, does nothing and returns False."""

        sql = "select user_id from users where username = :username"
        result = self.database.session.execute(sql, { "username": username }).fetchone()
        if result is not None:
            return False

        password_hash = generate_password_hash(password)
        sql = ("insert into users "
               "(username, password_hash, creation_time, password_set_time, latest_login_time) "
               "values (:username, :password_hash, 'now', 'now', null)")
        self.database.session.execute(sql, { "username": username, "password_hash": password_hash })
        self.database.session.commit()

        return True

    def login(self, username: str, password: str) -> Optional[int]:
        """Returns the user id for a user with a matching username and password.
        If no such combination is found, None is returned."""

        sql = "select user_id, password_hash from users where username = :username"
        result = self.database.session.execute(sql, { "username": username }).fetchone()
        if result is None:
            return None

        user_id, password_hash = result
        if password_hash is None: # Locked account
            return None
        if cast(Callable[[str, str], bool], check_password_hash)(password_hash, password):
            sql = "update users set latest_login_time = 'now' where user_id = :user_id"
            self.database.session.execute(sql, { "user_id": user_id })
            self.database.session.commit()
            return int(user_id) # reassuring the type system that user_id is an int
        return None

    def get_boards(self) -> List[Any]:
        """Returns a list of boards with the relevant information for index.html's listing."""

        sql = "select board_id, title, description from boards"
        results = self.database.session.execute(sql).fetchall()
        boards = []
        for result in results:
            board_id, title, description = result
            sql = "select count(*) from topics where parent_board_id = :board_id"
            topics = self.database.session.execute(sql, { "board_id": board_id }).fetchone()[0]
            sql = ("select count(*) from posts "
                   "join topics on parent_topic_id = topic_id "
                   "where parent_board_id = :board_id")
            posts = self.database.session.execute(sql, { "board_id": board_id }).fetchone()[0]
            boards.append((board_id, title, description, topics, posts))
        return boards

    def get_username(self, user_id: Optional[int]) -> Optional[str]:
        """Returns the username of the user with the given id, or None if there is no
        user with the id, or the id is None."""

        if user_id is None:
            return None
        sql = "select username from users where user_id = :user_id"
        result = self.database.session.execute(sql, { "user_id": user_id }).fetchone()
        if result is None:
            return None
        return str(result[0])


def run_migrations(app: Flask, sql_alchemy_db: Any) -> bool:
    """Checks the database's forum_version table for the current version,
    and applies any unapplied migration files from the migrations
    directory at the root of the repository. Returns False if all
    migrations can't be applied.
    """

    # TODO(stability): Should the database be locked somehow, during migrations? pylint: disable=W0511

    result = sql_alchemy_db.session.execute("select exists ( select from "
                                "information_schema.tables where "
                                "table_name = 'forum_schema_version' )")
    db_exists = result.fetchone()[0]
    if db_exists:
        result = sql_alchemy_db.session.execute("select version from forum_schema_version")
        db_version = result.fetchone()[0]
    else:
        db_version = -1

    app.logger.info("Database version: {}".format(db_version))
    while True:
        try:
            next_db_version = db_version + 1
            next_sql_path = "forum/migrations/version_{}.sql".format(next_db_version)
            with open(next_sql_path, "r") as migration_sql:
                app.logger.info("Migrating to version {}.".format(next_db_version))
                sql = migration_sql.read()
                sql_alchemy_db.session.execute(sql)
                result = sql_alchemy_db.session.execute("select version from forum_schema_version")
                db_version = result.fetchone()[0]
                if db_version != next_db_version:
                    app.logger.error(("Abort! After running migration sql, "
                                      "the version is {}, "
                                      "instead of the expected {}."
                                      ).format(db_version, next_db_version))
                    return False
                sql_alchemy_db.session.commit()
        except FileNotFoundError:
            break
    app.logger.info("Database up-to-date.")
    return True


def setup(app: Flask) -> Optional[ForumDatabase]:
    """Connects to the PostgreSQL database and runs migrations if needed,
    returning False on errors."""

    url = getenv("DATABASE_URL")
    if url is None or len(url) == 0:
        app.logger.error("DATABASE_URL is not specified!")
        return None
    url = url.replace("postgres://", "postgresql://")

    app.config["SQLALCHEMY_DATABASE_URI"] = url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    sql_alchemy_db = SQLAlchemy(app)
    migrations_successful = run_migrations(app, sql_alchemy_db)
    if not migrations_successful:
        return None

    return ForumDatabase(sql_alchemy_db)
