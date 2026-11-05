# First real-debate annotation candidates

## Source and limits

- WELT, **TV-DUELL: Remigration? Migration? Höcke (AfD) und Voigt (CDU) liefern sich Schlagabtausch bei WELT**.
- Published 2024-04-11; clip duration 21:08.
- Source: https://www.youtube.com/watch?v=C0IO0dApOMc
- Analysis based on all German automatic-caption events, downloaded with yt-dlp. No audio/video verification, model classification, or second human review performed.
- Speaker attribution inferred from conversational context, not verified diarization. Punctuation below is editorial. Quoted excerpts retain caption wording; other descriptions are paraphrases, not verbatim transcripts.
- This is an annotation memo, not a gold benchmark. Strong means strong textual evidence for a local rhetorical pattern, not a judgment about factual accuracy or a speaker's general intentions.
- Original captions, metadata, and timestamped working transcript remain in ignored `data/duel.*` files.

## 1. Strong candidate: whataboutism / tu quoque

**Context:** 02:04–02:24. Voigt contrasts CDU district-level migration measures with the record of AfD's district administrator in Sonneberg. His specific criticism is that the AfD administrator has implemented neither of the two measures he names.

**A — Voigt, 02:14–02:24:**

> „keine Bezahlkarte keine Arbeitsverpflichtung nichts“

**B — Höcke, 02:28–03:23:**

> „es war CDU Bundeskanzlerin Angela Merkel die die Grenzen geöffnet hat bzw nicht geschlossen hat“

Höcke goes on to blame CDU for migration-related costs and other harms, rather than answering the criticism about the AfD administrator's record.

**Why the label fits:** A challenges AfD's implementation record; B counters with alleged wrongdoing by A's party. The subject remains migration, so this is more specifically `whataboutism` than an unrelated `red_herring`.

**Scope matters:** From about 03:25 onward, Höcke does offer policy proposals in response to the moderator's earlier question. Do not label his entire contribution as pure evasion. This candidate concerns the opening rebuttal to Voigt's immediate criticism.

**Proposed main label:** `whataboutism`.

**Review status:** Single-pass caption analysis; strong candidate for independent review. Preserve the surrounding context when preparing benchmark input.

**Jump link:** https://www.youtube.com/watch?v=C0IO0dApOMc&t=124s

## 2. Possible strawman, but exclude from gold labels

**A — Höcke, approximately 05:42–07:07:** He prioritizes training people already in Germany, family policy, attracting emigrants back, and retaining trained workers. Around 06:00–06:08, an interrupted question and answer concern whether he rejects foreign recruitment in principle. The captions record the answer:

> „nicht grundsätzlich“

**B — Voigt, approximately 07:33–07:56:** He points to foreign doctors in Thuringian hospitals, then imagines Höcke being hospitalized under his own policy:

> „dann kommt dann irgendwann niemand wenn er den Knopf rückt“

**Why it is a candidate:** The hospital scenario can imply a much stronger exclusion of foreign staff than Höcke explicitly endorsed in this local exchange.

**Why it is not a clean strawman:** Voigt presents a predicted consequence of Höcke's policy, not necessarily a claim that Höcke explicitly demanded removal of all foreign doctors. Whether that consequence is justified requires policy evidence beyond this exchange. The interrupted captions around 06:00 also need audio verification. Höcke's subsequent objection does not itself prove a strawman occurred.

**Proposed main label:** Unresolved; do not assign `strohmann` as ground truth.

**Review status:** Ambiguous challenge case only.

**Jump link:** https://www.youtube.com/watch?v=C0IO0dApOMc&t=342s

## 3. Useful neutral control: direct answer to a concrete question

**A — Moderator, approximately 16:36–16:49:** Asks whether someone with German citizenship who enjoys Bosnian music and food at home may remain in Germany.

**B — Höcke, approximately 16:49–16:54:**

> „nein der darf bleiben wir haben das auch niemals in Abrede gestellt“

Here the initial negation occurs after a stay-or-leave question; the following clause gives an explicit answer that the person may stay. Höcke then discusses people present illegally, a distinct category.

**Why the label fits:** The immediate answer addresses the concrete hypothetical. Agreement with the surrounding politics is not required to recognize a direct answer. No clear fallacy appears in this short response.

**Proposed main label:** `sachlich`, limited to the immediate response. Do not infer `good_faith` or factual correctness solely from this.

**Review status:** Single-pass caption analysis; useful negative-control candidate, subject to speaker/audio confirmation.

**Jump link:** https://www.youtube.com/watch?v=C0IO0dApOMc&t=996s

## Tempting examples that should not become firm labels

- **09:31–11:17, disputed meaning of 20–30%:** Voigt and Höcke disagree about what an earlier speech meant. The source speech is not established by this clip. Neither the accusation nor the denial establishes a strawman.
- **11:56–14:07, book passage:** Both sides dispute the context of a quoted passage. The original surrounding text is required before judging distortion.
- **17:15–17:20, accusation of distorted words:** A complaint that the other side distorted a position is not itself a strawman by the complaining speaker. Accusation and commission require separate annotation.
- **14:31–15:55, repeated question about a book claim:** Candidate evasion, but the reply invokes missing context. Treat separately for review; current `MAIN` taxonomy has no `evasion` class, and forcing it into `red_herring` would obscure the distinction.

## Next annotation step

Independently review candidates 1 and 3 against the linked video. Confirm speaker boundaries and prepare faithful A/B excerpts before adding them to a scored benchmark. Keep candidate 2 and the disputed source quotations unscored. Do not balance the dataset by forcing ambiguous examples into fallacy classes.
