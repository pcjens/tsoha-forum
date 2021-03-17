from os import getenv
from flask_sqlalchemy import SQLAlchemy

def run_migrations(app):
    """Checks the database's forum_version table for the current version,
    and applies any unapplied migration files from the migrations
    directory at the root of the repository.
    """

    result = db.session.execute("select exists ( select from information_schema.tables where table_name = 'forum_schema_version' )")
    db_exists = result.fetchone()[0]
    if db_exists:
        result = db.session.execute("select version from forum_schema_version")
        db_version = result.fetchone()[0]
    else:
        db_version = -1

    app.logger.info("Database version: {}".format(db_version))
    while True:
        try:
            next_db_version = db_version + 1
            with open("forum/migrations/version_{}.sql".format(next_db_version), "r") as migration_sql:
                app.logger.info("Migrating to version {}.".format(next_db_version))
                sql = migration_sql.read()
                db.session.execute(sql)
                result = db.session.execute("select version from forum_schema_version")
                db_version = result.fetchone()[0]
                if db_version != next_db_version:
                    app.logger.error("Abort! After running migration sql, the version is {}, instead of the expected {}.".format(db_version, next_db_version))
                    break
                db.session.commit()
        except FileNotFoundError:
            break
    app.logger.info("Database up-to-date.")


def setup(app):
    """Connects to the PostgreSQL database and runs migrations if needed."""

    global db
    app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)
    run_migrations(app)

def get_hello():
    version = db.session.execute("select version from forum_schema_version").fetchone()[0]
    return "Hi! My database schema version is {}.".format(version)
