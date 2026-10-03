"""Export the exact model schema without including application data or secrets."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateIndex, CreateTable
from src.backend.models import db

lines = ["-- Generated from src/backend/models.py by tools/export_schema.py.", "PRAGMA foreign_keys=ON;"]
for table in db.metadata.sorted_tables:
    lines.append(str(CreateTable(table).compile(dialect=sqlite.dialect())).strip() + ";")
    for index in sorted(table.indexes, key=lambda item: item.name):
        lines.append(str(CreateIndex(index).compile(dialect=sqlite.dialect())) + ";")
(ROOT / "database" / "schema.sql").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
print("Exported database/schema.sql (schema only).")
