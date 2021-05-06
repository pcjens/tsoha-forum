"""Database access and maintenance functionality."""

from typing import Any, Optional, Callable, cast, List
from os import getenv
from datetime import datetime
import secrets
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask import Flask
from werkzeug.security import generate_password_hash, check_password_hash
from mistletoe import HTMLRenderer, Document # type: ignore
import bleach
from forum.validation import is_valid_title, is_valid_post_content
from forum import migrations

class ForumDatabase:
    """Holder of database access, provider of persistent data."""

    def __init__(self, database: Any) -> None:
        self.database = database
        self.markdown_renderer = HTMLRenderer()

    def set_admin(self, username: str) -> None:
        """Makes the given user an administrator. Used to set admin rights via
        the ADMIN_USERNAME environment variable."""
        sql = ("insert into user_roles (role_id, user_id) "
               "values (1, (select user_id from users where username = :username)) "
               "on conflict do nothing")
        self.database.session.execute(sql, { "username": username })
        self.database.session.commit()

    def logged_in(self, user_id: Optional[int]) -> bool:
        """Returns true if the given user id is not None, and is an actual user's user id."""
        if user_id is None:
            return False
        sql = "select * from users where user_id = :user_id"
        result = self.database.session.execute(sql, { "user_id": user_id }).first()
        return result is not None

    def register(self, username: str, password: str) -> bool:
        """Creates a new user with the given username and password,
        if the username has not been taken. If it has, does nothing and returns False."""

        sql = "select * from users where username = :username"
        result = self.database.session.execute(sql, { "username": username }).first()
        if result is not None:
            return False

        password_hash = generate_password_hash(password)
        sql = ("insert into users "
               "(username, password_hash, creation_time, password_set_time, latest_login_time) "
               "values (:username, :password_hash, 'now', 'now', null)")
        self.database.session.execute(sql, { "username": username, "password_hash": password_hash })
        self.database.session.commit()

        return True

    def login(self, username: str, password: str) -> Optional[int]:
        """Returns the user id for a user with a matching username and password.
        If no such combination is found, None is returned."""

        sql = "select user_id, password_hash from users where username = :username"
        result = self.database.session.execute(sql, { "username": username }).first()
        if result is None:
            return None

        user_id, password_hash = result
        if password_hash is None: # Locked account
            return None
        if cast(Callable[[str, str], bool], check_password_hash)(password_hash, password):
            csrf_token = secrets.token_urlsafe()
            sql = ("update users set latest_login_time = 'now', csrf_token = :csrf_token "
                   "where user_id = :user_id")
            self.database.session.execute(sql, { "user_id": user_id, "csrf_token": csrf_token })
            self.database.session.commit()
            return int(user_id) # reassuring the type system that user_id is an int
        return None

    def logout(self, user_id: str) -> None:
        """Clears any session-specific database entries related to the user."""

        sql = "update users set csrf_token = null where user_id = :user_id"
        self.database.session.execute(sql, { "user_id": user_id })
        self.database.session.commit()

    def validate_csrf_token(self, user_id: int, csrf_token: str) -> bool:
        """Returns true if the user session has a matching CSRF-prevention token.

        Implemented according to the Synchronizer Token Pattern in the OWASP cheatsheet."""

        sql = "select count(*) from users where user_id = :user_id and csrf_token = :csrf_token"
        variables = { "user_id": user_id, "csrf_token": csrf_token }
        matches: int = self.database.session.execute(sql, variables).scalar()
        return matches == 1

    def get_csrf_token(self, user_id: int) -> Optional[str]:
        """Returns the synchronizer token to be served to the user, to prevent CSRF attacks.

        Implemented according to the Synchronizer Token Pattern in the OWASP cheatsheet."""

        sql = "select csrf_token from users where user_id = :user_id"
        token: Optional[str] = self.database.session.execute(sql, { "user_id": user_id }).scalar()
        return token

    def delete_post(self, post_id: int, user_id: int) -> None:
        """Deletes the post if the user owns it."""

        sql = ("delete from posts where author_user_id = :user_id and post_id = :post_id "
               "returning parent_topic_id")
        result = self.database.session.execute(sql, { "user_id": user_id, "post_id": post_id })
        topic_id = result.scalar()
        sql = "select count(*) = 0 from posts where parent_topic_id = :topic_id"
        emptied_topic = self.database.session.execute(sql, { "topic_id": topic_id }).scalar()
        if emptied_topic:
            sql = "delete from topics where topic_id = :topic_id"
            self.database.session.execute(sql, { "topic_id": topic_id })
        self.database.session.commit()

    def edit_post(self, post_id: int, user_id: int, title: str, content: str) -> bool:
        """Edits the topic with the new title and content."""

        sql = ("select count(*) = 1 from posts "
               "where post_id = :post_id and author_user_id = :user_id")
        result = self.database.session.execute(sql, { "post_id": post_id, "user_id": user_id })
        post_exists = result.scalar()
        if not post_exists:
            return False

        title_original = title
        title = bleach.clean(title.strip())
        content_original = content
        content = bleach.clean(content.strip()).replace("&gt;", ">")
        content = self.markdown_renderer.render(Document(content)).strip()
        if not is_valid_title(title) or not is_valid_post_content(content):
            return False

        sql = ("update posts set title = :title, title_original = :title_original, "
               "content = :content, content_original = :content_original, edit_time = 'now' "
               "where author_user_id = :user_id and post_id = :post_id")
        variables = {
            "user_id": user_id,
            "post_id": post_id,
            "title": title,
            "title_original": title_original,
            "content": content,
            "content_original": content_original
        }
        self.database.session.execute(sql, variables)
        self.database.session.commit()

        return True

    def create_post(self, topic_id: int, user_id: int, title: str, content: str) -> Optional[int]:
        """Creates a new topic in the given topic."""

        sql = "select count(*) from topics where topic_id = :topic_id"
        result = self.database.session.execute(sql, { "topic_id": topic_id }).scalar()
        if result == 0:
            return None

        title_original = title
        title = bleach.clean(title.strip())
        content_original = content
        content = bleach.clean(content.strip()).replace("&gt;", ">")
        content = self.markdown_renderer.render(Document(content)).strip()
        if not is_valid_title(title) or not is_valid_post_content(content):
            return None

        sql = ("insert into posts (parent_topic_id, author_user_id, title, title_original, "
               "content, content_original, creation_time) "
               "values (:topic_id, :user_id, :title, :title_original, "
               ":content, :content_original, 'now') "
               "returning post_id")
        variables = {
            "topic_id": topic_id,
            "user_id": user_id,
            "title": title,
            "title_original": title_original,
            "content": content,
            "content_original": content_original
        }
        post_id: int = self.database.session.execute(sql, variables).scalar()
        self.database.session.commit()

        return post_id

    def create_topic(self, board_id: int, user_id: int, title: str, content: str) -> Optional[int]:
        """Creates a new topic on the board, with the initial post containing
        the given title and content."""

        sql = "select count(*) from boards where board_id = :board_id"
        result = self.database.session.execute(sql, { "board_id": board_id }).scalar()
        if result == 0:
            return None

        sql = ("insert into topics (parent_board_id, sticky) values (:board_id, FALSE) "
               "returning topic_id")
        topic_id: int = self.database.session.execute(sql, { "board_id": board_id }).scalar()
        # Don't commit yet, as create_post may fail.
        post_id = self.create_post(topic_id, user_id, title, content)
        if post_id is None:
            return None
        # This is technically not needed, create_post already
        # committed, but future refactoring may change this.
        self.database.session.commit()
        return topic_id

    def get_boards(self) -> List[Any]:
        """Returns a list of boards with the relevant information for index.html's listing."""

        sql = "select board_id, title, description from boards"
        results = self.database.session.execute(sql).fetchall()
        boards = []
        for result in results:
            board_id, title, description = result
            sql = "select count(*) from topics where parent_board_id = :board_id"
            topics = self.database.session.execute(sql, { "board_id": board_id }).scalar()
            sql = ("select count(*) from posts "
                   "join topics on parent_topic_id = topic_id "
                   "where parent_board_id = :board_id")
            posts = self.database.session.execute(sql, { "board_id": board_id }).scalar()
            sql = ("select parent_topic_id, post_id, title, creation_time from posts "
                   "join topics on parent_topic_id = topic_id "
                   "where parent_board_id = :board_id "
                   "order by creation_time desc limit 1")
            result = self.database.session.execute(sql, { "board_id": board_id }).first()
            last_topic_id, last_post_id, last_title, last_time = (None, None, None, None)
            if result is not None:
                last_topic_id, last_post_id, last_title, last_time = result
            boards.append((board_id, title, description, topics, posts, last_topic_id,
                           last_post_id, last_title, last_time))
        return boards

    def get_topics(self, board_id: int) -> List[Any]:
        """Returns a list of topics for the given board."""

        sql = "select topic_id from topics where parent_board_id = :board_id"
        results = self.database.session.execute(sql, { "board_id": board_id }).fetchall()
        topics: List[Any] = []
        for result in results:
            topic_id = result[0]
            sql = ("select title, author_user_id from posts "
                   "where parent_topic_id = :topic_id "
                   "order by creation_time asc limit 1")
            result = self.database.session.execute(sql, { "topic_id": topic_id }).first()
            if result is None:
                # This shouldn't happen anymore, but old versions of
                # tsoha-forum could get the database in this state.
                continue
            title, author_user_id = result
            sql = ("select post_id, title, creation_time from posts "
                   "where parent_topic_id = :topic_id "
                   "order by creation_time desc limit 1")
            result = self.database.session.execute(sql, { "topic_id": topic_id }).first()
            last_post_id, last_title, last_time = (None, None, None)
            if result is not None:
                last_post_id, last_title, last_time = result
            sql = "select username from users where user_id = :user_id"
            author = self.database.session.execute(sql, { "user_id": author_user_id }).scalar()
            sql = "select count(*) - 1 from posts where parent_topic_id = :topic_id"
            replies = self.database.session.execute(sql, { "topic_id": topic_id }).scalar()
            topics.append((topic_id, title, author, replies, last_post_id, last_title, last_time))
        topics.sort(key = lambda row: cast(datetime, row[4]), reverse = True)
        return topics

    def get_posts(self, topic_id: int, user_id: int) -> List[Any]:
        """Returns a list of posts for the given topic."""
        # pylint: disable = R0914

        sql = ("select p.post_id, u.username, p.title, p.title_original, "
               "p.content, p.content_original, p.creation_time, p.edit_time, p.author_user_id "
               "from posts as p join users as u on author_user_id = user_id "
               "where parent_topic_id = :topic_id "
               "order by p.creation_time asc")
        results = self.database.session.execute(sql, { "topic_id": topic_id }).fetchall()
        posts: List[Any] = []
        for result in results:
            post_id, username, title, title_original, content, content_original, \
                creation_time, edit_time, author_user_id = result
            owned = author_user_id == user_id
            posts.append((post_id, username, title, title_original, content, content_original,
                          creation_time, edit_time, owned))
        return posts

    def search_posts(self, dictionary: str, search_string: str) -> List[Any]:
        """Returns a list of posts related to the given search string."""

        sql = ("select p.post_id, t.topic_id, b.board_id, u.username, "
               "p.title, p.content, p.creation_time, p.edit_time "
               "from posts p "
               "join users u on author_user_id = user_id "
               "join topics t on parent_topic_id = topic_id "
               "join boards b on parent_board_id = board_id "
               "where to_tsvector(:dict, p.title || ' ' || p.content) "
               "@@ plainto_tsquery(:dict, :query)")
        result = self.database.session.execute(sql, { "dict": dictionary, "query": search_string })
        posts: List[Any] = result.fetchall()
        return posts

    def get_username(self, user_id: Optional[int]) -> Optional[str]:
        """Returns the username of the user with the given id, or None if there is no
        user with the id, or the id is None."""

        if user_id is None:
            return None
        sql = "select username from users where user_id = :user_id"
        user: Optional[str] = self.database.session.execute(sql, { "user_id": user_id }).scalar()
        return user

    def get_board_name(self, board_id: Optional[int]) -> Optional[str]:
        """Returns the name of the board with the given id, or None if there is no
        board with the id, or the id is None."""

        if board_id is None:
            return None
        sql = "select title from boards where board_id = :board_id"
        title: Optional[str] = self.database.session.execute(sql, { "board_id": board_id }).scalar()
        return title


def setup(app: Flask) -> Optional[ForumDatabase]:
    """Connects to the PostgreSQL database and runs migrations if needed,
    returning False on errors."""

    url = getenv("DATABASE_URL")
    if url is None or len(url) == 0:
        app.logger.error("DATABASE_URL is not specified!")
        return None
    url = url.replace("postgres://", "postgresql://")

    app.config["SQLALCHEMY_DATABASE_URI"] = url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    sql_alchemy_db = SQLAlchemy(app)
    migrations_successful = migrations.run(app, sql_alchemy_db)
    if not migrations_successful:
        return None

    return ForumDatabase(sql_alchemy_db)
