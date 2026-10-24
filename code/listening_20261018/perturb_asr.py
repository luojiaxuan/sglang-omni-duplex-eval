"""Parakeet text of every perturbed reply, in the scoring venv.

argv: perturbation directory, Parakeet .nemo checkpoint.
"""
import json
import sys
from pathlib import Path

from benchmarks.duplex.reference_asr import load_nemo_model
from benchmarks.duplex.run_artifacts import file_sha256
from benchmarks.duplex.v15_audio import write_json

out, nemo = Path(sys.argv[1]), Path(sys.argv[2])
document = json.loads((out / "replies.json").read_text())
model = load_nemo_model(nemo, "cuda")
hypotheses = model.transcribe([str(out / reply["wav"]) for reply in document["replies"]])
for reply, hypothesis in zip(document["replies"], hypotheses, strict=True):
    reply["asr_text"] = hypothesis.text
document["asr"] = {"checkpoint_sha256": file_sha256(nemo), "device_type": "cuda"}
write_json(out / "replies.json", document)
