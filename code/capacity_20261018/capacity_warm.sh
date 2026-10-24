#!/bin/bash
# note (luojiaxuan): one MiniCPM-o server at max_sessions $3, a short warm-up recording at
# that concurrency so every batch shape has run once, then the client-side serving sweep.
# The first sweep without warm-up put nearly every late unit in the first wave of sessions.
# $1 run directory, $2 server commit, $3 max_sessions, $4 comma-separated levels, $5 output name.
set -uo pipefail
R=$1; SERVER_SHA=$2; M=$3; LEVELS=$4; NAME=$5; FDB=$R/fdb; PORT=8400; STARTUP_LIMIT_S=1200
export PYTHONPATH=$R/src:$R/pyshim HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0
cd $R/src
MODEL_PATH=$(grep '^MODEL_PATH' $R/logs/setup.log | cut -d' ' -f2)
MODEL_REVISION=$(grep '^MODEL_REVISION' $R/logs/setup.log | cut -d' ' -f2)
RECORD=(--url ws://127.0.0.1:$PORT/v1/realtime --profile minicpmo-native-pr2377
  --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)"
  --server-revision $SERVER_SHA --model openbmb/MiniCPM-o-4_5 --model-revision $MODEL_REVISION --timeout 90)
python -m sglang_omni.cli serve --model-path $MODEL_PATH --variant session --enable-realtime \
  --host 127.0.0.1 --port $PORT --max_sessions $M > $R/logs/server-$NAME.log 2>&1 &
SERVER=$!
START=$SECONDS
until curl -sf -o /dev/null http://127.0.0.1:$PORT/health; do
  if ! kill -0 $SERVER 2>/dev/null || (( SECONDS - START > STARTUP_LIMIT_S )); then echo "SERVER_FAILED $NAME"; exit 1; fi
  sleep 10
done
echo "SERVER_UP $NAME max_sessions=$M after $((SECONDS - START)) s"
python -m benchmarks.eval.benchmark_duplex_v15 record "${RECORD[@]}" --concurrency $M --max-per-subset 10 \
  --output $R/warmup-$NAME > $R/logs/warmup-$NAME.log 2>&1
echo "WARMUP_EXIT $?"
python -m benchmarks.eval.benchmark_duplex_serving sweep --dataset v1.5 --concurrency $LEVELS --output $R/$NAME -- \
  "${RECORD[@]}" --max-per-subset 16 > $R/logs/$NAME.log 2>&1
echo "SWEEP_EXIT $?"
kill $SERVER; wait $SERVER
echo "CAPACITY_DONE $NAME"
