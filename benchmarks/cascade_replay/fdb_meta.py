# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path


def sample_meta(d: Path, duration: float) -> dict:
    """Turn-taking samples end the user turn at their first annotated event; pause samples at the end of
    input, and carry the annotated pause."""
    if (d / "turn_taking.json").exists():
        return {"task": "turn", "user_end": float(json.loads((d / "turn_taking.json").read_text())[0]["timestamp"][0]),
                "duration": duration}
    pause = json.loads((d / "pause.json").read_text())[0]["timestamp"]
    return {"task": "pause", "user_end": duration, "duration": duration, "pause": [float(pause[0]), float(pause[1])]}
