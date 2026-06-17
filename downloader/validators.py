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

PLATFORM_HELP = {
    "YouTube": "Use public YouTube URLs you own or have permission to download. Private, paid, or age-gated content may fail.",
    "TikTok": "Use public TikTok video URLs. Region blocks, login walls, and removed videos may fail.",
    "Instagram": "Use public Instagram post or reel URLs. Private accounts and login-only content are not supported.",
    "Facebook": "Use public Facebook video URLs. Private posts, groups, and login-only content are not supported.",
    "Other / Auto-detect": "Let yt-dlp auto-detect supported public URLs. URLift does not bypass platform restrictions.",
}


def platform_help(platform: str) -> str:
    """Return short user-facing guidance for a selected platform."""
    return PLATFORM_HELP.get(platform, PLATFORM_HELP["Other / Auto-detect"])


def platform_from_url(url: str) -> str | None:
    """Return a known platform name from a URL host, if one can be inferred."""
    host = urlparse(url.strip()).netloc.lower()
    for platform, domains in PLATFORM_DOMAINS.items():
        if any(host == domain or host.endswith(f".{domain}") for domain in domains):
            return platform
    return None


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
        return False, "URL does not match selected platform"

    return True, ""


def validate_output_dir(path: str) -> tuple[bool, str]:
    """Validate that the selected output folder exists and is a directory."""
    if not path.strip():
        return False, "Invalid output folder"

    output_dir = Path(path).expanduser()
    if not output_dir.exists() or not output_dir.is_dir():
        return False, "Invalid output folder"

    return True, ""
