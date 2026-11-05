# Search-only discovery batch

**Open [discovery.html](discovery.html).** Offline search, per-pattern filters, URL-format filters, page-cache status, and video-view-count sorting. Existing [index.html](index.html) links to this separate queue.

```bash
xdg-open docs/fallacies/discovery.html
```

## Scope

- **341 search attempts:** 282 Bing queries and 59 YouTube searches.
- **All 42 existing patterns searched separately on both platforms.** Video searches include 42 per-pattern queries, 12 named-debate/call-out searches, and five English fallbacks for initially empty categories.
- **433 additional source leads across 192 hosts.** Routine HTTP/HTTPS, www, and mobile-Wikipedia aliases merged; known reference aliases excluded. Similar articles at different URLs can still duplicate content. Hosts are not independent authorities.
- **164 video-URL leads:** 161 have video-search metadata; three came only from reference links. Channels, approximate search-time view counts, and durations retained where supplied.
- **61 source-page texts cached locally** from a bounded 160-URL page-fetch selection.
- Reference links followed through **30 previously cached German topic pages and 10 additionally retrieved English topic pages**. Reference paths retain parent URL, locator, retrieval date, cache path, hash, and revision ID where available.

These are **source leads, not 433 A/B examples or verified fallacies**. Existing 152 examples, classifier taxonomy, training data, and evaluation fixtures remain unchanged. Every lead remains `unreviewed_search_lead`.

All 42 patterns currently have at least one new lead after English fallback searches. This does **not** mean every pattern has a verified real-debate example or German-original example. The coverage table tracks search associations, not confirmed occurrences. The repository's 42 patterns include debate tactics and cognitive biases; they are not an exhaustive list of all logical fallacies.

## Named-debate starting points

These descriptions identify search results, not findings about the speakers:

- [Explicit Whataboutism-titled Lanz clip](discovery.html#lead-00c6fb620326).
- [Lanz–Ulrich Siegmund rhetoric analysis](discovery.html#lead-bfd93cc95539).
- [Merz–Scholz duel rhetoric analysis](discovery.html#lead-d6ce4a592352).
- [Höcke–Voigt duel/body-language analysis](discovery.html#lead-7f1adbc3de96).
- [Video titled as an ad-hominem example from the 2020 US presidential debate](discovery.html#lead-51c7b73a67a3).
- [Reference to Mehdi Hasan's Trump/Gish-gallop article](discovery.html#lead-5a0045f462f4): page access denied; retained as a reference lead, not a retrieved article.

Use **Video-Hinweis**, search for participant names, then sort by **Video-Aufrufe**. Counts are approximate search metadata, not independently checked audience measurements. Original footage, analyses, reactions, lessons, satire, and potentially misleading uploads are not yet reliably separated.

## What was—and was not—done

Search terms explicitly targeted each pattern, common German/English names, debate accusations, forums, and named TV/interview participants. Compound spellings and simpler queries supplemented poorly performing searches. Counts describe attempts, not necessarily distinct query strings or independent sources.

Bing returned many grossly off-topic results. Topic-term and argument-context screening removed obvious irrelevant hits. Video screening used title terms or named-debate context; it did not inspect arguments. Reference links are topic associations, not proof that a cited article contains a debate or endorses a classification. Literal-use and etymology-only reference sections were excluded where section back-links identified them. Short citation titles were capped; some unvisited references retain generated host-only titles.

**No videos watched, media downloaded, transcripts verified, timestamps located, or labels audited.** A title or snippet alleging a fallacy remains its publisher's claim. A rhetoric/body-language analysis may contain no relevant fallacy at all. Search titles can be translated, sensationalized, edited, or misleading; authenticity and original language are unverified.

Material includes moderated TV. There is **no moderator-free, recency, or measured-popularity guarantee**. English material supplements German discovery; it is not silently presented as German-original speech.

## Retrieval snapshot

Of the 160 selected page URLs:

| Status | URLs |
|---|---:|
| Page text cached, HTTP 200 | 61 |
| Redirect recorded but not followed by the bounded parallel fetch | 45 |
| Robots disallowed | 16 |
| HTTP 403 | 11 |
| Fetch/robots errors | 10 |
| Host skipped after an earlier access failure | 12 |
| HTTP 404 / 405 / 410 | 5 |

Another **112 leads were not selected for page fetching**; **161 have video-search metadata only**. A cached page may still be a definition, access notice, irrelevant discussion, or incomplete extraction. HTTP 200 is not semantic verification.

Google reached a traffic-verification challenge, Qwant returned HTTP 403, and Mojeek returned a CAPTCHA. Those paths stopped. Existing blocked search services were not retried. No login, CAPTCHA, paywall, or robots restrictions bypassed. Source requests were bounded and throttled; parallel page fetching used independent host groups. Redirects in that bounded pass were recorded rather than silently followed outside the explicit URL set.

## Files and reproducibility

- [discovery.json](discovery.json): frozen review queue, query records, query associations, reference paths, retrieval metadata, and coverage counts.
- [discovery_queries.json](discovery_queries.json): explicit search plan, including platform and search intent.
- [discovery_source_urls.json](discovery_source_urls.json): 160-URL page-fetch selection.
- [discovery_reference_urls.json](discovery_reference_urls.json): reference-parent allowlist.
- `data/fallacy_search_leads/`: raw search HTML, flat video-search metadata, and query logs; gitignored.
- `data/fallacy_sources/`: page HTML/PDF, extracted text, and shared retrieval manifest; gitignored.

Page hashes identify retrieved bytes. Video-query hashes identify search-metadata snapshots, **not video content**. Search rankings and view counts can change. Read cached `.txt` files for local text inspection; the review HTML loads no remote resources unless a source link is clicked.

To fetch the bounded page list with the regular collector:

```bash
python scripts/collect-fallacy-sources.py \
  --sources docs/fallacies/discovery_source_urls.json --keep-going
```

The collector updates the local cache/manifest. It does **not** automatically update this frozen discovery JSON or annotations. Do not use `--refresh` to retry denied hosts. Reconcile retrieval metadata deliberately before publishing a later snapshot.

Regenerate/check the offline view without network access:

```bash
python scripts/render-fallacy-discovery.py
python scripts/render-fallacy-discovery.py --check
python -m unittest discover -s tests -v
```
