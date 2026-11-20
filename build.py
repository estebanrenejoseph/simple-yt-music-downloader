#!/usr/bin/env python3
"""
build.py — Builds the single-file `symd` executable with PyInstaller.

Usage:
    pip install -r requirements.txt pyinstaller
    python3 build.py            (Windows: py build.py)

Result: dist/symd (dist/symd.exe on Windows).

PyInstaller does not cross-compile: run this script on each operating system
you want an executable for (Linux and Windows are covered by the GitHub
Actions workflow in .github/workflows/build.yml).

The executable is built as a console program (no --windowed) so that CLI
output works in a terminal. On Windows, symd.py hides the console window
when the program is started by a double-click.
"""

import importlib.util
import sys
from pathlib import Path

REQUIRED_MODULES = {
    "PyInstaller": "pip install pyinstaller",
    "yt_dlp": "pip install yt-dlp",
    "mutagen": "pip install mutagen",
    "customtkinter": "pip install customtkinter",
    "tkinter": "Debian/Ubuntu: sudo apt install python3-tk | Fedora: sudo dnf install python3-tkinter "
               "| macOS (Homebrew): brew install python-tk | Windows: reinstall Python with 'tcl/tk' enabled",
}


def preflight() -> None:
    """Stops early, with a clear message, if something needed for the build is missing."""
    missing = [
        f"  - {name}: {hint}"
        for name, hint in REQUIRED_MODULES.items()
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        sys.exit("Cannot build, missing requirements:\n" + "\n".join(missing))


def main() -> None:
    preflight()
    import PyInstaller.__main__ as pyinstaller

    here = Path(__file__).resolve().parent

    pyinstaller.run([
        str(here / "symd.py"),
        "--name", "symd",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--paths", str(here),
        # CustomTkinter ships theme JSON files and fonts that must be bundled
        "--collect-all", "customtkinter",
        # yt-dlp loads its extractors and post-processors dynamically
        "--collect-all", "yt_dlp",
        "--collect-submodules", "mutagen",
        "--distpath", str(here / "dist"),
        "--workpath", str(here / "build"),
        "--specpath", str(here / "build"),
    ])

    exe = "symd.exe" if sys.platform.startswith("win") else "symd"
    print(f"\nDone: {here / 'dist' / exe}")
    print(f"Quick check: {here / 'dist' / exe} --version")


if __name__ == "__main__":
    main()
