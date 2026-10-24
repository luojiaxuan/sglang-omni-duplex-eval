#!/bin/bash
# usage: score_v15.sh; v1.5 reference phases on GPU 1 (export, Parakeet ASR with the #2666 fix, timing, judge requests, summary)
set -euo pipefail
cd /data/runs/20261009-fdb
PY=/data/runs/20261009-fdb/score-venv/bin/python
NEMO=/data/models/parakeet/parakeet-tdt-0.6b-v2.nemo
export PYTHONPATH=/data/runs/20261009-fdb/src HF_HOME=/data/cache/huggingface
runs=()
for d in rec/v15-nemotron-s*-p*; do runs+=(--run "$d"); done
ref=(--reference-source fdb-src --tree model=ref-v15/audio --out ref-v15/scores)
rm -rf ref-v15
$PY -m benchmarks.eval.benchmark_duplex_reference export --engine sglang --trace-format realtime-pcm16-v1 "${runs[@]}" --dataset-root /data/data/fdb/v1.5 --out ref-v15/audio
CUDA_VISIBLE_DEVICES=1 $PY -m benchmarks.eval.benchmark_duplex_reference asr "${ref[@]}" --nemo $NEMO --nemo-sha256 d99e39955c9d3d0350d8fb7c75e40c64a2b2eaeb003883d7c941fd2e8747b28c --device cuda
CUDA_VISIBLE_DEVICES= $PY -m benchmarks.eval.benchmark_duplex_reference timing "${ref[@]}" --audio-loader soundfile
$PY -m benchmarks.eval.benchmark_duplex_reference prepare-judge "${ref[@]}"
$PY -m benchmarks.eval.benchmark_duplex_reference summarize "${ref[@]}"
echo V15_PREPARED
