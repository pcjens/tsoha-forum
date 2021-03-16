from flask import Flask
import forum.db as db
import forum.routes as routes

app = Flask(__name__)
db.setup(app)
routes.setup(app)
