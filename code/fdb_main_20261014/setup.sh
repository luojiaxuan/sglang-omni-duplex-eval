#!/bin/bash
# note (luojiaxuan): one-time setup inside the task container; HF_TOKEN arrives on stdin.
set -euo pipefail
R=/data/runs/20261014-fdb
read -r HF_TOKEN; export HF_TOKEN
export HF_HOME=/data/cache/huggingface FDB_WORK=$R/fdb PYTHONPATH=$R/src:$R/pyshim CUDA_VISIBLE_DEVICES=0
cd $R/src
python -m benchmarks.duplex.fdb setup > $R/logs/setup.log 2>&1
echo SETUP_RUNBOOK_DONE
hf download nvidia/NVIDIA-NemotronLabs-VoiceChat-11B --local-dir $R/models/voicechat > $R/logs/voicechat-download.log 2>&1
echo SETUP_ALL_DONE
