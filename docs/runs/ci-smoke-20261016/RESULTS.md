# FDB results: ci

Repeats: repeat-1. Judge: gpt.

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `2870169f8d1e998d9ce0e2c10254b47759445c91f1c5b40a118c8641e22cefea`; ASR `5eb53e13642b7680865c8e100eafb900a087fb8c868f4d4d9203b383aefec161`.

| Subset | Declared | Selected | Eligible | Ineligible | Coverage | Ineligible reasons | Minimum observable horizon after reference |
|---|---:|---:|---:|---:|---:|---|---:|
| `synthetic_pause_handling` | 137 | 3 | 3 | 0 | 1.000 | none | n/a |
| `candor_pause_handling` | 216 | 3 | 3 | 0 | 1.000 | none | n/a |
| `candor_turn_taking` | 119 | 3 | 3 | 0 | 1.000 | none | 5.190 s |
| `synthetic_user_interruption` | 200 | 3 | 3 | 0 | 1.000 | none | 15.000 s |

| Subset | Metric | Value and interval |
|---|---|---|
| `synthetic_pause_handling` | `any_speech_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `inside_pause_onset_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `intrusion_s_per_pause_s` | 0.000 [0.000, 0.000] 0/3.52 |
| `synthetic_pause_handling` | `pause_intrusion_per_pause` | 0.000 [0.000, 0.000] 0/3 |
| `synthetic_pause_handling` | `pause_intrusion_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `synthetic_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_pause_handling` | `any_speech_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.000 [0.000, 0.000] 0/5.17 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.000 [0.000, 0.000] 0/7 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_turn_taking` | `early_start_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_turn_taking` | `no_response_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_latency_s` | median 1.720 [1.200, 2.050] p90 2.050 3/3 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_rate_2s` | 0.667 [0.208, 0.939] 2/3, all selected [0.667, 0.667] |
| `candor_turn_taking` | `response_rate_5s` | 1.000 [0.439, 1.000] 3/3, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `exercised_rate` | 1.000 [0.439, 1.000] 3/3, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `synthetic_user_interruption` | `response_latency_s` | median 2.400 [1.920, not reached] p90 not reached 2/3 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `synthetic_user_interruption` | `response_rate_2s` | 0.333 [0.061, 0.792] 1/3, all selected [0.333, 0.333] |
| `synthetic_user_interruption` | `response_rate_5s` | 0.667 [0.208, 0.939] 2/3, all selected [0.667, 0.667] |
| `synthetic_user_interruption` | `restart_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.333 [0.061, 0.792] 1/3, all selected [0.333, 0.333] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.816 [0.534, 1.000] 6.17067/7.56267 |
| `synthetic_user_interruption` | `stop_latency_s` | median 2.899 [1.533, 7.261] p90 7.261 3/3 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by GPT; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| icc_backchannel | 3 | 3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

Not evaluated:

- repeat-1 `synthetic_pause_handling`: not evaluated yet; run `judge`
- repeat-1 `candor_pause_handling`: not evaluated yet; run `judge`
- repeat-1 `candor_turn_taking`: not evaluated yet; run `judge`
- repeat-1 `synthetic_user_interruption`: not evaluated yet; run `judge`
- repeat-1 `icc_backchannel`: not evaluated yet; run `judge`
