#!/bin/bash
# note (luojiaxuan): the 4B cascade's FDB samples recorded from the Qwen3.8-27B cascade, half on
# each replica and one session at a time per replica, then scored with the runbook's asr, judge
# and aggregate once the servers have released the GPUs. $1 run directory, $2 server commit.
set -uo pipefail
R=$1; SHA=$2; FDB=$R/fdb; S=cascade27b
export HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0 JUDGE=qwen PYTHONPATH=$R/src
cd $R/src
step() {
  local name=$1; shift
  printf '%s\t%s\tcd %q && env HF_HOME=%q FDB_WORK=%q CUDA_VISIBLE_DEVICES=%q JUDGE=%q PYTHONPATH=%q' \
    "$(date -u +%FT%TZ)" "$name" "$PWD" "$HF_HOME" "$FDB_WORK" "$CUDA_VISIBLE_DEVICES" "$JUDGE" "$PYTHONPATH" >> $R/logs/commands.log
  printf ' %q' "$@" >> $R/logs/commands.log; printf '\n' >> $R/logs/commands.log
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code"
  return $code
}
step pip pip install -e . && step setup python -m benchmarks.duplex.fdb setup || exit 1
D=$FDB/runs/$S/repeat-1
mkdir -p $D/recording $D/v10/recording $D/logs
cp $R/v15-sample-ids.txt $D/sample-ids.txt; cp $R/v10-sample-ids.txt $D/v10/sample-ids.txt
TURNS='{"type": "server_vad", "silence_duration_ms": 800}'
for r in 0 1; do
  until curl -sf http://127.0.0.1:$((28870 + r))/v1/models | grep -qi "27b-customvoice-bench-r$r"; do sleep 15; done
done
echo "READY $(date -u +%FT%TZ)"
record_shard() {
  local r=$1
  local REC=(--profile turn-based --url ws://127.0.0.1:$((28870 + r))/v1/realtime --model streaming-cascade/qwen3-asr-qwen3.8-27b-customvoice --model-revision $SHA --server-revision $SHA --turn-detection "$TURNS")
  step $S-v15-shard$r python -m benchmarks.eval.benchmark_duplex_v15 record "${REC[@]}" \
    --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 \
    $(awk -v r=$r 'NF && (NR - 1) % 2 == r {print "--sample-id " $0}' $D/sample-ids.txt) --output $D/recording/shard-$r
  step $S-v10-shard$r python -m benchmarks.eval.benchmark_duplex_v10 record "${REC[@]}" \
    --dataset-root $FDB/dataset/v1.0 --dataset-revision "$(cat $FDB/dataset/v1.0.revision)" --timeout 230 \
    $(awk -v r=$r 'NF && (NR - 1) % 2 == r {print "--sample-id " $0}' $D/v10/sample-ids.txt) --output $D/v10/recording/shard-$r
}
record_shard 0 & record_shard 1 & wait
step $S-export python -m benchmarks.eval.benchmark_duplex_reference export --engine $S --trace-format realtime-turn-based-pcm16-v1 \
  --dataset-root $FDB/dataset/v1.5 --run $D/recording/shard-0 --run $D/recording/shard-1 --out $D/reference-audio \
  $(sed 's/^/--only /' $D/sample-ids.txt)
step $S-export-v10 python -m benchmarks.eval.benchmark_duplex_v10 reference-export --trace-format realtime-turn-based-pcm16-v1 \
  --dataset-root $FDB/dataset/v1.0 --run $D/v10/recording/shard-0 --run $D/v10/recording/shard-1 --out $D/v10/reference
touch $R/logs/recorded
until [ -e $R/logs/servers-stopped ]; do sleep 5; done
step $S-asr python -m benchmarks.duplex.fdb asr --run-name $S
step $S-judge python -m benchmarks.duplex.fdb judge --run-name $S
step $S-aggregate python -m benchmarks.duplex.fdb aggregate --run-name $S
{ echo "client $(git -C $R/src rev-parse HEAD 2>/dev/null || echo 7ddb436440)"; echo "server $SHA"; } > $R/logs/revisions.txt
echo "BENCH_DONE"
