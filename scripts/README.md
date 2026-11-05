# Script workflows

Run from repo root. Dataset tooling uses Python 3.10+ and the standard library; no model server or GPU required.

## Accepted dataset

```bash
python scripts/build-shared-dataset.py
python scripts/build-shared-dataset.py --check
```

Private source text: `data/datasets/accepted_mm_used.json`. Output: **`data/datasets/shared/accepted.jsonl`**, plus searchable `index.html` and `manifest.json`. Only the 107 explicitly accepted examples are retained. No review queue or research catalog is imported.

Without private text, validate the committed metadata:

```bash
python scripts/build-shared-dataset.py --metadata-only --check
```

Authoritative accepted decisions: `datasets/reviews/mm_used.json`. Confirmed German exchanges: `eval/fixtures/debate_cases.json`. See [dataset contract and rights](../datasets/README.md).

## Other tools

| Script | Purpose |
|---|---|
| `prepare-debate-corpus.py` | Optional raw MM-USED TSV normalization; preserves source labels/splits/spans, but does not add examples to the accepted dataset |
| `fetch-yt.sh` | Download captions/audio into ignored `data/` |
| `serve-d1-llamacpp.sh`, `serve-d1-mlx.sh` | Start local classifier backends |

Unreviewed research collection and translation-review UI tooling were removed with the discarded examples. Previous versions remain in git history.

## Tests

```bash
python -m unittest discover -s tests -v
```

No additional Python packages needed for dataset tests. Optional Node.js exercises reader search. Full-text integration test skips on clones without private source text. These tests do not measure classifier accuracy or translation fidelity.
