"""Update helpers for URLift and its yt-dlp engine."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from urllib.request import urlopen

from yt_dlp.version import __version__ as YTDLP_VERSION


APP_VERSION = "1.1.0"
PYPI_YTDLP_URL = "https://pypi.org/pypi/yt-dlp/json"


class UpdateError(Exception):
    """Raised when an update action cannot be completed."""


@dataclass(frozen=True)
class YtdlpUpdateInfo:
    installed_version: str
    latest_version: str

    @property
    def update_available(self) -> bool:
        return _version_key(self.installed_version) != _version_key(self.latest_version)


def installed_ytdlp_version() -> str:
    return YTDLP_VERSION


def check_ytdlp_update(timeout: int = 8) -> YtdlpUpdateInfo:
    """Check PyPI for the latest yt-dlp version."""
    try:
        with urlopen(PYPI_YTDLP_URL, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise UpdateError(f"Could not check yt-dlp updates: {exc}") from exc

    latest = str(payload.get("info", {}).get("version") or "").strip()
    if not latest:
        raise UpdateError("Could not read the latest yt-dlp version from PyPI.")

    return YtdlpUpdateInfo(installed_version=installed_ytdlp_version(), latest_version=latest)


def update_ytdlp() -> None:
    """Upgrade yt-dlp in the active Python environment."""
    if getattr(sys, "frozen", False):
        raise UpdateError("Packaged URLift builds cannot update yt-dlp in place. Install a newer URLift release instead.")

    command = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise UpdateError(result.stderr.strip() or result.stdout.strip() or "yt-dlp update failed.")


def _version_key(value: str) -> tuple[int | str, ...]:
    parts: list[int | str] = []
    for part in value.replace("-", ".").split("."):
        if part.isdigit():
            parts.append(int(part))
        elif part:
            parts.append(part)
    return tuple(parts)
