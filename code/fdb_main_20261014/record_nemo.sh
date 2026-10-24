#!/bin/bash
# note (luojiaxuan): one native-duplex server and one serial recorder on GPU $1, v1.0 then v1.5.
set -uo pipefail
K=$1; R=/data/runs/20261014-fdb; PORT=$((8097 + K)); SHA=eb7e97ed9438ef4e4352656aec6170aeeb90966f
FDB=$R/fdb; export PYTHONPATH=$R/src:$R/pyshim HF_HOME=/data/cache/huggingface CUDA_VISIBLE_DEVICES=$K
cd $R/src
python examples/run_nemotron_voicechat_duplex.py --model-path $R/models/voicechat --serve --port $PORT > $R/logs/nemo-server-g$K.log 2>&1 &
SERVER=$!
for i in $(seq 1 180); do curl -sf -o /dev/null http://127.0.0.1:$PORT/ && break; sleep 5; done
echo "server g$K up after $((i * 5)) s"
COMMON="--server-revision $SHA --model nvidia/NVIDIA-NemotronLabs-VoiceChat-11B --profile nemotron-voicechat-pr2188"
python -m benchmarks.eval.benchmark_duplex_v10 record --dataset-root $FDB/dataset/v1.0 --url ws://127.0.0.1:$PORT/v1/realtime \
  --output $R/rec/v10-nemo-g$K --dataset-revision "$(cat $FDB/dataset/v1.0.revision)" --timeout 230 $COMMON \
  $(sed 's#^#--sample-id #' $R/shards/v10-g$K.txt) > $R/logs/rec-v10-nemo-g$K.log 2>&1
echo "v10 g$K exit $?"
python -m benchmarks.eval.benchmark_duplex_v15 record --dataset-root $FDB/dataset/v1.5 --url ws://127.0.0.1:$PORT/v1/realtime \
  --output $R/rec/v15-nemo-g$K --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 $COMMON \
  $(sed 's#^#--sample-id #' $R/shards/v15-g$K.txt) > $R/logs/rec-v15-nemo-g$K.log 2>&1
echo "v15 g$K exit $?"
kill $SERVER; wait $SERVER
echo "NEMO_G${K}_DONE"
