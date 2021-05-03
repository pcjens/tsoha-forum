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
from forum.validation import is_valid_username, is_valid_password

def setup(app: Flask, database: ForumDatabase) -> None: # pylint: disable = R0914, R0915
    """Sets up Flask routes and the templating system.

    This is where the variables mentioned in the template files are set."""

    def make_jinja_env(lang: str, use_null_translations: bool) -> Any:
        jinja_env: Any = Environment(
            loader = PackageLoader("forum", "templates"),
            autoescape = select_autoescape([]), # No autoescape, for rendering html in user posts.
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
        return jinja_env, translations

    jinja_envs = {}
    translations = {}
    for lang in os.listdir("translations/"):
        if os.path.isdir("translations/{}".format(lang)):
            jinja_envs[lang], translations[lang] = make_jinja_env(lang, False)
    default_lang = os.getenv("DEFAULT_LANG", default = "en")

    def fill_and_render_template(template_path: str, variables: Dict[str, Any]) -> Any:
        lang = session.get("lang", default_lang)
        jinja_env = jinja_envs[lang]
        template = jinja_env.get_template(template_path)
        logged_in_user = None
        csrf_token = None
        if "user_id" in session:
            logged_in_user = database.get_username(session["user_id"])
            csrf_token = database.get_csrf_token(session["user_id"])
        variables.update({
            "lang": lang,
            "languages": list(jinja_envs),
            "current_language": session.get("lang", default_lang),
            "current_path": request.full_path,
            "logged_in_user": logged_in_user,
            "csrf_token": csrf_token
        })
        return template.render(variables)

    def login_required(route: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(route)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if not database.logged_in(session.get("user_id")):
                login_params = {}
                if "error" in request.args:
                    login_params["error"] = request.args["error"]
                return fill_and_render_template("login.html", login_params), 401
            return route(*args, **kwargs)
        return decorated_function

    def csrf_token_required(route: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(route)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            if ("csrf_token" not in request.form or
                not database.validate_csrf_token(session["user_id"], request.form["csrf_token"])):
                return fill_and_render_template("error-403.html", {}), 403
            return route(*args, **kwargs)
        return decorated_function

    def templated(template_path: str) -> Callable[..., Any]:
        def decorator(route: Callable[..., Dict[str, Any]]) -> Callable[..., Any]:
            @wraps(route)
            def decorated_function(*args: Any, **kwargs: Any) -> Any:
                variables = route(*args, **kwargs)
                if "error_code" in variables:
                    code = variables["error_code"]
                    template = "error-{}.html".format(code)
                    return fill_and_render_template(template, variables), variables["error_code"]
                return fill_and_render_template(template_path, variables)
            return decorated_function
        return decorator

    def redirect_form_error(error: str) -> Response:
        base_url = request.form["redirect_url"]
        param = "error=" + error
        if "?" in base_url:
            return redirect(base_url + "&" + param)
        return redirect(base_url + "?" + param)

    @app.errorhandler(404)
    @templated("")
    def page_not_found(error: Any) -> Dict[str, int]:
        return { "error_code": 404 }

    @app.errorhandler(500)
    @templated("")
    def internal_server_error(error: Any) -> Dict[str, int]:
        return { "error_code": 500 }

    @app.route("/")
    @login_required
    @templated("index.html")
    def index() -> Any:
        return { "boards": database.get_boards() }

    @app.route("/board/<int:board_id>")
    @login_required
    @templated("board.html")
    def board(board_id: int) -> Any:
        board_name = database.get_board_name(board_id)
        if board_name is None:
            return { "error_code": 404 }
        return {
            "board_id": board_id,
            "board_name": board_name,
            "topics": database.get_topics(board_id)
        }

    @app.route("/board/<int:board_id>/topic/<int:topic_id>")
    @login_required
    @templated("topic.html")
    def topic(board_id: int, topic_id: int) -> Any:
        posts = database.get_posts(topic_id, session["user_id"])
        if len(posts) == 0:
            return { "error_code": 404 }
        return {
            "board_id": board_id,
            "board_name": database.get_board_name(board_id),
            "topic_id": topic_id,
            "topic_name": posts[0][2],
            "posts": posts
        }

    @app.route("/change_language", methods = ["POST"])
    def change_language() -> Response:
        session["lang"] = request.form["new_language"]
        return redirect(request.form["redirect_url"])

    @app.route("/logout", methods = ["POST"])
    @login_required
    def logout() -> Response:
        database.logout(session["user_id"])
        del session["user_id"]
        return redirect(request.form["redirect_url"])

    @app.route("/login", methods = ["POST"])
    def login() -> Response:
        user_id = database.login(request.form["username"], request.form["password"])
        if user_id is not None and database.logged_in(user_id):
            session["user_id"] = user_id
            return redirect(request.form["redirect_url"])
        return redirect_form_error("invalid_credentials")

    @app.route("/register", methods = ["POST"])
    def register() -> Any:
        username = request.form["username"]
        password = request.form["password"]
        if password != request.form["confirm-password"]:
            return redirect_form_error("passwords_dont_match")
        if not is_valid_username(username):
            return redirect_form_error("invalid_username")
        if not is_valid_password(password):
            return redirect_form_error("invalid_password")
        if database.register(username, password):
            user_id = database.login(username, password)
            session["user_id"] = user_id
            return redirect(request.form["redirect_url"])
        return redirect_form_error("username_taken")

    @app.route("/board/<int:board_id>", methods = ["POST"])
    @csrf_token_required
    @login_required
    def new_topic(board_id: int) -> Any:
        title = request.form["title"]
        content = request.form["content"]
        topic_id = database.create_topic(board_id, session["user_id"], title, content)
        if topic_id is None:
            return redirect(request.form["redirect_url"])
        return redirect("/board/{}/topic/{}".format(board_id, topic_id))

    @app.route("/board/<int:board_id>/topic/<int:topic_id>", methods = ["POST"])
    @csrf_token_required
    @login_required
    def new_post(board_id: int, topic_id: int) -> Any:
        title = request.form["title"]
        content = request.form["content"]
        post_id = database.create_post(topic_id, session["user_id"], title, content)
        if post_id is None:
            return redirect(request.form["redirect_url"])
        return redirect("/board/{}/topic/{}#{}".format(board_id, topic_id, post_id))

    @app.route("/board/<int:board_id>/topic/<int:topic_id>/edit/<int:post_id>", methods = ["POST"])
    @csrf_token_required
    @login_required
    def edit_post(board_id: int, topic_id: int, post_id: int) -> Any:
        if "confirm_edit" not in request.form:
            return redirect("/board/{}/topic/{}#{}".format(board_id, topic_id, post_id))
        title = request.form["title"]
        content = request.form["content"]
        database.edit_post(post_id, session["user_id"], title, content)
        return redirect("/board/{}/topic/{}#{}".format(board_id, topic_id, post_id))

    @app.route("/board/<int:board_id>/topic/<int:topic_id>/delete/<int:post_id>",
               methods = ["POST"])
    @csrf_token_required
    @login_required
    def delete_post(board_id: int, topic_id: int, post_id: int) -> Any:
        if "confirm_deletion" not in request.form:
            return redirect("/board/{}/topic/{}#{}".format(board_id, topic_id, post_id))
        database.delete_post(post_id, session["user_id"])
        posts_after = database.get_posts(topic_id, session["user_id"])
        if len(posts_after) > 0:
            return redirect("/board/{}/topic/{}".format(board_id, topic_id))
        return redirect("/board/{}".format(board_id))

    @app.route("/search", methods = ["GET"])
    @login_required
    @templated("search.html")
    def search() -> Dict[str, Any]:
        query_string = request.args.get("q")
        if query_string is None:
            return { "error_code": 404 }
        lang = session.get("lang", default_lang)
        def _(message: str) -> str:
            translated_string: str = translations[lang].gettext(message)
            return translated_string
        search_language = _("postgres-search-dictionary")
        return {
            "query_string": query_string,
            "posts": database.search_posts(search_language, query_string)
        }
