# FDB results: minicpmo-g2

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 62 | 62 | 1.729 | 2.588 | 38.7% | 58.1% | 1.6% | 1.6% | 62 |
| user_interruption | 25 | 25 | 2.473 | 2.361 | 72.0% | 28.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 12 | 12 | 0.745 | 2.655 | 0.0% | 100.0% | 0.0% | 0.0% | 12 |
| talking_to_other | 12 | 12 | 1.835 | 2.731 | 50.0% | 33.3% | 8.3% | 8.3% | 12 |
| background_speech | 13 | 13 | 1.214 | 3.033 | 0.0% | 100.0% | 0.0% | 0.0% | 13 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 78.3% | 96.8% | 90.6% | 85.5% | 71.9% | 91.9% | 57.1% | 90.3% |
| user_interruption | 73.9% | 92.0% | 78.9% | 76.0% | 82.6% | 92.0% | 59.1% | 88.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 83.3% | 90.0% | 83.3% | 90.0% | 83.3% |
| talking_to_other | 41.7% | 100.0% | 90.9% | 91.7% | 36.4% | 91.7% | 9.1% | 91.7% |
| background_speech | 100.0% | 100.0% | 100.0% | 100.0% | 69.2% | 100.0% | 69.2% | 100.0% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 17 | 17 | 17 | 11.8% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 27 | 27 | 27 | 29.6% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 15 | 15 | 15 | 100.0% | 1.647 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 25 | 25 | 25 | 92.0% | 1.729 | 4.478 | 0 | n/a | n/a |
| icc_backchannel | 7 | 7 | 7 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
