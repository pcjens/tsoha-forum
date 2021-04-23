"""Validation methods for user-submitted data."""

import gzip
from typing import Set

def load_common_passwords() -> Set[str]:
    """Loads all rows from the uncompressed contents of forum/common_passwords.txt.gz
    and creates a set containing every row. Used in is_valid_password()."""

    passwords = set()
    with gzip.open("forum/common_passwords.txt.gz", "rt") as passwords_file:
        for password in passwords_file.readlines():
            passwords.add(password.strip())
    return passwords

COMMON_PASSWORDS = load_common_passwords()

def is_valid_username(username: str) -> bool:
    """Returns True if the username is allowed."""
    return len(username) > 1 and len(username) <= 20 and \
        not username[0].isspace() and not username[-1].isspace()

def is_valid_password(password: str) -> bool:
    """Returns True if the password is allowed."""
    return len(password) >= 10 and password not in COMMON_PASSWORDS

def is_valid_title(title: str) -> bool:
    """Returns True if the title is allowed."""

    max_length = 50
    if len(title) > 4 and title[0:2] == "Re: ":
        max_length = 54
    return len(title) > 1 and len(title) <= max_length and \
        not title[0].isspace() and not title[-1].isspace()
