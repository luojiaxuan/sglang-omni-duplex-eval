#!/bin/bash
# note (luojiaxuan): serving sweep of the Qwen3.8-27B cascade, one concurrency level per replica
# and GPU at the same time, on the same v1.5 sessions as the 4B sweep. $1 run directory, $2 server commit.
set -uo pipefail
R=$1; SHA=$2; FDB=$R/fdb
export HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0 PYTHONPATH=$R/src
cd $R/src
step() {
  local name=$1; shift
  printf '%s\t%s\tcd %q && env HF_HOME=%q FDB_WORK=%q PYTHONPATH=%q' "$(date -u +%FT%TZ)" "$name" "$PWD" "$HF_HOME" "$FDB_WORK" "$PYTHONPATH" >> $R/logs/commands.log
  printf ' %q' "$@" >> $R/logs/commands.log; printf '\n' >> $R/logs/commands.log
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code"
  return $code
}
step pip pip install -e . && step setup python -m benchmarks.duplex.fdb setup || exit 1
for r in 0 1 2 3; do
  until curl -sf http://127.0.0.1:$((28870 + r))/v1/models | grep -qi "27b-customvoice-bench-r$r"; do sleep 15; done
done
echo "READY $(date -u +%FT%TZ)"
TURNS='{"type": "server_vad", "silence_duration_ms": 800}'
LEVELS=(2 4 8 16)
for r in 0 1 2 3; do
  L=${LEVELS[$r]}
  step cascade27b-c$L python -m benchmarks.eval.benchmark_duplex_serving sweep --dataset v1.5 --concurrency $L \
    --output $R/serving/cascade27b/c$L -- --profile turn-based --url ws://127.0.0.1:$((28870 + r))/v1/realtime \
    --model streaming-cascade/qwen3-asr-qwen3.8-27b-customvoice --model-revision $SHA --server-revision $SHA \
    --turn-detection "$TURNS" --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" \
    --timeout 90 --max-per-subset 16 &
done
wait
RUNS=()
for L in "${LEVELS[@]}"; do RUNS+=(--run $(ls -d $R/serving/cascade27b/c$L/concurrency-*)); done
step cascade27b-serving-report python -m benchmarks.eval.benchmark_duplex_serving report "${RUNS[@]}" --output $R/serving/cascade27b/serving.json
cp $R/logs/cascade27b-serving-report.log $R/serving/cascade27b/SERVING.md
echo "SWEEP_DONE"
