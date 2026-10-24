| N | mean open | sessions failed | 503 | pacing violations | unit miss | unit lag p50 / p90 / p99 (ms) | first audio p50 / p90 (ms) | buffer needed p50 / p90 (ms) | underrun replies | RTF p90 | meets targets |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 1.0 | 0/200 | 0 | 0 | 0.0% | 178 / 208 / 264 | 184 / 207 | 58 / 97 | 53/228 | - | yes |
| 2 | 2.0 | 0/128 | 0 | 0 | 0.0% | 202 / 261 / 329 | 216 / 261 | 62 / 118 | 49/144 | - | yes |
| 4 | 4.0 | 0/128 | 0 | 0 | 0.0% | 219 / 321 / 451 | 252 / 312 | 74 / 159 | 70/149 | - | yes |
| 8 | 7.8 | 0/128 | 0 | 0 | 0.5% | 242 / 445 / 810 | 309 / 419 | 138 / 292 | 96/143 | - | yes |
| 16 | 15.5 | 0/128 | 0 | 0 | 2.6% | 404 / 772 / 1125 | 481 / 865 | 283 / 652 | 116/147 | - | unit miss rate at most 1% |
| 24 | 21.2 | 0/128 | 0 | 0 | 20.5% | 498 / 1235 / 1797 | 672 / 1021 | 383 / 1063 | 120/154 | - | unit miss rate at most 1% |
| 32 | 28.3 | 7/128 | 0 | 7 | 59.8% | 1360 / 3375 / 6070 | 1300 / 2027 | 1586 / 3372 | 136/143 | - | no failed sessions; no input pacing violations; unit miss rate at most 1% |

Highest concurrency meeting the targets: 8.

