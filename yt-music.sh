#!/bin/bash 

DIR=/home/esteb/Music/Playlist/

Lien=$1 

yt-dlp -P "$DIR" -x --download-archive "$DIR/.archive.txt" --no-overwrites -i --audio-format mp3 --audio-quality 0 --add-metadata --embed-thumbnail -o "%(title)s [%(id)s].%(ext)s" "$Lien"

for file in "$DIR"/*.mp3; do
  [ -f "$file" ] || continue

  # Extraction du tag 'artist' ou 'ARTIST' via ffprobe
  artist=$(ffprobe -v error -show_entries format_tags=artist -of default=noprint_wrappers=1:nokey=1 "$file")

  # Valeur de repli si la métadonnée est absente ou vide
  artist="${artist:-Artiste Inconnu}"

  # Nettoyage des éventuels caractères interdits dans un nom de dossier (comme '/')
  artist_dir="${artist//\//-}"

  # Création du sous-dossier et déplacement du fichier
  mkdir -p "$DIR/$artist_dir"
  mv "$file" "$DIR/$artist_dir/"
done

# 1. Récupère la liste triée des IDs et titres de la playlist en ligne
yt-dlp --flat-playlist --print "%(id)s - %(title)s" "$Lien" | sort > /tmp/playlist_online.txt

# 2. Extrait les IDs de 11 caractères déjà téléchargés sur ton disque
find "$DIR" -maxdepth 2 -type f -name "*\[*\].mp3" \
  | grep -oE '\[[a-zA-Z0-9_-]{11}\]' \
  | tr -d '[]' \
  | sort -u > /tmp/local_ids.txt

# 3. Affiche uniquement les morceaux en ligne qui n'apparaissent pas en local
grep -vFf /tmp/local_ids.txt /tmp/playlist_online.txt
