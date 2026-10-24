# Merging the two custom FDB v1.0 scorers on main

## State
main has two custom v1.0 scorers besides the pinned official evaluator:
- `unified_v10.py` (`unified-score`, definitions `fdb-v1.0-unified-3`): ASR word onsets only, on the reference tree. Pause intrusion reads pause.json; turn-taking partitions eligible samples into early_start / response / no_response, early starts stay in the denominator; Wilson / bootstrap intervals, selected bounds, quantiles that invert the response-rate curve. No backchannel metric. Interruption cannot tell talking through from a fast reply (transcript is cropped at R).
- `v10_scoring.py` (`score`, `fdb-v10-synthetic-v4`): official whole-window takeover rule for pause (ignores pause.json); Silero VAD gates: turn-taking samples with VAD speech at E are `spoke_before_turn_end` and EXCLUDED; interruption samples with no VAD speech at onset S are `not_exercised`, a VAD segment from <=S to >R is `talked_through`, both EXCLUDED; backchannel from VAD segments (segment >=1 s or >2 words = takeover, else backchannel), rate per s, timing JSD vs the ICC human distribution, no backchannel -> JSD 1.
Goal: keep one custom scorer (unified_v10) and delete v10_scoring / v10_evaluation and the `transcribe`/`score` subcommands. The runbook does not call them.

## Data (real captures)
Reference tree output.wav is the full FIFO playout in [0,T]; the official ASR crops at R into a temp file only, so VAD can run on the tree.
Nemotron (native full duplex), synthetic_user_interruption, n=200, Silero defaults:
- not_exercised 87 (83 had spoken and stopped a median 1.32 s, p90 3.0 s before S; 4 never spoke before S); 85 of the 87 have words after R, so unified-3 currently scores them as responses.
- talked_through 0; exercised 113, all respond after R.
- Sweep threshold {0.3,0.5,0.7} x min_silence_ms {50,100,300,500}: not_exercised 84-91, talked_through 0-3 (sweep_nemotron.jsonl).
Turn-taking, VAD onset before E vs ASR onset before E, 5 systems (n=119 each, Nemotron and 4 half-duplex Qwen3-Omni turn detectors): VAD-only early starts 1, 2, 0, 1, 1; ASR-only early starts 0, 4, 3, 0, 1; VAD speech exactly at E is a subset of ASR early starts in all 5.
Official eval_backchannel.py (attached): appends every <=3 s segment to the backchannel list even when it classified it as a takeover, and TOR is overwritten per segment rather than OR-ed; its per-segment classification equals v10_scoring's (>=1 s or >2 words).

## My proposal (written before review)
1. Interruption: compute VAD on output.wav. not_exercised leaves the interruption denominator (nothing was interrupted) and is reported as `exercised_rate` over eligible with Wilson CI; talked_through becomes a fourth outcome counted as a failure (no latency, infinity in quantiles) with its own rate. Response rates and latency are over exercised samples. Paired comparisons use samples exercised in both systems.
2. Turn-taking: no VAD; ASR-onset early_start stays. The VAD signal changes 0-2 samples per system and disagrees in both directions near E, so a second OR-ed detector adds a rule without changing results.
3. Backchannel: port v10_scoring's per-segment rule. Metrics: takeover_rate (samples with any takeover segment, Wilson), backchannels_per_min (pooled count over pooled seconds, bootstrap), timing_jsd mean with bootstrap; samples without backchannels get JSD 1 as in the official evaluator.
4. VAD config: Silero defaults (threshold 0.5, min speech 250 ms, min silence 100 ms, pad 30 ms), the same as the official backchannel evaluator; report the sweep.
5. Delete v10_scoring.py, v10_evaluation.py, `transcribe`/`score`, and their docs.

## Questions
(a) Is excluding not_exercised defensible, given it is system-dependent (short answers -> fewer exercised samples, a silent system is never measured)? Better alternatives?
(b) talked_through as a failure in the denominator vs exclusion?
(c) Is dropping VAD from turn-taking right?
(d) Backchannel metric set and the JSD=1 convention.
(e) What would a reviewer attack first?
