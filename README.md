# simple-yt-music-downloader (`symd`)

A simple Python tool to download and sort music from YouTube Music, standard YouTube videos, or playlist links. One program, two ways to use it:

* `symd` opens the **graphical interface**
* `symd [options] <link>` runs the **command-line** version

It extracts high-quality audio, embeds metadata and thumbnails, and organizes your local music library. It uses the `yt-dlp` and `mutagen` Python libraries directly, and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the GUI.

## Features

* **One executable:** `symd` works as a terminal command or opens the GUI, and can be packaged as a standalone file.
* **High-Quality Audio:** best available quality by default, with support for `mp3`, `flac`, `m4a`, `opus`.
* **Live progress (GUI):** progress bar covering the whole playlist, current track, scrolling logs, and a cancel button.
* **Automatic Sorting:** reads artist tags with `mutagen` and moves newly downloaded tracks into artist folders.
* **Authentication Support:** use a `cookies.txt` file for private playlists or premium accounts.
* **Audit Missing Tracks:** compares your local files with an online playlist and writes `missing.txt`.
* **Smart Archiving (Optional):** records downloaded video IDs in `.archive.txt` to avoid redundant downloads, even if you move or delete the files.
* **Cross-platform:** Linux, macOS and Windows.

## Project structure

```
symd/
├── symd.py             # Single entry point: GUI with no argument, CLI otherwise
├── cli.py              # Command-line interface
├── gui.py              # Graphical interface (CustomTkinter)
├── core.py             # Core logic: download, sort, audit (no UI code)
├── deps.py             # Dependency check shared by both interfaces
├── build.py            # Builds the standalone executable (PyInstaller)
├── requirements.txt
└── .github/workflows/build.yml   # Builds the Linux and Windows executables
```

## Dependencies

* **Python 3.10+** (not needed to *run* the standalone executable)
* **`yt-dlp`**, **`mutagen`**, **`customtkinter`** (Python packages, see `requirements.txt`)
* **`ffmpeg`** (system package): required by `yt-dlp` to extract and convert audio. It is **not** bundled in the executable.
* **`tkinter`**: bundled with Python on Windows and macOS. On Debian/Ubuntu: `sudo apt install python3-tk`

```bash
pip install -r requirements.txt

# ffmpeg and tkinter (Debian/Ubuntu)
sudo apt update
sudo apt install ffmpeg python3-tk
```

On macOS: `brew install ffmpeg`. On Windows: `winget install ffmpeg`.

## Running from source

```bash
python3 symd.py                      # opens the GUI
python3 symd.py --gui                # same
python3 symd.py [options] <link>     # command line
python3 symd.py --version            # symd and library versions
```

On Windows, use `py` instead of `python3`.

## Building the `symd` executable

```bash
pip install -r requirements.txt pyinstaller
python3 build.py            # Windows: py build.py
```

`build.py` first checks that everything needed is installed (including Tkinter) and tells you what is missing. The result is a single file: `dist/symd` (`dist/symd.exe` on Windows). Check it with:

```bash
dist/symd --version
```

### Install it so `symd` works from any terminal

```bash
# Linux
tar -xzf symd-linux-x86_64.tar.gz
sudo cp symd /usr/local/bin/           # or: cp symd ~/.local/bin/
```

On Windows, copy `symd-windows-x86_64.exe` to a folder in your `PATH` and rename it `symd.exe`.

Then:

```bash
symd                                                            # opens the GUI
symd -f flac -s "https://music.youtube.com/playlist?list=..."   # CLI
```

On Windows, double-clicking `symd.exe` opens the GUI and hides the console window; run from a terminal, it keeps the terminal as usual.

### Platform notes

* **ffmpeg is not bundled.** It must be installed on the machine running `symd` (`sudo apt install ffmpeg` on Linux, `winget install ffmpeg` on Windows).
* **Linux:** the binary needs a desktop environment with Tk support only for the GUI; the CLI works anywhere. It targets x86_64.
* **Windows:** unsigned single-file PyInstaller executables are sometimes flagged by SmartScreen or antivirus software. This is a known false positive; code signing avoids it.

## Graphical interface

1. Paste a video or playlist link.
2. Choose the destination folder (and optionally a `cookies.txt` file).
3. Pick a format and tick the options you want: sort by artist, archive mode, export missing tracks.
4. Click **Start**. Follow the progress bar and the logs, and use **Cancel** to stop.

The search depth selector is only enabled when *Export missing tracks* is ticked. If you also sort by artist, use a depth of `2` or more so the audit looks inside artist folders.

## Command line

```
usage: symd [options] <link>

Options:
  -d, --dir <dir>        Target directory for downloads (default: current directory)
  -f, --format <format>  Audio format: best, mp3, flac, m4a, opus (default: best)
  -g, --depth <depth>    Search depth for existing local tracks (default: 1)
  -c, --cookies <file>   Path to a cookies.txt file for authenticated downloads
  -a, --archive          Enable archive mode (records downloaded IDs in .archive.txt)
  -e, --export           Export a missing tracks report (missing.txt)
  -s, --sort             Sort tracks into artist subdirectories
  -h, --help             Display the help message
```

### Examples

**Basic download to the current directory:**

```bash
symd "https://youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

**Download as FLAC, save to a specific folder, and sort by artist:**

```bash
symd -f flac -d "/home/user/Music" -s "https://music.youtube.com/watch?v=..."
```

**Download using cookies and export a missing tracks list:**

```bash
symd -c "cookies.txt" -e "https://youtube.com/playlist?list=..."
```

**Archive mode to prevent re-downloading existing tracks:**

```bash
symd -a "https://youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

**Full workflow: sorted, archived, with a missing tracks report:**

```bash
symd -s -g 2 -e -a -d "/home/user/Music" "https://music.youtube.com/playlist?list=..."
```

## Notes

* **Sorting:** only files downloaded during the current run are moved into artist folders. Tracks without an artist tag go to `Artist Unknown`.
* **Missing tracks audit:** local tracks are matched by the 11-character video ID in the file name (`Title [ID].ext`). With format `best`, all common audio extensions are taken into account.
* **Cancel:** cancelling stops the download at the next progress update; tracks already completed are kept (and sorted if sorting is enabled).
* **Executable size and startup:** the single-file build bundles Python, yt-dlp and CustomTkinter, so it is large (tens of MB) and takes a moment to start.
* **Keeping yt-dlp up to date:** YouTube changes often. The executable embeds the yt-dlp version present at build time, so rebuild after `pip install -U yt-dlp` if downloads start failing.

## License

Distributed under the MIT License. See `LICENSE` for more information.
