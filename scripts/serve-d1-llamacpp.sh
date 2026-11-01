#!/usr/bin/env bash
# Win/Linux/macOS: llama.cpp release with /v1/systemone (ggml-org/llama.cpp v0.8.0+). Then: export D1_URL=http://127.0.0.1:8096/v1/systemone
exec llama-server -hf "${D1_MODEL:-LiquidAI/d1-2B-GGUF:Q8_0}" --host 127.0.0.1 --port "${PORT:-8096}" "$@"
