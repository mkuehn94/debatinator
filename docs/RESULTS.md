# Results (2026-11-01, M1 Max, d1-3B MLX 8-bit)

## 1. Clean snippets (`eval/snippets.py`)
12 hand-written German pairs: A states a position, B answers with one labeled pattern.

| Variant | Result | Latency |
|---|---|---|
| 8 × `noul` (one yes/no per trick), threshold 0.5 | recall 1.0, **precision 0.42**: red_herring fires on almost every bad answer (0.8–0.97) | 0.8–1.3 s |
| **1 × `choice`** "which pattern fits best" | **11/12**; only miss: whataboutism → red_herring | **~200 ms** |
| school of thought (`choice`, 5 options) | 7/12, drifts to "neutral" | – |

→ Main label via `choice`; `noul` only for flags that are not mutually exclusive.

## 2. Real duel, fixed 20 s windows (WELT TV duel Höcke vs. Voigt, 21 min, YT auto captions)
- 63 windows, 0.5 s median. steelman 27 (!), strohmann 14, sachlich 10, red_herring 6, …
- Probabilities low (0.25–0.5). With p ≥ 0.4: 26 hits, ~10 plausible.
- steelman = catch-all bucket (quoting the opponent, listing one's own program). Moderator transitions → red_herring.
- Cause: no punctuation, no speakers, windows mix both politicians and the moderator.

## 3. Real duel, per speaker turn (`eval/diarize.py` + `eval/turns.py`)
- pyannote community-1, 3 speakers, ~1 min for 21 min audio (MPS). Moderator = least talk time, skipped.
- `choice` without steelman/good_faith + 2 `noul` positives; trick only at p ≥ 0.5.
- 26 politician turns → 19 sachlich, 4 strohmann, 2 red_herring, 1 falsches_dilemma; positives never ≥ 0.7. ~1.1–1.2 s per turn.
- Spot-check of the 7 hits (one reviewer, not a gold standard): ~4 plausible
  - ✓ dodging the question about one's own book quote (2×) → red_herring (really: **evasion**)
  - ✓ "Sie verdrehen mir das Wort im Mund" → strohmann, but labeled on the turn of the one **complaining** about it
  - ✗ "nein nein nein" → falsches_dilemma; a literal book quote → strohmann

## Learned
1. Speaker separation is required; analyze turns, not time slices.
2. Add **evasion**; split **strawman accusation** from strawman.
3. Split long turns; keep the opponent's last turn as context.
4. Positives as separate `noul` with a high threshold.
5. Clean snippets overestimate quality a lot. Need a small labeled real-debate set as a benchmark.
