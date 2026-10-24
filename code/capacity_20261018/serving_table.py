"""One markdown row per recorded level from the serving.json files under a capacity directory.

argv: capacity directory (holding <level>-<tag>/serving.json).
"""
import json
import sys
from pathlib import Path


def ms(seconds):
    return f"{seconds * 1000:.0f}"


rows = []
for path in Path(sys.argv[1]).glob("*/serving.json"):
    for level in json.loads(path.read_text())["levels"]:
        rows.append((level["concurrency"], path.parent.name, level))
rows.sort(key=lambda row: (row[0], row[1]))
print("| 档 | 平均在线 | 失败会话 | 503 | 发包迟到 | 超时单元 | 超时率 | 单元延迟 p50/p90/p99/max (ms) | 首音 p50/p90 (ms) | 起播缓冲 p90 (ms) |")
print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for _, name, level in rows:
    lag = level["unit_lag_s"]
    first = level["first_audio_latency_s"]
    print(
        f"| {name} | {level['mean_open_sessions']:.1f} | {level['sessions_failed']}/{level['sessions']}"
        f" | {level['admission_denials']} | {level['input_pacing_violations']}"
        f" | {level['units_missed']}/{level['units_expected']} | {level['unit_miss_rate'] * 100:.2f}%"
        f" | {ms(lag['p50'])}/{ms(lag['p90'])}/{ms(lag['p99'])}/{ms(lag['max'])}"
        f" | {ms(first['p50'])}/{ms(first['p90'])} | {ms(level['startup_buffer_needed_s']['p90'])} |"
    )
