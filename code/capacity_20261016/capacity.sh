#!/bin/bash
# note (luojiaxuan): starts MiniCPM-o with the largest max_sessions that fits one GPU,
# then sweeps client concurrency up to it with the client-side serving metrics.
# $1 run directory, $2 server commit.
set -uo pipefail
R=$1; SERVER_SHA=$2; FDB=$R/fdb; PORT=8400; STARTUP_LIMIT_S=1200
export PYTHONPATH=$R/src:$R/pyshim HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0
cd $R/src
MODEL_PATH=$(grep '^MODEL_PATH' $R/logs/setup.log | cut -d' ' -f2)
MODEL_REVISION=$(grep '^MODEL_REVISION' $R/logs/setup.log | cut -d' ' -f2)
MAX=0
for M in 64 48 32 24 16; do
  python -m sglang_omni.cli serve --model-path $MODEL_PATH --variant session --enable-realtime \
    --host 127.0.0.1 --port $PORT --max_sessions $M > $R/logs/server-m$M.log 2>&1 &
  SERVER=$!
  START=$SECONDS
  until curl -sf -o /dev/null http://127.0.0.1:$PORT/health; do
    if ! kill -0 $SERVER 2>/dev/null || (( SECONDS - START > STARTUP_LIMIT_S )); then break; fi
    sleep 10
  done
  if curl -sf -o /dev/null http://127.0.0.1:$PORT/health; then
    MAX=$M; echo "SERVER_UP max_sessions=$M after $((SECONDS - START)) s"; break
  else
    echo "SERVER_FAILED max_sessions=$M"; kill $SERVER 2>/dev/null; wait $SERVER
  fi
done
(( MAX > 0 )) || { echo CAPACITY_NO_SERVER; exit 1; }
LEVELS=$(for N in 8 16 24 32 48 64; do (( N <= MAX )) && printf '%s,' $N; done); LEVELS=${LEVELS%,}
echo "SWEEP_LEVELS $LEVELS"
python -m benchmarks.eval.benchmark_duplex_serving sweep --dataset v1.5 --concurrency $LEVELS --output $R/sweep -- \
  --url ws://127.0.0.1:$PORT/v1/realtime --profile minicpmo-native-pr2377 \
  --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" \
  --server-revision $SERVER_SHA --model openbmb/MiniCPM-o-4_5 --model-revision $MODEL_REVISION \
  --timeout 90 --max-per-subset 16 > $R/logs/sweep.log 2>&1
echo "SWEEP_EXIT $?"
kill $SERVER; wait $SERVER
echo CAPACITY_DONE
