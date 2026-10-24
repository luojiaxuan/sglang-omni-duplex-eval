#!/bin/bash
# usage: score_sweep.sh <arm> <gpu>; official-caliber v1.0 scoring of one sweep arm: export, Parakeet ASR, upstream evaluate
set -euo pipefail
S=/data/runs/20261010-sweep
PY=$S/score-venv/bin/python
export PYTHONPATH=$S/harness-score HF_HOME=/data/cache/huggingface CUDA_VISIBLE_DEVICES=$2
NEMO=$(cat $S/logs/nemo_path.txt)
cd $S
rm -rf score/$1 && mkdir -p score/$1
$PY -m benchmarks.eval.benchmark_duplex_v10 reference-export --run rec/$1 --dataset-root data/fdb/v1.0 --out score/$1/ref --trace-format realtime-legacy-pcm16-v1
echo EXPORT_DONE
$PY -m benchmarks.eval.benchmark_duplex_v10 reference-asr --tree score/$1/ref --reference-source fdb-src --nemo "$NEMO" \
  --nemo-sha256 d99e39955c9d3d0350d8fb7c75e40c64a2b2eaeb003883d7c941fd2e8747b28c --device cuda
echo ASR_DONE
$PY -m benchmarks.eval.benchmark_duplex_v10 reference-evaluate --tree score/$1/ref --reference-source fdb-src
echo EVALUATE_DONE
