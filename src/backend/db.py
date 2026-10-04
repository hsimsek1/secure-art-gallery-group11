"""One SQLite connection per request, using Python's standard library."""
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def record_auth(action, user_id=None):
    connection = get_db()
    connection.execute(
        "INSERT INTO audit_logs (user_id, action, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (user_id, action),
    )
    connection.commit()
