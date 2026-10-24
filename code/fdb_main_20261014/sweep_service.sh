#!/bin/bash
# note (luojiaxuan): one MiniCPM-o server with max_sessions 8 on GPU $2 and the request
# event recorder on, recording the same 16 v1.5 pairs at client concurrency $1.
set -uo pipefail
C=$1; K=$2; R=/data/runs/20261014-fdb; PORT=$((8300 + K)); FDB=$R/fdb; OUT=$R/svc/c$C
export PYTHONPATH=$R/src:$R/pyshim HF_HOME=/data/cache/huggingface CUDA_VISIBLE_DEVICES=$K
cd $R/src
python -m sglang_omni.cli serve --model-path $FDB/models/MiniCPM-o-4_5 --variant session --enable-realtime \
  --host 127.0.0.1 --port $PORT --max_sessions 8 > $R/logs/svc-server-c$C.log 2>&1 &
SERVER=$!
until curl -sf -o /dev/null http://127.0.0.1:$PORT/health; do
  kill -0 $SERVER 2>/dev/null || { echo "SVC_C${C}_SERVER_DIED"; exit 1; }
  sleep 10
done
mkdir -p $OUT
curl -sf -X POST http://127.0.0.1:$PORT/start_request_profile -H 'Content-Type: application/json' \
  -d "{\"run_id\": \"c$C\", \"event_dir\": \"$OUT/events\"}"; echo
python -m benchmarks.eval.benchmark_duplex_v15 record --dataset-root $FDB/dataset/v1.5 \
  --url ws://127.0.0.1:$PORT/v1/realtime --output $OUT/run --server-revision eb7e97ed9438ef4e4352656aec6170aeeb90966f \
  --model openbmb/MiniCPM-o-4_5 --model-revision 503e754207c94da6bb26850b4469f367c9ea3582 \
  --profile minicpmo-native-pr2377 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" \
  --timeout 90 --concurrency $C --max-per-subset 4 > $R/logs/svc-record-c$C.log 2>&1
echo "record c$C exit $?"
curl -sf -X POST http://127.0.0.1:$PORT/stop_request_profile -H 'Content-Type: application/json' -d "{\"run_id\": \"c$C\"}"; echo
kill $SERVER; wait $SERVER
echo "SVC_C${C}_DONE"
