"""Rebuild a pack's logs tar without the private server log and replace it on HF."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

run_root, pack_dir, repo, prefix = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
target = pack_dir / "logs-and-scripts.tar"
manifest = json.loads((pack_dir / "MANIFEST.json").read_text())
paths = manifest["logs-and-scripts.tar"]["members"]
subprocess.run(["tar", "cf", str(target), "-C", str(run_root), "--exclude=logs/session-server.log", *paths], check=True)
assert b"session-server.log" not in subprocess.run(["tar", "tf", str(target)], check=True, capture_output=True).stdout
manifest["logs-and-scripts.tar"].update(bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest())
(pack_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
api = HfApi(token=os.environ["HF_TOKEN"])
api.create_commit(repo_id=repo, repo_type="dataset", commit_message=f"{prefix}: drop the server log from the logs tar", operations=[
    CommitOperationAdd(path_in_repo=f"{prefix}/{name}", path_or_fileobj=str(pack_dir / name)) for name in ("logs-and-scripts.tar", "MANIFEST.json")])
remote = {info.path.split("/")[-1]: info.size for info in api.get_paths_info(repo, [f"{prefix}/logs-and-scripts.tar", f"{prefix}/MANIFEST.json"], repo_type="dataset")}
print(prefix, "revision", api.dataset_info(repo).sha, "tar remote", remote["logs-and-scripts.tar"], "local", target.stat().st_size)
