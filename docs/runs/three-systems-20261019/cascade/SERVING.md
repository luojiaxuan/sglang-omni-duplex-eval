| N | mean open | sessions failed | 503 | pacing violations | unit miss | unit lag p50 / p90 / p99 (ms) | first audio p50 / p90 (ms) | buffer needed p50 / p90 (ms) | underrun replies | RTF p90 | meets targets |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 1.0 | 0/200 | 0 | 0 | - | - / - / - | 101 / 143 | 0 / 0 | 0/300 | 0.87 | yes |
| 2 | 2.0 | 0/128 | 0 | 0 | - | - / - / - | 117 / 225 | 0 / 0 | 2/192 | 0.86 | yes |
| 4 | 4.0 | 0/128 | 0 | 0 | - | - / - / - | 117 / 234 | 0 / 0 | 0/192 | 0.86 | yes |
| 8 | 7.8 | 0/128 | 0 | 0 | - | - / - / - | 122 / 246 | 0 / 0 | 0/192 | 0.84 | yes |
| 16 | 15.3 | 0/128 | 0 | 0 | - | - / - / - | 146 / 297 | 0 / 0 | 0/192 | 0.85 | yes |
| 24 | 14.7 | 112/128 | 0 | 0 | - | - / - / - | 257 / 317 | 0 / 0 | 0/24 | 0.88 | no failed sessions |
| 32 | 15.2 | 122/128 | 0 | 10 | - | - / - / - | 322 / 339 | 0 / 0 | 0/9 | 0.86 | no failed sessions; no input pacing violations |

Highest concurrency meeting the targets: 16.

