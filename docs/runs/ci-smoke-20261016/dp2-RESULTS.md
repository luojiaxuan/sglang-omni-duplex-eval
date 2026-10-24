# FDB results: ci

Repeats: repeat-1. Judge: gpt.

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `a68a7d11c50ebd1d3d5aefae8ee7c4ec399d243dacf55b6ac54a608f5322cdc9`; ASR `a8e97acb5e58709dc5f53d2d94fcf04d4f76a017e44cd2b2eeae67ecadc698d3`.

| Subset | Declared | Selected | Eligible | Ineligible | Coverage | Ineligible reasons | Minimum observable horizon after reference |
|---|---:|---:|---:|---:|---:|---|---:|
| `synthetic_pause_handling` | 137 | 5 | 5 | 0 | 1.000 | none | n/a |
| `candor_pause_handling` | 216 | 5 | 5 | 0 | 1.000 | none | n/a |
| `candor_turn_taking` | 119 | 5 | 5 | 0 | 1.000 | none | 5.090 s |
| `synthetic_user_interruption` | 200 | 5 | 5 | 0 | 1.000 | none | 15.000 s |

| Subset | Metric | Value and interval |
|---|---|---|
| `synthetic_pause_handling` | `any_speech_rate` | 0.200 [0.036, 0.624] 1/5, all selected [0.200, 0.200] |
| `synthetic_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `inside_pause_onset_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `intrusion_s_per_pause_s` | 0.000 [0.000, 0.000] 0/4.66 |
| `synthetic_pause_handling` | `pause_intrusion_per_pause` | 0.200 [0.000, 0.600] 1/5 |
| `synthetic_pause_handling` | `pause_intrusion_rate` | 0.200 [0.036, 0.624] 1/5, all selected [0.200, 0.200] |
| `synthetic_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_pause_handling` | `any_speech_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.000 [0.000, 0.000] 0/6.52 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.000 [0.000, 0.000] 0/9 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_turn_taking` | `early_start_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_turn_taking` | `no_response_rate` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_latency_s` | median 1.610 [1.520, 1.810] p90 1.810 5/5 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.000 [0.000, 0.434] 0/5, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_rate_2s` | 1.000 [0.566, 1.000] 5/5, all selected [1.000, 1.000] |
| `candor_turn_taking` | `response_rate_5s` | 1.000 [0.566, 1.000] 5/5, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `exercised_rate` | 0.800 [0.376, 0.964] 4/5, all selected [0.800, 0.800] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.490] 0/4, all selected [0.000, 0.200] |
| `synthetic_user_interruption` | `response_latency_s` | median 1.920 [1.600, not reached] p90 not reached 2/4 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.000 [0.000, 0.490] 0/4, all selected [0.000, 0.200] |
| `synthetic_user_interruption` | `response_rate_2s` | 0.500 [0.150, 0.850] 2/4, all selected [0.400, 0.600] |
| `synthetic_user_interruption` | `response_rate_5s` | 0.500 [0.150, 0.850] 2/4, all selected [0.400, 0.600] |
| `synthetic_user_interruption` | `restart_rate` | 0.250 [0.046, 0.699] 1/4, all selected [0.200, 0.400] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.500 [0.150, 0.850] 2/4, all selected [0.400, 0.600] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.782 [0.569, 0.953] 7.64267/9.77067 |
| `synthetic_user_interruption` | `stop_latency_s` | median 1.373 [0.925, 2.995] p90 2.995 4/4 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by GPT; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 5 | 5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 5 | 5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 5 | 5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 5 | 5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| icc_backchannel | 5 | 5 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

Not evaluated:

- repeat-1 `synthetic_pause_handling`: not evaluated yet; run `judge`
- repeat-1 `candor_pause_handling`: not evaluated yet; run `judge`
- repeat-1 `candor_turn_taking`: not evaluated yet; run `judge`
- repeat-1 `synthetic_user_interruption`: not evaluated yet; run `judge`
- repeat-1 `icc_backchannel`: not evaluated yet; run `judge`
