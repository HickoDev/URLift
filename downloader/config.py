"""Application paths and shared configuration."""

from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "URLift"
DATABASE_NAME = "history.sqlite3"


def default_download_dir() -> Path:
    """Return the default media download folder."""
    return Path.home() / "Downloads" / APP_NAME


def app_data_dir() -> Path:
    """Return a per-user folder for local app data."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def database_path() -> Path:
    """Return the SQLite database path used for download history."""
    return app_data_dir() / DATABASE_NAME

