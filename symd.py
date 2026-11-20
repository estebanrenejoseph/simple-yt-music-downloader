#!/usr/bin/env python3
"""
symd — simple-yt-music-downloader, single entry point.

    symd                 opens the graphical interface
    symd --gui           same as above
    symd [options] LINK  runs the command-line interface (see `symd -h`)
    symd --version       prints versions (also checks the bundled libraries)

Build a standalone executable with `python3 build.py`.
"""

import os
import sys

__version__ = "1.0.0"


def _hide_own_console() -> None:
    """
    Windows only: hides the console window when the program was started by a
    double-click (it is then the only process attached to that console).
    When launched from an existing terminal, the terminal is left untouched.
    """
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        hwnd = kernel32.GetConsoleWindow()
        if not hwnd:
            return
        process_ids = (ctypes.c_uint * 2)()
        if kernel32.GetConsoleProcessList(process_ids, 2) == 1:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:  # noqa: BLE001 — cosmetic only, never block startup
        pass


def _print_version() -> None:
    """
    Prints symd and library versions. Importing core, mutagen and customtkinter
    also proves they are available, which makes this a handy smoke test for a
    freshly built executable (no display or ffmpeg needed).
    """
    import core  # noqa: F401 — imports yt_dlp and mutagen
    import customtkinter
    import mutagen
    import yt_dlp.version

    print(f"symd {__version__}")
    print(f"yt-dlp {yt_dlp.version.__version__}")
    print(f"mutagen {mutagen.version_string}")
    print(f"customtkinter {customtkinter.__version__}")


def main() -> None:
    args = sys.argv[1:]

    if args and args[0] in ("--version", "-V"):
        _print_version()
        return

    if not args or args[0] in ("--gui", "gui"):
        _hide_own_console()
        from gui import main as gui_main
        gui_main()
    else:
        from cli import main as cli_main
        cli_main(args)


if __name__ == "__main__":
    main()
