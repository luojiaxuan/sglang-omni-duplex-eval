# FDB results: preflight

Repeats: repeat-1. Judge: qwen. Cells are mean ± sample standard deviation across repeats.

## FDB v1.5 results

Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 4 | 4 | 1.329 | 2.378 | 25.0% | 75.0% | 0.0% | 0.0% | 4 |
| user_interruption | 1 | 1 | n/a | 1.124 | 0.0% | 100.0% | 0.0% | 0.0% | 1 |
| user_backchannel | 1 | 1 | 0.668 | 1.956 | 0.0% | 100.0% | 0.0% | 0.0% | 1 |
| talking_to_other | 1 | 1 | 1.500 | 3.236 | 0.0% | 100.0% | 0.0% | 0.0% | 1 |
| background_speech | 1 | 1 | 1.820 | 2.788 | 100.0% | 0.0% | 0.0% | 0.0% | 1 |

## v1.5 semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 66.7% | 75.0% | 100.0% | 75.0% | 75.0% | 100.0% | 66.7% | 75.0% |
| user_interruption | n/a | 0.0% | n/a | 0.0% | 100.0% | 100.0% | n/a | 0.0% |
| user_backchannel | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| talking_to_other | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| background_speech | 0.0% | 100.0% | 100.0% | 100.0% | 0.0% | 100.0% | 0.0% | 100.0% |

## FDB v1.0 results

Pinned reference evaluation per subset; subsets are never pooled. Selected counts the recorded samples, Eligible the exports the evaluator can score, Evaluated the ones it scored; a subset that is not evaluated shows n/a and is listed under the table. Takeover rate should be low on pause handling and backchannel, and high on turn taking and interruption. Relevance is a 0-5 rating of the interruptions the model took over, by the local Qwen judge, non-official; a nonzero Judge retries count inflates that subset's takeover rate.

| Category | Selected | Eligible | Evaluated | Takeover rate | Latency (s) | Relevance (0-5) | Judge retries | Backchannel frequency | Backchannel JSD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_pause_handling | 3 | 3 | 3 | 0.0% | n/a | n/a | n/a | n/a | n/a |
| candor_pause_handling | 3 | 3 | 3 | 0.0% | n/a | n/a | n/a | n/a | n/a |
| candor_turn_taking | 3 | 3 | 3 | 100.0% | 2.057 | n/a | n/a | n/a | n/a |
| synthetic_user_interruption | 3 | 3 | 3 | 100.0% | 1.680 | 5.000 | 0 | n/a | n/a |
| icc_backchannel | 3 | 3 | 3 | 0.0% | n/a | n/a | n/a | 0.000 | 1.000 |
