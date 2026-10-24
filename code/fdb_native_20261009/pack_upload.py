"""Pack this run's artifacts into tar shards and upload them to a private HF dataset.

usage: pack_upload.py <repo_id> <path_in_repo>   (HF token on stdin)
"""

import json
import subprocess
import sys
from pathlib import Path

from huggingface_hub import HfApi

RUN = Path("/data/luojiaxuan/home/runs/20261009-fdb")
OUT = Path("/data/luojiaxuan/home/upload/20261009-fdb")
SHARDS = {
    **{f"rec-{d.name}.tar": [f"rec/{d.name}"] for d in sorted((RUN / "rec").iterdir())},
    "ref-v10.tar": ["ref-v10/export", "ref-v10/logs", "ref-v10/logs-nograph", "ref-v10/qwen-interrupt"],
    "ref-v10-nograph-transcripts.tar": ["ref-v10/export-nograph"],
    "ref-v15.tar": ["ref-v15"],
    "gated-v10.tar": ["gated-v10"],
    "judge-and-scripts.tar": ["judge", "logs", "lists", "v10_shard0.txt", "v10_shard1.txt", "v10_shard2.txt",
                              "v10_shard3.txt", "v15_shard0.txt", "v15_shard1.txt", "v15_shard2.txt", "v15_shard3.txt",
                              "serve.sh", "record.sh", "supervise.sh", "remaining.py", "chain.sh", "post_v15.sh",
                              "post_qwen.sh", "score_v15.sh", "score_v10_reference.sh", "gated_v10.sh",
                              "export_v10_reference.py", "graphs_off.py", "run_v10_interruption_local_judge.py"],
}


def main() -> None:
    repo_id, prefix = sys.argv[1], sys.argv[2]
    api = HfApi(token=sys.stdin.readline().strip())
    print("whoami", api.whoami()["name"], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, members in SHARDS.items():
        target = OUT / name
        excludes = ["--exclude=ref-v10/export-nograph/*/*/output.wav"] if name.startswith("ref-v10-nograph") else []
        subprocess.run(["tar", "-cf", str(target), *excludes, "-C", str(RUN), *members], check=True)
        digest = subprocess.run(["sha256sum", str(target)], check=True, capture_output=True, text=True).stdout.split()[0]
        manifest[name] = {"bytes": target.stat().st_size, "sha256": digest, "members": members}
        print(name, manifest[name]["bytes"], flush=True)
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    api.create_repo(repo_id, repo_type="dataset", private=True, exist_ok=True)
    api.upload_folder(folder_path=str(OUT), repo_id=repo_id, repo_type="dataset", path_in_repo=prefix,
                      commit_message=f"{prefix}: FDB v1.0 and v1.5 captures and scores")
    info = api.dataset_info(repo_id, files_metadata=True)
    remote = {s.rfilename: s.size for s in info.siblings if s.rfilename.startswith(prefix + "/")}
    for name, meta in manifest.items():
        assert remote.get(f"{prefix}/{name}") == meta["bytes"], name
    print("UPLOADED", info.sha, len(remote), flush=True)


if __name__ == "__main__":
    main()
