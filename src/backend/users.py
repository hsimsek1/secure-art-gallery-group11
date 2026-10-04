"""The small account object Flask-Login uses for the current user."""
from dataclasses import dataclass

from flask_login import UserMixin


@dataclass
class User(UserMixin):
    id: int
    username: str
    password_hash: str
    role: str
