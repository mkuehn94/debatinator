# Results (2026-11-01, M1 Max d1-3B MLX 8-bit + Linux RTX 4070 Ti SUPER d1-2B GGUF Q8_0)

## 1. Clean snippets (`eval/snippets.py`)
12 hand-written German pairs: A states a position, B answers with one labeled pattern.

| Variant | Result | Latency |
|---|---|---|
| 8 × `noul` (one yes/no per trick), threshold 0.5 | recall 1.0, **precision 0.42**: red_herring fires on almost every bad answer (0.8–0.97) | 0.8–1.3 s |
| **1 × `choice`** "which pattern fits best" | **11/12**; only miss: whataboutism → red_herring | **~200 ms** |
| school of thought (`choice`, 5 options) | 7/12, drifts to "neutral" | – |

→ Main label via `choice`; `noul` only for flags that are not mutually exclusive.

### d1-2B GGUF Q8_0 on llama.cpp — Linux, RTX 4070 Ti SUPER (2026-11-01)
Arch Linux, llama.cpp `0.8.0-dev` (b12032, prebuilt CUDA 12.8 x64), driver 615.78.08, 16 GB VRAM fully offloaded (`-ngl 999`), `/v1/systemone`, Python 3.14.9. Two independent runs on the same machine (setup run + manual rerun), `snippets.py choice`:

| | Run 1 (setup) | Run 2 (rerun) |
|---|---|---|
| top1 `choice` | 10/12 | 10/12 |
| per-case labels + probabilities | identical (2 decimals) | identical (2 decimals) |
| median (snippets.py) | 337 ms | 326 ms |
| mean ± sd | 341.5 ± 17.4 ms | 327.8 ± 16.0 ms |
| p90 / min–max | 360 / 325–387 ms | 330 / 315–376 ms |

- pooled latency: median 329 ms, 334.6 ± 17.8 ms → run-to-run spread across the two runs is only ~3 %.
- same 2 misses in both runs: good_faith → whataboutism (p 0.23), ad_hominem → red_herring (p 0.32) — the known class-overlap pairs. Slowest case in both runs is no. 7 (steelman, longest text, 376–387 ms) → latency scales with turn length.
- **top1 = 83.3 %, Wilson 95 % CI [55–95 %]**: with n = 12 every single miss is within noise; the labeled real-debate benchmark (Learned 5) is the real gate.
- vs M1 Max d1-3B MLX (11/12 @ ~200 ms): accuracy not distinguishable (McNemar exact, 3 discordant cases, p = 1.0); latency ~1.6× — but this confounds backend and model size (2B GGUF Q8_0 vs 3B MLX), not a clean backend-only number.
- per-case probabilities are bit-stable across runs → snippet set is regression-grade for taxonomy changes.

- maybe need to take a closer look at those 12 examples and add more.

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
