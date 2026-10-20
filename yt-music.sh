#!/bin/bash 

# Sécurité d'exécution : arrête le script en cas d'erreur ou d'échec dans un pipe
set -eo pipefail

# ==============================================================================
# SCRIPT: yt-music.sh
# DESCRIPTION: Automates the downloading and management of music tracks from 
#              YouTube/YouTube Music using yt-dlp. Includes features for metadata 
#              extraction, directory sorting by artist, cookie-based authentication, 
#              and missing track auditing.
# ==============================================================================

# ------------------------------------------------------------------------------
# 0. DEPENDENCY CHECK
# ------------------------------------------------------------------------------

# Vérification préalable des exécutables système
for cmd in yt-dlp ffprobe python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Erreur critique : la commande '$cmd' est introuvable. Veuillez l'installer." >&2
    exit 1
  fi
done

# Vérification du module Python mutagen (requis par yt-dlp pour les pochettes et métadonnées)
if ! python3 -c "import mutagen" >/dev/null 2>&1; then
  echo "Erreur critique : le module Python 'mutagen' est manquant." >&2
  echo "yt-dlp en a besoin pour intégrer les métadonnées et convertir les pochettes." >&2
  echo "Installation : 'sudo apt install python3-mutagen' ou 'python3 -m pip install mutagen'" >&2
  exit 1
fi

# ------------------------------------------------------------------------------
# 1. DEFAULT CONFIGURATION VARIABLES
# ------------------------------------------------------------------------------

DIR="." 
sort_mode=false 
format="best" 
depth="1" 
export=false 
use_cookies=false 
cookies="" 
use_archive=false

# ------------------------------------------------------------------------------
# 2. COMMAND-LINE ARGUMENT PARSING
# ------------------------------------------------------------------------------

while getopts "d:f:g:c:esha" opt; do
  case ${opt} in
    d) DIR="$OPTARG" ;;
    f) format="$OPTARG" ;;
    g) depth="$OPTARG" ;;
    c) cookies="$OPTARG"; use_cookies=true ;;
    e) export=true ;;
    s) sort_mode=true ;;
    a) use_archive=true ;;
    h) 
      echo '
      
## Usage : 
yt-music.sh [options] <link>

Options:
  -d <dir>     Target directory for downloads (default: current directory)
  -f <format>  Audio format: best, mp3, flac, m4a, opus, etc. (default: best)
  -g <depth>   Search depth for existing local tracks (default: 1)
  -c <file>    Path to a cookies.txt file for authenticated downloads
  -a           Enable archive mode (records downloaded IDs in .archive.txt)
  -e           Export a missing tracks report (missing.txt)
  -s           Enable sort mode (organizes tracks into artist subdirectories)
  -h           Display this help message 
  
## Examples : 

Basic download to the current directory:

./yt-music.sh "https://youtube.com/playlist?list=..."


Download as FLAC, save to a specific folder, and sort by artist:

./yt-music.sh -f flac -d "/home/user/Music" -s "https://music.youtube.com/watch?v=..."


Download using cookies and export a missing tracks list:

./yt-music.sh -c "cookies.txt" -e "https://youtube.com/playlist?list=..."

Download a playlist with archive mode enabled to prevent re-downloading existing tracks:

./yt-music.sh -a "https://youtube.com/playlist?list=..."

Redownload a playlist sorted, with error and archive mode, in the Music directory, with depth 2 to compare already downloaded tracks to the playliste : 

./yt-music.sh -s -g 2 -e -a -d "/home/user/Music" "https://music.youtube.com/playlist?list=..."

' ; exit 0 ;;
    \?) echo "Invalid option : -$OPTARG" >&2; exit 1 ;;
    :) echo "Option -$OPTARG needs an argument." >&2; exit 1 ;;
  esac
done

shift $((OPTIND -1))

# Sécurité : vérifier que le lien a bien été fourni en argument positionnel
if [ -z "${1:-}" ]; then
  echo "Erreur : Aucun lien cible fourni." >&2
  exit 1
fi

link=$1

# ------------------------------------------------------------------------------
# 3. YT-DLP DOWNLOAD CONFIGURATION
# ------------------------------------------------------------------------------

yt_dlp_args=(
    -P "$DIR" 
    -x 
    --no-overwrites 
    -i 
    --audio-format "$format" 
    --audio-quality 0 
    --add-metadata 
    --embed-thumbnail 
    -o "%(title)s [%(id)s].%(ext)s" 
)

# Active l'archivage uniquement si le flag -a est fourni
if [ "$use_archive" = true ]; then
    yt_dlp_args+=(--download-archive "$DIR/.archive.txt")
fi

if [ "$use_cookies" = true ]; then
    yt_dlp_args+=(--cookies "$cookies")
fi

yt_dlp_args+=("$link")

# ------------------------------------------------------------------------------
# 4. EXECUTE DOWNLOAD
# ------------------------------------------------------------------------------

echo "Démarrage du processus de téléchargement..."
# Exécution de yt-dlp avec l'expansion du tableau d'arguments
yt-dlp "${yt_dlp_args[@]}"

# ------------------------------------------------------------------------------
# 5. POST-DOWNLOAD SORTING (ARTIST DIRECTORIES)
# ------------------------------------------------------------------------------

if [ "$sort_mode" = true ]; then
  echo "Tri des fichiers audio par artiste..."
  
  # Activation de nullglob pour éviter les erreurs si le dossier est vide
  shopt -s nullglob
  for file in "$DIR"/*."$format"; do
    [ -f "$file" ] || continue

    # Le "|| true" évite que le set -e ne coupe le script si ffprobe échoue sur un fichier
    artist=$(ffprobe -v error -show_entries format_tags=artist -of default=noprint_wrappers=1:nokey=1 "$file" || true)
    
    artist="${artist:-Artist Unknown}"
    artist_dir="${artist//\//-}"

    mkdir -p "$DIR/$artist_dir"
    mv "$file" "$DIR/$artist_dir/"
  done
  # Désactivation de nullglob pour la suite du script
  shopt -u nullglob
fi

# ------------------------------------------------------------------------------
# 6. MISSING TRACKS AUDIT & EXPORT
# ------------------------------------------------------------------------------

if [ "$export" = true ]; then
  echo "Audit des pistes manquantes..."
  
  yt-dlp --flat-playlist --print "%(id)s - %(title)s" "$link" | sort > /tmp/playlist_online.txt
  
  find "$DIR" -maxdepth "$depth" -type f -name "*\[*\].$format" \
    | grep -oE '\[[a-zA-Z0-9_-]{11}\]' \
    | tr -d '[]' \
    | sort -u > /tmp/local_ids.txt

  echo "Tracks not found locally :"
  
  # Le "|| true" est vital ici : si grep ne trouve aucune ligne correspondante (ce qui signifie
  # qu'aucune piste ne manque), il renvoie l'erreur 1. On intercepte cela pour ne pas crasher.
  grep -vFf /tmp/local_ids.txt /tmp/playlist_online.txt > "$DIR/missing.txt" || true
  
  if [ -s "$DIR/missing.txt" ]; then
      cat "$DIR/missing.txt"
  else
      echo "Aucune piste manquante détectée. La bibliothèque locale est synchronisée."
      rm "$DIR/missing.txt"
  fi
fi
