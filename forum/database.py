"""Database access and maintenance functionality."""

from typing import Any, Optional
from os import getenv
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask import Flask


class ForumDatabase:
    """Holder of database access, provider of persistent data."""

    def __init__(self, database: Any) -> None:
        self.database = database

    def first_row_value(self, sql: str) -> Any:
        """Returns the first row returned by the given SQL query."""
        return self.database.session.execute(sql).fetchone()[0]

    def get_hello(self) -> str:
        """Returns a friendly hello, which only works if the database works."""
        version = self.first_row_value("select version from forum_schema_version")
        return "Hi! My database schema version is {}.".format(version)


def run_migrations(app: Flask, sql_alchemy_db: Any) -> bool:
    """Checks the database's forum_version table for the current version,
    and applies any unapplied migration files from the migrations
    directory at the root of the repository. Returns False if all
    migrations can't be applied.
    """

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
