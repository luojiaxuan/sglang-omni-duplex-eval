"""Tar each run directory under run_root/source, upload the tars with a manifest, and check remote sizes."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from huggingface_hub import HfApi

run_root, source, pack_dir, repo, prefix = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4], sys.argv[5]
members = {f"{name}.tar": [name] for name in sorted(p.name for p in (run_root / source).iterdir())}
members["logs-and-scripts.tar"] = ["logs", "shards", "setup.sh", "shards.py", "record_minicpmo.sh", "record_qwen.sh", "record_nemo.sh", "sweep_service.sh", "service_table.py", "pyshim"]
pack_dir.mkdir(parents=True, exist_ok=True)
manifest = {}
for tar_name, paths in members.items():
    target = pack_dir / tar_name
    base = run_root / source if tar_name != "logs-and-scripts.tar" else run_root
    subprocess.run(["tar", "cf", str(target), "-C", str(base), "--exclude=logs/session-server.log", *paths], check=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest[tar_name] = {"bytes": target.stat().st_size, "sha256": digest, "members": paths}
(pack_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
api = HfApi(token=os.environ["HF_TOKEN"])
print("whoami", api.whoami()["name"])
api.upload_folder(repo_id=repo, repo_type="dataset", folder_path=str(pack_dir), path_in_repo=prefix,
                  commit_message=f"Add {prefix}")
remote = {info.path.split("/")[-1]: info.size for info in api.get_paths_info(
    repo, [f"{prefix}/{name}" for name in [*manifest, "MANIFEST.json"]], repo_type="dataset")}
bad = {name: (entry["bytes"], remote.get(name)) for name, entry in manifest.items() if remote.get(name) != entry["bytes"]}
print("revision", api.dataset_info(repo).sha)
print("uploaded", len(remote), "files; size mismatches:", bad)
