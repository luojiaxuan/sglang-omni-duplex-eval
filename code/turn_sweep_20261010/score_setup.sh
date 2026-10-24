#!/bin/bash
# usage: score_setup.sh (inside the container); builds the scoring venv and fetches the pinned Parakeet checkpoint
set -euo pipefail
S=/data/runs/20261010-sweep
export UV_CACHE_DIR=/data/cache/uv HF_HOME=/data/cache/huggingface
cd $S
uv venv -q -p 3.12 score-venv
VIRTUAL_ENV=$S/score-venv uv pip install -q --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cu130 \
  torch==2.11.0 torchaudio==2.11.0 "nemo_toolkit[asr]==3.0.0" silero-vad==6.2.1 openai pydantic scipy soundfile tqdm websockets python-dotenv "torchcodec==0.11.*"
echo VENV_DONE
$S/score-venv/bin/python -c "from huggingface_hub import hf_hub_download; print(hf_hub_download('nvidia/parakeet-tdt-0.6b-v2', 'parakeet-tdt-0.6b-v2.nemo', revision='ae9ad07059c7c739ffaf932226a8fe64ae2620b0'))" > $S/logs/nemo_path.txt
echo NEMO_DONE
echo SCORE_SETUP_DONE
