# simple-yt-music-downloader

A simple, robust bash script to download and sort music from YouTube Music, standard YouTube videos, or playlist links. 

This tool automates the process of extracting high-quality audio, embedding metadata and thumbnails, and organizing your local music library.

## Features

* **High-Quality Audio:** Downloads the best available audio format by default, with support for `mp3`, `flac`, `m4a`, `opus`, and more.
* **Smart Archiving:** Keeps track of downloaded IDs to prevent redundant downloads, even if you move the files.
* **Automatic Sorting:** Extracts artist metadata to automatically organize tracks into artist-specific folders.
* **Authentication Support:** Use a `cookies.txt` file to download from private playlists or premium accounts.
* **Audit Missing Tracks:** Compares your local files against an online playlist to generate a report of missing or failed downloads.
* **Smart Archiving (Optional):** Use the `-a` flag to keep track of downloaded video IDs in `.archive.txt`, preventing redundant downloads in future runs.

## Dependencies

Before running the script, ensure you have the following dependencies installed on your system:

* **`yt-dlp`**: The core downloading engine.
* **`ffprobe`** (part of the `ffmpeg` package): Used for extracting artist metadata from the audio files.
* **`mutagen`** (Python package): Required by `yt-dlp` to embed audio metadata and convert thumbnails.

**Installation (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install yt-dlp ffmpeg python3-mutagen

## Installation

1. Clone or download the script to your local machine.
2. Make the script executable:
```bash
chmod +x yt-music.sh
```

## Usage

Usage: ./yt-music.sh [options] <link>

Options:
  -d <dir>     Target directory for downloads (default: current directory)
  -f <format>  Audio format: best, mp3, flac, m4a, opus, etc. (default: best)
  -g <depth>   Search depth for existing local tracks (default: 1)
  -c <file>    Path to a cookies.txt file for authenticated downloads
  -a           Enable archive mode (records downloaded IDs in .archive.txt)
  -e           Export a missing tracks report (missing.txt)
  -s           Enable sort mode (organizes tracks into artist subdirectories)
  -h           Display this help message

## Examples

**Basic download to the current directory:**
```bash
./yt-music.sh "https://youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

**Download as FLAC, save to a specific folder, and sort by artist:**
```bash
./yt-music.sh -f flac -d "/home/user/Music" -s "https://music.youtube.com/watch?v=..."
```

**Download using cookies and export a missing tracks list:**
```bash
./yt-music.sh -c "cookies.txt" -e "https://youtube.com/playlist?list=..."
```
**Download a playlist with archive mode enabled to prevent re-downloading existing tracks:**
```bash
./yt-music.sh -a "[https://youtube.com/playlist?list=YOUR_PLAYLIST_ID](https://youtube.com/playlist?list=YOUR_PLAYLIST_ID)"

## License

Distributed under the MIT License. See `LICENSE` for more information.
