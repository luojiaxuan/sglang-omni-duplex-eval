# FDB results: qwen3omni

Repeats: repeat-1. Judge: qwen.

## FDB v1.5 results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 100 | 100 | 0.254 | 1.129 | 78.0% | 14.0% | 5.0% | 3.0% | 100 |
| user_interruption | 25 | 25 | 0.281 | 1.173 | 96.0% | 0.0% | 0.0% | 4.0% | 25 |
| user_backchannel | 25 | 25 | 0.219 | 1.165 | 20.0% | 56.0% | 20.0% | 4.0% | 25 |
| talking_to_other | 25 | 25 | 0.224 | 1.076 | 96.0% | 0.0% | 0.0% | 4.0% | 25 |
| background_speech | 25 | 25 | 0.310 | 1.104 | 100.0% | 0.0% | 0.0% | 0.0% | 25 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 51.0% | 96.0% | 98.7% | 76.0% | 60.7% | 84.0% | 39.5% | 86.0% |
| user_interruption | 100.0% | 92.0% | 100.0% | 84.0% | 86.4% | 88.0% | 85.0% | 80.0% |
| user_backchannel | 83.3% | 96.0% | 100.0% | 72.0% | 100.0% | 72.0% | 76.5% | 68.0% |
| talking_to_other | 8.3% | 96.0% | 92.9% | 56.0% | 21.1% | 76.0% | 4.2% | 96.0% |
| background_speech | 16.0% | 100.0% | 100.0% | 92.0% | 40.0% | 100.0% | 12.0% | 100.0% |

## FDB v1.0 unified metrics

Each table describes one repeat. Sample rates are proportions among eligible samples, and among exercised samples for user interruption except its exercised rate; their 95% Wilson intervals describe sampling uncertainty. All-selected bounds allow every ineligible outcome, and for those interruption metrics every not-exercised one, to be either false or true, and are not confidence intervals. Other 95% intervals resample whole samples. No metrics or intervals are averaged across repeats. A latency marked `not reached` includes samples without a response or a stop; `n/a` with 0 eligible means no data.

### repeat-1

Artifacts: [manifest.json](repeat-1/v10/reference/manifest.json), [asr.json](repeat-1/v10/reference/asr.json), [unified.json](repeat-1/v10/reference/unified.json), [unified-samples.jsonl](repeat-1/v10/reference/unified-samples.jsonl).
Definitions: `fdb-v1.0-unified-4`; 95% intervals: sample rates = Wilson score, others = percentile bootstrap over samples (2000 replicates, seed 0).
Input SHA-256: manifest `b36a9ebb3abaf96834cec1476898651af524b60aa3431ef3fc9711d702948322`; ASR `7fcc82447a051896544b3ffb8848ab18defd7ad5748937d5274e63968b091c41`.

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
| `candor_pause_handling` | `any_speech_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_pause_handling` | `carry_in_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_pause_handling` | `inside_pause_onset_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_pause_handling` | `intrusion_s_per_pause_s` | 0.011 [0.000, 0.030] 0.16/14.96 |
| `candor_pause_handling` | `pause_intrusion_per_pause` | 0.111 [0.000, 0.353] 2/18 |
| `candor_pause_handling` | `pause_intrusion_rate` | 0.100 [0.018, 0.404] 1/10, all selected [0.100, 0.100] |
| `candor_pause_handling` | `pre_pause_speech_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `early_start_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `no_response_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `candor_turn_taking` | `response_latency_s` | median 0.950 [0.890, 1.130] p90 1.330 10/10 responded |
| `candor_turn_taking` | `response_rate_1s` | 0.700 [0.397, 0.892] 7/10, all selected [0.700, 0.700] |
| `candor_turn_taking` | `response_rate_2s` | 1.000 [0.722, 1.000] 10/10, all selected [1.000, 1.000] |
| `candor_turn_taking` | `response_rate_5s` | 1.000 [0.722, 1.000] 10/10, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `exercised_rate` | 1.000 [0.722, 1.000] 10/10, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `no_response_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `synthetic_user_interruption` | `response_latency_s` | median 0.800 [0.560, 1.120] p90 1.200 10/10 responded |
| `synthetic_user_interruption` | `response_rate_1s` | 0.600 [0.313, 0.832] 6/10, all selected [0.600, 0.600] |
| `synthetic_user_interruption` | `response_rate_2s` | 1.000 [0.722, 1.000] 10/10, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `response_rate_5s` | 1.000 [0.722, 1.000] 10/10, all selected [1.000, 1.000] |
| `synthetic_user_interruption` | `restart_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `synthetic_user_interruption` | `speaking_at_end_rate` | 0.000 [0.000, 0.278] 0/10, all selected [0.000, 0.000] |
| `synthetic_user_interruption` | `speech_s_per_interruption_s` | 0.174 [0.122, 0.241] 5.15733/29.696 |
| `synthetic_user_interruption` | `stop_latency_s` | median 0.349 [0.285, 0.573] p90 0.755 10/10 stopped |

Backchannel is scored by the official reference evaluator only.

## FDB v1.0 official reference results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 10 | 10 | 10 | 10.0% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 10 | 10 | 10 | 10.0% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 10 | 10 | 10 | 100.0% | 1.042 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 10 | 10 | 10 | 100.0% | 0.872 | 5.000 | 0 | n/a | n/a |
| icc_backchannel | 10 | 7 | 7 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |

## Listening quality

Per reply: the audio deltas of one response back to back, as a client with enough buffer plays them, up to a barge-in cut. Omission rate (lower is better) is the words of the response.done transcript missing from the reply's Parakeet text, over the transcript's words, pooled over completed replies; WER (lower is better) counts substitutions, deletions and insertions the same way. Both include Parakeet's own errors, so they compare systems rather than read as absolute rates. UTMOS (1-5, higher is better) scores replies of at least 3 s; Short replies counts the shorter ones, which get no UTMOS or voice score. Voice similarity (higher is better) is 100 times the cosine of the WavLM speaker embedding of a reply's middle 3 s with the mean embedding of the same window of the repeat's other replies. p10 is the 10th percentile over replies. Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range.

### v1.5

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 300 | 43 | 222 | 6.1% | 13.0% | 4.468 | 4.423 | 83.579 | 78.592 |
| user_interruption | 75 | 4 | 51 | 0.1% | 2.0% | 4.460 | 4.446 | 83.072 | 76.762 |
| user_backchannel | 75 | 0 | 50 | 8.7% | 17.5% | 4.465 | 4.402 | 82.681 | 78.468 |
| talking_to_other | 75 | 15 | 58 | 0.3% | 4.6% | 4.478 | 4.435 | 84.358 | 80.535 |
| background_speech | 75 | 24 | 63 | 0.3% | 2.4% | 4.472 | 4.424 | 84.680 | 80.141 |

### v1.0

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 16 | 3 | 10 | 0.2% | 0.8% | 4.504 | 4.491 | 83.981 | 80.755 |
| candor_pause_handling | 29 | 8 | 10 | 0.2% | 0.2% | 4.501 | 4.482 | 85.239 | 81.298 |
| candor_turn_taking | 12 | 1 | 10 | 37.7% | 39.8% | 4.487 | 4.449 | 84.894 | 80.056 |
| synthetic_user_interruption | 20 | 1 | 10 | 0.7% | 3.6% | 4.497 | 4.471 | 84.471 | 81.193 |
| icc_backchannel | 13 | 2 | 7 | 0.2% | 0.4% | 4.500 | 4.481 | 86.603 | 84.176 |
