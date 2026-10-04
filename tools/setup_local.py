"""Generate local-only Flask configuration and passwords once."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent.parent
instance = root / "instance"
config_path = instance / "config.py"
credentials_path = root / "local-credentials.txt"

if config_path.exists() or credentials_path.exists() or (root / ".env").exists():
    raise SystemExit("Local configuration already exists. No files changed.")

instance.mkdir(exist_ok=True)

passwords = {}
for role in ("admin", "employee", "guest"):
    passwords[role] = secrets.token_urlsafe(18)

secret_key = secrets.token_hex(32)
# repr() adds the quotes needed for a Python string in config.py.
config_lines = ["SECRET_KEY = " + repr(secret_key)]
for role, password in passwords.items():
    setting_name = "SEED_" + role.upper() + "_PASSWORD"
    config_lines.append(setting_name + " = " + repr(password))

# "x" creates a new file and refuses to overwrite an existing one.
with config_path.open("x", encoding="utf-8") as config_file:
    config_file.write("\n".join(config_lines) + "\n")

with credentials_path.open("x", encoding="utf-8") as credentials_file:
    credentials_file.write("Group 11 LOCAL DEMO ACCOUNTS - never upload this file\n")
    for role, password in passwords.items():
        username = role + "11"
        credentials_file.write(f"{role} | {username} | {password}\n")

print("Created ignored instance/config.py and local-credentials.txt. Keep both private.")
