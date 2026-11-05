# German fallacy examples for review

This is the research authoring/review collection, not the final accepted dataset. All 152 examples also appear as **pending** records in the [shared dataset](../../datasets/README.md). Search leads in `discovery.json` are not example records and are not merged into it.

**Open [`index.html`](index.html).** Works directly from disk: no server, external scripts, fonts, APIs, or model connection.

```bash
xdg-open docs/fallacies/index.html
```

Quick buttons: **Neue Recherche**, **Echte Forumswechsel**, **Politische Redepassagen**, **Bestrittene Quellenlabels**. Filters combine search, repository coverage, provenance, assessment, material type, classification basis, and collection batch.

## New: search-only discovery queue

**Open [`discovery.html`](discovery.html)** for additional unreviewed source leads, separate from the 152 A/B examples. Explicit searches cover every existing pattern; named-debate searches and reference-link follow-ups supplement those searches. German-first, with English fallback material.

- [`DISCOVERY.md`](DISCOVERY.md): scope, coverage gaps, retrieval limits, and how to resume.
- [`discovery.json`](discovery.json): source URLs, short search excerpts, query associations, reference paths, cache hashes, and retrieval status.
- [`discovery_queries.json`](discovery_queries.json): explicit per-pattern query plan.
- [`discovery_source_urls.json`](discovery_source_urls.json): bounded page-fetch allowlist.
- [`discovery_reference_urls.json`](discovery_reference_urls.json): topic pages whose reference links were followed.

**Search tags are not fallacy labels. A search hit is not a verified debate, call-out, quotation, or popularity measurement.** Gaps stay visible. No leads promoted into examples, training data, or evaluation fixtures.

Other views:

- [`RESEARCH.md`](RESEARCH.md): latest research scope, useful starting cases, and limitations.
- [`examples.md`](examples.md): readable German examples and explanations.
- [`catalog.json`](catalog.json): canonical editable examples, schema 2.
- [`sources.json`](sources.json): attribution, URLs, access dates, document hashes, and rights notes.
- [`research_log.json`](research_log.json): latest candidate-by-candidate retrieval and selection audit.
- [`source_urls.json`](source_urls.json): explicit collector allowlist; includes rejected and inaccessible candidates, **not only accepted references**.

## Collection size

**42 patterns, 152 A/B examples**, including all seven existing repository fallacy labels. Extensions include debate tactics and cognitive biases, not just formal logical errors. Categories overlap; these are not 42 exhaustive, mutually exclusive classes.

| Provenance | Examples |
|---|---:|
| Concrete retrieved scenarios, paraphrased into A/B form | 132 |
| Newly written teaching examples from the first collection | 14 |
| Newly written negative controls from the first collection | 6 |

Assessments: **109 proposed error examples, 25 non-fallacious cases, 18 context-dependent cases**. All remain unreviewed.

### Latest expansion

**106 additions, zero new synthetic examples.** Followed source links, forum parents/replies, and thread pagination; did not turn search summaries into examples.

- **85 distinct candidate URLs across 41 hosts**, represented by 86 discovery records because one URL occurred twice.
- **73 distinct pages/documents retrieved successfully**: 74 successful source records, including that duplicate.
- **59 new source records from 31 hosts actually used** in examples or essential context. The full collection has 93 source records; neither URLs nor host counts imply independent authorities.
- Blocked, robots-disallowed, timed-out, irrelevant, and definition-only candidates remain visible in the audit.

The additions distinguish:

| Material | New examples |
|---|---:|
| Website teaching scenarios | 77 |
| Actual written forum exchanges | 10 |
| Examples, jokes, or remembered sayings posted in forums | 8 |
| Political speech passages checked against official transcripts | 4 |
| Political remarks reported only by secondary sources | 5 |
| Historical illustrations / parables | 2 |

**A lesson hosted on a forum is not automatically a real exchange. A hypothetical Nationalrat scene is not an actual parliamentary record. A German translation of a US speech is not German-original speech.** The metadata preserves these distinctions.

## Source families

New material includes Seniorentreff, Allmystery, Amerika-Forum, ICE-Treff, Netz-Treff, Shia-Forum, Taucher.Net, Prüfpunkt, Mimikama, Studyflix, Der goldene Aluhut, HOHE LUFT, Forum für Streitkultur, state teacher-training material from Baden-Württemberg, Hochschule Fulda, DRZE, Humanistische Union, and rhetoric/communication websites.

Political passages include:

