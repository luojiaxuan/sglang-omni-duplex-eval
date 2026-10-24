"""One row per client concurrency: the recorder's load block and server Unit timing.

argv: the sweep directory and the model's nominal Unit length in ms.
"""
import json
import sys
from pathlib import Path

from sglang_omni.profiler.duplex_metrics import build_duplex_session_metrics

unit_ms = float(sys.argv[2])
rows = []
for level_dir in sorted(Path(sys.argv[1]).glob("c*"), key=lambda p: int(p.name[1:])):
    load = json.loads((level_dir / "run" / "run.json").read_text())["load"]
    metrics = build_duplex_session_metrics(level_dir / "events")
    finished = [u for u in metrics["units"] if u["ready_to_finished_ms"] is not None]
    rows.append({
        "concurrency": load["concurrency"],
        "variants_passed": load["variants_passed"],
        "input_pacing_violations": load["input_pacing_violations"],
        "admission_denials": load["variants_with_admission_denials"],
        "initial_delay_s": load["initial_delay_s"],
        "units": len(metrics["units"]),
        "units_finished": len(finished),
        # note (luojiaxuan): a Unit misses its deadline when the server needs longer
        # than one nominal Unit to finish it, since the next Unit is due by then; the
        # short last Unit of a session is held to the same bound, not to its own audio.
        "deadline_misses": sum(u["ready_to_finished_ms"] > unit_ms for u in finished),
        "ready_to_first_output_ms": metrics["summary"]["ready_to_first_output_ms"],
        "ready_to_finished_ms": metrics["summary"]["ready_to_finished_ms"],
        "thinker_service_ms": metrics["summary"]["stages"]["thinker"]["service_ms"],
    })
print(json.dumps(rows, indent=1))
