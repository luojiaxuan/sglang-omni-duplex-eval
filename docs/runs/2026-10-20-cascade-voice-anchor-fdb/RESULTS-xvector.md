# FDB results: cascadexvec

Repeats: repeat-1. Judge: qwen.

## FDB v1.5 results

Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range. Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 100 | 100 | 0.172 | 1.006 | 80.0% | 14.0% | 6.0% | 0.0% | 100 |
| user_interruption | 25 | 25 | 0.146 | 1.044 | 96.0% | 4.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 25 | 25 | 0.182 | 1.000 | 24.0% | 52.0% | 24.0% | 0.0% | 25 |
| talking_to_other | 25 | 25 | 0.190 | 0.988 | 100.0% | 0.0% | 0.0% | 0.0% | 25 |
| background_speech | 25 | 25 | 0.172 | 0.993 | 100.0% | 0.0% | 0.0% | 0.0% | 25 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 52.5% | 99.0% | 100.0% | 99.0% | 70.8% | 96.0% | 45.3% | 95.0% |
| user_interruption | 100.0% | 96.0% | 100.0% | 96.0% | 86.4% | 88.0% | 85.7% | 84.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 96.0% | 100.0% | 96.0% |
| talking_to_other | 8.0% | 100.0% | 100.0% | 100.0% | 44.0% | 100.0% | 4.0% | 100.0% |
| background_speech | 4.0% | 100.0% | 100.0% | 100.0% | 56.0% | 100.0% | 0.0% | 100.0% |

## Listening quality

Per reply: the audio deltas of one response back to back, as a client with enough buffer plays them, up to a barge-in cut. Omission rate (lower is better) is the words of the response.done transcript missing from the reply's Parakeet text, over the transcript's words, pooled over completed replies; WER (lower is better) counts substitutions, deletions and insertions the same way. Both include Parakeet's own errors, so they compare systems rather than read as absolute rates. UTMOS (1-5, higher is better) scores replies of at least 3 s; Short replies counts the shorter ones, which get no UTMOS or voice score. Voice similarity (higher is better) is 100 times the cosine of the WavLM speaker embedding of a reply's middle 3 s with the mean embedding of the same window of the repeat's other replies. p10 is the 10th percentile over replies. Numeric cells are mean ± sample standard deviation across repeats where values exist; counts are a value or range.

### v1.5

| Category | Replies | Short replies | Compared replies | Omission rate | WER | UTMOS mean | UTMOS p10 | Voice similarity mean | Voice similarity p10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 300 | 58 | 223 | 0.5% | 2.7% | 4.521 | 4.489 | 76.759 | 70.580 |
| user_interruption | 75 | 6 | 51 | 0.1% | 0.9% | 4.519 | 4.503 | 76.799 | 69.651 |
| user_backchannel | 75 | 7 | 50 | 0.3% | 2.5% | 4.514 | 4.481 | 75.666 | 66.144 |
| talking_to_other | 75 | 18 | 58 | 0.6% | 4.5% | 4.528 | 4.489 | 77.627 | 73.176 |
| background_speech | 75 | 27 | 64 | 1.0% | 3.4% | 4.528 | 4.507 | 77.222 | 71.282 |
