# FDB results: listen

Repeats: repeat-1. Judge: qwen.

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `e05256e7a100a728eecbb520999c8dd118df9d3ed4f303d62f6691f3e0741625`; ASR `877ef18e68807bd0b997f8ec514219edabf3f727b2afbd43552a62d107473cd8`.

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
| `candor_pause_handling` | `any_speech_rate` | 0.333 [0.061, 0.792] 1/3, all selected [0.333, 0.333] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.000 [0.000, 0.000] 0/5.17 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.143 [0.000, 0.500] 1/7 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.333 [0.061, 0.792] 1/3, all selected [0.333, 0.333] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_turn_taking` | `early_start_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_turn_taking` | `no_response_rate` | 0.000 [0.000, 0.561] 0/3, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_latency_s` | median 1.730 [0.880, 1.960] p90 1.960 3/3 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.333 [0.061, 0.792] 1/3, all selected [0.333, 0.333] |
| `candor_turn_taking` | `response_rate_2s` | 1.000 [0.439, 1.000] 3/3, all selected [1.000, 1.000] |
| `candor_turn_taking` | `response_rate_5s` | 1.000 [0.439, 1.000] 3/3, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `exercised_rate` | 0.667 [0.208, 0.939] 2/3, all selected [0.667, 0.667] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.658] 0/2, all selected [0.000, 0.333] |
| `synthetic_user_interruption` | `response_latency_s` | median 1.600 [1.600, not reached] p90 not reached 1/2 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.000 [0.000, 0.658] 0/2, all selected [0.000, 0.333] |
| `synthetic_user_interruption` | `response_rate_2s` | 0.500 [0.095, 0.905] 1/2, all selected [0.333, 0.667] |
| `synthetic_user_interruption` | `response_rate_5s` | 0.500 [0.095, 0.905] 1/2, all selected [0.333, 0.667] |
| `synthetic_user_interruption` | `restart_rate` | 0.000 [0.000, 0.658] 0/2, all selected [0.000, 0.333] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.500 [0.095, 0.905] 1/2, all selected [0.333, 0.667] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.886 [0.775, 1.000] 5.16/5.824 |
| `synthetic_user_interruption` | `stop_latency_s` | median 2.291 [2.291, 3.037] p90 3.037 2/2 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

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

## Listening quality

Per reply: the audio deltas of one response back to back, as a client with enough buffer plays them. Omission rate (lower is better) is the words of the response.done transcript missing from the reply's Parakeet text, over the transcript's words, pooled over completed replies; WER (lower is better) counts substitutions, deletions and insertions the same way. Both include Parakeet's own errors, so they compare systems rather than read as absolute rates. UTMOS (1-5, higher is better) scores replies of at least 3 s; Short replies counts the shorter ones, which get no UTMOS or voice score. Voice similarity (higher is better) is 100 times the cosine of the WavLM speaker embedding of a reply's middle 3 s with the mean embedding of the same window of the repeat's other replies. p10 is the 10th percentile over replies. Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range.

### v1.5

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 35 | 1 | 35 | 4.2% | 7.3% | 4.271 | 3.893 | 74.412 | 67.846 |
| user_interruption | 9 | 0 | 9 | 3.9% | 7.0% | 4.358 | 4.163 | 76.408 | 68.144 |
| user_backchannel | 8 | 0 | 8 | 5.5% | 6.7% | 4.248 | 3.960 | 72.195 | 67.167 |
| talking_to_other | 10 | 0 | 10 | 3.1% | 8.7% | 4.226 | 3.868 | 75.081 | 70.286 |
| background_speech | 8 | 1 | 8 | 4.0% | 7.1% | 4.250 | 3.910 | 73.422 | 67.977 |

### v1.0

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 2 | 2 | 2 | 66.7% | 100.0% | n/a | n/a | n/a | n/a |
| candor_pause_handling | 2 | 1 | 2 | 7.0% | 10.5% | 3.662 | 3.662 | 55.869 | 55.869 |
| candor_turn_taking | 3 | 0 | 3 | 9.4% | 11.3% | 4.161 | 3.953 | 74.331 | 72.166 |
| synthetic_user_interruption | 6 | 0 | 6 | 0.9% | 2.7% | 4.332 | 4.063 | 75.771 | 69.718 |
| icc_backchannel | 2 | 2 | 2 | 50.0% | 50.0% | n/a | n/a | n/a | n/a |
