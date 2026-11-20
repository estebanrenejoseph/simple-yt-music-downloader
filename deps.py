#!/usr/bin/env python3
"""
deps.py — Dependency verification module, shared between the CLI and GUI versions.

This module intentionally does not import yt_dlp or mutagen so that it can run
successfully even when they are absent, allowing it to display a clear, user-friendly error message.
"""

import importlib.util
import shutil
import sys

# True inside a PyInstaller executable, where Python packages are bundled
FROZEN = getattr(sys, "frozen", False)


def missing_dependencies() -> list[str]:
    """Checks for required external Python packages and system binaries, returning a list of detected issues (empty list = all OK)."""
    problems: list[str] = []

    # Python packages are bundled in the frozen executable: only check them when running from source
    if not FROZEN:
        if importlib.util.find_spec("yt_dlp") is None:
            problems.append("The Python module 'yt-dlp' is missing.\nInstallation: pip install yt-dlp")

        if importlib.util.find_spec("mutagen") is None:
            problems.append("The Python module 'mutagen' is missing.\nInstallation: pip install mutagen")

    if shutil.which("ffmpeg") is None:
        problems.append(
            "'ffmpeg' could not be found (required by yt-dlp to extract and convert audio).\n"
            "Installation: sudo apt install ffmpeg (Linux), brew install ffmpeg (macOS), "
            "winget install ffmpeg (Windows)"
        )

    return problems
