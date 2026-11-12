"""
Audit Log Persistence (Data Layer)
Pluggable storage backends for the incident audit log. Pick a backend by name with
`get_audit_store()`; to add a new backend, subclass `AuditStore` and register it in
`AUDIT_BACKENDS`.
"""

import csv
import os
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.defaults import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
FIELDS = [
    "date",
    "timestamp",
    "worker_id",
    "zone",
    "status",
    "is_violation",
    "confidence",
    "action",
]


def _normalize(entry: Dict[str, Any]) -> Dict[str, Any]:
    row = {f: entry.get(f) for f in FIELDS}
    row["is_violation"] = bool(row["is_violation"])
    try:
        row["confidence"] = float(row["confidence"]) if row["confidence"] is not None else None
    except (TypeError, ValueError):
        row["confidence"] = None
    return row


class AuditStore(ABC):
    """Interface every audit-log backend implements."""

    label: str = ""

    @abstractmethod
    def append(self, entry: Dict[str, Any]) -> None: ...

    @abstractmethod
    def load(self, limit: int = 5000) -> List[Dict[str, Any]]:
        """Return up to `limit` most recent entries, oldest first."""

    @abstractmethod
    def clear(self) -> None: ...

    @property
    @abstractmethod
    def location(self) -> str: ...


class CsvAuditStore(AuditStore):
    label = "CSV"

    FILENAME = "audit_log.csv"

    def __init__(self, path: Path = DATA_DIR / "audit_log.csv") -> None:
        self.path = Path(path)

    @property
    def location(self) -> str:
        return str(self.path)

    def append(self, entry: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not self.path.exists() or self.path.stat().st_size == 0
        with open(self.path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            if is_new:
                writer.writeheader()
            writer.writerow(_normalize(entry))

    def load(self, limit: int = 5000) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        with open(self.path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))[-limit:]
        out: List[Dict[str, Any]] = []
        for r in rows:
            r["is_violation"] = str(r.get("is_violation", "")).strip().lower() == "true"
            try:
                r["confidence"] = float(r["confidence"]) if r.get("confidence") else None
            except ValueError:
                r["confidence"] = None
            out.append(r)
        return out

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


class SqliteAuditStore(AuditStore):
    label = "SQL (SQLite)"

    FILENAME = "audit_log.db"

    def __init__(self, path: Path = DATA_DIR / "audit_log.db") -> None:
        self.path = Path(path)

    @property
    def location(self) -> str:
        return str(self.path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS audit_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, timestamp TEXT, "
            "worker_id TEXT, zone TEXT, status TEXT, is_violation INTEGER, "
            "confidence REAL, action TEXT)"
        )
        return conn

    def append(self, entry: Dict[str, Any]) -> None:
        row = _normalize(entry)
        conn = self._connect()
        try:
            with conn:  # commits on success
                conn.execute(
                    f"INSERT INTO audit_log ({', '.join(FIELDS)}) "
                    f"VALUES ({', '.join('?' for _ in FIELDS)})",
                    [int(row[f]) if f == "is_violation" else row[f] for f in FIELDS],
                )
        finally:
            conn.close()

    def load(self, limit: int = 5000) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        conn = self._connect()
        try:
            cur = conn.execute(
                f"SELECT {', '.join(FIELDS)} FROM audit_log ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = [dict(zip(FIELDS, r)) for r in cur.fetchall()]
        finally:
            conn.close()
        for r in rows:
            r["is_violation"] = bool(r["is_violation"])
        rows.reverse()
        return rows

    def clear(self) -> None:
        if not self.path.exists():
            return
        conn = self._connect()
        try:
            with conn:
                conn.execute("DELETE FROM audit_log")
        finally:
            conn.close()


# Registry: dropdown label -> store factory. Extend here to add backends.
AUDIT_BACKENDS: Dict[str, type] = {
    CsvAuditStore.label: CsvAuditStore,
    SqliteAuditStore.label: SqliteAuditStore,
}
DEFAULT_AUDIT_BACKEND = CsvAuditStore.label
DEFAULT_AUDIT_DIR = str(DATA_DIR)  # absolute path


def resolve_audit_dir(directory: Optional[str] = None) -> Path:
    """Expand `~`/env vars; relative paths are resolved from the project root."""
    if not directory or not str(directory).strip():
        return DATA_DIR
    path = Path(os.path.expandvars(os.path.expanduser(str(directory).strip())))
    return path if path.is_absolute() else PROJECT_ROOT / path


def validate_audit_dir(directory: Optional[str]) -> Optional[str]:
    """Return an error message if the folder can't be created/written, else None."""
    path = resolve_audit_dir(directory)
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok")
        probe.unlink()
    except OSError as exc:
        return f"{path}: {exc.strerror or exc}"
    return None


def get_audit_store(backend: str, directory: Optional[str] = None) -> AuditStore:
    """
    Return the store for a backend label (falls back to CSV for unknown names),
    saving inside `directory` (default: <project>/data).
    """
    cls = AUDIT_BACKENDS.get(backend, CsvAuditStore)
    return cls(resolve_audit_dir(directory) / cls.FILENAME)