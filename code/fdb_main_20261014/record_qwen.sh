#!/bin/bash
# note (luojiaxuan): one Qwen3-Omni turn-based server on GPU $1 with the default
# server VAD, and a serial recorder for that GPU's v1.5 and v1.0 shards.
set -uo pipefail
K=$1; R=/data/runs/20261014-fdb; PORT=$((8197 + K)); FDB=$R/fdb
export PYTHONPATH=$R/src:$R/pyshim HF_HOME=/data/cache/huggingface CUDA_VISIBLE_DEVICES=$K
cd $R/src
python -m sglang_omni.cli serve --config examples/configs/qwen3_omni_colocated_h200.yaml \
  --model-path $R/models/qwen3-omni --colocate --enable-realtime --host 127.0.0.1 --port $PORT \
  > $R/logs/qwen-server-g$K.log 2>&1 &
SERVER=$!
until curl -sf -o /dev/null http://127.0.0.1:$PORT/health; do
  kill -0 $SERVER 2>/dev/null || { echo "QWEN_G${K}_SERVER_DIED"; exit 1; }
  sleep 10
done
echo "server g$K up"
COMMON=(--url ws://127.0.0.1:$PORT/v1/realtime --server-revision eb7e97ed9438ef4e4352656aec6170aeeb90966f
  --model Qwen/Qwen3-Omni-30B-A3B-Instruct --model-revision 26291f793822fb6be9555850f06dfe95f2d7e695
  --runtime docker.io/hongccc/sglang-omni@sha256:ebe4239e29a764ee3a2806385c061c5fd438a26f01458e503d3822dcba5790df
  --profile qwen3-omni-half-duplex --turn-detection '{"type":"server_vad"}')
mapfile -t V15 < <(sed 's#^#--sample-id\n#' $R/shards/v15-g$K.txt)
mapfile -t V10 < <(sed 's#^#--sample-id\n#' $R/shards/v10-g$K.txt)
python -m benchmarks.eval.benchmark_duplex_v15 record --dataset-root $FDB/dataset/v1.5 --output $R/rec/v15-qwen-g$K \
  --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 "${COMMON[@]}" "${V15[@]}" > $R/logs/rec-v15-qwen-g$K.log 2>&1
echo "v15 g$K exit $?"
python -m benchmarks.eval.benchmark_duplex_v10 record --dataset-root $FDB/dataset/v1.0 --output $R/rec/v10-qwen-g$K \
  --dataset-revision "$(cat $FDB/dataset/v1.0.revision)" --timeout 230 "${COMMON[@]}" "${V10[@]}" > $R/logs/rec-v10-qwen-g$K.log 2>&1
echo "v10 g$K exit $?"
kill $SERVER; wait $SERVER
echo "QWEN_G${K}_DONE"
