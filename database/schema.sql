-- Generated from src/backend/models.py by tools/export_schema.py.

PRAGMA foreign_keys=ON;

CREATE TABLE persons (
	id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	kind VARCHAR(12) NOT NULL, 
	created_at DATETIME NOT NULL, 
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
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	session_version INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('guest','employee','admin')), 
	UNIQUE (username)
);

CREATE TABLE audit_logs (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	action VARCHAR(40) NOT NULL, 
	details VARCHAR(200) NOT NULL, 
	timestamp DATETIME NOT NULL, 
	result VARCHAR(12) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (result IN ('SUCCESS','REJECTED')), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp);

CREATE TABLE gallery_events (
	id INTEGER NOT NULL, 
	person_id INTEGER NOT NULL, 
	room_id INTEGER, 
	event_type VARCHAR(20) NOT NULL, 
	timestamp DATETIME NOT NULL, 
	created_by INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (event_type IN ('ENTER_GALLERY','LEAVE_GALLERY','ENTER_ROOM','LEAVE_ROOM')), 
	CHECK ((event_type IN ('ENTER_ROOM','LEAVE_ROOM') AND room_id IS NOT NULL) OR (event_type IN ('ENTER_GALLERY','LEAVE_GALLERY') AND room_id IS NULL)), 
	FOREIGN KEY(person_id) REFERENCES persons (id), 
	FOREIGN KEY(room_id) REFERENCES rooms (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE INDEX ix_gallery_events_person_id ON gallery_events (person_id);

CREATE INDEX ix_gallery_events_timestamp ON gallery_events (timestamp);
