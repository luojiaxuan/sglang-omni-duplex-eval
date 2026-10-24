"""Print the official-caliber v1.0 results of every sweep arm as one table.

usage: summarize_sweep.py <run dir>
"""

import json
import sys
from pathlib import Path

ARMS = ["vad500", "vad800", "vad1200", "semmed"]


def main() -> None:
    run = Path(sys.argv[1])
    rows = {}
    for arm in ARMS:
        summary = json.loads((run / "score" / arm / "ref" / "summary.json").read_text())
        record = json.loads((run / "rec" / arm / "run.json").read_text())["summary"]["variants"]
        rows[arm] = {
            "sessions": {k: record[k] for k in ("pass", "fail", "error", "invalid", "pending")},
            "subsets": {
                subset: {"selected": value["selected"], "evaluated": value["evaluated"], "result": value["result"]}
                for subset, value in summary["subsets"].items()
            },
        }
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
