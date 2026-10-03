# Verification results

Prepared October 3, 2026 (America/New_York). The current automated run completed with **62 passed, 0 failed, 0 errors** in 186.44 seconds. The machine-readable report is `docs/test-results.xml`.

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=docs/test-results.xml
```

The suite covers:

- successful and failed login, protected pages, disabled accounts, role enforcement and administrator access;
- password hashing, CSRF, cookie flags, logout revocation, no open redirects, failed-login throttling and safe error handling;
- SQL injection probes, Jinja output encoding/XSS, rejected forged actor/time/role fields and request-size bounds;
- gallery entry/exit, room entry/exit, duplicate and out-of-order events, wrong-room exits, second-room attempts, capacity, stale replay and missing references;
- serialized concurrent writers, transaction rollback, server-clock reversal and audit behavior;
- schema export, seed idempotency, SQLite foreign keys and check constraints.

The application was also run through the browser at `http://127.0.0.1:5000`. Observed behaviors:

1. `employee11` logged in and reached the dashboard.
2. An employee recorded `ENTER_GALLERY` for Demo Guest Alex; the dashboard changed to one person inside.
3. The employee recorded `ENTER_ROOM` for Painting Room; the dashboard showed room occupancy 1 and the person's location.
4. A second room entry was rejected with the message to leave the current room first.
5. Typing `/admin/users` as an employee returned a generic 403 page.
6. `admin11` reached user management and the audit log; the log showed successful and rejected events, logout and authorization denial.
7. Reloading the app preserved the SQLite event and audit records.

Database checks on the prepared local instance reported `PRAGMA integrity_check = ok` and no foreign-key errors. The prepared local database contains fictional demo events for the browser evidence; use a new person or a clean copy for a presentation that needs an empty event ledger.

This evidence verifies the local implementation. It does not establish HTTPS deployment, Docker execution, production load resistance, an instructor correctness-oracle result, Week 8 authorized penetration testing, or later Break It/Fix It work.
