"""JSON-backed settings persistence for URLift."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from downloader.config import default_download_dir, settings_path
from downloader.formats import VIDEO_720P
from downloader.validators import PLATFORMS


@dataclass
class AppSettings:
    default_output_folder: str
    default_platform: str = "Other / Auto-detect"
    default_output_type: str = "Video"
    default_video_quality: str = VIDEO_720P
    default_audio_quality: str = "MP3 audio"
    open_file_after_download: bool = False
    open_folder_after_download: bool = False
    keep_history: bool = True
    convert_video_for_windows: bool = True


class SettingsRepository:
    """Load and save user preferences from a per-user JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings_path()

    def load(self) -> AppSettings:
        defaults = _default_settings()
        if not self.path.exists():
            return defaults

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return defaults

        merged = asdict(defaults)
        merged.update({key: value for key, value in data.items() if key in merged})
        return _normalize_settings(merged)

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(settings), indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _default_settings() -> AppSettings:
    return AppSettings(default_output_folder=str(default_download_dir()))


def _normalize_settings(data: dict[str, Any]) -> AppSettings:
    settings = AppSettings(**data)
    if settings.default_platform not in PLATFORMS:
        settings.default_platform = "Other / Auto-detect"
    if settings.default_output_type not in {"Video", "Audio only"}:
        settings.default_output_type = "Video"
    return settings
