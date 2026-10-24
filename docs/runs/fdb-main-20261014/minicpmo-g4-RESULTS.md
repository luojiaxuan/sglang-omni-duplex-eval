# FDB results: minicpmo-g4

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 62 | 62 | 1.700 | 2.478 | 35.5% | 64.5% | 0.0% | 0.0% | 62 |
| user_interruption | 25 | 25 | 2.330 | 2.318 | 56.0% | 44.0% | 0.0% | 0.0% | 25 |
| user_backchannel | 12 | 12 | 0.692 | 2.551 | 0.0% | 100.0% | 0.0% | 0.0% | 12 |
| talking_to_other | 13 | 13 | 1.857 | 2.542 | 46.2% | 53.8% | 0.0% | 0.0% | 13 |
| background_speech | 12 | 12 | 1.227 | 2.820 | 16.7% | 83.3% | 0.0% | 0.0% | 12 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 72.4% | 93.5% | 80.4% | 82.3% | 75.0% | 90.3% | 48.1% | 83.9% |
| user_interruption | 59.1% | 88.0% | 52.9% | 68.0% | 91.3% | 92.0% | 38.9% | 72.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 83.3% | 100.0% | 83.3% |
| talking_to_other | 53.8% | 100.0% | 90.0% | 76.9% | 53.8% | 100.0% | 30.8% | 100.0% |
| background_speech | 90.9% | 91.7% | 91.7% | 100.0% | 40.0% | 83.3% | 36.4% | 91.7% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 17 | 17 | 17 | 17.6% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 27 | 27 | 27 | 22.2% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 15 | 15 | 15 | 80.0% | 1.542 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 25 | 25 | 25 | 96.0% | 1.513 | 3.792 | 0 | n/a | n/a |
| icc_backchannel | 7 | 7 | 7 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
