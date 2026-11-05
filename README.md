# Debatinator 4000 (or local AI debate suggestions in near real time)
Working on this with my good ([friend](https://github.com/Red-fuchs)). Debates and AI Engineering are our common interests! give him a follow!

Local live debate assistant: listens to a debate, transcribes it per speaker and labels each turn with classic debate tricks (strawman, red herring, slippery slope, false dilemma, ad hominem, whataboutism, anecdote) plus positives (steelman, good faith). Later: school of thought per speaker and 2–3 reply suggestions, shown as a dashboard or TUI.

## Challenges

- **Real-time Streaming vs. [Diarisation](https://en.wikipedia.org/wiki/Speaker_diarisation) Overhead:** Batch models like `pyannote` struggle in live setups. Balancing low-latency streaming speech-to-text with accurate speaker separation during overlaps and cross-talk on local hardware is tight. (optimal setup would be dealing with a single audio source in a 1 to 1 debate obviously, but testing beyong that is already planned)
- **Context Granularity & Turn Chunking:** Long monologoues might result in longer processing time of the argument. It's possible people even chain arguments together. Theoretically you could rhetorically dissect and counter each argument. A smarter choice would probably to explicitly state this in a debate and then just attacking the weakest of the arguments. However computationally this needs non trivial semantic understanding of the structure. 
- **Rhetorical Nuance vs. Small Model Size:** subtle fallacies (e.g., *strawman accusation* vs. *strawman*, *red herring* vs. *evasion*) are usually made to confuse your opponent (when done in bad-faith) with low-parameter decision models (`d1-2B/3B`) detecting those becomes a hard task, (false positives/negatives might be hard to tackle on rather slower hardware)
- **Cross-Platform Backend Parity:** Trying to make this program work on apple silicon and x86 at the same time is a challenge. Since both developers use either one or the other, this will be not be a big problem.
- **Live UI Synchronization:** Probably the hardest, understand the WHO in who is speaking and the CONTEXT. off topic, jokes, irony etc... Thats a common non trivial problem on speech analysis compared tp calssical NLP. 

Runs on **Windows/Linux (llama.cpp, CUDA)** and **macOS (MLX or llama.cpp Metal)**. Everything local.

- Concept: [docs/CONCEPT.md](docs/CONCEPT.md)
- Measurements so far: [docs/RESULTS.md](docs/RESULTS.md)
- **Accepted dataset: [datasets/README.md](datasets/README.md)** — 107 examples only: 4 Dekarldent exchanges + 103 translated passages. Uncertain, rejected and unreviewed examples removed.
- Provenance: [source/rights notes](docs/datasets/ENGLISH_DATASETS.md), [Dekarldent annotation notes](docs/debates/README.md).
- Developer workflows: [scripts/README.md](scripts/README.md).
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
| Win/Linux/macOS | `scripts/serve-d1-llamacpp.sh -c 2048 -ub 2048` (llama.cpp ≥ v0.8.0, context + physical batch size for long turns) | `http://127.0.0.1:8096/v1/systemone` |
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

## Dataset and development checks

```bash
python -m unittest discover -s tests -v
python scripts/build-shared-dataset.py --metadata-only --check

# With data/datasets/accepted_mm_used.json installed:
python scripts/build-shared-dataset.py
```

Complete accepted dataset: **`data/datasets/shared/accepted.jsonl`**; offline reader: `data/datasets/shared/index.html`. Schema and provenance are documented in [datasets/README.md](datasets/README.md). Dataset tests use the standard library; no model server needed. Private-data integration test skips on fresh clones.

`data/` is gitignored: audio, raw captions, imported English corpora and private German translations stay local. Dataset schema, metadata index and review decisions are committed. Back up `data/` separately; a clone alone does not restore imported full text.