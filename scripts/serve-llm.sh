#!/usr/bin/env bash
# Generative LLM for counter-arguments (OpenAI-compatible /v1/chat/completions). Used by live/server.py via LLM_URL.
# Needs a CUDA (or Metal) llama-server build — the CPU-only release runs ~17 tok/s, far too slow.
#   LLAMA_SERVER=/path/to/llama-server   GPU=1 (nvidia-smi index; default: the 3090)
PORT="${PORT:-8097}"
if (echo > "/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then
  echo "port ${PORT} already in use — LLM server probably running. Other port: PORT=8098 $0" >&2; exit 1
fi
BIN="${LLAMA_SERVER:-llama-server}"
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES="${GPU:-1}"   # same numbering as nvidia-smi
exec "$BIN" -hf "${LLM_MODEL:-unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M}" \
  --host 127.0.0.1 --port "${PORT}" -ngl 99 -c 4096 -np 1 -fa on "$@"
