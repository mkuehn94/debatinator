# Script workflows

Run from repo root. Dataset tools use Python 3.10+ and local files; only the collector/fetcher make network requests. Model/STT setup remains in the root README.

## Shared dataset (start here)

```bash
python scripts/build-translation-review.py         # requires private corpus/translation inputs
python scripts/build-shared-dataset.py             # shared local JSONL buckets + offline reader
python scripts/build-shared-dataset.py --check
```

Without private text, validate committed metadata:

```bash
python scripts/build-shared-dataset.py --metadata-only --check
```

Import a new review export, then regenerate shared output:

```bash
python scripts/build-translation-review.py --import-review PATH_TO_EXPORT.json
python scripts/build-shared-dataset.py
```

Authoritative review file: `datasets/reviews/mm_used.json`. Generated shared index/manifest live in `datasets/`; full text remains under ignored `data/datasets/shared/`. See [dataset contract and rights](../datasets/README.md).

## Research and source preparation

| Script | Purpose |
|---|---|
| `prepare-debate-corpus.py` | Normalize downloaded MM-USED TSV, deduplicate contexts, preserve labels/splits/spans; no translation |
| `collect-fallacy-sources.py` | Allowlisted, robots-aware source retrieval; raw caches under `data/`; never automatically approves labels |
| `render-fallacy-catalog.py` | Validate curated research catalog and rebuild `docs/fallacies/index.html` and `examples.md` |
| `render-fallacy-discovery.py` | Rebuild separate unreviewed search-lead HTML/markdown views |
| `fetch-yt.sh` | Download captions/audio into ignored `data/` |
| `serve-d1-llamacpp.sh`, `serve-d1-mlx.sh` | Start local classifier backends |

Use each script's `--help` for options. Renderers support `--check`, which rejects stale generated views without writing.

## Tests (no model server)

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/render-fallacy-catalog.py --check
python scripts/render-fallacy-discovery.py --check
python scripts/build-shared-dataset.py --metadata-only --check
```

Private translation integration tests skip explicitly if data is absent. Optional Node.js checks exercise generated review JavaScript. Tests do not measure classifier accuracy or translation fidelity.
