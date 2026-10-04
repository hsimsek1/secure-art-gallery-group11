"""Generate local-only Flask configuration and passwords once."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
instance = root / "instance"
config_path = instance / "config.py"
credentials_path = root / "local-credentials.txt"
if config_path.exists() or credentials_path.exists() or (root / ".env").exists():
    raise SystemExit("Local configuration already exists. No files changed.")

instance.mkdir(exist_ok=True)
passwords = {role: secrets.token_urlsafe(18) for role in ("admin", "employee", "guest")}
lines = [f"SECRET_KEY = {secrets.token_hex(32)!r}"]
lines += [f"SEED_{role.upper()}_PASSWORD = {password!r}" for role, password in passwords.items()]
with config_path.open("x", encoding="utf-8") as stream:
    stream.write("\n".join(lines) + "\n")
with credentials_path.open("x", encoding="utf-8") as stream:
    stream.write("Group 11 LOCAL DEMO ACCOUNTS - never upload this file\n")
    for role, password in passwords.items():
        stream.write(f"{role} | {role}11 | {password}\n")
print("Created ignored instance/config.py and local-credentials.txt. Keep both private.")
