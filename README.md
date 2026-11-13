#!/usr/bin/env python3
"""
yt_music.py — Command-line interface version.

Parses command-line arguments, verifies system and package dependencies,
and delegates execution to yt_music_core.run().
For the graphical user interface version, refer to yt_music_gui.py.
"""

import argparse
import sys
from pathlib import Path

from deps import missing_dependencies


def parse_args() -> argparse.Namespace:
    """Configures and parses command-line arguments for the script."""
    p = argparse.ArgumentParser(
        description="Download and organize music from YouTube / YouTube Music.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  yt_music.py "https://youtube.com/playlist?list=..."
  yt_music.py -f flac -d ~/Music -s "https://music.youtube.com/watch?v=..."
  yt_music.py -c cookies.txt -e "https://youtube.com/playlist?list=..."
  yt_music.py -a "https://youtube.com/playlist?list=..."
  yt_music.py -s -g 2 -e -a -d ~/Music "https://youtube.com/playlist?list=..."
""",
    )
    p.add_argument("link", help="Target video or playlist URL")
    p.add_argument("-d", "--dir", type=Path, default=Path("."),
                   help="Target destination directory (default: current directory)")
    p.add_argument("-f", "--format", default="best",
                   help="Audio format: best, mp3, flac, m4a, opus... (default: best)")
    p.add_argument("-g", "--depth", type=int, default=1,
                   help="Search depth for existing local tracks (default: 1)")
    p.add_argument("-c", "--cookies", type=Path,
                   help="Path to cookies.txt file for authenticated downloads")
    p.add_argument("-a", "--archive", action="store_true",
                   help="Enable archive mode (records downloaded video IDs in .archive.txt)")
    p.add_argument("-e", "--export", action="store_true",
                   help="Export a report of missing tracks (missing.txt)")
    p.add_argument("-s", "--sort", action="store_true",
                   help="Sort downloaded tracks into artist subdirectories")
    return p.parse_args()


def main() -> None:
    """Main application entry point handling argument parsing, dependency validation, and execution."""
    args = parse_args()

    # Verify that all mandatory dependencies are present before proceeding
    problems = missing_dependencies()
    if problems:
        sys.exit("Critical Error:\n\n" + "\n\n".join(problems))

    # Import core logic only after verification: yt_dlp and mutagen are guaranteed to be available
    from core import Options, Reporter, run

    opts = Options(
        link=args.link,
        dir=args.dir,
        format=args.format,
        depth=args.depth,
        cookies=args.cookies,
        archive=args.archive,
        export=args.export,
        sort=args.sort,
    )
    run(opts, Reporter(log=print))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted.")
    except FileNotFoundError as exc:
        sys.exit(f"Error: {exc}")
