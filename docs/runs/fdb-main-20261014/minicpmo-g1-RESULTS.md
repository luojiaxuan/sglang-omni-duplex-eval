# FDB results: minicpmo-g1

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 63 | 63 | 1.748 | 2.487 | 42.9% | 54.0% | 0.0% | 3.2% | 63 |
| user_interruption | 25 | 25 | 2.351 | 2.317 | 76.0% | 24.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 13 | 13 | 0.606 | 2.457 | 0.0% | 100.0% | 0.0% | 0.0% | 13 |
| talking_to_other | 12 | 12 | 2.027 | 2.602 | 33.3% | 50.0% | 0.0% | 16.7% | 12 |
| background_speech | 13 | 13 | 1.493 | 2.934 | 30.8% | 69.2% | 0.0% | 0.0% | 13 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 80.3% | 96.8% | 89.1% | 87.3% | 69.5% | 93.7% | 57.4% | 85.7% |
| user_interruption | 83.3% | 96.0% | 84.2% | 76.0% | 87.5% | 96.0% | 68.4% | 76.0% |
| user_backchannel | 100.0% | 100.0% | 91.7% | 92.3% | 100.0% | 92.3% | 91.7% | 92.3% |
| talking_to_other | 63.6% | 91.7% | 90.9% | 91.7% | 54.5% | 91.7% | 45.5% | 91.7% |
| background_speech | 69.2% | 100.0% | 92.3% | 100.0% | 16.7% | 92.3% | 16.7% | 92.3% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 17 | 17 | 17 | 5.9% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 27 | 27 | 27 | 25.9% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 15 | 15 | 15 | 73.3% | 1.540 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 25 | 25 | 25 | 84.6% | 1.554 | 4.476 | 1 | n/a | n/a |
| icc_backchannel | 7 | 7 | 7 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
