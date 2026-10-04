"""A login account represented as an ordinary Python object."""
from flask_login import UserMixin


# UserMixin supplies the methods Flask-Login expects, such as get_id().
class User(UserMixin):
    def __init__(self, database_row):
        self.id = database_row["id"]
        self.username = database_row["username"]
        self.role = database_row["role"]
