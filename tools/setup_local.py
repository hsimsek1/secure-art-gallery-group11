"""Generate local-only secrets once; never overwrite existing configuration."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
env_path = root / ".env"
credentials_path = root / "local-credentials.txt"
if env_path.exists() or credentials_path.exists():
    raise SystemExit("Configuration already exists. No files changed.")
passwords = {role: secrets.token_urlsafe(18) for role in ("admin", "employee", "guest")}
lines = ["SECRET_KEY=" + secrets.token_hex(32), "APP_ENV=development"]
lines += [f"SEED_{role.upper()}_PASSWORD={password}" for role, password in passwords.items()]
with env_path.open("x", encoding="utf-8") as stream:
    stream.write("\n".join(lines) + "\n")
with credentials_path.open("x", encoding="utf-8") as stream:
    stream.write("Group 11 LOCAL DEMO ACCOUNTS - never upload this file\n")
    for role, password in passwords.items():
        stream.write(f"{role} | {role}11 | {password}\n")
print("Created ignored .env and local-credentials.txt. Keep both private.")
