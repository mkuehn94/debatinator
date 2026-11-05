# MM-USED source and translation rights

Current dataset: [107 accepted examples](../../datasets/README.md), comprising four German-original Dekarldent exchanges and **103 accepted German translations** of MM-USED passages. Uncertain/rejected translations and the unreviewed research catalog were removed; older research notes and review tooling remain in git history.

## Source

- [MM-USED official repository](https://github.com/nlp-unibo/multimodal-am-fallacy)
- [EACL 2024 paper](https://aclanthology.org/2024.eacl-short.16/)
- [Inspected source TSV](https://github.com/nlp-unibo/multimodal-am-fallacy/blob/main/local_database/MM-DatasetFallacies/no_duplicates/dataset.csv)
- [Underlying USED release](https://github.com/pierpaologoffredo/IJCAI2022)
- [Original research manifest](research_manifest.json): source URLs, hashes, corpus counts and license evidence. This is provenance history, not a list of accepted examples.

The inspected source contains 1,057 labeled English snippets from US political debates, with 242 context blocks and six broad source categories. These are source-corpus counts, **not** current dataset counts. Only the 103 passages with explicit user agreement remain selected.

Source labels and subcategories remain verbatim. They are not automatically equivalent to this project's main classifier labels. In particular, tu quoque is not every instance of whataboutism, and slogans/emotional language are not inherently logical fallacies.

## Translation and evidence

- German text is assistant-translated, not independently human-validated translation.
- The user waived per-example translation ratings and reviewed label agreement instead.
- Names, US institutions, negation and claims are retained rather than rewritten as German political situations.
- English context remains available; only explicitly marked cropped German context windows were translated.
- No clean A/B dialogue or speaker identity was invented for these passages.
- Source audio timestamps refer to English recordings and were not audio-verified. Translation does not create German speech data or validate German STT.
- Source split, debate/context groups, original IDs and exact span candidates remain preserved in accepted records.

## Rights

The MM-USED repository declares **CC BY 4.0**. Its older USED upstream declares **CC BY-NC-SA 4.0**. Do not assume the downstream BY declaration removes upstream restrictions. The newer ElecDeb60to20 release has different license evidence and must not be conflated with this selected MM-USED source.

No new blanket license is assigned to imported text. Keep attribution, source hashes and modification notes. Clarify the rights chain before redistribution or commercial use. Full English contexts and German translations therefore stay local under gitignored `data/`; only accepted metadata and judgments are committed.

Accepted private source: `data/datasets/accepted_mm_used.json`. Rebuild with `python scripts/build-shared-dataset.py`. Keep a separate backup: git hashes/metadata cannot recreate translated text.
