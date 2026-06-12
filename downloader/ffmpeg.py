"""FFmpeg discovery for system and bundled app environments."""

from __future__ import annotations

import shutil
from pathlib import Path


def find_ffmpeg() -> Path | None:
    """Return an FFmpeg executable path from PATH or the portable dependency."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return Path(system_ffmpeg)

    try:
        import imageio_ffmpeg
    except ImportError:
        return None

    ffmpeg_path = Path(imageio_ffmpeg.get_ffmpeg_exe())
    if ffmpeg_path.exists():
        return ffmpeg_path
    return None

