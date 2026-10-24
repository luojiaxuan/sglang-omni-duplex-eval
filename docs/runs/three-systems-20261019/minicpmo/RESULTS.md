# FDB results: minicpmo

Repeats: repeat-1. Judge: qwen.

## FDB v1.5 results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 100 | 100 | 1.608 | 2.586 | 25.0% | 70.0% | 2.0% | 3.0% | 100 |
| user_interruption | 25 | 25 | 2.343 | 2.344 | 56.0% | 36.0% | 4.0% | 4.0% | 25 |
| user_backchannel | 25 | 25 | 0.760 | 2.600 | 0.0% | 96.0% | 0.0% | 4.0% | 25 |
| talking_to_other | 25 | 25 | 1.890 | 2.609 | 32.0% | 64.0% | 0.0% | 4.0% | 25 |
| background_speech | 25 | 25 | 1.469 | 2.935 | 12.0% | 84.0% | 4.0% | 0.0% | 25 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 85.6% | 97.0% | 87.9% | 91.0% | 66.3% | 89.0% | 54.0% | 87.0% |
| user_interruption | 75.0% | 96.0% | 72.7% | 88.0% | 83.3% | 96.0% | 54.5% | 88.0% |
| user_backchannel | 100.0% | 96.0% | 95.8% | 96.0% | 95.5% | 88.0% | 95.5% | 88.0% |
| talking_to_other | 79.2% | 96.0% | 87.0% | 92.0% | 45.5% | 88.0% | 31.8% | 88.0% |
| background_speech | 88.0% | 100.0% | 95.5% | 88.0% | 38.1% | 84.0% | 33.3% | 84.0% |

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `a6293fa4a6c1bc196b6fb37f49ddd1daba17ea1e61f08c62e6672fabb89a5edc`; ASR `7ef316468018c39104172bf31973eab327246535de64d3806ec5ceb6665d9f92`.

| Subset | Declared | Selected | Eligible | Ineligible | Coverage | Ineligible reasons | Minimum observable horizon after reference |
|---|---:|---:|---:|---:|---:|---|---:|
| `synthetic_pause_handling` | 137 | 10 | 10 | 0 | 1.000 | none | n/a |
| `candor_pause_handling` | 216 | 10 | 10 | 0 | 1.000 | none | n/a |
| `candor_turn_taking` | 119 | 10 | 10 | 0 | 1.000 | none | 5.070 s |
| `synthetic_user_interruption` | 200 | 10 | 10 | 0 | 1.000 | none | 15.000 s |

| Subset | Metric | Value and interval |
|---|---|---|
| `synthetic_pause_handling` | `any_speech_rate` | 0.300 [0.108, 0.603] 3/10, all selected [0.300, 0.300] |
| `synthetic_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `inside_pause_onset_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `intrusion_s_per_pause_s` | 0.000 [0.000, 0.000] 0/12.24 |
| `synthetic_pause_handling` | `pause_intrusion_per_pause` | 0.300 [0.000, 0.600] 3/10 |
| `synthetic_pause_handling` | `pause_intrusion_rate` | 0.300 [0.108, 0.603] 3/10, all selected [0.300, 0.300] |
| `synthetic_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `any_speech_rate` | 0.400 [0.168, 0.687] 4/10, all selected [0.400, 0.400] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.300 [0.108, 0.603] 3/10, all selected [0.300, 0.300] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.111 [0.000, 0.250] 1.66/14.96 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.333 [0.071, 0.611] 6/18 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.400 [0.168, 0.687] 4/10, all selected [0.400, 0.400] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `early_start_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `no_response_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `response_latency_s` | median 1.520 [1.050, 1.870] p90 not reached 8/10 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `response_rate_2s` | 0.800 [0.490, 0.943] 8/10, all selected [0.800, 0.800] |
| `candor_turn_taking` | `response_rate_5s` | 0.800 [0.490, 0.943] 8/10, all selected [0.800, 0.800] |
| `synthetic_user_interruption` | `exercised_rate` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.299] 0/9, all selected [0.000, 0.100] |
| `synthetic_user_interruption` | `response_latency_s` | median 1.760 [1.520, not reached] p90 not reached 5/9 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.000 [0.000, 0.299] 0/9, all selected [0.000, 0.100] |
| `synthetic_user_interruption` | `response_rate_2s` | 0.556 [0.267, 0.811] 5/9, all selected [0.500, 0.600] |
| `synthetic_user_interruption` | `response_rate_5s` | 0.556 [0.267, 0.811] 5/9, all selected [0.500, 0.600] |
| `synthetic_user_interruption` | `restart_rate` | 0.333 [0.121, 0.646] 3/9, all selected [0.300, 0.400] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.444 [0.189, 0.733] 4/9, all selected [0.400, 0.500] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.716 [0.517, 0.930] 19.144/26.7413 |
| `synthetic_user_interruption` | `stop_latency_s` | median 2.429 [0.445, 3.048] p90 4.552 9/9 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 10 | 10 | 10 | 30.0% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 10 | 10 | 10 | 30.0% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 10 | 10 | 10 | 80.0% | 1.181 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 10 | 10 | 10 | 90.0% | 1.484 | 4.222 | 0 | n/a | n/a |
| icc_backchannel | 10 | 10 | 10 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |

## Listening quality

Per reply: the audio deltas of one response back to back, as a client with enough buffer plays them, up to a barge-in cut. Omission rate (lower is better) is the words of the response.done transcript missing from the reply's Parakeet text, over the transcript's words, pooled over completed replies; WER (lower is better) counts substitutions, deletions and insertions the same way. Both include Parakeet's own errors, so they compare systems rather than read as absolute rates. UTMOS (1-5, higher is better) scores replies of at least 3 s; Short replies counts the shorter ones, which get no UTMOS or voice score. Voice similarity (higher is better) is 100 times the cosine of the WavLM speaker embedding of a reply's middle 3 s with the mean embedding of the same window of the repeat's other replies. p10 is the 10th percentile over replies. Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range.

### v1.5

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 228 | 11 | 228 | 6.0% | 9.6% | 4.166 | 3.791 | 76.150 | 69.471 |
| user_interruption | 68 | 2 | 68 | 6.2% | 9.2% | 4.176 | 3.832 | 76.368 | 68.701 |
| user_backchannel | 51 | 0 | 51 | 8.2% | 11.5% | 4.104 | 3.678 | 77.178 | 71.402 |
| talking_to_other | 59 | 5 | 59 | 4.1% | 9.4% | 4.182 | 3.801 | 75.454 | 69.410 |
| background_speech | 50 | 4 | 50 | 4.7% | 7.7% | 4.203 | 3.898 | 75.516 | 68.627 |

### v1.0

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 7 | 5 | 7 | 14.0% | 25.6% | 3.917 | 3.676 | 77.383 | 75.292 |
| candor_pause_handling | 10 | 7 | 10 | 15.0% | 22.5% | 4.174 | 3.841 | 74.655 | 72.635 |
| candor_turn_taking | 11 | 2 | 11 | 10.1% | 12.6% | 4.052 | 3.819 | 76.417 | 70.931 |
| synthetic_user_interruption | 18 | 0 | 18 | 5.9% | 14.2% | 4.237 | 3.818 | 74.955 | 67.562 |
| icc_backchannel | 10 | 10 | 10 | 35.0% | 40.0% | n/a | n/a | n/a | n/a |
