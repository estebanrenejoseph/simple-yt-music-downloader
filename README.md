# simple-yt-music-downloader

A simple Python tool to download and sort music from YouTube Music, standard YouTube videos, or playlist links, with both a **graphical interface** and a **command-line** version.

It extracts high-quality audio, embeds metadata and thumbnails, and organizes your local music library. It uses the `yt-dlp` and `mutagen` Python libraries directly, and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the GUI.

## Features

* **Two interfaces:** a CustomTkinter GUI (`yt_music_gui.py`) and a CLI (`yt_music.py`) sharing the same core.
* **High-Quality Audio:** best available quality by default, with support for `mp3`, `flac`, `m4a`, `opus`.
* **Live progress (GUI):** progress bar covering the whole playlist, current track, scrolling logs, and a cancel button.
* **Automatic Sorting:** reads artist tags with `mutagen` and moves newly downloaded tracks into artist folders.
* **Authentication Support:** use a `cookies.txt` file for private playlists or premium accounts.
* **Audit Missing Tracks:** compares your local files with an online playlist and writes `missing.txt`.
* **Smart Archiving (Optional):** records downloaded video IDs in `.archive.txt` to avoid redundant downloads, even if you move or delete the files.
* **Cross-platform:** Linux, macOS and Windows.

## Project structure

```
yt-music-gui/
├── yt_music_gui.py     # Graphical interface (CustomTkinter)
├── yt_music.py         # Command-line interface
├── yt_music_core.py    # Core logic: download, sort, audit (no UI code)
├── deps.py             # Dependency check shared by both interfaces
└── requirements.txt
```

Keep all files in the same folder.

## Dependencies

* **Python 3.10+**
* **`yt-dlp`**, **`mutagen`**, **`customtkinter`** (Python packages, see `requirements.txt`)
* **`ffmpeg`** (system package): required by `yt-dlp` to extract and convert audio
* **`tkinter`**: bundled with Python on Windows and macOS. On Debian/Ubuntu: `sudo apt install python3-tk`

`customtkinter` is only needed for the GUI; the CLI works without it.

```bash
pip install -r requirements.txt

# ffmpeg and tkinter (Debian/Ubuntu)
sudo apt update
sudo apt install ffmpeg python3-tk
```

On macOS: `brew install ffmpeg`. On Windows: `winget install ffmpeg`.

## Graphical interface

```bash
python3 yt_music_gui.py
```

1. Paste a video or playlist link.
2. Choose the destination folder (and optionally a `cookies.txt` file).
3. Pick a format and tick the options you want: sort by artist, archive mode, export missing tracks.
4. Click **Lancer**. Follow the progress bar and the logs, and use **Annuler** to stop.

The search depth selector is only enabled when *Exporter les pistes manquantes* is ticked. If you also sort by artist, use a depth of `2` or more so the audit looks inside artist folders.

## Command line

```
usage: yt_music.py [options] <link>

Options:
  -d, --dir <dir>        Target directory for downloads (default: current directory)
  -f, --format <format>  Audio format: best, mp3, flac, m4a, opus, etc. (default: best)
  -g, --depth <depth>    Search depth for existing local tracks (default: 1)
  -c, --cookies <file>   Path to a cookies.txt file for authenticated downloads
  -a, --archive          Enable archive mode (records downloaded IDs in .archive.txt)
  -e, --export           Export a missing tracks report (missing.txt)
  -s, --sort             Enable sort mode (organizes tracks into artist subdirectories)
  -h, --help             Display the help message
```

### Examples

**Basic download to the current directory:**

```bash
python3 yt_music.py "https://youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

**Download as FLAC, save to a specific folder, and sort by artist:**

```bash
python3 yt_music.py -f flac -d "/home/user/Music" -s "https://music.youtube.com/watch?v=..."
```

**Download using cookies and export a missing tracks list:**

```bash
python3 yt_music.py -c "cookies.txt" -e "https://youtube.com/playlist?list=..."
```

**Archive mode to prevent re-downloading existing tracks:**

```bash
python3 yt_music.py -a "https://youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

**Full workflow: sorted, archived, with a missing tracks report:**

```bash
python3 yt_music.py -s -g 2 -e -a -d "/home/user/Music" "https://music.youtube.com/playlist?list=..."
```

## Notes

* **Sorting:** only files downloaded during the current run are moved into artist folders. Tracks without an artist tag go to `Artist Unknown`.
* **Missing tracks audit:** local tracks are matched by the 11-character video ID in the file name (`Title [ID].ext`). With format `best`, all common audio extensions are taken into account.
* **Cancel:** cancelling stops the download at the next progress update; tracks already completed are kept (and sorted if sorting is enabled).

## License

Distributed under the MIT License. See `LICENSE` for more information.
