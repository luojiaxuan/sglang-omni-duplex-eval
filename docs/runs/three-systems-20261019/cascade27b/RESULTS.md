# FDB results: cascade27b

Repeats: repeat-1. Judge: qwen.

## FDB v1.5 results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 100 | 100 | 0.166 | 1.320 | 60.0% | 31.0% | 5.0% | 4.0% | 100 |
| user_interruption | 25 | 25 | 0.145 | 1.423 | 72.0% | 12.0% | 8.0% | 8.0% | 25 |
| user_backchannel | 25 | 25 | 0.182 | 1.288 | 4.0% | 76.0% | 12.0% | 8.0% | 25 |
| talking_to_other | 25 | 25 | 0.159 | 1.309 | 76.0% | 24.0% | 0.0% | 0.0% | 25 |
| background_speech | 25 | 25 | 0.175 | 1.260 | 88.0% | 12.0% | 0.0% | 0.0% | 25 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 54.2% | 96.0% | 95.5% | 88.0% | 87.2% | 86.0% | 44.0% | 84.0% |
| user_interruption | 95.7% | 92.0% | 95.2% | 84.0% | 94.4% | 72.0% | 86.7% | 60.0% |
| user_backchannel | 91.7% | 96.0% | 95.5% | 88.0% | 85.7% | 84.0% | 80.0% | 80.0% |
| talking_to_other | 20.8% | 96.0% | 95.5% | 88.0% | 82.6% | 92.0% | 20.8% | 96.0% |
| background_speech | 12.0% | 100.0% | 95.7% | 92.0% | 87.5% | 96.0% | 12.0% | 100.0% |

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `66e83d0ccf48a6b2e150fc4d38893a17556791ba54e4cb211d6f92e177c9ab2f`; ASR `c2140fbdc3aeffb2c3c8e8d3b41058f1e6673e280fc62e409102167a911e278e`.

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
| `synthetic_pause_handling` | `intrusion_s_per_pause_s` | 0.052 [0.000, 0.144] 0.64/12.24 |
| `synthetic_pause_handling` | `pause_intrusion_per_pause` | 0.100 [0.000, 0.300] 1/10 |
| `synthetic_pause_handling` | `pause_intrusion_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `synthetic_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `any_speech_rate` | 0.400 [0.168, 0.687] 4/10, all selected [0.400, 0.400] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.200 [0.057, 0.510] 2/10, all selected [0.200, 0.200] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.129 [0.000, 0.332] 1.93/14.96 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.389 [0.062, 0.688] 7/18 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.400 [0.168, 0.687] 4/10, all selected [0.400, 0.400] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `early_start_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `no_response_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_latency_s` | median 1.210 [1.110, 1.440] p90 1.730 9/10 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_rate_2s` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `candor_turn_taking` | `response_rate_5s` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `synthetic_user_interruption` | `exercised_rate` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.299] 0/9, all selected [0.000, 0.100] |
| `synthetic_user_interruption` | `response_latency_s` | median 1.120 [0.640, 1.200] p90 1.360 9/9 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.333 [0.121, 0.646] 3/9, all selected [0.300, 0.400] |
| `synthetic_user_interruption` | `response_rate_2s` | 1.000 [0.701, 1.000] 9/9, all selected [0.900, 1.000] |
| `synthetic_user_interruption` | `response_rate_5s` | 1.000 [0.701, 1.000] 9/9, all selected [0.900, 1.000] |
| `synthetic_user_interruption` | `restart_rate` | 0.000 [0.000, 0.299] 0/9, all selected [0.000, 0.100] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.000 [0.000, 0.299] 0/9, all selected [0.000, 0.100] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.168 [0.129, 0.226] 4.264/25.3973 |
| `synthetic_user_interruption` | `stop_latency_s` | median 0.456 [0.307, 0.648] p90 0.787 9/9 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 10 | 10 | 10 | 10.0% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 10 | 10 | 10 | 40.0% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 10 | 10 | 10 | 100.0% | 1.133 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 10 | 10 | 10 | 100.0% | 0.960 | 4.400 | 0 | n/a | n/a |
| icc_backchannel | 10 | 10 | 10 | 10.0% | n/a | n/a | n/a | 0.004 | 0.979 |

## Listening quality

Per reply: the audio deltas of one response back to back, as a client with enough buffer plays them, up to a barge-in cut. Omission rate (lower is better) is the words of the response.done transcript missing from the reply's Parakeet text, over the transcript's words, pooled over completed replies; WER (lower is better) counts substitutions, deletions and insertions the same way. Both include Parakeet's own errors, so they compare systems rather than read as absolute rates. UTMOS (1-5, higher is better) scores replies of at least 3 s; Short replies counts the shorter ones, which get no UTMOS or voice score. Voice similarity (higher is better) is 100 times the cosine of the WavLM speaker embedding of a reply's middle 3 s with the mean embedding of the same window of the repeat's other replies. p10 is the 10th percentile over replies. Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range.

### v1.5

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 300 | 81 | 203 | 0.4% | 2.5% | 4.240 | 3.758 | 67.865 | 57.079 |
| user_interruption | 75 | 18 | 50 | 0.1% | 3.0% | 4.209 | 3.759 | 67.475 | 58.941 |
| user_backchannel | 75 | 23 | 50 | 0.1% | 2.2% | 4.296 | 3.921 | 68.920 | 57.371 |
| talking_to_other | 75 | 23 | 50 | 0.8% | 2.4% | 4.258 | 3.787 | 68.033 | 60.493 |
| background_speech | 75 | 17 | 53 | 0.4% | 2.3% | 4.205 | 3.644 | 67.169 | 55.205 |

### v1.0

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 16 | 4 | 9 | 0.0% | 2.3% | 4.393 | 4.258 | 72.007 | 64.963 |
| candor_pause_handling | 29 | 9 | 11 | 0.0% | 2.0% | 4.154 | 3.882 | 70.823 | 65.578 |
| candor_turn_taking | 12 | 2 | 11 | 0.0% | 0.0% | 4.101 | 3.759 | 66.479 | 60.456 |
| synthetic_user_interruption | 20 | 0 | 11 | 0.0% | 1.3% | 4.286 | 4.025 | 68.587 | 61.915 |
| icc_backchannel | 20 | 0 | 7 | 0.0% | 0.7% | 4.251 | 3.945 | 68.762 | 63.632 |
