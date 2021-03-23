"""Flask routes, template setup, language handling."""

# W0612 and W0613 are for unused variables and arguments. Flask's
# architecture causes a lot of false positives, so they're disabled.
# pylint: disable = W0612, W0613

import gettext
import os
from typing import Any
from jinja2 import Environment, PackageLoader, select_autoescape
from flask import session, request, redirect, Flask
from werkzeug import Response
from forum.database import ForumDatabase

def setup(app: Flask, database: ForumDatabase) -> None:
    """Sets up Flask routes and the templating system.

    This is where the variables mentioned in the template files are set."""

    def make_jinja_env(lang: str, use_null_translations: bool) -> Any:
        jinja_env: Any = Environment(
            loader = PackageLoader("forum", "templates"),
            autoescape = select_autoescape(["html"]),
            extensions = ["jinja2.ext.i18n"]
        )
        jinja_env.policies["ext.i18n.trimmed"] = True
        if use_null_translations:
            translations = gettext.NullTranslations()
        else:
            translations = gettext.translation("tsohaforum", "translations/", languages = [lang])
        # Environment is so dynamic, even pylint doesn't like it.
        # pylint: disable = E1101
        jinja_env.install_gettext_translations(translations, newstyle = True)
        return jinja_env

    jinja_envs = {}
    for lang in os.listdir("translations/"):
        if os.path.isdir("translations/{}".format(lang)):
            jinja_envs[lang] = make_jinja_env(lang, False)
    jinja_envs["en"] = make_jinja_env("en", True)
    default_lang = os.getenv("DEFAULT_LANG", default = "en")

    @app.route("/")
    def index() -> Any:
        jinja_env = jinja_envs[session.get("lang", default_lang)]
        template = jinja_env.get_template("index.html")
        variables = {
            "message": database.get_hello(),
            "languages": list(jinja_envs),
            "current_language": session.get("lang", default_lang),
            "current_path": request.path
        }
        return template.render(variables)

    @app.route("/change_language", methods = ["POST"])
    def change_language() -> Response:
        app.logger.info("Change lang to: " + request.form["new_language"])
        session["lang"] = request.form["new_language"]
        return redirect(request.form["redirect_url"])
