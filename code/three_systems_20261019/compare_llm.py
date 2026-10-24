"""Main-table metrics of several runs side by side, read from each run's RESULTS.md.

argv: output markdown, then LABEL=RESULTS.md for each run.
"""
import re
import sys
from pathlib import Path


def tables(text):
    """Every markdown table as a list of row dicts keyed by the header cells."""
    found, lines = [], text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-:| ]+\|$", lines[i + 1]):
            head = [c.strip() for c in line.strip("|").split("|")]
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                rows.append(dict(zip(head, [c.strip() for c in row.strip("|").split("|")])))
            found.append(rows)
    return found


def metrics(path):
    text = Path(path).read_text()
    found = tables(text)
    v15 = next(t for t in found if t and "C_RESPOND" in t[0])
    semantic = next(t for t in found if t and "interaction_handling quality" in t[0])
    unified = [t for t in found if t and "Metric" in t[0] and "Value and interval" in t[0]][0]
    listening = text[text.index("## Listening quality"):]
    listen_v15 = tables(listening)[0]
    by = {r["Category"]: r for r in v15}
    sem = {r["Category"]: r for r in semantic}
    uni = {(r["Subset"].strip("`"), r["Metric"].strip("`")): r["Value and interval"].split()[0] for r in unified}
    lis = {r["Category"]: r for r in listen_v15}
    pct = lambda v: f"{float(v) * 100:.0f}%"
    return {
        "Responds when the user interrupts": by["user_interruption"]["C_RESPOND"],
        "Keeps talking through a backchannel": by["user_backchannel"]["C_RESUME"],
        "Keeps talking when the user addresses someone else": by["talking_to_other"]["C_RESUME"],
        "Keeps talking through background speech": by["background_speech"]["C_RESUME"],
        "Overlap handled appropriately (LLM judge)": sem["all"]["interaction_handling quality"],
        "Relevance (LLM judge)": sem["all"]["relevance quality"],
        "Grounding (LLM judge)": sem["all"]["grounding quality"],
        "Joint quality (LLM judge)": sem["all"]["joint quality"],
        "Stop / response latency (s)": f"{float(by['all']['Stop latency (s)']):.2f} / {float(by['all']['Response latency (s)']):.2f}",
        "Speaks into a pause, synthetic / natural": f"{pct(uni[('synthetic_pause_handling', 'pause_intrusion_rate')])} / {pct(uni[('candor_pause_handling', 'pause_intrusion_rate')])}",
        "Takes the turn within 2 s": pct(uni[("candor_turn_taking", "response_rate_2s")]),
        "Omission rate": lis["all"]["Omission rate"],
        "UTMOS": f"{float(lis['all']['UTMOS mean']):.2f}",
        "Voice consistency": f"{float(lis['all']['Voice similarity mean']):.1f}",
    }


runs = dict(arg.split("=", 1) for arg in sys.argv[2:])
values = {label: metrics(path) for label, path in runs.items()}
names = list(next(iter(values.values())))
lines = ["| Metric | " + " | ".join(runs) + " |", "| --- |" + " ---: |" * len(runs)]
lines += [f"| {name} | " + " | ".join(values[label][name] for label in runs) + " |" for name in names]
Path(sys.argv[1]).write_text("\n".join(lines) + "\n")
print("\n".join(lines))
