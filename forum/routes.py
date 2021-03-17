import forum.db as db
from jinja2 import Environment, PackageLoader, select_autoescape
from flask import request_started, session, request, redirect, g
import gettext
import os

def setup(app):
    jinja_env = Environment(
        loader = PackageLoader("forum", "templates"),
        autoescape = select_autoescape(["html"]),
        extensions = ["jinja2.ext.i18n"]
    )
    jinja_env.policies["ext.i18n.trimmed"] = True

    translations = {}
    for lang in os.listdir("translations/"):
        if os.path.isdir("translations/{}".format(lang)):
            translations[lang] = gettext.translation("tsohaforum", "translations/", languages = [lang])
    translations["en"] = gettext.NullTranslations()
    default_lang = os.getenv("DEFAULT_LANG", default = "en")


    @request_started.connect_via(app)
    def handle_translations_for_request(sender):
        """At the start of each request, the correct translations are
        installed.

        TODO(optimization): Installing new translations for every request is probably quite slow.
        """
        if "lang" in session and session["lang"] in translations:
            jinja_env.install_gettext_translations(translations[session["lang"]], newstyle = True)
        else:
            jinja_env.install_gettext_translations(translations[default_lang], newstyle = True)

    @request_started.connect_via(app)
    def populate_global_template_vars(sender):
        g.global_template_vars = {
            "languages": list(translations),
            "current_language": session.get("lang", default_lang),
            "current_path": request.path
        }


    @app.route("/")
    def index():
        template = jinja_env.get_template("index.html")
        variables = { "message": db.get_hello() }
        variables.update(g.global_template_vars)
        return template.render(variables)

    @app.route("/change_language", methods = ["POST"])
    def change_language():
        app.logger.info("Change lang to: " + request.form["new_language"]);
        session["lang"] = request.form["new_language"]
        return redirect(request.form["redirect_url"])
