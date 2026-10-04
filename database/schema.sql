-- Generated from src/backend/models.py by tools/export_schema.py.

PRAGMA foreign_keys=ON;

CREATE TABLE persons (
	id INTEGER NOT NULL,
	name VARCHAR(80) NOT NULL,
	kind VARCHAR(12) NOT NULL,
	PRIMARY KEY (id),
	CHECK (kind IN ('guest','employee'))
);

CREATE TABLE rooms (
	id INTEGER NOT NULL,
	name VARCHAR(80) NOT NULL,
	capacity INTEGER NOT NULL,
	PRIMARY KEY (id),
	CHECK (capacity > 0),
	UNIQUE (name)
);

CREATE TABLE users (
	id INTEGER NOT NULL,
	username VARCHAR(40) NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	role VARCHAR(12) NOT NULL,
	PRIMARY KEY (id),
	CHECK (role IN ('guest','employee','admin')),
	UNIQUE (username)
);

CREATE TABLE audit_logs (
	id INTEGER NOT NULL,
	user_id INTEGER,
	action VARCHAR(20) NOT NULL,
	timestamp DATETIME NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);
