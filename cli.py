#!/usr/bin/env python3
"""
cli.py — Command-line interface for symd.

Parses arguments, verifies dependencies, then delegates to core.run().
Normally invoked through symd.py: `symd [options] <link>`.
"""

import argparse
import sys
from pathlib import Path

from deps import missing_dependencies


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Defines and parses the command-line arguments."""
    p = argparse.ArgumentParser(
        prog="symd",
        description="Download and organize music from YouTube / YouTube Music.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Run 'symd' with no argument (or 'symd --gui') to open the graphical interface.

Examples:
  symd "https://youtube.com/playlist?list=..."
  symd -f flac -d ~/Music -s "https://music.youtube.com/watch?v=..."
  symd -c cookies.txt -e "https://youtube.com/playlist?list=..."
  symd -a "https://youtube.com/playlist?list=..."
  symd -s -g 2 -e -a -d ~/Music "https://music.youtube.com/playlist?list=..."
""",
    )
    p.add_argument("link", help="Video or playlist link")
    p.add_argument("-d", "--dir", type=Path, default=Path("."),
                   help="Target directory for downloads (default: current directory)")
    p.add_argument("-f", "--format", default="best",
                   help="Audio format: best, mp3, flac, m4a, opus (default: best)")
    p.add_argument("-g", "--depth", type=int, default=1,
                   help="Search depth for existing local tracks (default: 1)")
    p.add_argument("-c", "--cookies", type=Path,
                   help="Path to a cookies.txt file for authenticated downloads")
    p.add_argument("-a", "--archive", action="store_true",
                   help="Enable archive mode (records downloaded IDs in .archive.txt)")
    p.add_argument("-e", "--export", action="store_true",
                   help="Export a missing tracks report (missing.txt)")
    p.add_argument("-s", "--sort", action="store_true",
                   help="Sort tracks into artist subdirectories")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Runs the full pipeline from the command line."""
    args = parse_args(argv)

    problems = missing_dependencies()
    if problems:
        sys.exit("Critical error:\n\n" + "\n\n".join(problems))

    # Imported after the check: yt_dlp and mutagen are guaranteed to be present
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

    try:
        run(opts, Reporter(log=print))
    except KeyboardInterrupt:
        sys.exit("\nInterrupted.")
    except FileNotFoundError as exc:
        sys.exit(f"Error: {exc}")


if __name__ == "__main__":
    main()
