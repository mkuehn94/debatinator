# Accepted German debate-pattern dataset

**107 examples, all explicitly accepted by the user:**

- **4 Dekarldent exchanges:** 2 `strohmann`, 1 `whataboutism`, 1 `ad_hominem`.
- **103 translated MM-USED passages:** original source labels and your notes preserved.

Rejected, uncertain, pending and unreviewed research examples have been removed. There is no remaining review queue. Previous research and discarded judgments remain recoverable from git history, not part of the current dataset.

## Use these files

| File | Contents |
|---|---|
| **`data/datasets/shared/accepted.jsonl`** | **Complete 107-record dataset, including text and provenance** |
| `data/datasets/shared/index.html` | Offline searchable reader; every displayed example is accepted |
| `data/datasets/shared/manifest.json` | Counts, input hashes and source limitations |
| [`index.jsonl`](index.jsonl) | Committed metadata for the same 107 records; `input: null` |
| [`schema.json`](schema.json) | Shared JSON Schema; only `accepted` / `agree` records allowed |
| [`manifest.json`](manifest.json) | Committed counts and source-input hashes |

Full imported text stays under gitignored `data/`. No duplicate `all.jsonl` or rejected/uncertain/pending buckets are generated.

## Authoritative inputs

- [`../eval/fixtures/debate_cases.json`](../eval/fixtures/debate_cases.json): four confirmed German A/B paraphrases, timestamps and source links.
- [`inputs/mm_used.json`](inputs/mm_used.json): **103** accepted source identities, original labels/splits, attribution and content fingerprints; no imported text.
- [`reviews/mm_used.json`](reviews/mm_used.json): **103** explicit agreement decisions and their notes. No rejected or uncertain judgments retained here.
- `data/datasets/accepted_mm_used.json`: private text, English context and translation provenance for those same 103 accepted passages. Supporting context is evidence, not additional labeled examples.

Edit source records rather than the generated index. The builder refuses non-agreement judgments, unconfirmed fixtures, duplicate IDs and source/content drift. Future additions require explicit label acceptance and matching source metadata/content fingerprints; they are never included merely because a source annotated them.

## Build and check

Python 3.10+; standard library only. No model, GPU or network needed.

```bash
# With accepted private source text installed:
python scripts/build-shared-dataset.py
python scripts/build-shared-dataset.py --check

# Fresh clone without private text:
python scripts/build-shared-dataset.py --metadata-only --check

python -m unittest discover -s tests -v
```

Core tests work without private data. Full-text integration test skips explicitly if the accepted private text is missing. Node.js is optional for the offline reader's JavaScript test.

## Record contract and limitations

- `id` is stable and collection-prefixed; `source.record_id` preserves original identity.
- `input_kind` distinguishes **exchange** (A/B) from **passage**. MM passages have no invented A/B opponent or speaker.
- `input` contains text and context only; labels, rationales and judgments stay outside it. Committed metadata uses `input: null`.
- `text_kind` distinguishes caption-based German paraphrases from assistant translations. Neither implies a verbatim, audio-verified German transcript.
- `label` preserves namespace, value and subcategory. **Only the four Dekarldent cases have confirmed `project_main` labels.** MM-USED categories are not silently mapped to the classifier's taxonomy.
- `review` contains acceptance, exact note and translation metadata. Optional German corrections remain separate from original `input.text_de`; alternative categories in notes are not automatic reannotations.
- `source` retains attribution pointers, original split and leakage group IDs. Resolve `metadata_file` from repo root; `#sources` means that JSON file's source registry.
- `evidence` contains timestamps, rationales and verification limits. Do not feed label rationales to a scored classifier.
- `source_input_sha256` detects drift in original text/context.

Acceptance means agreement with the recorded label—not audio verification, factual endorsement, independent annotation, or proof that every source category is a logical fallacy. Slogans/emotional appeals are broader rhetorical categories. The 107 examples are **not 107 ready-made d1 MAIN benchmark cases**. No reviewed neutral controls or new train/test splits are supplied.

Preserve MM-USED's `source.source_split` and keep records sharing `source.group_ids` together in any future partition. English originals and German translations must not be placed in different evaluation splits.

## Rights and backup

No blanket dataset license is assigned. MM-USED declares CC BY 4.0; its USED upstream declares CC BY-NC-SA 4.0. Attribution remains in `inputs/mm_used.json`; clarify the chain before publishing imported text or using it commercially. See [source/rights notes](../docs/datasets/ENGLISH_DATASETS.md).

**Git stores schema, accepted metadata/decisions and the four Dekarldent paraphrases—not private MM-USED text.** Back up `data/datasets/accepted_mm_used.json` separately. Restoring that file allows full local rebuilds. Hashes alone cannot restore translations; a metadata-only build is not a full-text dataset export.
