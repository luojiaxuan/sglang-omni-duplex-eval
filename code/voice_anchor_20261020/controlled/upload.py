"""Upload the voice-anchor experiment to the public run dataset and check every file landed. argv: run directory."""
import hashlib
import json
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi

run = Path(sys.argv[1])
api = HfApi(token=os.environ["HF_TOKEN"])
print("whoami", api.whoami()["name"])
prefix = "20261020-cascade-voice-anchor"
files = ["voice-anchor.tar", "anchor_sweep.json", "xvector.json", "summary.json", "timbre_exp2.py", "anchor_sweep.py", "xvector.py", "servers.sh", "MANIFEST.json"]
manifest = {name: {"bytes": (run / "upload" / name).stat().st_size,
                   "sha256": hashlib.sha256((run / "upload" / name).read_bytes()).hexdigest()}
            for name in files if name != "MANIFEST.json"}
manifest["source"] = "private main 3dd888e02ac44fd64414241fc9ea55ab80a22adc, Qwen3-TTS-12Hz-1.7B CustomVoice and Base, one H200"
(run / "upload" / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
commit = api.upload_folder(repo_id="gavinlaw/sglang-omni-fdb-native-runs", repo_type="dataset", folder_path=str(run / "upload"),
                           path_in_repo=prefix, commit_message="Cascade voice anchor experiment (2026-10-20)")
print("revision", commit.oid)
info = {i.path: i.size for i in api.get_paths_info("gavinlaw/sglang-omni-fdb-native-runs", [f"{prefix}/{f}" for f in files], repo_type="dataset", revision=commit.oid)}
bad = {f: (info.get(f"{prefix}/{f}"), (run / "upload" / f).stat().st_size) for f in files if info.get(f"{prefix}/{f}") != (run / "upload" / f).stat().st_size}
print("uploaded", len(info), "size mismatches", bad)
