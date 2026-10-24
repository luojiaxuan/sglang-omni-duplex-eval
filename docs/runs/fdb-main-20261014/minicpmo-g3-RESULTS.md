# FDB results: minicpmo-g3

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 62 | 62 | 1.645 | 2.523 | 33.9% | 61.3% | 1.6% | 3.2% | 62 |
| user_interruption | 25 | 25 | 2.217 | 2.332 | 56.0% | 40.0% | 0.0% | 4.0% | 25 |
| user_backchannel | 12 | 12 | 0.695 | 2.756 | 0.0% | 91.7% | 0.0% | 8.3% | 12 |
| talking_to_other | 12 | 12 | 1.756 | 2.620 | 33.3% | 58.3% | 8.3% | 0.0% | 12 |
| background_speech | 13 | 13 | 1.365 | 2.706 | 23.1% | 76.9% | 0.0% | 0.0% | 13 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 70.0% | 96.8% | 82.8% | 93.5% | 71.9% | 91.9% | 50.0% | 90.3% |
| user_interruption | 54.2% | 96.0% | 54.5% | 88.0% | 95.5% | 88.0% | 47.6% | 84.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 91.7% | 100.0% | 91.7% | 100.0% | 91.7% |
| talking_to_other | 63.6% | 91.7% | 100.0% | 100.0% | 36.4% | 91.7% | 18.2% | 91.7% |
| background_speech | 76.9% | 100.0% | 100.0% | 100.0% | 38.5% | 100.0% | 38.5% | 100.0% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 17 | 17 | 17 | 5.9% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 27 | 27 | 27 | 25.9% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 15 | 15 | 15 | 93.3% | 1.294 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 25 | 25 | 25 | 100.0% | 1.482 | 4.240 | 0 | n/a | n/a |
| icc_backchannel | 7 | 7 | 7 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
