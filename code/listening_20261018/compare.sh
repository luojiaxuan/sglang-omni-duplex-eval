#!/bin/bash
# note (luojiaxuan): MiniCPM-o through the runbook and the cascade through the recorder
# CLIs on the same v1.5 and v1.0 samples, then the listening metrics of both.
# $1 run directory, $2 cascade server commit.
set -uo pipefail
R=$1; CASC_SHA=$2; FDB=$R/fdb; C=$R/cascade
export HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0 JUDGE=gpt PYTHONPATH=$R/src:$R/pyshim
cd $R/src
step() {
  local name=$1; shift
  local start=$SECONDS
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code seconds=$((SECONDS - start))"
  return $code
}
step pip pip install -e . && step setup python -m benchmarks.duplex.fdb setup || exit 1
step mcpo-generate python -m benchmarks.duplex.fdb generate --run-name compare --v15-per-subset 25 --v10-per-subset 10 --num-shards 2 &
MCPO=$!
REPEAT=$FDB/runs/compare/repeat-1
until [ -s $REPEAT/sample-ids.txt ] && [ -s $REPEAT/v10/sample-ids.txt ]; do sleep 5; done
until curl -sf http://127.0.0.1:28765/v1/models | grep -q customvoice-bench; do sleep 15; done
echo "CASCADE_READY"
V15_IDS=$(sed 's/^/--sample-id /' $REPEAT/sample-ids.txt | tr '\n' ' ')
V10_IDS=$(sed 's/^/--sample-id /' $REPEAT/v10/sample-ids.txt | tr '\n' ' ')
ONLY=$(sed 's/^/--only /' $REPEAT/sample-ids.txt | tr '\n' ' ')
TURNS='{"type": "server_vad", "silence_duration_ms": 800}'
RECORD=(--profile turn-based --turn-detection "$TURNS" --url ws://127.0.0.1:28765/v1/realtime
  --model streaming-cascade/qwen3-asr-qwen3-tts-customvoice --model-revision $CASC_SHA --server-revision $CASC_SHA --concurrency 2)
mkdir -p $C/recording $C/v10/recording
step casc-v15 python -m benchmarks.eval.benchmark_duplex_v15 record "${RECORD[@]}" \
  --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 \
  $V15_IDS --output $C/recording/shard-0
step casc-v10 python -m benchmarks.eval.benchmark_duplex_v10 record "${RECORD[@]}" \
  --dataset-root $FDB/dataset/v1.0 --dataset-revision "$(cat $FDB/dataset/v1.0.revision)" --timeout 230 \
  $V10_IDS --output $C/v10/recording/shard-0
step casc-export python -m benchmarks.eval.benchmark_duplex_reference export --engine cascade \
  --trace-format realtime-turn-based-pcm16-v1 --dataset-root $FDB/dataset/v1.5 --run $C/recording/shard-0 \
  --out $C/reference-audio $ONLY
step casc-export-v10 python -m benchmarks.eval.benchmark_duplex_v10 reference-export \
  --trace-format realtime-turn-based-pcm16-v1 --dataset-root $FDB/dataset/v1.0 --run $C/v10/recording/shard-0 \
  --out $C/v10/reference
wait $MCPO
echo "MCPO_GENERATE_EXIT $?"
step mcpo-asr python -m benchmarks.duplex.fdb asr --run-name compare
step mcpo-aggregate python -m benchmarks.duplex.fdb aggregate --run-name compare
step casc-transcribe $FDB/scoring-venv/bin/python -m benchmarks.eval.benchmark_duplex_listening transcribe \
  --manifest $C/reference-audio/reference-manifest.json --manifest $C/v10/reference/manifest.json --out $C/listening \
  --nemo $FDB/models/parakeet-tdt-0.6b-v2/parakeet-tdt-0.6b-v2.nemo \
  --nemo-sha256 d99e39955c9d3d0350d8fb7c75e40c64a2b2eaeb003883d7c941fd2e8747b28c --device cuda
step casc-score python -m benchmarks.eval.benchmark_duplex_listening score --out $C/listening --device cuda
echo "COMPARE_EXIT $?"
