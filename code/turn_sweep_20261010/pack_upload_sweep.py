"""Pack the turn-detection sweep into tar shards and upload them to the public HF run dataset.

usage: pack_upload_sweep.py <repo_id> <path_in_repo>   (HF token on stdin)
"""

import json
import subprocess
import sys
from pathlib import Path

from huggingface_hub import HfApi

RUN = Path("/data/runs/20261010-sweep")
OUT = Path("/data/upload/20261010-sweep")
ARMS = ["vad500", "vad800", "vad1200", "semmed"]
SHARDS = {
    **{f"rec-{arm}.tar": [f"rec/{arm}"] for arm in ARMS},
    "score.tar": [f"score/{arm}" for arm in ARMS],
    "logs-and-scripts.tar": ["logs", "sweep_serve.sh", "sweep_arm.sh", "sweep_record.sh", "score_setup.sh",
                             "score_sweep.sh", "summarize_sweep.py"],
}


def main() -> None:
    repo_id, prefix = sys.argv[1], sys.argv[2]
    api = HfApi(token=sys.stdin.readline().strip())
    print("whoami", api.whoami()["name"], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, members in SHARDS.items():
        target = OUT / name
        subprocess.run(["tar", "-cf", str(target), "-C", str(RUN), *members], check=True)
        digest = subprocess.run(["sha256sum", str(target)], check=True, capture_output=True, text=True).stdout.split()[0]
        manifest[name] = {"bytes": target.stat().st_size, "sha256": digest, "members": members}
        print(name, manifest[name]["bytes"], flush=True)
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    api.upload_folder(folder_path=str(OUT), repo_id=repo_id, repo_type="dataset", path_in_repo=prefix,
                      commit_message=f"{prefix}: turn-detection sweep captures and official-caliber v1.0 scores")
    info = api.dataset_info(repo_id, files_metadata=True)
    remote = {s.rfilename: s.size for s in info.siblings if s.rfilename.startswith(prefix + "/")}
    for name, meta in manifest.items():
        assert remote.get(f"{prefix}/{name}") == meta["bytes"], name
    print("UPLOADED", info.sha, len(remote), flush=True)


if __name__ == "__main__":
    main()
