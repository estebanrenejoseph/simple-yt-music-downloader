"""
yt_music_core.py — Business logic, independent of the interface (CLI or GUI):
  - Downloading (yt_dlp)
  - Sorting by artist (mutagen)
  - Missing tracks auditing

The interface passes an `Options` object and a `Reporter` to `run()`. The Reporter
receives logs, progress updates, and allows cancellation from another thread.

Dependencies (yt_dlp, mutagen, ffmpeg) are verified by deps.py prior
to importing this module.
"""

import os
import re
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import mutagen
import yt_dlp
from yt_dlp.utils import DownloadCancelled

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".opus", ".ogg", ".wav", ".aac", ".webm", ".mka"}
ID_PATTERN = re.compile(r"\[([a-zA-Z0-9_-]{11})\]")


# ------------------------------------------------------------------------------
# 1. OPTIONS AND REPORTER
# ------------------------------------------------------------------------------

@dataclass
class Options:
    link: str
    dir: Path = Path(".")
    format: str = "best"
    depth: int = 1
    cookies: Path | None = None
    archive: bool = False
    export: bool = False
    sort: bool = False


class Reporter:
    """
    Bridge between the business logic and the user interface.

    log      : callable(str)              — receives each log message
    progress : callable(float, str) | None — fraction 0..1 and status text
    cancel() can be invoked safely from any thread.
    """

    def __init__(
        self,
        log: Callable[[str], None] = print,
        progress: Callable[[float, str], None] | None = None,
    ):
        self._log = log
        self._progress = progress
        self._cancel = threading.Event()

    def log(self, message: str) -> None:
        self._log(message)

    def progress(self, fraction: float, text: str = "") -> None:
        if self._progress:
            self._progress(max(0.0, min(1.0, fraction)), text)

    def cancel(self) -> None:
        self._cancel.set()

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()


class _YdlLogger:
    """Redirects yt_dlp internal log messages to the Reporter."""

    def __init__(self, reporter: Reporter):
        self.reporter = reporter

    def debug(self, msg: str) -> None:
        # yt_dlp also sends general informational messages through debug()
        if not msg.startswith("[debug] "):
            self.reporter.log(msg)

    def info(self, msg: str) -> None:
        self.reporter.log(msg)

    def warning(self, msg: str) -> None:
        self.reporter.log("Warning: " + msg.removeprefix("WARNING: "))

    def error(self, msg: str) -> None:
        self.reporter.log("Error: " + msg.removeprefix("ERROR: "))


# ------------------------------------------------------------------------------
# 2. DOWNLOADING
# ------------------------------------------------------------------------------

def download(opts: Options, reporter: Reporter) -> list[Path]:
    """Downloads the target link and returns the list of successfully produced file paths."""
    downloaded: list[Path] = []

    def progress_hook(d):
        if reporter.cancelled:
            raise DownloadCancelled("Cancelled by user")
        if d["status"] not in ("downloading", "finished"):
            return
        info = d.get("info_dict") or {}
        index = info.get("playlist_index") or 1
        total = info.get("n_entries") or info.get("playlist_count") or 1
        size = d.get("total_bytes") or d.get("total_bytes_estimate")
        if d["status"] == "finished":
            track_fraction = 1.0
        elif size:
            track_fraction = (d.get("downloaded_bytes") or 0) / size
        else:
            track_fraction = 0.0
        reporter.progress(
            ((index - 1) + track_fraction) / total,
            f"[{index}/{total}] {info.get('title', '')}",
        )

    def pp_hook(d):
        # The final post-processor (MoveFiles) provides the definitive target file path
        if d["status"] == "finished" and d["postprocessor"] == "MoveFiles":
            path = Path(d["info_dict"]["filepath"])
            downloaded.append(path)
            reporter.log(f"✔ {path.name}")

    ydl_opts = {
        "paths": {"home": str(opts.dir)},
        "outtmpl": "%(title)s [%(id)s].%(ext)s",
        "format": "bestaudio/best",
        "overwrites": False,
        "ignoreerrors": True,
        "writethumbnail": True,
        "noprogress": True,  # Progress reporting is handled via custom progress_hooks
        "logger": _YdlLogger(reporter),
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [pp_hook],
        "postprocessors": [
            {"key": "FFmpegExtractAudio",
             "preferredcodec": opts.format,
             "preferredquality": "0"},
            {"key": "FFmpegMetadata", "add_metadata": True},
            {"key": "EmbedThumbnail"},
        ],
    }
    if opts.archive:
        ydl_opts["download_archive"] = str(opts.dir / ".archive.txt")
    if opts.cookies:
        ydl_opts["cookiefile"] = str(opts.cookies)

    reporter.log("Starting download process...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([opts.link])
    except DownloadCancelled:
        reporter.log("Download interrupted.")

    return downloaded


# ------------------------------------------------------------------------------
# 3. SORTING BY ARTIST
# ------------------------------------------------------------------------------

def read_artist(path: Path) -> str:
    """Reads the artist metadata tag from an audio file using mutagen, defaulting to 'Artist Unknown'."""
    try:
        audio = mutagen.File(path, easy=True)
        if audio and audio.get("artist"):
            return audio["artist"][0]
    except Exception:
        pass
    return "Artist Unknown"


def sort_by_artist(files: list[Path], root: Path, reporter: Reporter) -> None:
    """Sorts downloaded audio files into dedicated subdirectories named after their respective artists."""
    reporter.log("Sorting audio files by artist...")
    for f in files:
        if not f.is_file():
            continue
        artist_dir = root / read_artist(f).replace("/", "-")
        artist_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), str(artist_dir / f.name))
        reporter.log(f"→ {artist_dir.name}/{f.name}")


