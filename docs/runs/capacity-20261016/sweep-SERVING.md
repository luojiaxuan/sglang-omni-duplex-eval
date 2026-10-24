| N | mean open | sessions failed | 503 | pacing violations | unit miss | unit lag p50 / p90 / p99 (ms) | first audio p50 / p90 (ms) | buffer needed p50 / p90 (ms) | underrun replies | RTF p90 | meets targets |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 8 | 7.8 | 3/128 | 0 | 3 | 7.2% | 238 / 453 / 5608 | 304 / 505 | 91 / 227 | 78/143 | - | no failed sessions; no input pacing violations; unit miss rate at most 1% |
| 16 | 15.5 | 13/128 | 0 | 13 | 11.5% | 340 / 654 / 867 | 416 / 648 | 213 / 516 | 105/132 | - | no failed sessions; no input pacing violations; unit miss rate at most 1% |
| 24 | 21.0 | 11/128 | 0 | 11 | 14.9% | 471 / 933 / 1351 | 584 / 875 | 356 / 730 | 120/136 | - | no failed sessions; no input pacing violations; unit miss rate at most 1% |
| 32 | 30.0 | 16/128 | 0 | 16 | 29.0% | 611 / 1150 / 1631 | 770 / 1070 | 450 / 830 | 111/131 | - | no failed sessions; no input pacing violations; unit miss rate at most 1% |
| 48 | 26.1 | 126/128 | 0 | 19 | 98.3% | 210 / 270 / 326 | 231 / 269 | 64 / 100 | 1/3 | - | no failed sessions; no input pacing violations; unit miss rate at most 1% |

No recorded concurrency meets the targets.
