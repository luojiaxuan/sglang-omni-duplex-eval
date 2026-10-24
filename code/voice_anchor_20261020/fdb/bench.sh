#!/bin/bash
# note (luojiaxuan): the 10-19 cascade FDB samples recorded one session at a time from the anchored
# cascade, then scored with the runbook's asr, judge and aggregate once the servers have released
# the GPU. $1 run directory, $2 server commit.
set -uo pipefail
R=$1; SHA=$2; FDB=$R/fdb; S=cascadeanchor
export HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0 JUDGE=qwen PYTHONPATH=$R/src:$R/pyshim
cd $R/src
step() {
  local name=$1; shift
  printf '%s\t%s\tcd %q && env HF_HOME=%q FDB_WORK=%q CUDA_VISIBLE_DEVICES=%q JUDGE=%q PYTHONPATH=%q' \
    "$(date -u +%FT%TZ)" "$name" "$PWD" "$HF_HOME" "$FDB_WORK" "$CUDA_VISIBLE_DEVICES" "$JUDGE" "$PYTHONPATH" >> $R/logs/commands.log
  printf ' %q' "$@" >> $R/logs/commands.log; printf '\n' >> $R/logs/commands.log
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code $(date -u +%FT%TZ)"
  return $code
}
step pip pip install -e . && step setup python -m benchmarks.duplex.fdb setup || exit 1
D=$FDB/runs/$S/repeat-1
mkdir -p $D/recording $D/v10/recording $D/logs
cp $R/v15-sample-ids.txt $D/sample-ids.txt; cp $R/v10-sample-ids.txt $D/v10/sample-ids.txt
TURNS='{"type": "server_vad", "silence_duration_ms": 800}'
until curl -sf http://127.0.0.1:28865/v1/models | grep -qi "vivian-anchor-bench"; do sleep 15; done
echo "READY $(date -u +%FT%TZ)"
REC=(--profile turn-based --url ws://127.0.0.1:28865/v1/realtime --model streaming-cascade/qwen3-asr-qwen3-tts-vivian-anchor --model-revision $SHA --server-revision $SHA --turn-detection "$TURNS")
step $S-v15 python -m benchmarks.eval.benchmark_duplex_v15 record "${REC[@]}" \
  --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 \
  $(sed 's/^/--sample-id /' $D/sample-ids.txt) --output $D/recording/shard-0
step $S-v10 python -m benchmarks.eval.benchmark_duplex_v10 record "${REC[@]}" \
  --dataset-root $FDB/dataset/v1.0 --dataset-revision "$(cat $FDB/dataset/v1.0.revision)" --timeout 230 \
  $(sed 's/^/--sample-id /' $D/v10/sample-ids.txt) --output $D/v10/recording/shard-0
step $S-export python -m benchmarks.eval.benchmark_duplex_reference export --engine $S --trace-format realtime-turn-based-pcm16-v1 \
  --dataset-root $FDB/dataset/v1.5 --run $D/recording/shard-0 --out $D/reference-audio \
  $(sed 's/^/--only /' $D/sample-ids.txt)
step $S-export-v10 python -m benchmarks.eval.benchmark_duplex_v10 reference-export --trace-format realtime-turn-based-pcm16-v1 \
  --dataset-root $FDB/dataset/v1.0 --run $D/v10/recording/shard-0 --out $D/v10/reference
touch $R/logs/recorded
until [ -e $R/logs/servers-stopped ]; do sleep 5; done
step $S-asr python -m benchmarks.duplex.fdb asr --run-name $S
step $S-judge python -m benchmarks.duplex.fdb judge --run-name $S
step $S-aggregate python -m benchmarks.duplex.fdb aggregate --run-name $S
{ echo "client 7ddb436440"; echo "server $SHA plus the anchored bench profile"; } > $R/logs/revisions.txt
echo "BENCH_DONE"