- Three passages from the **Bundestag debate of 13 November 2014**, checked in official **Plenarprotokoll 18/66**. These are marked context-dependent risk arguments, **not three proven fallacies**.
- George W. Bush's **20 September 2001** speech, checked in the archived White House transcript and paraphrased in German. Original language explicitly `en`.
- Five secondary-source reports, including remarks attributed to Christian Lindner, Tilman Kuban, Joseph McCarthy, and Donald Trump. Their original recordings were not verified.

Earlier sources remain German Wikipedia, Quarks/WDR, and Schopenhauer's *Die Kunst, Recht zu behalten*.

## Review and provenance

**Every label remains `needs_user_review`.** Separate from the four user-confirmed real-debate cases in `eval/fixtures/debate_cases.json`. No classifier taxonomy, training data, evaluation fixtures, or benchmark scores changed.

Each pattern has `id`, German name/definition, `kind`, `repo_label` or `null`, sources, and a caution about legitimate lookalikes.

Each example has:

- Stable `id`; German `a`, `b`; optional context. **Assessment targets B in that context, not the person.**
- `origin`: `source_example_adaptation`, `synthetic_from_definition`, or `synthetic_control`.
- `source_locator`: section, post/date, or transcript page; editorial additions are identified.
- `proposed_label`, `assessment`, explanation, and source references.
- `setting`: website lesson, forum lesson, actual forum exchange, secondary-reported political remark, transcript-checked speech, or historical illustration.
- `dialogue_status`: adapted dialogue, compressed exchange, editorial A/B setup, or constructed dialogue. Even transcript-checked monologues can have an **editorial A prompt, not a real preceding speaker**.
- `label_basis`: `source_explicit`, `editorial_interpretation`, or `editorial_disagreement`.
- Optional `source_claimed_label` when the source's wording differs or needs special treatment.
- Per-example review status; latest additions have `collection_batch`.

Transcript-checked speeches additionally carry speaker, date, and `verification: official_transcript_checked`. **No new passage is audio-verified.**

### Do not inherit source errors

Several source classifications are deliberately disputed:

- Lindner's preference for not governing over governing badly does not, by itself, claim there are only two possible options.
- A warning about a traffic fine can be a relevant practical reason, not a fallacious threat.
- A valid deduction from a general medication premise is not automatically circular; the premise may still need evidence.
- Explicit clarification questions, humor, consistent standards, and evidence-backed risk concerns are not automatically fallacies.

Mimikama discloses possible AI-assisted drafting; its illustrative dialogues are not evidence of actual debates. The collection is not politically or statistically representative, does not measure popularity, and cannot establish intent from a transcript alone.

Before promoting any case into evaluation fixtures: review its label, verify sufficient context, decide whether an adaptation is acceptable, obtain faithful source text if necessary, and add matching negatives. Do not report teaching-example accuracy as real-debate performance.

## Reproduction and access policy

Collector uses `requests`, a descriptive user agent, robots checks, sequential source requests, and at least 1.5 seconds between page requests. No login, paywall, CAPTCHA, or certificate restrictions were bypassed. Reddit was excluded by robots; Gutefrage, LEO, and religionsforum could not be retrieved through this environment.

```bash
# Cache missing allowlisted pages; default stops on access denial/rate limiting.
python scripts/collect-fallacy-sources.py

# Skip failed hosts, continue other hosts; previously denied hosts remain skipped.
python scripts/collect-fallacy-sources.py --keep-going

# Explicit refresh, not an automatic access-control workaround.
python scripts/collect-fallacy-sources.py --refresh

# Regenerate offline views after curated data edits.
python scripts/render-fallacy-catalog.py
python scripts/render-fallacy-catalog.py --check
python -m unittest discover -s tests -v
```

PDF extraction optionally requires the system utility `pdftotext` (Poppler). Its raw PDF hash identifies the original document, not extracted text. A failed extraction is logged rather than interpreted as evidence.

Raw HTML/PDF/text, search-discovery caches, and working manifests remain under ignored **`data/`**. Tracked files contain short original paraphrases and commentary, not a redistributed bulk scrape. `sources.json` and `research_log.json` are curated snapshots: refreshing caches does **not** silently update their hashes, revisions, classifications, or reviewed locators.

## Attribution and reuse

- Wikipedia-derived adaptations link to revisions and credit contributors. Article text is generally CC BY-SA 4.0, with exceptions for embedded material. Follow applicable attribution/share-alike requirements.
- Schopenhauer's original German work is public domain in Germany; website layout and editorial additions are not assumed public domain.
- No open redistribution license was verified for most new sources. Brief paraphrases do not relicense their original text, images, recordings, or user posts.
- Forum pseudonyms/profiles are not copied into example text. Links and post locators preserve inspection context; labels concern arguments, not assessments of individual users.
- No books were unlocked, bought, or bulk-copied. Public availability is not blanket redistribution permission.
