#!/bin/bash
# note (luojiaxuan): the same H100 server and warm-up as capacity_h100.sh, for the levels
# above 8 once 8 passes, repeats outermost.
# $1 run directory, $2 server commit.
set -uo pipefail
R=$1; SERVER_SHA=$2; FDB=$R/fdb; PORT=8099; STARTUP_LIMIT_S=1200
export PYTHONPATH=$R/src:$R/pyshim HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0
cd $R/src
MODEL_PATH=$(grep '^MODEL_PATH' $R/logs/setup.log | cut -d' ' -f2)
MODEL_REVISION=$(grep '^MODEL_REVISION' $R/logs/setup.log | cut -d' ' -f2)
RECORD=(--url ws://127.0.0.1:$PORT/v1/realtime --profile minicpmo-native-pr2377
  --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)"
  --server-revision $SERVER_SHA --model openbmb/MiniCPM-o-4_5 --model-revision $MODEL_REVISION --timeout 90)
OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 python -m sglang_omni.cli serve \
  --model-path $MODEL_PATH --variant session --max_sessions 64 \
  --thinker.engine.kv_cache_bytes 17179869184 \
  --perception.gpu_memory_fraction null \
  --perception.total_reserve_bytes 17179869184 \
  --talker.engine.max_total_tokens 65536 \
  --talker.gpu_memory_fraction 0.08 \
  --enable-realtime --host 127.0.0.1 --port $PORT > $R/logs/server-high.log 2>&1 &
SERVER=$!
START=$SECONDS
until curl -sf -o /dev/null http://127.0.0.1:$PORT/health; do
  if ! kill -0 $SERVER 2>/dev/null || (( SECONDS - START > STARTUP_LIMIT_S )); then echo "SERVER_FAILED"; exit 1; fi
  sleep 10
done
echo "SERVER_UP after $((SECONDS - START)) s"
python -m benchmarks.eval.benchmark_duplex_v15 record "${RECORD[@]}" --concurrency 8 --max-per-subset 2 \
  --output $R/warmup-high > $R/logs/warmup-high.log 2>&1
echo "WARMUP_EXIT $?"
for REPEAT in 1 2; do
  for LEVEL in 12 10 14; do
    python -m benchmarks.eval.benchmark_duplex_serving sweep --dataset v1.5 --concurrency $LEVEL \
      --output $R/h100/c$LEVEL-r$REPEAT -- "${RECORD[@]}" --max-per-subset 16 > $R/logs/c$LEVEL-r$REPEAT.log 2>&1
    echo "LEVEL_DONE c$LEVEL-r$REPEAT exit $?"
  done
done
kill $SERVER; wait $SERVER
echo "CAPACITY_DONE"
