#!/usr/bin/env bash
# fetch-yt.sh <youtube-url> <name>  → data/<name>.json3 (auto captions de) + data/<name>.wav (16 kHz mono)
# RATE=60K caps the download (shared links)
set -euo pipefail
url=$1; name=$2; mkdir -p data
yt-dlp --skip-download --write-auto-subs --sub-langs "${SUB_LANG:-de-orig}" --sub-format json3 -o "data/$name" "$url"
mv "data/$name.${SUB_LANG:-de-orig}.json3" "data/$name.json3"
yt-dlp -q -f "worstaudio[ext=m4a]/worstaudio" --limit-rate "${RATE:-60K}" -o "data/$name.%(ext)s" "$url"
ffmpeg -loglevel error -y -i "data/$name".m4a -ac 1 -ar 16000 "data/$name.wav"
echo "data/$name.json3 data/$name.wav"