# ------------------------------------------------------------------------------
# 4. MISSING TRACKS AUDIT
# ------------------------------------------------------------------------------

def online_tracks(opts: Options, reporter: Reporter) -> dict[str, str]:
    """Extracts all video IDs and titles from the online playlist or video link without downloading."""
    ydl_opts = {
        "extract_flat": True,
        "ignoreerrors": True,
        "noprogress": True,
        "logger": _YdlLogger(reporter),
    }
    if opts.cookies:
        ydl_opts["cookiefile"] = str(opts.cookies)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(opts.link, download=False)
    if not info:
        return {}
    entries = info.get("entries") or [info]
    return {e["id"]: e.get("title", "") for e in entries if e and e.get("id")}


def local_ids(root: Path, depth: int, fmt: str) -> set[str]:
    """Recursively scans the local directory up to a given search depth to collect existing video IDs from filenames."""
    ids = set()
    wanted = AUDIO_EXTENSIONS if fmt == "best" else {f".{fmt.lower()}"}
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        level = len(Path(dirpath).relative_to(root).parts) + 1  # equivalent to find -maxdepth
        if level >= depth:
            dirnames.clear()
        for name in filenames:
            if Path(name).suffix.lower() in wanted:
                m = ID_PATTERN.search(name)
                if m:
                    ids.add(m.group(1))
    return ids


def audit_missing(opts: Options, reporter: Reporter) -> list[tuple[str, str]]:
    """Compares online tracks against local files, exports missing ones to missing.txt, and logs the report."""
    reporter.log("Auditing missing tracks...")
    online = online_tracks(opts, reporter)
    have = local_ids(opts.dir, opts.depth, opts.format)
    missing = sorted((i, t) for i, t in online.items() if i not in have)

    report = opts.dir / "missing.txt"
    if missing:
        lines = [f"{i} - {t}" for i, t in missing]
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        reporter.log(f"Tracks not found locally ({len(missing)}):")
        for line in lines:
            reporter.log("  " + line)
        reporter.log(f"Report saved to {report}")
    else:
        report.unlink(missing_ok=True)
        reporter.log("No missing tracks detected. Local library is fully synchronized.")
    return missing


# ------------------------------------------------------------------------------
# 5. COMMON ENTRY POINT (CLI and GUI)
# ------------------------------------------------------------------------------

def run(opts: Options, reporter: Reporter) -> None:
    """Executes the full pipeline: downloading, sorting, and auditing according to options."""
    if opts.cookies and not opts.cookies.is_file():
        raise FileNotFoundError(f"Cookies file not found: {opts.cookies}")

    opts.dir.mkdir(parents=True, exist_ok=True)

    files = download(opts, reporter)

    if opts.sort:
        sort_by_artist(files, opts.dir, reporter)

    if reporter.cancelled:
        reporter.log("Cancelled.")
        return

    if opts.export:
        audit_missing(opts, reporter)

    reporter.progress(1.0, "Complete")
    reporter.log("Complete.")
