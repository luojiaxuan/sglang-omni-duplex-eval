#!/bin/bash
# note (luojiaxuan): the FDB smoke a MiniCPM-o CI stage would run, timed step by step on
# one GPU: runbook setup without the judge model, a small generate, then asr, which
# also writes the v1.0 unified scores. GPU memory is sampled every 2 s.
set -uo pipefail
R=$1
export HF_HOME=/data/cache/huggingface FDB_WORK=$R/fdb CUDA_VISIBLE_DEVICES=0 JUDGE=gpt PYTHONPATH=$R/src:$R/pyshim
cd $R/src
( while true; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits >> $R/logs/gpu-mem.log; sleep 2; done ) &
SAMPLER=$!
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
step generate python -m benchmarks.duplex.fdb generate --run-name ci --v15-per-subset 1 --v10-per-subset 3 && \
step asr python -m benchmarks.duplex.fdb asr --run-name ci
echo "SMOKE_EXIT $?"
kill $SAMPLER
echo "PEAK_GPU_MIB $(sort -n $R/logs/gpu-mem.log | tail -1)"
