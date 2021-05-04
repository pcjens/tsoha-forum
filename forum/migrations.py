"""Database migrations. Only upgrades are supported (i.e. not
downgrades). Launching multiple instances of the forum may cause
issues with duplicate migrations, so it's recommended to wait until
the first instance is up and running before starting the other
ones."""

from typing import Any
from flask import Flask

def run(app: Flask, sql_alchemy_db: Any) -> bool:
    """Checks the database's forum_version table for the current version,
    and applies any unapplied migration files from the migrations
    directory at the root of the repository. Returns False if all
    migrations can't be applied.
    """

    def query_forum_version() -> int:
        result = sql_alchemy_db.session.execute("select version from forum_schema_version")
        db_version: int = result.scalar()
        return db_version

    db_exists = sql_alchemy_db.session.execute("select exists ( select from "
                                               "information_schema.tables where "
                                               "table_name = 'forum_schema_version' )").scalar()
    if db_exists:
        db_version = query_forum_version()
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
            db_version = query_forum_version()
            if db_version != next_db_version:
                app.logger.error(("Abort! After running migration sql, "
                                  "the version is {}, "
                                  "instead of the expected {}."
                                  ).format(db_version, next_db_version))
                return False
            sql_alchemy_db.session.commit()
        except FileNotFoundError:
            app.logger.info("Database up-to-date.")
            break
    return True
