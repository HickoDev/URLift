"""yt-dlp format presets used by URLift."""

from __future__ import annotations

from dataclasses import dataclass


VIDEO_BEST = "Best video quality"
VIDEO_1080P = "1080p MP4"
VIDEO_720P = "720p MP4"
VIDEO_480P = "480p MP4"
MP3_AUDIO = "MP3 audio"
M4A_AUDIO = "M4A audio"

WINDOWS_COMPATIBLE_BEST = (
    "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/"
    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
    "best[ext=mp4][acodec^=mp4a]/best[ext=mp4]/best"
)


def _windows_compatible_height(max_height: int) -> str:
    return (
        f"bestvideo[height<={max_height}][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"best[height<={max_height}][ext=mp4][acodec^=mp4a]/"
        f"best[height<={max_height}][ext=mp4]/best[height<={max_height}]/best"
    )


VIDEO_PRESETS = {
    VIDEO_BEST: WINDOWS_COMPATIBLE_BEST,
    VIDEO_1080P: _windows_compatible_height(1080),
    VIDEO_720P: _windows_compatible_height(720),
    VIDEO_480P: _windows_compatible_height(480),
}

AUDIO_PRESETS = {
    MP3_AUDIO: "mp3",
    M4A_AUDIO: "m4a",
}


@dataclass(frozen=True)
class DownloadFormat:
    label: str
    ytdlp_format: str
    output_type: str
    audio_codec: str | None = None


def video_format(label: str) -> DownloadFormat:
    """Return the yt-dlp video format config for a UI label."""
    return DownloadFormat(
        label=label,
        ytdlp_format=VIDEO_PRESETS[label],
        output_type="video",
    )


def audio_format(label: str) -> DownloadFormat:
    """Return the yt-dlp audio format config for a UI label."""
    return DownloadFormat(
        label=label,
        ytdlp_format="bestaudio/best",
        output_type="audio",
        audio_codec=AUDIO_PRESETS[label],
    )
