#!/bin/bash
# note (luojiaxuan): smoke-records a Session-graph turn-based server on GPU $1 with the
# recorder's turn-based profile: three samples per subset of v1.5 and v1.0, then the
# v1.5 export, whose protocol gate and playout cut this checks.
set -uo pipefail
K=$1; R=/data/runs/20261014-fdb; PORT=8765; FDB=$R/fdb; OUT=$R/rec-ga
export HF_HOME=/data/cache/huggingface CUDA_VISIBLE_DEVICES=$K
cd $R/src-session
PYTHONPATH=$R/src-session:$R/pyshim python -m sglang_omni.cli serve --config examples/qwen3_omni/session.yaml \
  --model-path $R/models/qwen3-omni --enable-realtime --host 127.0.0.1 --port $PORT > $R/logs/session-server.log 2>&1 &
SERVER=$!
until curl -sf -o /dev/null http://127.0.0.1:$PORT/health; do
  kill -0 $SERVER 2>/dev/null || { echo SESSION_SERVER_DIED; exit 1; }
  sleep 10
done
curl -sf http://127.0.0.1:$PORT/v1/realtime/capabilities > $R/logs/session-capabilities.json
echo "server up"
cd $R/src-ga; export PYTHONPATH=$R/src-ga:$R/pyshim
COMMON=(--url ws://127.0.0.1:$PORT/v1/realtime --server-revision 3bcc7b9d52fb86131332bb268d9b47d94432ff67
  --model Qwen/Qwen3-Omni-30B-A3B-Instruct --model-revision 26291f793822fb6be9555850f06dfe95f2d7e695
  --profile turn-based --turn-detection '{"type":"server_vad"}' --max-per-subset 3)
python -m benchmarks.eval.benchmark_duplex_v15 record --dataset-root $FDB/dataset/v1.5 --output $OUT/v15 \
  --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 "${COMMON[@]}" > $R/logs/ga-v15-record.log 2>&1
echo "v15 record exit $?"
python -m benchmarks.eval.benchmark_duplex_v10 record --dataset-root $FDB/dataset/v1.0 --output $OUT/v10 \
  --dataset-revision "$(cat $FDB/dataset/v1.0.revision)" --timeout 230 "${COMMON[@]}" > $R/logs/ga-v10-record.log 2>&1
echo "v10 record exit $?"
kill $SERVER; wait $SERVER
python -m benchmarks.eval.benchmark_duplex_reference export --engine session-turn-based --trace-format realtime-turn-based-pcm16-v1 \
  --run $OUT/v15 --out $OUT/v15-ref --dataset-root $FDB/dataset/v1.5 > $R/logs/ga-v15-export.log 2>&1
echo "v15 export exit $?"
echo SESSION_DONE
