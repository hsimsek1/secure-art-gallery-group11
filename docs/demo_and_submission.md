# Professor demonstration and submission checklist

## A short demonstration script

Have the local server running, `local-credentials.txt` open privately, and the design report available. Use a new fictional person so the demo does not depend on previous test data. Allow about five minutes.

1. **Architecture and login:** "We are Group 11, Huseyin Simsek and Gustavo Pepe. The browser submits forms to Flask. Our service validates operations and SQLAlchemy persists them in SQLite." Log in as `guest11`. Show aggregate occupancy and explain why no person names or history are exposed. Log out.
2. **Employee workflow:** Log in as `employee11`, open Persons and create `Professor Demo Visitor` with type Guest. Note the new person ID. On Record event, select that person and ENTER_GALLERY with No room. Show gallery occupancy increase.
3. **Movement integrity:** Record ENTER_ROOM in Painting Room. Try ENTER_ROOM in Sculpture Room without leaving Painting Room. Show the rejection. Try LEAVE_GALLERY while still in the room; show that rejection too. After each response explicitly reselect your demo person because the simple form returns to its default selection.
4. **Complete the visit:** Record LEAVE_ROOM in Painting Room, then LEAVE_GALLERY with No room. Show restored occupancy. Open History, filter by the new person ID, and show the four accepted events. Rejected movements do not appear as accepted history.
5. **Server authorization:** While still an employee, type `http://127.0.0.1:5000/admin/users` into the address bar. Show 403. "Removing the link would not be enough; Flask checks the role on the server." Return to the dashboard and log out.
6. **Administration and accountability:** Log in as `admin11`. Show Manage users and Audit log, including accepted/rejected movements and the authorization failure. Do not display passwords or .env during the presentation. Explain that disabling another account revokes its existing sessions.
7. **Tests and design:** Show the latest Pytest results. Open the architecture, dashed trust boundaries, ERD and six STRIDE threats. Explain the four legal movement transitions and the transaction in `services.py`. State that full Week 8 security testing and instructor oracle results are still pending.

Optional persistence demonstration: log out, stop/restart the server without reinitializing or deleting the database, sign in and query the same history. Entries should persist.

## What both students should be able to explain

- Why a User account is different from a tracked Person.
- Why passwords are hashed instead of encrypted or stored directly.
- Why authorization belongs on routes and service writes, not only in navigation links.
- How a CSRF token differs from the login session.
- Why SECRET_KEY comes from at least 32 random bytes and stays out of Git.
- How the ledger reconstructs occupancy and how BEGIN IMMEDIATE plus expected_version prevents conflicting/stale requests.
- Why gallery occupancy includes room occupants, and why room exit must precede gallery exit.
- What audit entries prove and why a host administrator is still trusted.
- Which protections are implemented and which are planned.

## Personal checks before submission

- [ ] Confirm the course's actual Phase I deadline and upload location in Canvas; the provided handout says Fall 2024/09-25.
- [ ] Confirm both full names, Group 11 and course number on the report.
- [x] Create the GitHub repository: https://github.com/hsimsek1/secure-art-gallery-group11.
- [x] Insert the actual repository URL into README/report sources and rebuild/review the final PDF.
- [ ] Confirm the pushed files, required visibility and partner/instructor access.
- [ ] Inspect staged files: no .env, local passwords, databases, virtual environment or caches.
- [ ] Install from a clean checkout on Gustavo's computer, generate new local secrets and run initialization, seeding and tests.
- [ ] Run the demo as guest, employee and administrator; verify a manually typed admin URL returns 403 for employee.
- [ ] Review both PDFs and confirm every design/control claim matches the code.
- [ ] Rehearse the five-minute script; both members must explain major components.
- [ ] Confirm your instructor's policy on AI assistance and acknowledge assistance if required.
- [ ] Submit the Phase I PDF and other currently assigned deliverables to Canvas; verify the submission receipt.
- [ ] Keep Week 8 testing, Week 9 oracle/deployment checks and later BIBIFI phases on the schedule. Do not describe them as completed.
