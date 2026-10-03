# HTTP endpoint contracts

The application uses Flask form routes and HTML responses. This is a permitted backend architecture under F26_BIBIFI_Project.pdf section 1.1. No JSON API is claimed. POST content is form-encoded. Obtain `csrf_token` from the rendered form and send the session cookie with the POST. Never send passwords in URLs.

| Endpoint | Fields or filters | Successful result |
| --- | --- | --- |
| POST `/login` | username (1-40 chars), password (1-128), csrf_token | 302 dashboard; 401 generic failure; 429 source throttle |
| POST `/logout` | csrf_token only | 302 login; all old session versions for the account invalidated |
| GET `/dashboard` | None | 200 aggregate counts; staff also receive named occupancy |
| POST `/persons` | name (trimmed 1-80, no control characters), kind (`guest` or `employee`), csrf_token | 302 persons list; audit written |
| POST `/events` | person_id, event_type, room_id (blank for gallery), expected_version (latest event ID or 0), csrf_token | 302 dashboard on success; 409 for invalid state/stale form |
| GET `/history` | Optional person_id, room_id, event_type, start, end (YYYY-MM-DD UTC), page (positive) | 200; 25 records/page newest first; filter values preserved in page links |
| POST `/admin/users` | username (3-40 lowercase letters/digits/underscores), password (12-128), role (`guest`, `employee`, `admin`), csrf_token | 302 users list; duplicate username 409 |
| POST `/admin/users/<id>` | role, active (`0` or `1`), csrf_token | 302; self-update 409; missing user 404 |
| GET `/admin/audit` | Optional page | 200; 25 records/page newest first |

Valid event_type values: ENTER_GALLERY, LEAVE_GALLERY, ENTER_ROOM, LEAVE_ROOM. IDs must be positive integers of at most nine digits. expected_version also accepts zero. The server ignores no unexpected fields: it rejects them. `created_by`, `timestamp`, event ID and roles on normal forms are not writable. All roles come from Users and all event actors come from the authenticated session.

Unauthenticated protected requests redirect to login. An authenticated wrong-role request returns 403. Malformed input and CSRF failure return 400; oversized body 413; unsupported method 405. Missing routes return 404. Database errors return generic 503 and other unexpected errors generic 500. Unknown route/input details, exception text, file paths and SQL parameters are not returned.

Gallery conflict responses contain a plain-language reason and a fresh version token. Invalid event data is audited without logging the raw form. A stale rejection can follow another person's valid event because versioning covers the global ledger. Refresh before a new deliberate attempt. Browsers should follow the successful redirect to avoid accidental form resubmission.

Permission scope: employees can manage movements for all fictional tracked persons; guests cannot read any individual's history, even their own. Administrators can create/change user accounts and review logs, but no role can alter stored event/audit rows through an application endpoint. Direct database access is outside this trust boundary.
