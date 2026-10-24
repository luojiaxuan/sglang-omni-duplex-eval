"""Upload the anchored cascade FDB run to the public run dataset and check every file landed. argv: run directory."""
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

from huggingface_hub import HfApi

run = Path(sys.argv[1])
api = HfApi(token=os.environ["HF_TOKEN"])
print("whoami", api.whoami()["name"])
prefix = "20261020-cascade-voice-anchor/fdb-rerun-xvector"
up = run / "upload-xvector"
up.mkdir(exist_ok=True)
with tarfile.open(up / "cascadexvec-fdb.tar", "w") as tar:
    tar.add(run / "fdb" / "runs" / "cascadexvec", arcname="cascadexvec")
    tar.add(run / "xvector-examples", arcname="xvector-examples")
with tarfile.open(up / "logs.tar", "w") as tar:
    tar.add(run / "logs", arcname="logs")
names = ["cascadexvec-fdb.tar", "logs.tar"]
manifest = {n: {"bytes": (up / n).stat().st_size, "sha256": hashlib.sha256((up / n).read_bytes()).hexdigest()} for n in names}
manifest["source"] = "private main 3dd888e02ac44fd64414241fc9ea55ab80a22adc with the x-vector bench profile; client sglang-omni a1939b97 plus 7ddb4364"
(up / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
names.append("MANIFEST.json")
commit = api.upload_folder(repo_id="gavinlaw/sglang-omni-fdb-native-runs", repo_type="dataset", folder_path=str(up),
                           path_in_repo=prefix, commit_message="Cascade voice anchor: FDB v1.5 re-run with the speaker-embedding clone (2026-10-21)")
print("revision", commit.oid)
info = {i.path: i.size for i in api.get_paths_info("gavinlaw/sglang-omni-fdb-native-runs", [f"{prefix}/{n}" for n in names], repo_type="dataset", revision=commit.oid)}
print("size mismatches", {n: (info.get(f"{prefix}/{n}"), (up / n).stat().st_size) for n in names if info.get(f"{prefix}/{n}") != (up / n).stat().st_size})
