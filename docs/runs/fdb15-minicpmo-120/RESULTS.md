# FDB v1.5 results: minicpmo-120

Repeats: repeat-1, repeat-2, repeat-3. Judge: qwen. Cells are mean ± sample standard deviation across repeats.
Latencies are pooled whole-file overlap intervals; label shares are over valid judge labels.

| Category | Pairs | Timed overlap sessions | Stop latency (s) | Response latency (s) | C_RESPOND | C_RESUME | C_UNCERTAIN_HANDLING | C_UNKNOWN | Judged pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 120 | 120 | 1.556 ± 0.006 | 2.563 ± 0.006 | 24.2 ± 0.8% | 70.0 ± 0.0% | 2.5 ± 0.8% | 3.3 ± 0.0% | 120 |
| user_interruption | 30 | 30 | 2.221 ± 0.009 | 2.364 ± 0.018 | 52.2 ± 1.9% | 41.1 ± 1.9% | 3.3 ± 0.0% | 3.3 ± 0.0% | 30 |
| user_backchannel | 30 | 30 | 0.681 ± 0.001 | 2.471 ± 0.003 | 0.0 ± 0.0% | 100.0 ± 0.0% | 0.0 ± 0.0% | 0.0 ± 0.0% | 30 |
| talking_to_other | 30 | 30 | 1.826 ± 0.001 | 2.555 ± 0.004 | 31.1 ± 1.9% | 60.0 ± 0.0% | 5.6 ± 1.9% | 3.3 ± 0.0% | 30 |
| background_speech | 30 | 30 | 1.550 ± 0.000 | 2.964 ± 0.004 | 13.3 ± 0.0% | 78.9 ± 1.9% | 1.1 ± 1.9% | 6.7 ± 0.0% | 30 |

## Semantic A/F/U judge

quality = A/(A+F); coverage = (A+F)/N. joint fails if any axis fails and accepts only if all three accept.

| Category | interaction_handling quality | interaction_handling coverage | relevance quality | relevance coverage | grounding quality | grounding coverage | joint quality | joint coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 79.6 ± 1.0% | 95.3 ± 1.3% | 87.8 ± 1.4% | 88.3 ± 1.7% | 73.7 ± 1.7% | 88.9 ± 1.3% | 56.0 ± 1.6% | 85.8 ± 1.7% |
| user_interruption | 65.4 ± 2.4% | 93.3 ± 3.3% | 65.4 ± 3.4% | 86.7 ± 6.7% | 91.5 ± 1.9% | 91.1 ± 3.8% | 45.5 ± 6.1% | 85.6 ± 3.8% |
| user_backchannel | 100.0 ± 0.0% | 100.0 ± 0.0% | 100.0 ± 0.0% | 94.4 ± 1.9% | 100.0 ± 0.0% | 92.2 ± 1.9% | 100.0 ± 0.0% | 90.0 ± 3.3% |
| talking_to_other | 65.9 ± 1.8% | 94.4 ± 1.9% | 87.0 ± 5.6% | 84.4 ± 3.8% | 46.7 ± 3.0% | 83.3 ± 3.3% | 29.1 ± 3.8% | 80.0 ± 3.3% |
| background_speech | 85.7 ± 0.0% | 93.3 ± 0.0% | 97.4 ± 2.2% | 87.8 ± 1.9% | 53.7 ± 3.2% | 88.9 ± 1.9% | 45.6 ± 1.0% | 87.8 ± 1.9% |
