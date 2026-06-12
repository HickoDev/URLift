"""Helpers for loading files in development and PyInstaller builds."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(name: str) -> Path:
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        return Path(bundle_dir) / name
    return Path(__file__).resolve().parents[1] / name

