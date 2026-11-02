# Debatinator 4000

Local debate assistant: detects rhetorical patterns (fallacies, good-faith arguments) in live/recorded debates using small decision models.

## Key files
- `eval/taxonomy.py` - debate pattern definitions (German), d1 question structure
- `eval/snippets.py` - 12 clean test cases, 11/12 @ ~200-330ms
- `eval/turns.py` - per-speaker turn analysis (real duel: 7 hits, ~4 plausible)
- `eval/diarize.py` - pyannote speaker separation
- `docs/CONCEPT.md` - full pipeline, dashboard design, cross-platform strategy
- `docs/RESULTS.md` - measurements, learned lessons

## Stack
- **Models**: Liquid d1-2B/3B (GGUF Q8_0 llama.cpp or MLX) for fast classification, bigger LLMs for slow pass
- **STT**: whisper.cpp/faster-whisper (CUDA) | Apple SpeechAnalyzer/Qwen3-ASR (Mac)
- **Diarization**: pyannote `speaker-diarization-community-1`
- **Backend**: llama.cpp `/v1/systemone` (Win/Linux), MLX (Mac)
  - Long debate turns need: `-c 2048 -ub 2048` (context + physical batch size)

## Dev conventions
- German instructions (debates are German), English code/docs
- `data/` gitignored (audio, captions, big files)
- All local, no external APIs
- Cross-platform: Win/Linux (CUDA) + macOS (Metal/MLX)

## Known issues (TODO.md)
1. **Pyannote diarization quality is poor** — assigns moderator intro to all 3 speakers, speaker boundaries drift
2. Recursive accusation: "you're building a strawman" → who accuses whom?
3. Good-faith debates have zero fallacies → need counter-argument generation
4. Streaming STT + diarization = hard (batch models don't work live)
5. Long turns need chunking (~30s) with opponent context
6. Positives rare (steelman, good_faith) → separate high-threshold questions

## When helping
- Read TODO.md + RESULTS.md before suggesting changes to taxonomy/pipeline
- Test changes via `eval/snippets.py choice` (baseline: 10-11/12)
- Don't bloat responses with full file dumps unless asked
- Latency matters: target <3s utterance-end → chip display
