# Secure Art Gallery Web Application

**BIBIFI Group 11 - Huseyin Simsek and Gustavo Pepe**

Kent State CS 4/53401, Secure Programming, Fall 2026

[GitHub repository](https://github.com/hsimsek1/secure-art-gallery-group11)

## Current milestone: Weeks 4-6

This version contains the team requirements, secure design, and a small working backend and database. Log in to view rooms loaded from SQLite. An administrator-only page demonstrates authorization. This satisfies the Week 6 demonstration: **Browser -> Flask -> SQLite with authentication**.

## Technology and structure

Python 3.12, Flask, Flask-SQLAlchemy/SQLAlchemy, Flask-Login, SQLite, Werkzeug password hashing, Jinja, HTML and CSS. Existing Flask-WTF handles CSRF; python-dotenv loads local secrets; pytest runs the tests.

- `src/backend/`: application setup, database models and routes.
- `src/frontend/`: login, room list and administrator demonstration templates.
- `database/`: schema and fictional seed records.
- `docs/`: requirements/design PDFs, editable Markdown and three SVG diagrams.
- `tests/functional/` and `tests/security/`: 14 milestone tests.
- `tools/`: generate local credentials, export the schema, rebuild the reports.

There are four tables: Users, Persons, Rooms and a small AuditLogs table for login/logout activity. Persons are seeded reference records only. Sessions use Flask signed cookies, so no session table is needed.

## Installation and database setup

Install Python 3.12, then open PowerShell in the repository:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/setup_local.py
.\.venv\Scripts\python.exe -m flask --app src.backend init-db
.\.venv\Scripts\python.exe -m flask --app src.backend seed
```

The setup script generates a local secret and three random passwords. It will not overwrite existing configuration. **If this workspace already has `.env` and `local-credentials.txt`, skip that script.** Initialization and seeding can be repeated without deleting existing records.

This simplified version uses ignored `instance/week6.db`. Any older `instance/gallery.db` remains untouched and is not used by this version. Reference data includes two fictional persons and Painting Room (capacity 10) and Sculpture Room (capacity 5).

For macOS/Linux, use `python3.12 -m venv .venv` and replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

## Run and log in

```powershell
.\.venv\Scripts\python.exe -m flask --app src.backend run --host=127.0.0.1 --port=5000
```

Open http://127.0.0.1:5000. Stop the server with Ctrl+C. Read your passwords in the local, ignored `local-credentials.txt`.

| Account | Role | Current access |
| --- | --- | --- |
| guest11 | User/Guest | Login, room list and logout |
| employee11 | Employee | Login, room list and logout |
| admin11 | Administrator | The same access plus the administrator page |

Employees have their own role, but the Week 6 room-list permissions match Guest permissions. Account management is not included. Accounts are created by the seed command, with Werkzeug scrypt password hashes stored in the database.

## Routes and authorization

| Method / path | Access | Purpose |
| --- | --- | --- |
| GET / | Public | Redirect to login or dashboard |
| GET, POST /login | Public | Display login form and authenticate |
| POST /logout | Logged-in user | End the current session |
| GET /dashboard | Logged-in user | Read and display room records |
| GET /admin | Administrator | Demonstrate the server-side role check |

These Flask routes are the backend; a separate REST API is not required. `login_required` protects the pages. The administrator route checks the role loaded from the database and returns 403 for Guest and Employee accounts. Hiding a navigation link is not the authorization control.

## Basic security

Passwords are salted and hashed. Sessions use a local signing secret, HttpOnly/SameSite cookies and a 30-minute lifetime. Login and logout forms require CSRF tokens. Login fields are validated, queries use SQLAlchemy bound values, and Jinja escapes output. Request bodies are limited to 16 KiB.

The small authentication log stores action, time and an optional user ID, never passwords or tokens. There is no audit browser. Secrets, credentials, databases and virtual environments are excluded from Git. This is a local HTTP demonstration with debugging off; it is not a production deployment or a complete security assessment.

## Tests and demonstration

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests use temporary databases and cover login for all three roles, invalid passwords, login protection, logout, password hashing, administrator access/denial, initialization, repeatable seed data, schema consistency, input validation and CSRF. GitHub Actions installs the pinned dependencies on Python 3.12 and runs the same command. `pytest.ini` uses pytest's default temporary-directory behavior.

To demonstrate Week 6: initialize and seed the database, log in as Employee, view the seeded rooms, open `/admin` to see access denied, log out, then log in as Administrator and open `/admin` successfully.

## Requirements and design

- [Team and requirements](docs/phase1_requirements.pdf): concise project scope, stack, roles, functional/security requirements and security goals.
- [Design document](docs/design_document.pdf): architecture, DFD, trust boundaries, ERD and six STRIDE threats.
- Matching `.md` files are the editable report sources; `docs/diagrams/` contains the SVG diagrams.

The scope follows **F26_BIBIFI_Project.pdf, pages 4-5**. Full gallery events, occupancy, history, persons/account management and state validation belong to the later application milestone and are absent here. Docker appears in the overall repository layout on page 7, but it is omitted from this Weeks 4-6 version because it is not required by that milestone's implementation checklist.

After changing the models, `python tools/export_schema.py` refreshes the schema file. To rebuild the PDFs and diagrams, run `python tools/build_reports.py` in a documentation environment with ReportLab available; ReportLab is not needed to run the application. Review the PDF layout after rebuilding.
