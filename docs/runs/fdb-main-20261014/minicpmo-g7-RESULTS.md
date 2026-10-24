# FDB results: minicpmo-g7

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 62 | 62 | 1.608 | 2.550 | 37.1% | 58.1% | 4.8% | 0.0% | 62 |
| user_interruption | 25 | 25 | 1.857 | 2.311 | 68.0% | 28.0% | 4.0% | 0.0% | 25 |
| user_backchannel | 12 | 12 | 0.777 | 2.446 | 0.0% | 100.0% | 0.0% | 0.0% | 12 |
| talking_to_other | 13 | 13 | 1.932 | 2.976 | 23.1% | 69.2% | 7.7% | 0.0% | 13 |
| background_speech | 12 | 12 | 1.549 | 2.930 | 25.0% | 66.7% | 8.3% | 0.0% | 12 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 82.8% | 93.5% | 85.4% | 77.4% | 71.4% | 90.3% | 50.0% | 71.0% |
| user_interruption | 71.4% | 84.0% | 53.8% | 52.0% | 91.7% | 96.0% | 38.5% | 52.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 83.3% | 100.0% | 83.3% | 100.0% | 75.0% |
| talking_to_other | 76.9% | 100.0% | 100.0% | 100.0% | 40.0% | 76.9% | 40.0% | 76.9% |
| background_speech | 91.7% | 100.0% | 91.7% | 100.0% | 33.3% | 100.0% | 33.3% | 100.0% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 17 | 17 | 17 | 23.5% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 27 | 27 | 27 | 22.2% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 14 | 14 | 14 | 100.0% | 1.471 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 25 | 25 | 25 | 100.0% | 1.542 | 4.440 | 0 | n/a | n/a |
| icc_backchannel | 7 | 7 | 7 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
