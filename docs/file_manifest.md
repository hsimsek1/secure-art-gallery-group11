# Project file manifest

The following files are intended for review and GitHub upload. Generated caches, virtual environments, local databases, credentials and rendered QA images are ignored.

| Path | Purpose |
| --- | --- |
| `README.md` | Installation, roles, accounts, architecture, controls, tests, limits and Docker notes |
| `.gitignore`, `.dockerignore`, `.env.example` | Prevent secrets, local data and caches from entering Git or images |
| `requirements.txt`, `pytest.ini` | Pinned direct dependencies and test configuration |
| `Dockerfile`, `docker-compose.yml` | Optional reproducible container layout from the assignment |
| `src/backend/models.py` | Users, Persons, Rooms, GalleryEvents and AuditLogs models |
| `src/backend/services.py` | State reconstruction, serialized transactions and movement rules |
| `src/backend/__init__.py` | Flask factory, configuration, database commands, CSRF, sessions and safe errors |
| `src/backend/routes.py` | Login, logout, dashboard, events, persons, history and admin routes |
| `src/frontend/templates/*.html` | Minimal Jinja pages for all required demonstrations |
| `src/frontend/static/style.css` | Local accessible styling with no external CDN |
| `database/schema.sql` | Schema-only SQLite export |
| `database/seed.sql` | Fictional rooms and tracked persons; no credentials |
| `tests/conftest.py` | Isolated test app, CSRF and login helpers |
| `tests/functional/test_workflow.py` | Core workflow, database and administration tests |
| `tests/security/test_access.py` | Authentication, authorization, CSRF, session, input and output tests |
| `tests/security/test_movement.py` | Invalid transitions, capacity, replay and concurrent-write tests |
| `tests/security/test_integrity.py` | Audit/error/schema/rollback/production-config tests |
| `.github/workflows/tests.yml` | Pytest workflow for the GitHub repository |
| `tools/setup_local.py` | One-time local secret/password generator; refuses overwrite |
| `tools/export_schema.py` | Regenerates schema.sql from the models |
| `tools/build_reports.py` | Builds the two PDF reports and SVG diagrams |
| `docs/phase1_requirements.pdf` | Polished Phase I requirements report |
| `docs/design_document.pdf` | Secure design, DFD, trust boundaries, ERD, STRIDE and controls |
| `docs/phase1_requirements.md` | Editable source for the Phase I report |
| `docs/design_document.md` | Editable source for the design report |
| `docs/requirements_audit.md` | Traceability against the supplied official documents |
| `docs/api.md` | Endpoint fields, permissions and status behavior |
| `docs/demo_and_submission.md` | Professor demonstration and personal submission checklist |
| `docs/github_setup.md` | Safe steps to push and verify the Group 11 GitHub repository |
| `docs/verification_results.md` | Automated and browser verification evidence |
| `docs/test-results.xml` | JUnit result from the 62-test run |
| `docs/diagrams/*.svg` | Vector architecture, DFD and ERD source diagrams |
| `docs/screenshots/dashboard.png` | Browser smoke-test evidence |

Do not upload `.env`, `local-credentials.txt`, `instance/gallery.db`, `.venv`, `.pytest_cache`, `__pycache__` or `docs/.render`. The ignore checks were run locally and exclude them.
