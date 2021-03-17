import forum.db as db
from jinja2 import Environment, PackageLoader, select_autoescape
from flask import request_started, session, request, redirect, g
import gettext
import os

def setup(app):
    def make_jinja_env(lang, use_null_translations):
        jinja_env = Environment(
            loader = PackageLoader("forum", "templates"),
            autoescape = select_autoescape(["html"]),
            extensions = ["jinja2.ext.i18n"]
        )
        jinja_env.policies["ext.i18n.trimmed"] = True
        if use_null_translations:
            translations = gettext.NullTranslations()
        else:
            translations = gettext.translation("tsohaforum", "translations/", languages = [lang])
        jinja_env.install_gettext_translations(translations, newstyle = True)
        return jinja_env

    jinja_envs = {}
    for lang in os.listdir("translations/"):
        if os.path.isdir("translations/{}".format(lang)):
            jinja_envs[lang] = make_jinja_env(lang, False)
    jinja_envs["en"] = make_jinja_env("en", True)
    default_lang = os.getenv("DEFAULT_LANG", default = "en")

    @request_started.connect_via(app)
    def populate_global_template_vars(sender):
        g.global_template_vars = {
            "languages": list(jinja_envs),
            "current_language": session.get("lang", default_lang),
            "current_path": request.path
        }


    @app.route("/")
    def index():
        jinja_env = jinja_envs[session.get("lang", default_lang)]
        template = jinja_env.get_template("index.html")
        variables = { "message": db.get_hello() }
        variables.update(g.global_template_vars)
        return template.render(variables)

    @app.route("/change_language", methods = ["POST"])
    def change_language():
        app.logger.info("Change lang to: " + request.form["new_language"]);
        session["lang"] = request.form["new_language"]
        return redirect(request.form["redirect_url"])
