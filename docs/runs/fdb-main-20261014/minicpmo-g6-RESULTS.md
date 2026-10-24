# FDB results: minicpmo-g6

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 62 | 62 | 1.742 | 2.421 | 45.2% | 53.2% | 0.0% | 1.6% | 62 |
| user_interruption | 25 | 25 | 2.382 | 2.302 | 84.0% | 16.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 12 | 12 | 0.700 | 2.549 | 8.3% | 91.7% | 0.0% | 0.0% | 12 |
| talking_to_other | 13 | 13 | 1.923 | 2.384 | 30.8% | 61.5% | 0.0% | 7.7% | 13 |
| background_speech | 12 | 12 | 1.359 | 2.774 | 16.7% | 83.3% | 0.0% | 0.0% | 12 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 89.8% | 95.2% | 92.5% | 85.5% | 70.7% | 93.5% | 62.3% | 85.5% |
| user_interruption | 95.5% | 88.0% | 94.4% | 72.0% | 87.5% | 96.0% | 84.2% | 76.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 83.3% | 100.0% | 91.7% | 100.0% | 75.0% |
| talking_to_other | 76.9% | 100.0% | 84.6% | 100.0% | 25.0% | 92.3% | 15.4% | 100.0% |
| background_speech | 83.3% | 100.0% | 91.7% | 100.0% | 54.5% | 91.7% | 50.0% | 100.0% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 18 | 18 | 18 | 5.6% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 27 | 27 | 27 | 22.2% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 15 | 15 | 15 | 80.0% | 1.568 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 25 | 25 | 25 | 96.0% | 1.493 | 4.458 | 0 | n/a | n/a |
| icc_backchannel | 6 | 6 | 6 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
