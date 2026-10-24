#!/bin/bash
# usage: fdb15_repeats.sh <run dir> <num gpus>
# Runs the sglang-omni#2668 FDB v1.5 runbook for MiniCPM-o with --per-subset 30 and three repeats,
# one GPU per repeat, then aggregates. A failed generate is retried once from an empty repeat directory.
RUN=$1
NGPU=$2
NAME=minicpmo-120
cd $RUN/src
unset CUDA_VISIBLE_DEVICES
export FDB_WORK=/data/fdb PYTHONPATH=/data/pyshim HF_HOME=/data/cache/huggingface
mkdir -p $RUN/logs

python -m benchmarks.duplex.fdb_v15 setup > $RUN/logs/setup.log 2>&1 || { echo "SETUP_FAILED"; exit 1; }
echo "SETUP_DONE"

run_repeat() {
  local k=$1 gpu=$2
  local env=(GPU=$gpu SERVER_PORT=$((8096 + k)) JUDGE_PORT=$((29999 + k)))
  local attempt
  for attempt in 1 2; do
    if env "${env[@]}" python -m benchmarks.duplex.fdb_v15 generate --run-name $NAME --repeat $k --per-subset 30 \
        > $RUN/logs/r$k-generate-a$attempt.log 2>&1; then
      break
    fi
    echo "r$k generate attempt $attempt failed"
    rm -rf $FDB_WORK/runs/$NAME/repeat-$k
    if [ $attempt = 2 ]; then echo "FAILED r$k generate"; return 1; fi
  done
  env "${env[@]}" python -m benchmarks.duplex.fdb_v15 asr --run-name $NAME --repeat $k > $RUN/logs/r$k-asr.log 2>&1 \
    || { echo "FAILED r$k asr"; return 1; }
  env "${env[@]}" python -m benchmarks.duplex.fdb_v15 judge --run-name $NAME --repeat $k > $RUN/logs/r$k-judge.log 2>&1 \
    || { echo "FAILED r$k judge"; return 1; }
  echo "DONE r$k"
}

if [ "$NGPU" -ge 3 ]; then
  run_repeat 1 0 & run_repeat 2 1 & run_repeat 3 2 &
else
  (run_repeat 1 0; run_repeat 3 0) & run_repeat 2 1 &
fi
wait
python -m benchmarks.duplex.fdb_v15 aggregate --run-name $NAME > $RUN/logs/aggregate.log 2>&1 && echo "ALL_DONE" || echo "AGGREGATE_FAILED"
