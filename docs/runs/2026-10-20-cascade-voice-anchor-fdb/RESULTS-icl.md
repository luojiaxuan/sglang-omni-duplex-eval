# FDB results: cascadeanchor

Repeats: repeat-1. Judge: qwen.

## FDB v1.5 results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 100 | 100 | 0.184 | 1.422 | 73.0% | 17.0% | 10.0% | 0.0% | 100 |
| user_interruption | 25 | 25 | 0.153 | 1.488 | 96.0% | 4.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 25 | 25 | 0.183 | 1.380 | 16.0% | 60.0% | 24.0% | 0.0% | 25 |
| talking_to_other | 25 | 25 | 0.222 | 1.388 | 88.0% | 4.0% | 8.0% | 0.0% | 25 |
| background_speech | 25 | 25 | 0.193 | 1.432 | 92.0% | 0.0% | 8.0% | 0.0% | 25 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 55.6% | 99.0% | 100.0% | 99.0% | 66.0% | 97.0% | 46.9% | 98.0% |
| user_interruption | 100.0% | 100.0% | 100.0% | 100.0% | 79.2% | 96.0% | 79.2% | 96.0% |
| user_backchannel | 96.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 96.0% | 100.0% |
| talking_to_other | 12.0% | 100.0% | 100.0% | 100.0% | 40.0% | 100.0% | 4.0% | 100.0% |
| background_speech | 12.5% | 96.0% | 100.0% | 96.0% | 43.5% | 92.0% | 8.3% | 96.0% |

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `82e59e4495a9ea863e6267e6f9b8120db95f38d751e3ecd83b306900b656cdf7`; ASR `fb39a14f2f4ed82f9ea7070c892da2cb0896de9ed1188c38a74e3fdff8d30d2a`.

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
| `synthetic_pause_handling` | `intrusion_s_per_pause_s` | 0.046 [0.000, 0.126] 0.56/12.24 |
| `synthetic_pause_handling` | `pause_intrusion_per_pause` | 0.100 [0.000, 0.300] 1/10 |
| `synthetic_pause_handling` | `pause_intrusion_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `synthetic_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `any_speech_rate` | 0.800 [0.490, 0.943] 8/10, all selected [0.800, 0.800] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.300 [0.108, 0.603] 3/10, all selected [0.300, 0.300] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.115 [0.000, 0.226] 1.72/14.96 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.556 [0.400, 0.700] 10/18 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.800 [0.490, 0.943] 8/10, all selected [0.800, 0.800] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `early_start_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `no_response_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_latency_s` | median 1.240 [1.030, 1.440] p90 1.570 9/10 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_turn_taking` | `response_rate_2s` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `candor_turn_taking` | `response_rate_5s` | 0.900 [0.596, 0.982] 9/10, all selected [0.900, 0.900] |
| `synthetic_user_interruption` | `exercised_rate` | 0.700 [0.397, 0.892] 7/10, all selected [0.700, 0.700] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.354] 0/7, all selected [0.000, 0.300] |
| `synthetic_user_interruption` | `response_latency_s` | median 0.640 [0.560, 1.200] p90 1.280 7/7 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.714 [0.359, 0.918] 5/7, all selected [0.500, 0.800] |
| `synthetic_user_interruption` | `response_rate_2s` | 1.000 [0.646, 1.000] 7/7, all selected [0.700, 1.000] |
| `synthetic_user_interruption` | `response_rate_5s` | 1.000 [0.646, 1.000] 7/7, all selected [0.700, 1.000] |
| `synthetic_user_interruption` | `restart_rate` | 0.000 [0.000, 0.354] 0/7, all selected [0.000, 0.300] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.000 [0.000, 0.354] 0/7, all selected [0.000, 0.300] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.244 [0.150, 0.351] 4.99467/20.4693 |
| `synthetic_user_interruption` | `stop_latency_s` | median 0.509 [0.285, 1.384] p90 1.437 7/7 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 10 | 10 | 10 | 0.0% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 10 | 10 | 10 | 70.0% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 10 | 10 | 10 | 100.0% | 1.109 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 10 | 10 | 10 | 100.0% | 0.848 | 4.700 | 0 | n/a | n/a |
| icc_backchannel | 10 | 10 | 10 | 20.0% | n/a | n/a | n/a | 0.006 | 0.977 |

## Listening quality

Per reply: the audio deltas of one response back to back, as a client with enough buffer plays them, up to a barge-in cut. Omission rate (lower is better) is the words of the response.done transcript missing from the reply's Parakeet text, over the transcript's words, pooled over completed replies; WER (lower is better) counts substitutions, deletions and insertions the same way. Both include Parakeet's own errors, so they compare systems rather than read as absolute rates. UTMOS (1-5, higher is better) scores replies of at least 3 s; Short replies counts the shorter ones, which get no UTMOS or voice score. Voice similarity (higher is better) is 100 times the cosine of the WavLM speaker embedding of a reply's middle 3 s with the mean embedding of the same window of the repeat's other replies. p10 is the 10th percentile over replies. Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range.

### v1.5

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 301 | 40 | 226 | 0.4% | 2.4% | 4.530 | 4.493 | 79.520 | 74.762 |
| user_interruption | 75 | 4 | 51 | 0.1% | 0.5% | 4.535 | 4.493 | 79.997 | 75.230 |
| user_backchannel | 75 | 5 | 50 | 0.5% | 1.6% | 4.520 | 4.487 | 79.739 | 74.389 |
| talking_to_other | 76 | 14 | 61 | 0.1% | 4.2% | 4.536 | 4.495 | 79.419 | 75.154 |
| background_speech | 75 | 17 | 64 | 0.9% | 3.5% | 4.532 | 4.498 | 78.777 | 74.584 |

### v1.0

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 16 | 5 | 10 | 0.7% | 4.2% | 4.539 | 4.517 | 78.414 | 72.843 |
| candor_pause_handling | 29 | 15 | 17 | 3.7% | 6.7% | 4.517 | 4.486 | 79.625 | 75.182 |
| candor_turn_taking | 12 | 2 | 11 | 0.0% | 0.0% | 4.536 | 4.516 | 83.142 | 78.487 |
| synthetic_user_interruption | 20 | 2 | 14 | 0.0% | 1.0% | 4.540 | 4.519 | 80.125 | 76.322 |
| icc_backchannel | 20 | 6 | 12 | 0.0% | 1.6% | 4.529 | 4.490 | 79.646 | 75.698 |
