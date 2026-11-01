# Debatinator 4000 — concept (draft 2026-11-01)

Live debate assistant: listens to a debate, transcribes it and shows a dashboard that is quick to learn at a glance.
Origin: Discord chat redfuchs × Pink Panther, 2026-10-31.

## Dashboard panels
1. **Trick detector** (top, visual, color-coded chips per utterance)
   - negative: strawman, red herring, slippery slope, false dilemma, ad hominem, whataboutism, moving goalposts, appeal to authority, Gish gallop, loaded question
   - positive: steelman, good faith, concession, source cited, clarifying question
   - each hit = label + quoted span + 1-line reason + confidence; click → explanation card (learning mode)
2. **Schools of thought / ideology** per speaker: running profile (e.g. libertarian, Austrian econ, Keynesian, conservative, progressive …) with evidence quotes; updates slowly, not per sentence
3. **Reply suggestions**: 2-3 short answers for "our" speaker (counter, steelman-then-counter, question back), as inspiration, not as a script
4. Optional: **prediction** of where the current argument is heading (PP's idea: you can often predict the end of an argument)

## Pipeline
```
audio source ─► STT (streaming, per speaker if possible) ─► utterance events (speaker, t0, t1, text)
   ├ Discord: per-speaker tracks (discord-recorder style)
   ├ YouTube/file: yt-dlp + diarization (or a single track)
   └ mic / system audio
utterance window (last N utterances + rolling summary)
   ─► LLM via OpenAI-compatible API (llama.cpp llama-server, vMLX, LM Studio …)
       JSON-schema/grammar-constrained output: {tricks[], stance_updates[], replies[]}
   ─► event bus (WebSocket) ─► web dashboard (browser, any OS)
```
- Two speeds: fast pass per utterance (small model, tricks only), slow pass every ~60 s (bigger model: ideology, replies, summary)
- Everything local; recordings only with consent (announce in the channel, same as the recorder)

## Cross-platform (Windows + Linux + macOS)
| Layer | Win/Linux (NVIDIA) | macOS (M1 Max) |
|---|---|---|
| STT | whisper.cpp / faster-whisper (CUDA) | Apple SpeechAnalyzer (`hoer`), Qwen3-ASR MLX |
| LLM | llama.cpp `llama-server` (CUDA/Vulkan), GBNF/JSON schema | vMLX / zunder / llama.cpp Metal |
| Core + dashboard | same code: one binary or Node/Python + static web UI | same |
- Only contract between layers: OpenAI-compatible `/v1/chat/completions` + `/v1/audio/transcriptions` (or a local STT CLI) → backends are swappable.
- Kitsune (Mac voice assistant) consumes the same core as a "debate mode": speaks a short hint or shows the menu-bar popover.

## Reusable building blocks (already exist on the redfuchs side)
| Block | What | Win/Linux |
|---|---|---|
| **Liquid d1-2B (GGUF)** decision model | one forward pass, typed questions with probabilities: `noul` (yes/no + P), `choice` (1 of N), `score`, `read` (extract span) → trick detector + school of thought as calibrated scores, no free text, ~0.5-1 s | `llama-server -hf LiquidAI/d1-2B-GGUF:Q8_0`, `POST /v1/systemone` ✓ |
| llama.cpp `/v1/realtime` (LFM3-Audio-2B GGUF + mmproj, ~2 GB) | websocket live STT (`?intent=transcription`), OpenAI-realtime-like events, client-side commit (no server VAD) | ✓ CUDA |
| JSON-schema/grammar-constrained output | fixed schema for reply suggestions | llama.cpp native ✓ |
| Discord recorder (Node) | one FLAC per speaker, synced; live STT; chunked LLM evaluation with prompts + schema | Node ✓, live STT is Mac-only → swap in realtime STT |
| `netz` (Rust CLI) | web search + read a page → fact-check lookups | builds, untested on Win |
| offline Wikipedia RAG (Rust, in progress) | background on claims/terms, CPU only | ✓ |
| Silero VAD turn detector | utterance boundaries for the client commit | ✓ (onnx) |

Mapping: **fast pass = d1-2B** (each utterance: N `noul` questions for tricks + 1 `choice` for school of thought), **slow pass = generative LLM** (Gemma-4-E4B or bigger) with RAG context for the reply suggestions. Small LLMs (LFM3-1.7B) make up facts → never let them generate replies without context.

## Phases
| P | Content | Done when |
|---|---|---|
| 0 | offline: transcript file → analysis JSON → static dashboard | a recorded YouTube debate is labeled sensibly (manual spot-check of 20 hits) |
| 1 | live: mic/system audio → STT → fast pass → live dashboard | latency utterance-end → chip < 3 s |
| 2 | Discord per-speaker source, slow pass (ideology, replies) | 1 h session runs stable |
| 3 | Kitsune debate mode (Mac), learning-mode cards | – |

## Open questions for max
1. Primary language of the debates (German, English, both)? 
 - (Max: I would focus on german first)
2. Main source: Discord, YouTube, or both? 
- (Max: For training? anything that is fair use. youtube might be easier to gather)
3. Your hardware/OS for the test (GPU, VRAM) → model size for the fast/slow pass 
- (Max: see [Results](docs/Results.md).)
4. Which of the two dashboard mockups should we use? (redfuchs prefers the upper one: quick to learn visually) 
- (Max has no problems with that but we also though about a TUI implementation. hoenstly dashboard is better anyway, more freedom, bigger text, start with one first, KISS)
5. Tech stack preference for the shared core (Rust single binary vs. Node vs. Python)? 
