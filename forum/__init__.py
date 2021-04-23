"""A forum server using Flask and SQLAlchemy."""

import sys
from os import getenv
from flask import Flask
import forum.database
import forum.routes

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["SESSION_COOKIE_SECURE"] = True
database = forum.database.setup(app)
if database is None:
    sys.exit(1)
forum.routes.setup(app, database)
