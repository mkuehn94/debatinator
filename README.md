# Debatinator 4000

Local live debate assistant: listens to a debate, transcribes it per speaker and labels each turn with classic debate tricks (strawman, red herring, slippery slope, false dilemma, ad hominem, whataboutism, anecdote) plus positives (steelman, good faith). Later: school of thought per speaker and 2–3 reply suggestions, shown as a dashboard.

Runs on **Windows/Linux (llama.cpp, CUDA)** and **macOS (MLX or llama.cpp Metal)**. Everything local.

- Concept: [docs/CONCEPT.md](docs/CONCEPT.md)
- Measurements so far: [docs/RESULTS.md](docs/RESULTS.md)
- Discussion/tasks: pp-pipeline issue #6

## How it works (current eval pipeline)

```
YouTube URL ─ scripts/fetch-yt.sh ─► data/<name>.json3 (auto captions, word timestamps)
                                 └─► data/<name>.wav  ─ eval/diarize.py (pyannote community-1) ─► <name>.turns.json
captions + turns ─ eval/turns.py ─► per speaker turn: d1 decision model ─► <name>.labels.json
```

The classifier is **Liquid d1** (decision model): no text generation, one forward pass, returns probabilities for typed questions (`choice`, `noul` = yes/no, `score`). Questions live in [eval/taxonomy.py](eval/taxonomy.py).

## Setup

```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                 # pyannote pulls torch; CUDA build on NVIDIA
```
pyannote `speaker-diarization-community-1` needs accepting the model terms on Hugging Face once + `HF_TOKEN` (first download only).
Also needed: `yt-dlp`, `ffmpeg`.

### d1 server

| OS | Command | `D1_URL` |
|---|---|---|
| Win/Linux/macOS | `scripts/serve-d1-llamacpp.sh` (llama.cpp release ≥ v0.8.0 with `/v1/systemone`, pulls `LiquidAI/d1-2B-GGUF:Q8_0`) | `http://127.0.0.1:8096/v1/systemone` |
| macOS | `D1_MODEL=<mlx d1 dir> scripts/serve-d1-mlx.sh` (mlx-vlm main) | default `http://127.0.0.1:8095/v1/decisions` |

On Windows run the `.sh` steps in Git Bash/WSL or call the commands directly.

## Run

```bash
cd eval
python snippets.py choice          # 12 clean German snippets, sanity check (expect ~11/12)
python snippets.py noul            # per-trick yes/no variant (worse precision, for comparison)

cd .. && scripts/fetch-yt.sh "https://www.youtube.com/watch?v=C0IO0dApOMc" duel
python eval/diarize.py data/duel.wav data/duel.turns.json 3
cd eval && python turns.py ../data/duel.json3 ../data/duel.turns.json
```

`data/` is git-ignored: no audio or captions in the repo.

## Status / next

- [x] d1 as trick detector on clean snippets: one `choice` question 11/12 @ ~200 ms (d1-3B MLX)
- [x] real TV duel per speaker turn: noise down from 26 to 7 hits, ~4 plausible
- [ ] taxonomy: add **evasion**, split **strawman accusation** from strawman
- [ ] split long turns (1–2 min) into ~30 s chunks with the opponent's last turn as context
- [ ] d1-2B GGUF on llama.cpp (Win/Linux path), same numbers
- [ ] HTML dashboard (timeline, color chips per speaker, explanation cards)
- [ ] live mode (realtime STT), Discord per-speaker tracks, Kitsune debate mode on Mac
