"""Download only what the serving sweep needs: the FDB v1.5 dataset and MiniCPM-o.

The runbook's own setup also builds the scoring venv and fetches the v1.0 data,
Parakeet and the judge, none of which a serving sweep reads; gdown is the only
scoring tool the dataset step calls, so the scoring venv here holds just that.
"""

import subprocess
import sys

from huggingface_hub import snapshot_download

from benchmarks.duplex.fdb import setup_assets
from benchmarks.duplex.fdb.common import MODEL_ID, load_settings

settings = load_settings("capacity")
setup_assets.setup_model_extra()
(settings.fdb_work / "models").mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, "-m", "venv", str(settings.scoring_venv)], check=True)
subprocess.run([str(settings.scoring_venv / "bin" / "pip"), "install", "--quiet", "gdown"], check=True)
setup_assets.setup_dataset(
    "[v1.5]",
    settings,
    settings.dataset,
    settings.dataset_revision_file,
    settings.dataset_dir / "zips",
    setup_assets.SUBSETS,
    setup_assets.DATASET_DRIVE_FILE_IDS,
)
snapshot_download(MODEL_ID, revision=settings.model_revision, local_dir=settings.model_path)
print(f"MODEL_PATH {settings.model_path}")
print(f"MODEL_REVISION {settings.model_revision}")
