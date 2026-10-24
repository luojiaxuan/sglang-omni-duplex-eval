"""Side-by-side listening metrics of two systems on the same samples, and the
worst replies of each per metric.

argv: output markdown, then LABEL=LISTENING_DIR for each system.
"""
import json
import sys
from pathlib import Path

COLUMNS = (
    ("replies", "replies", "{}"),
    ("short_replies", "short", "{}"),
    ("compared_replies", "compared", "{}"),
    ("omission_rate", "omission", "{:.1%}"),
    ("word_error_rate", "WER", "{:.1%}"),
    ("utmos_mean", "UTMOS", "{:.2f}"),
    ("utmos_p10", "UTMOS p10", "{:.2f}"),
    ("voice_similarity_mean", "voice", "{:.1f}"),
    ("voice_similarity_p10", "voice p10", "{:.1f}"),
)
WORST = 5


def cell(value, fmt):
    return "n/a" if value is None else fmt.format(value)


out = Path(sys.argv[1])
systems = dict(arg.split("=", 1) for arg in sys.argv[2:])
lines = []
summaries = {
    label: json.loads((Path(path) / "summary.json").read_text())["datasets"]
    for label, path in systems.items()
}
for dataset in ("v1.5", "v1.0"):
    categories = sorted({c for s in summaries.values() for c in s.get(dataset, {})})
    if "all" in categories:
        categories = ["all"] + [c for c in categories if c != "all"]
    lines += [f"## {dataset}", "", "| category | system | " + " | ".join(t for _, t, _ in COLUMNS) + " |",
              "|---|---|" + "---:|" * len(COLUMNS)]
    for category in categories:
        for label, summary in summaries.items():
            group = summary.get(dataset, {}).get(category)
            if group is None:
                continue
            lines.append(f"| {category} | {label} | " + " | ".join(cell(group[k], f) for k, _, f in COLUMNS) + " |")
    lines.append("")
for label, path in systems.items():
    replies = json.loads((Path(path) / "scores.json").read_text())["replies"]
    statuses = {}
    for reply in replies:
        statuses[str(reply["status"])] = statuses.get(str(reply["status"]), 0) + 1
    durations = sorted(reply["duration_s"] for reply in replies if reply["wav"])
    lines += [f"## {label}: replies", "", f"statuses {statuses}; with audio {len(durations)}; "
              f"duration median {durations[len(durations) // 2]:.1f} s" if durations else "", ""]
    compared = [r for r in replies if r["word_errors"] and r["word_errors"]["reference_words"]]
    compared.sort(key=lambda r: -r["word_errors"]["deletions"] / r["word_errors"]["reference_words"])
    lines += [f"### {label}: highest omission", ""]
    for r in compared[:WORST]:
        e = r["word_errors"]
        lines.append(f"- `{r['sample_id']}` {r['variant']} {r['duration_s']:.1f} s, {e['deletions']}/{e['reference_words']} deleted; "
                     f"said: {r['transcript']!r}; heard: {r['asr_text']!r}")
    for key, title in (("utmos", "lowest UTMOS"), ("voice_similarity", "lowest voice similarity")):
        scored = sorted((r for r in replies if r[key] is not None), key=lambda r: r[key])
        lines += ["", f"### {label}: {title}", ""]
        for r in scored[:WORST]:
            lines.append(f"- `{r['sample_id']}` {r['variant']} {r['duration_s']:.1f} s, {key} {r[key]:.2f}; heard: {r['asr_text']!r}; wav `{r['wav']}`")
    lines.append("")
out.write_text("\n".join(lines) + "\n")
print(out.read_text())
