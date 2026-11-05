# English fallacy datasets and German translation feasibility

**Shared dataset entry point:** [datasets/README.md](../../datasets/README.md). This document records source research and the specialized translation-review workflow, not a separate final dataset.

## Result

**Yes: published English datasets exist, including annotated political-debate corpora.** The closest inspected source is **MM-USED-fallacies**. It is substantially closer to this project's spoken-debate setting than web teaching examples, but it is **not an exact drop-in dataset for all 42 patterns**.

Downloaded and inspected real files, not only paper abstracts or search summaries. [Research manifest](research_manifest.json) records source URLs, hashes, counts, and license evidence. Raw corpora and the German pilot stay under gitignored `data/`; no imported text or source labels were added to benchmark fixtures.

## Closest match: MM-USED-fallacies

- [Official repository](https://github.com/nlp-unibo/multimodal-am-fallacy)
- [Paper: EACL 2024](https://aclanthology.org/2024.eacl-short.16/)
- [Inspected data file](https://github.com/nlp-unibo/multimodal-am-fallacy/blob/main/local_database/MM-DatasetFallacies/no_duplicates/dataset.csv)
- [Repository license](https://github.com/nlp-unibo/multimodal-am-fallacy/blob/main/LICENSE)
- [Underlying USED release and license](https://github.com/pierpaologoffredo/IJCAI2022)

The inspected `no_duplicates/dataset.csv` is **tab-separated despite its extension**. Actual contents:

| Property | Verified count |
|---|---:|
| Labeled snippets | 1,057 |
| Distinct context blocks | 242 |
| Debates | 28 |
| Year range in this file | 1960–2012 |
| Main source categories | 6 |
| Neutral/non-fallacy cases | 0 |
| Snippets occurring literally in their source context | 1,057 |
| Snippets repeated within their own context, requiring span disambiguation | 20 |

Context blocks total roughly **283,000 English whitespace-delimited words**, versus **23,152 words in labeled snippets**. Translating snippets alone is much smaller, but loses argument context. Deduplicating context first avoids translating the same block repeatedly for different labels.

### Source categories

| Source label | Snippets |
|---|---:|
| `AppealtoEmotion` | 681 |
| `AppealtoAuthority` | 167 |
| `AdHominem` | 77 |
| `FalseCause` | 55 |
| `Slipperyslope` | 43 |
| `Slogans` | 34 |

Subcategories include loaded language, flag waving, appeal to pity/fear, false authority, popular opinion, circumstantial ad hominem, and **15 Tu quoque** snippets. Source categories are not automatically equivalent to this repository's labels. In particular:

- No dedicated **strawman**, **false dilemma**, or **anecdotal generalization** main class.
- Tu quoque is related to, but not interchangeable with, every instance of whataboutism.
- Loaded language, slogans, and emotional appeals are broader rhetorical categories; their occurrence does not by itself establish a logical fallacy.
- Examples retain source annotations, not newly approved project labels.

### Context, speakers, audio, and splits

Rows contain context text, the annotated snippet, component/relation labels, and English-audio alignment fields. Context blocks can concatenate multiple speakers without explicit speaker labels in this CSV. They are **not already clean, attributed A/B exchanges**; no opponent identity was invented during import.

Source splits are debate-disjoint in the inspected file:

| Split | Snippets | Debates |
|---|---:|---:|
| Train | 867 | 22 |
| Validation | 94 | 3 |
| Test | 96 | 3 |

No debate or identical context block crosses these splits. Preserve source grouping when translating; do not put English originals and German translations into different train/test partitions.

Audio timestamps locate **English recordings**. Translating transcripts does not create German speech data, validate German STT, or verify the original alignments. Recordings were not downloaded or listened to for this research.

## Other inspected candidates

| Dataset | What it provides | Fit and limitations |
|---|---|---|
| [ElecDeb60to20](https://github.com/pierpaologoffredo/ElecDeb60to20) | Real US debates, fallacy/component/relation annotations and separate speech-turn data. Inspected `fallacy_second_version.csv`: **2,744 rows**, six main categories, speaker field, 1960–2020. | Strong domain match, newer material than the inspected MM subset. No dedicated strawman class. Its [HF mirror](https://huggingface.co/datasets/MARIANNE-INRIA/ElecDeb60to20) declares **CC BY-NC-ND 4.0**, which matters for distributing translations. Do not conflate this release with the older USED license. |
| [MAFALDA](https://github.com/ChadiHelwe/MAFALDA) | **200 manually annotated gold records** with labeled spans, comments/explanations, and broader fallacy coverage. [NAACL 2024 paper](https://aclanthology.org/2024.naacl-long.270/). | Useful complement for strawman, false dilemma, circular reasoning, etc. Mixed text sources, not a clean collection of spoken A/B exchanges. Inspected file has 272 span entries, including `nothing` and `to clean` markers—not 272 confirmed fallacies. No explicit dataset reuse license found in inspected repository/card. |
| [CoCoLoFa](https://github.com/Crowd-AI-Lab/cocolofa) | Authors report **7,706 comments** attached to 648 news articles, eight fallacy types, reply links, and **3,130 `none` comments**. [Paper](https://arxiv.org/abs/2410.03457). | Useful contrastive/negative material and discussion structure. **Deliberately written by LLM-assisted crowdworkers**, not scraped spontaneous debate exchanges. No strawman/ad-hominem class among its eight types. No explicit reuse license found in inspected repository. Counts from authors' README, not an independent full-comment recount. |
| [LOGIC](https://github.com/causalNLP/logical-fallacy) | Educational fallacy examples. Inspected `edu_all.csv`: **2,452 rows**, including three miscellaneous rows; 2,449 after excluding those, across 13 other labels. [Paper](https://aclanthology.org/2022.findings-emnlp.532/). | Easier translation seed, weaker spoken-dialogue match. Mostly isolated examples; no neutral class in inspected file. [HF card](https://huggingface.co/datasets/tasksource/logical-fallacy) marks license unknown; source-webpage rights need attention. |

This is a researched shortlist, not a claim that every available English corpus was exhaustively searched.

## Translation rights: distinguish releases

The inspected sources have different license declarations:

1. MM-USED repository: **CC BY 4.0**.
2. Its older USED/ElecDeb60To16 upstream: **CC BY-NC-SA 4.0**. This permits adaptations under its conditions, including noncommercial and share-alike requirements.
3. The newer ElecDeb60to20 HF mirror: **CC BY-NC-ND 4.0**. ND does not allow sharing translated/adapted material under that license without additional permission; it does not mean all private noncommercial adaptation is forbidden.

Do not assume the MM repository's BY declaration removes upstream restrictions, or that every release of the corpus has identical terms. Keep attribution and source hashes. Clarify the license chain before publishing a German corpus or relying on commercial-use permission. The current pilot remains local/private in ignored `data/` for that reason. This project has not assigned a new blanket license to imported data.

## Work completed locally

### Normalized English corpus

```text
data/datasets/mm_used/contexts_en.jsonl    # 242 unique context blocks
data/datasets/mm_used/cases_en.jsonl       # 1,057 source annotations
data/datasets/mm_used/manifest.json        # hashes, counts, source/split/license notes
```

Every case references its context, preserves source labels and original split, and records all exact English span candidates. Repeated text is flagged rather than arbitrarily aligned. German fields remain `null`; these files do **not** claim a completed translation.

Rebuild from the downloaded source, without model or network calls:

```bash
python scripts/prepare-debate-corpus.py \
  data/dataset_research/mm-no-duplicates.csv
```

### German translation pilot

```text
data/datasets/mm_used/translation_pilot_de.md       # readable bilingual review
data/datasets/mm_used/translation_pilot_de.jsonl
data/datasets/mm_used/translation_pilot_manifest.json
```

**12 examples translated: two per source category**, with original English, German labeled snippet, German cropped context, source IDs, English-audio timestamps, and translation notes. Each German snippet has a newly computed span inside its translated context window.

These are **assistant-produced, human-unreviewed translations**, not human-validated gold labels. Only selected context windows were translated, not the complete 242-block corpus. Source labels were preserved even where questionable; translation was not used to silently repair annotation judgments. No fictional German speaker pair, synthetic counterargument, or German audio was added.

### Larger local translation review batch

```text
data/datasets/translation_review/index.html          # offline, searchable review UI
data/datasets/translation_review/dataset.json        # bilingual data + original English contexts
datasets/reviews/mm_used.json                       # authoritative user judgments (tracked)
scripts/build-translation-review.py                 # deterministic build and validation
```

**150 MM-USED snippets:** the original 12-case pilot plus 138 additional translations, spanning 28 debates and 112 source contexts. The latest continuation retains all 120 earlier examples and adds 30 passages. Sampling preserves source splits and labels, includes all 15 available `Tu quoque` rows, and covers the six source categories. It is coverage-oriented—not random, representative, or correctness-screened. All 150 English source passages remain beside their German translations; the full context is English. Twelve selected passages also have previously translated, explicitly cropped German context windows. No clean A/B dialogues or speaker identities are invented. This batch contains **no neutral controls**.

Open `data/datasets/translation_review/index.html` locally. Only source-label agreement needs review; the user requested no per-example translation rating. German corrections and notes remain optional. Search/filter by source class and subcategory; export review decisions as JSON, and import them later. Compatible exports from the original 100- and 120-example batches remain importable, with earlier translation judgments preserved as metadata. Changes are not automatically saved; export before closing. Data stays under gitignored `data/`; exported review files also stay local. Translations remain attributed to the assistant; waiving translation review does not mark them individually human-validated. Source labels are the dataset's annotation, not validated findings. Short slogans/fragments and questionable source judgments need context and review. No German audio is included.

User exports are persisted into `datasets/reviews/mm_used.json` using `--import-review` (custom `--directory` builds use their own local `review.json`). The builder validates batch/source identity, IDs, allowed judgments, notes, and corrections before applying changes. Subsequent rebuilds reload saved decisions and prefill the HTML controls. Source labels and original translations remain unchanged; disagreement is not a neutral label, uncertainty is not acceptance, and notes suggesting alternate categories are not automatic relabelings. Browser edits still require a new export/import to persist.

Current local review: **103 agree, 4 disagree, 42 uncertain, 1 pending**; two notes retained, no German corrections. These are user judgments about source labels, not individually validated German translations or benchmark gold labels.

The reproducible script checks selected IDs/text against the source, translation coverage, exact English span candidates, and pilot translation windows. Import/rebuild/check:

```bash
python scripts/build-translation-review.py --import-review ~/Downloads/mm-used-de-review-150-v3-review.json
python scripts/build-translation-review.py
python scripts/build-translation-review.py --check
python scripts/build-shared-dataset.py
```

Keep this research material out of validated training/evaluation fixtures until source labels have been reviewed and translation quality meets the intended use; the optional-review workflow itself establishes neither. Do not use the zero-neutral batch to estimate false-positive rates. Rights-chain note is recorded inside the private data; clarify before redistribution or commercial reuse.

## Full German version: required safeguards

- Translate context blocks once; retain debate, split, case, and source IDs.
- Preserve negation, quantifiers, modality, rhetorical force, repetitions, quotations, and speaker attribution where actually available.
- Preserve US names, institutions, and claims; do not rewrite debates as German political scenarios.
- Re-align labeled spans in German. English character offsets cannot be copied onto a translation.
- Review translation fidelity separately from whether the source fallacy label is defensible.
- Add independently reviewed neutral controls before measuring fallacy detection or false-positive rates; a positive-only six-class corpus cannot supply those metrics.
- Use broader supplementary corpora for missing categories only after checking provenance and rights.
- Keep translated text separate from German-original debates in any future evaluation.

**Recommendation:** use MM-USED as a real-debate seed, not as a complete substitute for the project's taxonomy or German-original evaluation data. The current 150-passage batch and review decisions feed the shared dataset; only explicitly accepted annotations enter its accepted bucket.
