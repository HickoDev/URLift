"""Input validation helpers for URLift."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


PLATFORMS = (
    "YouTube",
    "TikTok",
    "Instagram",
    "Facebook",
    "Other / Auto-detect",
)

PLATFORM_DOMAINS = {
    "YouTube": ("youtube.com", "youtu.be", "music.youtube.com"),
    "TikTok": ("tiktok.com",),
    "Instagram": ("instagram.com",),
    "Facebook": ("facebook.com", "fb.watch"),
}


def validate_url(url: str, platform: str) -> tuple[bool, str]:
    """Validate basic URL shape and platform-domain hints."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "Invalid URL"

    if platform == "Other / Auto-detect":
        return True, ""

    host = parsed.netloc.lower()
    domains = PLATFORM_DOMAINS.get(platform, ())
    if domains and not any(host == domain or host.endswith(f".{domain}") for domain in domains):
        return False, "Unsupported URL"

    return True, ""


def validate_output_dir(path: str) -> tuple[bool, str]:
    """Validate that the selected output folder exists and is a directory."""
    if not path.strip():
        return False, "Invalid output folder"

    output_dir = Path(path).expanduser()
    if not output_dir.exists() or not output_dir.is_dir():
        return False, "Invalid output folder"

    return True, ""

