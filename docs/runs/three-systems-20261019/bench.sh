#!/bin/bash
# note (luojiaxuan): the same v1.5 and v1.0 samples recorded one session at a time from each
# system, exported and scored with the runbook's asr, judge and aggregate steps, and a
# concurrency sweep per system for the serving metrics. $1 run directory, $2 server commit.
set -uo pipefail
R=$1; SHA=$2; FDB=$R/fdb
export HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0 JUDGE=qwen PYTHONPATH=$R/src:$R/pyshim
cd $R/src
step() {
  local name=$1; shift
  local start=$SECONDS
  # note (luojiaxuan): every command as it ran, with its environment, for the run doc.
  printf '%s	%s	cd %q && env HF_HOME=%q FDB_WORK=%q CUDA_VISIBLE_DEVICES=%q JUDGE=%q PYTHONPATH=%q'     "$(date -u +%FT%TZ)" "$name" "$PWD" "$HF_HOME" "$FDB_WORK" "$CUDA_VISIBLE_DEVICES" "$JUDGE" "$PYTHONPATH" >> $R/logs/commands.log
  printf ' %q' "$@" >> $R/logs/commands.log
  printf '
' >> $R/logs/commands.log
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code seconds=$((SECONDS - start))"
  return $code
}
step pip pip install -e . && step setup python -m benchmarks.duplex.fdb setup || exit 1
python - $FDB > $R/logs/selection.log 2>&1 <<'PY'
import sys
from pathlib import Path
from benchmarks.duplex.fdb.selection import SampleSelection, ids_text, select_samples, select_v10_samples
fdb = Path(sys.argv[1])
v15 = select_samples(fdb / "dataset" / "v1.5", SampleSelection(per_subset=25, subset_counts={}, sample_ids=None))
v10 = select_v10_samples(fdb / "dataset" / "v1.0", SampleSelection(per_subset=10, subset_counts={}, sample_ids=None))
(fdb / "v15-ids.txt").write_text(ids_text(v15))
(fdb / "v10-ids.txt").write_text(ids_text(v10))
print(len(v15), len(v10))
PY
echo "SELECTED $(cat $R/logs/selection.log)"
TURNS='{"type": "server_vad", "silence_duration_ms": 800}'
system_args() {
  case $1 in
    minicpmo) echo "28097 minicpmo-native-pr2377 openbmb/MiniCPM-o-4_5 503e754207c94da6bb26850b4469f367c9ea3582 realtime-pcm16-v1 MiniCPM-o";;
    qwen3omni) echo "28965 turn-based Qwen/Qwen3-Omni-30B-A3B-Instruct $SHA realtime-turn-based-pcm16-v1 qwen3.omni";;
    cascade) echo "28865 turn-based streaming-cascade/qwen3-asr-qwen3-tts-customvoice $SHA realtime-turn-based-pcm16-v1 customvoice-bench";;
  esac
}
levels() {
  case $1 in
    qwen3omni) echo "2 4 8 16";;
    *) echo "2 4 8 16 24 32";;
  esac
}
run_system() {
  local S=$1
  read -r PORT PROFILE MODEL REV FORMAT IDENT <<< "$(system_args $S)"
  until curl -sf http://127.0.0.1:$PORT/v1/models | grep -qi "$IDENT"; do sleep 15; done
  echo "READY $S"
  local RECORD=(--profile $PROFILE --url ws://127.0.0.1:$PORT/v1/realtime --model $MODEL --model-revision $REV --server-revision $SHA)
  [ "$PROFILE" = turn-based ] && RECORD+=(--turn-detection "$TURNS")
  local REPEAT=$FDB/runs/$S/repeat-1
  mkdir -p $REPEAT/recording $REPEAT/v10/recording $REPEAT/logs
  cp $FDB/v15-ids.txt $REPEAT/sample-ids.txt; cp $FDB/v10-ids.txt $REPEAT/v10/sample-ids.txt
  step $S-v15 python -m benchmarks.eval.benchmark_duplex_v15 record "${RECORD[@]}" \
    --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 \
    $(sed 's/^/--sample-id /' $FDB/v15-ids.txt) --output $REPEAT/recording/shard-0
  step $S-v10 python -m benchmarks.eval.benchmark_duplex_v10 record "${RECORD[@]}" \
    --dataset-root $FDB/dataset/v1.0 --dataset-revision "$(cat $FDB/dataset/v1.0.revision)" --timeout 230 \
    $(sed 's/^/--sample-id /' $FDB/v10-ids.txt) --output $REPEAT/v10/recording/shard-0
  step $S-export python -m benchmarks.eval.benchmark_duplex_reference export --engine $S --trace-format $FORMAT \
    --dataset-root $FDB/dataset/v1.5 --run $REPEAT/recording/shard-0 --out $REPEAT/reference-audio \
    $(sed 's/^/--only /' $FDB/v15-ids.txt)
  step $S-export-v10 python -m benchmarks.eval.benchmark_duplex_v10 reference-export --trace-format $FORMAT \
    --dataset-root $FDB/dataset/v1.0 --run $REPEAT/v10/recording/shard-0 --out $REPEAT/v10/reference
  touch $R/logs/$S.exported
  for LEVEL in $(levels $S); do
    step $S-c$LEVEL python -m benchmarks.eval.benchmark_duplex_serving sweep --dataset v1.5 --concurrency $LEVEL \
      --output $R/serving/$S/c$LEVEL -- "${RECORD[@]}" --dataset-root $FDB/dataset/v1.5 \
      --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 --max-per-subset 16
  done
  echo "SWEPT $S"
}
score_system() {
  local S=$1
  until [ -e $R/logs/$S.exported ]; do sleep 30; done
  step $S-asr python -m benchmarks.duplex.fdb asr --run-name $S
  step $S-judge python -m benchmarks.duplex.fdb judge --run-name $S
  step $S-aggregate python -m benchmarks.duplex.fdb aggregate --run-name $S
}
mkdir -p $R/serving
for S in minicpmo qwen3omni cascade; do run_system $S & done
for S in minicpmo qwen3omni cascade; do score_system $S; done
wait
{ echo "client $(git -C $R/src rev-parse HEAD)"; echo "server $SHA"; } > $R/logs/revisions.txt
pip freeze > $R/logs/pip-freeze-client.txt
$FDB/scoring-venv/bin/python -m pip freeze > $R/logs/pip-freeze-scoring.txt 2>&1
echo "BENCH_DONE"
