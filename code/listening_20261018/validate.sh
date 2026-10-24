#!/bin/bash
# note (luojiaxuan): a small runbook pass with the listening metrics on one GPU, then the
# controlled perturbations: runbook setup without the judge model, generate, asr,
# aggregate, then cut, click and pitch-shift copies of real replies scored the same way.
# $1 run directory.
set -uo pipefail
R=$1
export HF_HOME=/data/cache/huggingface FDB_WORK=$R/fdb CUDA_VISIBLE_DEVICES=0 JUDGE=gpt PYTHONPATH=$R/src:$R/pyshim
cd $R/src
step() {
  local name=$1; shift
  local start=$SECONDS
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code seconds=$((SECONDS - start))"
  return $code
}
step pip pip install -e . && \
step setup python -m benchmarks.duplex.fdb setup && \
step generate python -m benchmarks.duplex.fdb generate --run-name listen --v15-per-subset 4 --v10-per-subset 3 --num-shards 2 && \
step asr python -m benchmarks.duplex.fdb asr --run-name listen && \
step aggregate python -m benchmarks.duplex.fdb aggregate --run-name listen && \
step perturb-make python $R/perturb_make.py $R/fdb/runs/listen/repeat-1/listening $R/perturb && \
step perturb-asr $R/fdb/scoring-venv/bin/python $R/perturb_asr.py $R/perturb $R/fdb/models/parakeet-tdt-0.6b-v2/parakeet-tdt-0.6b-v2.nemo && \
step perturb-score python -m benchmarks.eval.benchmark_duplex_listening score --out $R/perturb --device cuda
echo "VALIDATE_EXIT $?"
