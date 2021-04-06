"""Flask routes, template setup, language handling."""

# W0612 and W0613 are for unused variables and arguments. Flask's
# architecture causes a lot of false positives, so they're disabled.
# pylint: disable = W0612, W0613

# The pylint error E1136 seems to be broken for type annotations:
# https://github.com/PyCQA/pylint/issues/2822
# pylint: disable = E1136

import gettext
import os
from functools import wraps
from typing import Any, Dict, Callable
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

    def fill_and_render_template(template_path: str, variables: Dict[str, Any]) -> Any:
        lang = session.get("lang", default_lang)
        jinja_env = jinja_envs[lang]
        template = jinja_env.get_template(template_path)
        variables.update({
            "lang": lang,
            "languages": list(jinja_envs),
            "current_language": session.get("lang", default_lang),
            "current_path": request.path,
            "logged_in_user": session.get("username")
        })
        return template.render(variables)

    def templated(template_path: str, login_required: bool = True) -> Callable[..., Any]:
        def decorator(route: Callable[..., Dict[str, Any]]) -> Callable[..., Any]:
            @wraps(route)
            def decorated_function(*args: Any, **kwargs: Any) -> Any:
                if login_required and not database.logged_in(session.get("user_id")):
                    login_params = {}
                    if "error" in request.args:
                        login_params["error"] = request.args["error"]
                    return fill_and_render_template("login.html", login_params)
                return fill_and_render_template(template_path, route(*args, **kwargs))
            return decorated_function
        return decorator

    def redirect_form_error(error: str) -> Response:
        base_url = request.form["redirect_url"]
        param = "error=" + error
        if "?" in base_url:
            return redirect(base_url + "&" + param)
        return redirect(base_url + "?" + param)

    @app.route("/")
    @templated("index.html")
    def index() -> Any:
        return { "boards": database.get_boards() }

    @app.route("/change_language", methods = ["POST"])
    def change_language() -> Response:
        session["lang"] = request.form["new_language"]
        return redirect(request.form["redirect_url"])

    @app.route("/logout", methods = ["POST"])
    def logout() -> Response:
        if "user_id" in session:
            del session["user_id"]
        return redirect(request.form["redirect_url"])

    @app.route("/login", methods = ["POST"])
    def login() -> Response:
        user_id = database.login(request.form["username"], request.form["password"])
        if user_id is not None and database.logged_in(user_id):
            session["user_id"] = user_id
            session["username"] = database.get_username(user_id)
            return redirect(request.form["redirect_url"])
        return redirect_form_error("invalid_credentials")

    @app.route("/register", methods = ["POST"])
    def register() -> Any:
        username = request.form["username"]
        password = request.form["password"]
        if password != request.form["confirm-password"]:
            return redirect_form_error("passwords_dont_match")
        if database.register(username, password):
            user_id = database.login(username, password)
            session["user_id"] = user_id
            session["username"] = database.get_username(user_id)
            return redirect(request.form["redirect_url"])
        return redirect_form_error("username_taken")
