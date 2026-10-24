# FDB results: minicpmo-g5

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 62 | 62 | 1.759 | 2.559 | 45.2% | 51.6% | 1.6% | 1.6% | 62 |
| user_interruption | 25 | 25 | 2.252 | 2.447 | 72.0% | 28.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 12 | 12 | 0.817 | 2.541 | 0.0% | 100.0% | 0.0% | 0.0% | 12 |
| talking_to_other | 13 | 13 | 1.820 | 2.649 | 61.5% | 38.5% | 0.0% | 0.0% | 13 |
| background_speech | 12 | 12 | 1.555 | 2.845 | 16.7% | 66.7% | 8.3% | 8.3% | 12 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 75.9% | 93.5% | 88.0% | 80.6% | 67.9% | 90.3% | 53.8% | 83.9% |
| user_interruption | 77.3% | 88.0% | 75.0% | 80.0% | 88.0% | 100.0% | 60.0% | 80.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 91.7% | 100.0% | 75.0% | 100.0% | 75.0% |
| talking_to_other | 46.2% | 100.0% | 87.5% | 61.5% | 8.3% | 92.3% | 7.7% | 100.0% |
| background_speech | 81.8% | 91.7% | 100.0% | 91.7% | 60.0% | 83.3% | 60.0% | 83.3% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 17 | 17 | 17 | 0.0% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 27 | 27 | 27 | 18.5% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 15 | 15 | 15 | 86.7% | 1.455 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 25 | 25 | 25 | 88.0% | 1.727 | 4.091 | 0 | n/a | n/a |
| icc_backchannel | 7 | 7 | 7 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
