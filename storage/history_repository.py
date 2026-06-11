"""Persistence helpers for download history."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from storage.database import get_connection


@dataclass(frozen=True)
class HistoryItem:
    id: int
    platform: str
    original_url: str
    media_title: str
    output_type: str
    selected_quality: str
    saved_file_path: str
    file_extension: str
    downloaded_at: str
    status: str
    error_message: str | None


class HistoryRepository:
    """SQLite-backed history repository."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path

    def add_entry(
        self,
        *,
        platform: str,
        original_url: str,
        media_title: str,
        output_type: str,
        selected_quality: str,
        saved_file_path: str = "",
        file_extension: str = "",
        status: str = "completed",
        error_message: str | None = None,
    ) -> int:
        downloaded_at = datetime.now().astimezone().isoformat(timespec="seconds")
        with closing(get_connection(self.db_path)) as connection:
            cursor = connection.execute(
                """
                INSERT INTO download_history (
                    platform,
                    original_url,
                    media_title,
                    output_type,
                    selected_quality,
                    saved_file_path,
                    file_extension,
                    downloaded_at,
                    status,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    platform,
                    original_url,
                    media_title,
                    output_type,
                    selected_quality,
                    saved_file_path,
                    file_extension,
                    downloaded_at,
                    status,
                    error_message,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_status(
        self,
        item_id: int,
        *,
        status: str,
        media_title: str | None = None,
        saved_file_path: str | None = None,
        file_extension: str | None = None,
        error_message: str | None = None,
    ) -> None:
        with closing(get_connection(self.db_path)) as connection:
            connection.execute(
                """
                UPDATE download_history
                SET status = ?,
                    media_title = COALESCE(?, media_title),
                    saved_file_path = COALESCE(?, saved_file_path),
                    file_extension = COALESCE(?, file_extension),
                    error_message = ?
                WHERE id = ?
                """,
                (
                    status,
                    media_title,
                    saved_file_path,
                    file_extension,
                    error_message,
                    item_id,
                ),
            )
            connection.commit()

    def fetch_all(self) -> list[HistoryItem]:
        with closing(get_connection(self.db_path)) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    platform,
                    original_url,
                    media_title,
                    output_type,
                    selected_quality,
                    saved_file_path,
                    file_extension,
                    downloaded_at,
                    status,
                    error_message
                FROM download_history
                ORDER BY downloaded_at DESC, id DESC
                """
            ).fetchall()
        return [HistoryItem(**dict(row)) for row in rows]

    def delete_item(self, item_id: int) -> None:
        with closing(get_connection(self.db_path)) as connection:
            connection.execute("DELETE FROM download_history WHERE id = ?", (item_id,))
            connection.commit()

    def clear(self) -> None:
        with closing(get_connection(self.db_path)) as connection:
            connection.execute("DELETE FROM download_history")
            connection.commit()
