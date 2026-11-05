# Debate classification fixtures

These are the authoritative Dekarldent source records. They also appear in the [shared dataset](../../datasets/README.md), alongside translated passages and unreviewed research examples. Edit fixtures here, then run `python scripts/build-shared-dataset.py`.

`debate_cases.json` stores timestamped, user-reviewed exchanges for the main classifier in `eval/taxonomy.py`.

Current set: **4 cases — 2 `strohmann`, 1 `whataboutism`, 1 `ad_hominem`.** These are selected positive examples, not a representative accuracy benchmark or a false-positive test set.

## Text provenance and review

- `text_kind: caption_based_paraphrase` means A/B inputs are German editorial paraphrases of real captioned exchanges, **not verbatim transcripts**. Do not report results on these inputs as results on original raw debate transcripts.
- `review.label_status: user_confirmed` records explicit user acceptance of the main labels after reviewing the assistant's analysis. It does not imply listening verification or blind independent annotation.
- Original caption files are under ignored `data/`; source URLs and spans allow retrieval without committing full transcripts.
- `expected_positives: null` means **not annotated**, not that all positive flags are false.
- Times are seconds relative to the linked upload. Caption boundaries are approximate; verify against audio before producing a verbatim fixture version.
- Participant claims are not independently fact-checked or endorsed.

## Fields and evaluation

Each case includes:

- Stable `id` and `source_id`, linked to root `sources` metadata.
- `a` and `b`: contextual contribution and response to classify. A/B roles are local to each case, not fixed speakers.
- `context`: additional background, particularly important when a short personal aside responds to a pending substantive argument.
- `a_speaker`, `b_speaker`, and separate source spans.
- `expected_main`: user-confirmed label using existing `MAIN` taxonomy keys.
- `rationale` and `scope_note`: why the label applies and which part of the conversation it covers. These are annotation metadata, **never model input**.

A future runner should construct input from `context`, `a`, and `b`, for example:

```python
state = f"Kontext: {case['context']}\n\nA: {case['a']}\n\nB: {case['b']}"
```

Use `MAIN`, `POSITIVE`, and existing decision thresholds from `eval/taxonomy.py`. Do not use the separate historical `CHOICE` question in `eval/snippets.py` as a substitute: it has different classes. No benchmark runner is introduced by these fixtures.
