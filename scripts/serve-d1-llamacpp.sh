#!/usr/bin/env bash
# Win/Linux/macOS: llama.cpp release with /v1/systemone (ggml-org/llama.cpp v0.8.0+). Then: export D1_URL=http://127.0.0.1:8096/v1/systemone
PORT="${PORT:-8096}"
# pre-flight: is the port already taken? (else llama-server dies with an obscure bind error)
# TODO: fix for non unix systems
if (echo > "/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null; then
  echo "port ${PORT} is already in use — a d1 server is probably already running. stop it, or use another port: PORT=8097 $0" >&2
  exit 1
fi
exec llama-server -hf "${D1_MODEL:-LiquidAI/d1-2B-GGUF:Q8_0}" --host 127.0.0.1 --port "${PORT}" "$@"
