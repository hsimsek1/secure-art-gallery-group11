# Official requirements audit through Week 6

Prepared October 3, 2026. Authority: `F26_BIBIFI_Project.pdf` for the application and schedule; `Project_Phase1-1.pdf` for Phase I report content/format. Gustavo Pepe's `BIBIFI doc.docx` is a draft, not a replacement specification. All three originals remain unchanged. The project repository is https://github.com/hsimsek1/secure-art-gallery-group11.

Status meanings: IMPLEMENTED = present in code; DOCUMENTED = delivered design/report material; VERIFIED = execution evidence in verification_results.md; REMAINING = not completed. A local test does not establish production security or oracle compliance.

## Week 4 — official pages 4-5

| Required item | Delivered evidence | Status |
| --- | --- | --- |
| Team of two and team information | Group 11, Huseyin Simsek and Gustavo Pepe in README and reports | DOCUMENTED |
| GitHub repository | https://github.com/hsimsek1/secure-art-gallery-group11; required files are on `main` | VERIFIED: repository populated; collaborator/Canvas checks remain |
| Technology stack | README and Phase I overview | DOCUMENTED; installed locally |
| User roles | guest/employee/admin in User model and role matrix | IMPLEMENTED and VERIFIED |
| Application description | README; Phase I overview | DOCUMENTED |
| Functional requirements | FR-01 through FR-07 | DOCUMENTED |
| Business logic requirements | BL-01 through BL-10 | DOCUMENTED and tested |
| Initial security requirements | SEC-01 through SEC-12; implementation status explicit | DOCUMENTED |
| Development environment | .venv, requirements.txt, setup tool, database commands and tests | VERIFIED locally; partner machine remaining |

## Week 5 — official pages 3-5

| Required item | Delivered evidence | Status |
| --- | --- | --- |
| Architecture diagram | design_document.pdf page 1; architecture.svg | DOCUMENTED |
| DFD with external entities, processes, stores and flows | design_document.pdf page 2; dfd.svg | DOCUMENTED |
| Visible trust boundaries | Dashed TB1 client/server and TB2 persistence boundaries | DOCUMENTED |
| ERD/database design | design_document.pdf page 3; erd.svg; schema.sql | DOCUMENTED and schema tested |
| At least six specific STRIDE threats | T1-T6, each with component, scenario, impact and mitigation | DOCUMENTED |
| Explicit security requirements | SEC IDs in Phase I plus design implementation checklist | DOCUMENTED |
| Secure Design Document | docs/design_document.pdf | DELIVERED |

## Week 6 — official page 5

| Required item | Delivered evidence | Status |
| --- | --- | --- |
| Schema and initialization | Five SQLAlchemy tables, schema.sql, init-db and seed | IMPLEMENTED and VERIFIED |
| Backend/API | Flask route handlers and service layer; api.md | IMPLEMENTED and VERIFIED; separate REST API not required |
| User accounts | Environment-seeded accounts and admin creation | IMPLEMENTED and VERIFIED |
| Password hashing | Werkzeug salted scrypt | IMPLEMENTED and VERIFIED |
| Login/logout | CSRF-protected form routes | IMPLEMENTED and VERIFIED |
| Sessions/tokens | Flask-Login signed cookies, expiry and database session version | IMPLEMENTED and targeted checks VERIFIED |
| Roles and authorization | Route decorators, active checks, write-time revalidation | IMPLEMENTED and VERIFIED |
| Browser -> backend -> database milestone | Browser login, recorded movement, occupancy, history and role denial | See browser evidence in verification_results.md |

## Additional requested work delivered early

The official schedule places most of these in Week 7, with comprehensive security testing in Week 8. They were requested for the current package and do not conflict with the official requirements.

| Requested item | Evidence |
| --- | --- |
| Four movement event types | Event model, services.py and event form |
| All invalid-state protections | Parameterized transition tests, capacity, stale replay, concurrent writers and transaction rollback |
| Current gallery/room occupancy | Event reconstruction and dashboard |
| Persons and historical search | Persons form; filters for person/room/type/date; paginated history |
| Administration | User creation, role/active changes, administrator-only audit |
| Basic audit logging | Login success/failure, logout, accepted/rejected movements, person and user changes, practical authorization denials |
| Reasonable Week 6 security | Hashing, SQLAlchemy, Jinja escaping, CSRF, server validation, role enforcement, secret exclusion, generic errors and basic source throttling |
| Minimal frontend | Login, dashboard, logout, occupancy, event form, persons, history, admin users and audit |

## Corrections to Gustavo's draft

| Draft issue | Resolution |
| --- | --- |
| Five STRIDE threats | Added T5 Denial of Service with component/scenario/impact/mitigation |
| “Tempering” | Corrected to Tampering |
| Unmarked DFD trust boundary | Visible labeled dashed boundaries in the new DFD |
| “SECRET_KEY is 32 bits hex” | At least 32 random bytes; generated as 64 hex characters in ignored .env |
| Controls described without code evidence | Explicit IMPLEMENTED and PLANNED labels, with test scope and limitations |
| Room entry only checks “not in that room” | Requires gallery presence and no occupied room at all |
| Gallery exit only checks “in gallery” | Also requires no current room |
| State and audit triggers | Replaced by ledger-derived state and explicit transaction audit writes |
| Own-only guest queries without a person/account relationship | Aggregate-only guest access; individual movement history is staff-only |
| Secure cookies always enabled | Enabled for production HTTPS configuration; local loopback HTTP documented |
| Account lockout and redundant deny hook | Simple local source throttle and explicit route/write guards; stronger controls remain planned |

## Phase I handout audit — pages 1-3

| Report requirement | Evidence |
| --- | --- |
| Overview, intended users and operating environment | Phase I pages 1-2 |
| Authentication, authorization, input validation, logging | SEC-01 through SEC-11 |
| Data protection at rest and in transit | SEC-12 and explicit local limitations; no unsupported encryption claim |
| Non-functional requirements (optional extra credit) | NFR-01 through NFR-06 |
| CIA and accountability goals | Phase I page 5 |
| Risk assessment and prioritization | Ranked risk table, likelihood/impact and residual risk |
| Compliance considerations (optional extra credit) | Phase I page 6 and official-source references; no blanket compliance claim |
| Professional PDF report | docs/phase1_requirements.pdf, six pages, visually checked |
| Canvas submission | REMAINING: student verifies date and submits |

## Required repository structure — official page 7

`src/backend/`, `src/frontend/`, `database/schema.sql`, `database/seed.sql`, `tests/functional/`, `tests/security/`, `docs/design_document.pdf`, `docker-compose.yml`, `README.md` and `.gitignore` are supplied. Docker is recommended in section 1.1 but listed in the required structure; providing its files reconciles both statements. Docker execution remains unverified here.

## Remaining items and source conflicts

- Grant required collaborator access and submit the assigned documents in Canvas.
- Confirm the Phase I due date: the supplied handout is labeled Fall 2024, while the main course project is Fall 2026. Do not interpret September 25, 2024 as a current deadline.
- Complete partner-machine setup verification and both students' explanation/review.
- Optional container verification needs a Docker installation.
- Weeks 8-11 remain scheduled work: full security assessment, deployed TLS/backups/monitoring as applicable, instructor oracle, authorized assigned-target breaking, fixes and final demonstration. Their completion is not claimed.
