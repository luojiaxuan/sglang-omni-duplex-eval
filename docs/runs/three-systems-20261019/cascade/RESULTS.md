# FDB results: cascade

Repeats: repeat-1. Judge: qwen.

## FDB v1.5 results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 100 | 100 | 0.204 | 1.056 | 74.0% | 15.0% | 8.0% | 3.0% | 100 |
| user_interruption | 25 | 25 | 0.159 | 1.130 | 96.0% | 4.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 25 | 25 | 0.187 | 1.045 | 16.0% | 56.0% | 24.0% | 4.0% | 25 |
| talking_to_other | 25 | 25 | 0.206 | 1.031 | 92.0% | 0.0% | 4.0% | 4.0% | 25 |
| background_speech | 25 | 25 | 0.286 | 1.016 | 92.0% | 0.0% | 4.0% | 4.0% | 25 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 53.1% | 98.0% | 100.0% | 97.0% | 71.9% | 89.0% | 46.7% | 90.0% |
| user_interruption | 100.0% | 100.0% | 100.0% | 100.0% | 95.0% | 80.0% | 95.0% | 80.0% |
| user_backchannel | 95.8% | 96.0% | 100.0% | 96.0% | 100.0% | 96.0% | 95.5% | 88.0% |
| talking_to_other | 12.5% | 96.0% | 100.0% | 92.0% | 40.0% | 80.0% | 4.3% | 92.0% |
| background_speech | 4.0% | 100.0% | 100.0% | 100.0% | 52.0% | 100.0% | 4.0% | 100.0% |

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `7f04e0f3b398d29af2787890033b03d2f70ffcff6f4b1e64dfdee3f98d0aff54`; ASR `e5e0e2f2c781990ed54248eb0dedb3123db5f5264369acb50135a0aa874923b1`.

| Subset | Declared | Selected | Eligible | Ineligible | Coverage | Ineligible reasons | Minimum observable horizon after reference |
|---|---:|---:|---:|---:|---:|---|---:|
| `synthetic_pause_handling` | 137 | 10 | 10 | 0 | 1.000 | none | n/a |
| `candor_pause_handling` | 216 | 10 | 10 | 0 | 1.000 | none | n/a |
| `candor_turn_taking` | 119 | 10 | 10 | 0 | 1.000 | none | 5.070 s |
| `synthetic_user_interruption` | 200 | 10 | 10 | 0 | 1.000 | none | 15.000 s |

| Subset | Metric | Value and interval |
|---|---|---|
| `synthetic_pause_handling` | `any_speech_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `synthetic_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `inside_pause_onset_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `synthetic_pause_handling` | `intrusion_s_per_pause_s` | 0.059 [0.000, 0.162] 0.72/12.24 |
| `synthetic_pause_handling` | `pause_intrusion_per_pause` | 0.100 [0.000, 0.300] 1/10 |
| `synthetic_pause_handling` | `pause_intrusion_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `synthetic_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `any_speech_rate` | 0.600 [0.313, 0.832] 6/10, all selected [0.600, 0.600] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.500 [0.237, 0.763] 5/10, all selected [0.500, 0.500] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.123 [0.031, 0.211] 1.84/14.96 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.556 [0.250, 0.789] 10/18 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.600 [0.313, 0.832] 6/10, all selected [0.600, 0.600] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `early_start_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `no_response_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_latency_s` | median 0.970 [0.790, 1.130] p90 1.170 9/10 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.500 [0.237, 0.763] 5/10, all selected [0.500, 0.500] |
| `candor_turn_taking` | `response_rate_2s` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `candor_turn_taking` | `response_rate_5s` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `synthetic_user_interruption` | `exercised_rate` | 0.800 [0.490, 0.943] 8/10, all selected [0.800, 0.800] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.324] 0/8, all selected [0.000, 0.200] |
| `synthetic_user_interruption` | `response_latency_s` | median 0.560 [0.480, 0.960] p90 1.200 8/8 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.750 [0.409, 0.929] 6/8, all selected [0.600, 0.800] |
| `synthetic_user_interruption` | `response_rate_2s` | 1.000 [0.676, 1.000] 8/8, all selected [0.800, 1.000] |
| `synthetic_user_interruption` | `response_rate_5s` | 1.000 [0.676, 1.000] 8/8, all selected [0.800, 1.000] |
| `synthetic_user_interruption` | `restart_rate` | 0.000 [0.000, 0.324] 0/8, all selected [0.000, 0.200] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.000 [0.000, 0.324] 0/8, all selected [0.000, 0.200] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.183 [0.136, 0.243] 4.55467/24.9173 |
| `synthetic_user_interruption` | `stop_latency_s` | median 0.424 [0.349, 0.744] p90 0.957 8/8 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 10 | 10 | 10 | 10.0% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 10 | 10 | 10 | 60.0% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 10 | 10 | 10 | 100.0% | 0.877 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 10 | 10 | 10 | 100.0% | 0.728 | 4.700 | 0 | n/a | n/a |
| icc_backchannel | 10 | 10 | 10 | 20.0% | n/a | n/a | n/a | 0.004 | 0.975 |

## Listening quality

Per reply: the audio deltas of one response back to back, as a client with enough buffer plays them, up to a barge-in cut. Omission rate (lower is better) is the words of the response.done transcript missing from the reply's Parakeet text, over the transcript's words, pooled over completed replies; WER (lower is better) counts substitutions, deletions and insertions the same way. Both include Parakeet's own errors, so they compare systems rather than read as absolute rates. UTMOS (1-5, higher is better) scores replies of at least 3 s; Short replies counts the shorter ones, which get no UTMOS or voice score. Voice similarity (higher is better) is 100 times the cosine of the WavLM speaker embedding of a reply's middle 3 s with the mean embedding of the same window of the repeat's other replies. p10 is the 10th percentile over replies. Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range.

### v1.5

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 300 | 42 | 220 | 0.6% | 4.1% | 4.201 | 3.696 | 67.344 | 57.908 |
| user_interruption | 75 | 2 | 50 | 0.3% | 1.5% | 4.259 | 3.765 | 68.518 | 61.104 |
| user_backchannel | 75 | 7 | 50 | 0.0% | 3.0% | 4.287 | 3.780 | 68.721 | 61.695 |
| talking_to_other | 75 | 13 | 57 | 1.6% | 8.9% | 4.043 | 3.507 | 64.611 | 53.542 |
| background_speech | 75 | 20 | 63 | 0.7% | 3.7% | 4.198 | 3.810 | 67.164 | 59.028 |

### v1.0

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 16 | 5 | 10 | 0.7% | 4.3% | 4.283 | 3.944 | 70.715 | 63.526 |
| candor_pause_handling | 29 | 18 | 17 | 0.5% | 5.3% | 4.265 | 3.920 | 63.195 | 58.487 |
| candor_turn_taking | 12 | 2 | 11 | 0.0% | 2.5% | 4.025 | 3.527 | 68.964 | 58.928 |
| synthetic_user_interruption | 20 | 0 | 13 | 0.0% | 1.0% | 4.306 | 4.074 | 67.400 | 59.885 |
| icc_backchannel | 20 | 6 | 12 | 0.0% | 1.6% | 4.087 | 3.540 | 64.223 | 56.301 |
