from flask import Flask
from os import getenv
import forum.db as db
import forum.routes as routes

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
db.setup(app)
routes.setup(app)
