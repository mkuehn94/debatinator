# Shared German debate-pattern dataset

**Start here.** One schema combines Dekarldent exchanges, translated MM-USED passages, and research examples without losing their different provenance or review status.

## Current contents

| Collection | All | Accepted | Rejected | Uncertain | Pending |
|---|---:|---:|---:|---:|---:|
| Dekarldent debate | 4 | 4 | 0 | 0 | 0 |
| Translated MM-USED | 150 | 103 | 4 | 42 | 1 |
| Research/teaching/forum catalog | 152 | 0 | 0 | 0 | 152 |
| **Total** | **306** | **107** | **4** | **42** | **153** |

Accepted means the user agreed with the recorded label. It does **not** mean audio-verified, independently fact-checked, representative, or a logical fallacy in every context. No automatic training/evaluation split is assigned.

## Files to use

### Full local dataset

Generated under **`data/datasets/shared/`**, which remains gitignored:

| File | Contents |
|---|---|
| `all.jsonl` | All 306 records, full inputs and provenance |
| **`accepted.jsonl`** | **107 accepted records, including all four Dekarldent cases** |
| `rejected.jsonl` | 4 rejected source annotations; **not** automatically neutral examples |
| `uncertain.jsonl` | 42 context/label uncertainties; excluded from accepted records |
| `pending.jsonl` | 153 records awaiting judgment |
| `index.html` | Offline searchable reader; accepted filter selected initially |
| `manifest.json` | Counts, input hashes, rights and evaluation caveats |

These are **review buckets**, not train/validation/test partitions. No examples are deleted because a source label was rejected.

### Version-controlled dataset definition

- [`schema.json`](schema.json): shared JSON Schema for every JSONL record.
- [`index.jsonl`](index.jsonl): all 306 metadata records, with `input: null` rather than imported text.
- [`manifest.json`](manifest.json): deterministic counts and hashes of authoritative inputs.
- [`inputs/mm_used.json`](inputs/mm_used.json): 150 source identities, source labels/splits, attribution, translation metadata and full-input fingerprints; no imported snippets or context blocks.
- **[`reviews/mm_used.json`](reviews/mm_used.json)**: authoritative user decisions, notes and optional German corrections. These survive a fresh clone.
- [`../eval/fixtures/debate_cases.json`](../eval/fixtures/debate_cases.json): authoritative Dekarldent A/B paraphrases and confirmed labels.
- [`../docs/fallacies/catalog.json`](../docs/fallacies/catalog.json): authoritative unreviewed research examples; linked source metadata remains alongside it.

The shared index is generated, not hand-edited. Original records remain the authoring sources. Existing specialized review pages are retained; they are not competing final datasets.

## Build and review workflow

Python 3.10+; shared builder uses only the standard library and never calls a model or network.

```bash
# With private translation data already installed:
python scripts/build-translation-review.py
python scripts/build-shared-dataset.py

# Verify full local output, without changing files:
python scripts/build-translation-review.py --check
python scripts/build-shared-dataset.py --check

# Fresh clone: build/check the committed metadata without private source text:
python scripts/build-shared-dataset.py --metadata-only --check
```

To record a new MM-USED review, export from `data/datasets/translation_review/index.html`, then:

```bash
python scripts/build-translation-review.py --import-review ~/Downloads/mm-used-de-review-150-v3-review.json
python scripts/build-shared-dataset.py
```

This updates `datasets/reviews/mm_used.json`, the review page, and shared outputs after validation. Browser edits alone do not persist to the repo. Custom `--directory` review builds keep their review file inside that custom directory.

Source text, translation content, and provenance must match the committed MM snapshot. A genuine translation/content change needs an explicit snapshot refresh (`mm_snapshot()` in the shared builder) and review of the resulting diff; the builder refuses silent drift. New source examples additionally require updating the translation selection/batch and review export. It never invents new German translations from hashes.

## Record contract

Every record follows the same schema:

- `id`: stable, collection-prefixed ID; `source.record_id` preserves the original identity.
- `input_kind`: `exchange` (A/B) or `passage` (single translated span). MM passages have `a: null`, `b: null`; no invented opponent or speaker.
- `input`: **only** model-visible text, English originals/context, and explicitly cropped translated windows. Metadata index uses `null`. Rationales and labels stay outside input.
- `text_kind`: distinguishes caption-based paraphrases, assistant translations and editorial teaching/forum adaptations. None are silently represented as verbatim German debate audio.
- `label`: original namespace, value and subcategory. `project_main` is populated **only** for explicitly confirmed main-taxonomy fixtures.
- `review`: accepted/rejected/uncertain/pending decision, exact note, translation-review metadata and optional correction. Alternative labels in notes are not automatic reannotations. Optional `correction_de` is retained separately, not silently substituted for original `input.text_de`.
- `source`: source pointers, original split, and leakage group IDs. Resolve `metadata_file` from repo root; `#sources` denotes the source registry in that JSON file.
- `evidence`: timestamps, spans, editorial rationales, source assessments and verification limits. **Do not feed this to a scored classifier.**
- `source_input_sha256`: canonical JSON hash of the original input, including context. This detects accidental source/translation drift.

### Labels are namespaced on purpose

`debinator_main:strohmann` and `mm_used:AppealtoAuthority` are not interchangeable target classes. Tu quoque is not automatically whataboutism; slogans and emotional appeals are not automatically fallacies. The 107 accepted records are useful review data, **not 107 ready-made d1 MAIN benchmark cases**. Only the four Dekarldent fixtures currently have confirmed `project_main` labels and A/B structure.

Keep all records sharing any `source.group_ids` together when creating future partitions. Preserve MM-USED's `source.source_split`; English originals and their German translations must not land in different partitions. Catalog controls remain unreviewed, so they are not established false-positive controls.

## Rights and portability

No blanket license is assigned to this mixed collection. Source-specific attribution and rights remain in their registries. MM-USED declares CC BY 4.0 while its USED upstream declares CC BY-NC-SA 4.0; clarify the chain before publishing text or using it commercially. See [dataset research](../docs/datasets/ENGLISH_DATASETS.md).

**A git clone contains the shared schema, complete metadata/decisions, Dekarldent paraphrases and research adaptations—not the private MM-USED translations or English context blocks.** To recreate full local outputs, restore the existing `data/datasets/translation_review/dataset.json`; to also rebuild its review page, restore `data/datasets/mm_used/` plus the translation review's selection and translation inputs. Keep a separate backup of ignored `data/`. A metadata-only build is not a full-text dataset export.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Core shared/schema/review tests work without private data. Private translation/full-output integration tests explicitly skip if inputs are absent. Node.js is optional for the translation UI's JavaScript runtime test; no model server or GPU is required. Existing d1 snippet accuracy/latency measurements are unchanged.
