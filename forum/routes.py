import forum.db as db

def setup(app):
    @app.route("/")
    def index():
        return "Hello from SQL: " + db.get_hello()
