"""SQLite connection and schema setup for URLift."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from downloader.config import database_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    original_url TEXT NOT NULL,
    media_title TEXT NOT NULL,
    output_type TEXT NOT NULL,
    selected_quality TEXT NOT NULL,
    saved_file_path TEXT NOT NULL,
    file_extension TEXT NOT NULL,
    downloaded_at TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT
);
"""


def get_connection(path: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection and ensure the schema exists."""
    db_path = path or database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    ensure_schema(connection)
    return connection


def ensure_schema(connection: sqlite3.Connection) -> None:
    """Create required database tables if they do not exist."""
    connection.execute(SCHEMA)
    connection.commit()

