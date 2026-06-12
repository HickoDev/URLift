"""Download engine built on the yt-dlp Python API."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtdlpDownloadError

from downloader.ffmpeg import find_ffmpeg
from downloader.formats import audio_format as audio_preset
from downloader.formats import video_format as video_preset


ProgressCallback = Callable[[str, float | None, str], None]


class URLiftDownloadError(Exception):
    """Raised when a download fails in a user-facing way."""


class FFmpegMissingError(URLiftDownloadError):
    """Raised when FFmpeg is required but unavailable."""


@dataclass(frozen=True)
class DownloadResult:
    title: str
    file_path: Path
    extension: str


def download_video(
    url: str,
    quality: str,
    output_dir: Path | str,
    progress_callback: ProgressCallback | None = None,
) -> DownloadResult:
    """Download a video using the requested quality preset."""
    preset = video_preset(quality)
    return _download(
        url=url,
        output_dir=Path(output_dir),
        format_selector=preset.ytdlp_format,
        expected_extension="mp4",
        progress_callback=progress_callback,
        postprocessors=[],
        force_aac_audio=True,
    )


def download_audio(
    url: str,
    audio_format: str,
    output_dir: Path | str,
    progress_callback: ProgressCallback | None = None,
) -> DownloadResult:
    """Download and extract audio using the requested audio format."""
    preset = audio_preset(audio_format)
    return _download(
        url=url,
        output_dir=Path(output_dir),
        format_selector=preset.ytdlp_format,
        expected_extension=preset.audio_codec or "mp3",
        progress_callback=progress_callback,
        postprocessors=[
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": preset.audio_codec,
            }
        ],
        force_aac_audio=False,
    )


def ensure_ffmpeg() -> None:
    """Raise a user-facing error if FFmpeg is not available on PATH."""
    if not find_ffmpeg():
        raise FFmpegMissingError("FFmpeg missing")


def _download(
    url: str,
    output_dir: Path,
    format_selector: str,
    expected_extension: str,
    progress_callback: ProgressCallback | None,
    postprocessors: list[dict[str, str | None]],
    force_aac_audio: bool,
) -> DownloadResult:
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        raise FFmpegMissingError("FFmpeg missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = time.time()

    def emit(status: str, percent: float | None = None, message: str | None = None) -> None:
        if progress_callback:
            progress_callback(status, percent, message or status)

    emit("Checking URL", 0.0)

    options = _ydl_options(
        output_dir=output_dir,
        format_selector=format_selector,
        postprocessors=postprocessors,
        progress_callback=emit,
        ffmpeg_path=ffmpeg_path,
    )

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
    except FFmpegMissingError:
        raise
    except YtdlpDownloadError as exc:
        message = _clean_error(str(exc))
        if "ffmpeg" in message.lower():
            raise FFmpegMissingError("FFmpeg missing") from exc
        raise URLiftDownloadError(message) from exc
    except Exception as exc:
        message = _clean_error(str(exc))
        if "ffmpeg" in message.lower():
            raise FFmpegMissingError("FFmpeg missing") from exc
        raise URLiftDownloadError(message or "Failed") from exc

    if not info:
        raise URLiftDownloadError("Unsupported URL")

    file_path = _resolve_file_path(info, output_dir, expected_extension, started_at)
    if force_aac_audio and file_path.suffix.lower() == ".mp4":
        emit("Converting", 100.0, "Converting")
        _convert_mp4_to_windows_compatible(file_path, ffmpeg_path)

    title = str(info.get("title") or file_path.stem)
    emit("Completed", 100.0)

    return DownloadResult(
        title=title,
        file_path=file_path,
        extension=file_path.suffix.lstrip("."),
    )


def _ydl_options(
    output_dir: Path,
    format_selector: str,
    postprocessors: list[dict[str, str | None]],
    progress_callback: Callable[[str, float | None, str | None], None],
    ffmpeg_path: Path,
) -> dict:
    return {
        "format": format_selector,
        "ffmpeg_location": str(ffmpeg_path),
        "outtmpl": {"default": str(output_dir / "%(title).180B [%(id)s].%(ext)s")},
        "noplaylist": True,
        "merge_output_format": "mp4",
        "windowsfilenames": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "progress_hooks": [_progress_hook(progress_callback)],
        "postprocessor_hooks": [_postprocessor_hook(progress_callback)],
        "postprocessors": postprocessors,
    }


def _progress_hook(
    callback: Callable[[str, float | None, str | None], None],
) -> Callable[[dict], None]:
    def hook(data: dict) -> None:
        status = data.get("status")
        if status == "downloading":
            percent = _percent_from_progress(data)
            message = "Downloading"
            if percent is not None:
                message = f"Downloading {percent:.1f}%"
            callback("Downloading", percent, message)
        elif status == "finished":
            callback("Converting", 100.0, "Converting")
        elif status == "error":
            callback("Failed", None, "Failed")

    return hook


def _postprocessor_hook(
    callback: Callable[[str, float | None, str | None], None],
) -> Callable[[dict], None]:
    def hook(data: dict) -> None:
        if data.get("status") in {"started", "processing"}:
            callback("Converting", 100.0, "Converting")
        elif data.get("status") == "finished":
            callback("Completed", 100.0, "Completed")

    return hook


def _percent_from_progress(data: dict) -> float | None:
    downloaded = data.get("downloaded_bytes")
    total = data.get("total_bytes") or data.get("total_bytes_estimate")
    if not downloaded or not total:
        return None
    return max(0.0, min(100.0, downloaded / total * 100))


def _resolve_file_path(
    info: dict,
    output_dir: Path,
    expected_extension: str,
    started_at: float,
) -> Path:
    candidates = _paths_from_info(info)
    for candidate in candidates:
        if candidate.exists():
            return candidate

    expected_suffix = f".{expected_extension.lower()}"
    recent_matches = [
        path
        for path in output_dir.glob(f"*{expected_suffix}")
        if path.is_file() and path.stat().st_mtime >= started_at - 2
    ]
    if recent_matches:
        return max(recent_matches, key=lambda path: path.stat().st_mtime)

    raise URLiftDownloadError("Completed file could not be found")


def _paths_from_info(info: dict) -> list[Path]:
    paths: list[Path] = []
    for key in ("filepath", "_filename", "filename"):
        value = info.get(key)
        if value:
            paths.append(Path(value))

    for item in info.get("requested_downloads") or []:
        for key in ("filepath", "_filename", "filename"):
            value = item.get(key)
            if value:
                paths.append(Path(value))

    return paths


def _convert_mp4_to_windows_compatible(file_path: Path, ffmpeg_path: Path) -> None:
    temp_path = file_path.with_name(f"{file_path.stem}.compat.tmp{file_path.suffix}")
    if temp_path.exists():
        temp_path.unlink()

    command = [
        str(ffmpeg_path),
        "-y",
        "-i",
        str(file_path),
        "-map",
        "0:v:0?",
        "-map",
        "0:a:0?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(temp_path),
    ]
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        startupinfo=startupinfo,
        creationflags=creationflags,
        check=False,
    )
    if result.returncode != 0:
        if temp_path.exists():
            temp_path.unlink()
        raise URLiftDownloadError(_clean_error(result.stderr) or "Failed")

    os.replace(temp_path, file_path)


def _clean_error(message: str) -> str:
    cleaned = message.strip()
    if cleaned.startswith("ERROR:"):
        cleaned = cleaned.removeprefix("ERROR:").strip()
    return cleaned or "Failed"
