# Secure Art Gallery Web Application

Kent State CS 4/53401 Secure Programming, Fall 2026. **BIBIFI Group 11: Huseyin Simsek and Gustavo Pepe.**

This beginner-friendly web application tracks guests and employees entering and leaving an art gallery and its rooms. It includes persistent records, authentication, server-side roles, validated movement events, occupancy, searchable history and basic security auditing.

**GitHub repository:** [hsimsek1/secure-art-gallery-group11](https://github.com/hsimsek1/secure-art-gallery-group11). The repository is public and is being populated with this local project. Original course PDFs and Gustavo's Word draft were read without modification.

## Current milestone

The official Week 6 milestone is backend + database + authentication/authorization. This project also implements requested Week 7 demonstration features and targeted early security checks. Full Week 8 security testing and the instructor's Week 9 oracle are **not complete**. See `docs/requirements_audit.md` and `docs/verification_results.md` for evidence and remaining work.

## Stack and architecture

Python 3.12, Flask, SQLite, Flask-SQLAlchemy/SQLAlchemy, Flask-Login, Flask-WTF, Jinja, HTML/CSS, Werkzeug scrypt, python-dotenv and Pytest. Optional Waitress and Docker support are included. No JavaScript framework, external CDN, separate API server or paid service is required.

```text
Browser -> Flask/Jinja web pages -> Python routes and movement service -> SQLAlchemy -> SQLite
```

The web and backend layers run in one Flask process. Data lives in the ignored `instance/gallery.db`, outside static files. Accounts are separate from tracked persons. There are five tables: `users`, `persons`, `rooms`, `gallery_events`, `audit_logs`. State is derived from the ordered event ledger. The design report includes architecture, DFD with trust boundaries, ERD and all six STRIDE categories.

## Installation on Windows PowerShell

Install Python 3.12 and open PowerShell inside this project folder. The `py` launcher commands below are for a normal Python installation; if your launcher is unavailable, use the full path of your Python 3.12 executable.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/setup_local.py
.\.venv\Scripts\python.exe -m flask --app src.backend init-db
.\.venv\Scripts\python.exe -m flask --app src.backend seed
.\.venv\Scripts\python.exe -m flask --app src.backend run --host=127.0.0.1 --port=5000
```

Open http://127.0.0.1:5000 in your browser. Stop the server with Ctrl+C. No environment activation or PowerShell execution-policy change is needed.

`setup_local.py` generates a signing secret using `secrets.token_hex(32)` and distinct random passwords. It refuses to overwrite existing `.env` or `local-credentials.txt`. Those files are ignored by Git and Docker. They already exist in the prepared local workspace; **skip setup_local.py there**. `init-db` creates missing tables without dropping existing data. `seed` preserves existing accounts/passwords and adds fictional reference records once. Do not delete the database to troubleshoot an ordinary startup problem.

## Installation on macOS or Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/setup_local.py
.venv/bin/python -m flask --app src.backend init-db
.venv/bin/python -m flask --app src.backend seed
.venv/bin/python -m flask --app src.backend run --host=127.0.0.1 --port=5000
```

## Roles and local test accounts

| Username | Role | Permissions |
| --- | --- | --- |
| `guest11` | User/Guest | Login/logout and aggregate gallery/room occupancy only |
| `employee11` | Employee | Guest permissions plus named occupancy, persons, event recording and event history |
| `admin11` | Administrator | Employee permissions plus user creation, roles, account status and audit log |

Read your generated passwords locally:

```powershell
Get-Content .\local-credentials.txt
```

There are deliberately no shared/default passwords in the repository. Keep passwords and `.env` out of commits, issue reports, screenshots and submissions. The database contains only scrypt hashes. Admins create users through `/admin/users`; public signup and password reset are outside this milestone. An admin cannot change their own role or disable their own account.

Seeded reference data: person 1, Demo Guest Alex; person 2, Demo Employee Sam; room 1, Painting Room (capacity 10); room 2, Sculpture Room (capacity 5). Both persons start outside on a fresh installation. Browser verification in this prepared workspace may have added demo events; create a new fictional person for a clean presentation.

## Database and movement rules

The models are in `src/backend/models.py`. `database/schema.sql` is a schema-only export; normal setup uses the Flask commands above. `database/seed.sql` contains only synthetic persons and rooms. User seed passwords are read from local environment settings and hashed at creation.

```powershell
.\.venv\Scripts\python.exe tools/export_schema.py
```

This command refreshes schema.sql after an intentional model change. It does not migrate an existing database; schema migrations are not implemented yet. Review changes before replacing any working database.

Legal transitions are outside -> gallery lobby -> one room -> gallery lobby -> outside. A person cannot enter twice, leave while outside, enter a room from outside, occupy two rooms, leave the wrong room, exceed capacity or leave the gallery while still in a room. Events and audit history have no application edit/delete operation.

Each form submits the latest ledger ID. `BEGIN IMMEDIATE` acquires SQLite's write reservation before reading state, validating and inserting an event plus its audit. Stale forms return 409; refresh and retry. Actor and timestamp always come from the server. The global version can reject an otherwise valid form when another person's movement was recorded; that conservative behavior keeps concurrency understandable.

## Endpoints

| Method and path | Who | Purpose |
| --- | --- | --- |
| GET/POST `/login` | Public | Login form / authenticate |
| POST `/logout` | Any logged-in account | Revoke that account's existing sessions |
| GET `/dashboard` | All three roles | Authorized current occupancy |
| GET/POST `/persons` | Employee, Admin | List/register tracked people |
| GET/POST `/events` | Employee, Admin | Form/record a validated movement |
| GET `/history` | Employee, Admin | Filter and paginate movement history |
| GET/POST `/admin/users` | Admin | List/create accounts |
| POST `/admin/users/<id>` | Admin | Change another account's role/status |
| GET `/admin/audit` | Admin | Paginated security log |

These are server-rendered form endpoints, not a JSON REST API. All POST requests require CSRF tokens. See `docs/api.md` for fields and status codes.

## Implemented security controls

- Salted scrypt password hashing; generic invalid-login responses; disabled-account checks.
- Database-loaded roles, route authorization, strict form allow-lists and revalidation before writes.
- Session clearing at login, HttpOnly/SameSite=Strict, 30-minute lifetime and database session-version revocation on logout/account changes.
- Global CSRF tokens on every POST form. All business changes use POST.
- SQLAlchemy bound queries, Jinja automatic output escaping and restrictive CSP.
- Server-side movement rules, write serialization, room capacity and stale-form protection.
- Audit success/failure, logout, accepted/rejected events, persons, administrative changes and authorization denials. No raw submitted passwords or tokens in logs.
- Generic error responses, including database outages; 16 KiB request/form limits, bounded form parts, 25-row history/audit pagination, basic failed-login source throttling.
- `.env`, credentials, local databases and virtual environments excluded from Git and container build contexts.

## Planned protections and limitations

- Local HTTP is loopback only. For network deployment, use a TLS reverse proxy, set `APP_ENV=production`, and verify HTTPS plus Secure cookies/HSTS. Changing that setting alone does not provide TLS.
- SQLite data and local configuration are not encrypted by the application. Host access controls, disk encryption, protected backups, restore drills, audit retention and monitoring remain deployment work.
- The IP/source throttle is deliberately basic. Distributed or simultaneous attempts, shared-IP users and long-term log growth need a broader Week 8 review. No per-account lockout or MFA is claimed.
- State calculation scans the full ledger. Person selectors/admin lists are unpaginated. This is a small classroom application, not a production-scale gallery system.
- A host/database administrator can alter SQLite files; application append-only records are not cryptographically tamper-proof.
- Logout revokes all sessions for an account. No separate per-device session list, password-reset flow or event-correction workflow exists.
- Do not collect real visitor data until privacy/retention/deployment requirements are resolved.
- Full Week 8 penetration testing, dependency-advisory review, instructor oracle testing and partner-machine installation remain future checks.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use isolated temporary SQLite files and randomly generated test passwords; they leave the demo database untouched. CSRF stays enabled during tests. Coverage includes every specifically requested test plus guest privacy, session revocation, throttling, input tampering, XSS/SQLi probes, rollback, schema/seed consistency, state capacity and concurrent writes. Exact latest results are in `docs/verification_results.md` and `docs/test-results.xml`.

## Optional serving and Docker

An alternative local server:

```powershell
.\.venv\Scripts\waitress-serve.exe --host=127.0.0.1 --port=5000 --call src.backend:create_app
```

The official required layout lists docker-compose.yml even though Docker is described as strongly recommended. Files are included. **Docker execution was not verified in this environment**; test these commands where Docker is installed:

```powershell
docker compose build
docker compose run --rm gallery python -m flask --app src.backend init-db
docker compose run --rm gallery python -m flask --app src.backend seed
docker compose up -d
docker compose logs gallery
docker compose down
```

Generate `.env` first. Container data uses a named volume separate from your local database; `down` preserves it. Never publish the service directly on the network without the planned deployment protections.

## Documents and presentation

- `docs/phase1_requirements.pdf`: Phase I requirements, roles, FR/BL/SEC/NFR IDs, CIA/accountability, risk and compliance.
- `docs/design_document.pdf`: architecture, DFD, trust boundaries, ERD, STRIDE and control status.
- Matching Markdown files: editable report sources; `docs/diagrams/*.svg`: vector diagrams.
- `docs/requirements_audit.md`: requirement-by-requirement official-source comparison.
- `docs/demo_and_submission.md`: professor demonstration and personal submission checklist.
- `docs/file_manifest.md`: every delivered project file and its purpose.

PDF sources can be rebuilt with `python tools/build_reports.py` in a documentation environment with ReportLab installed (not needed to run the web application). Review rendered pages after editing. The Phase I handout says Fall 2024/09-25; confirm the actual 2026 Canvas deadline rather than copying that old date.
