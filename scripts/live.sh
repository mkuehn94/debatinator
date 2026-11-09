#!/usr/bin/env bash
# Starts the live sidecar (audio → STT → LLM → SSE :8765) with the pip-installed CUDA libs on the path.
# Prereq: scripts/serve-llm.sh running.  Then: (cd app/src-tauri && cargo run)
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
NV=$("$PY" -c 'import os,nvidia; print(":".join(os.path.join(p,d,"lib") for p in nvidia.__path__ for d in os.listdir(p)))' 2>/dev/null || true)
export LD_LIBRARY_PATH="${NV}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"   # xet downloader hangs at 0 bytes here
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES="${GPU:-1}"   # whisper on the 3090 too (nvidia-smi index)
exec "$PY" live/server.py "$@"
