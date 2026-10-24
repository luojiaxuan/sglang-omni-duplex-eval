#!/bin/bash
# note (luojiaxuan): after bench.sh and quiet.sh, one serving table per system from the
# single-session recording and the sweep levels, and the files a rerun needs, gathered
# under summary/. $1 run directory.
set -uo pipefail
R=$1; FDB=$R/fdb; OUT=$R/summary
export PYTHONPATH=$R/src:$R/pyshim CUDA_VISIBLE_DEVICES=
cd $R/src
mkdir -p $OUT
report() {
  local NAME=$1; shift
  mkdir -p $OUT/$NAME
  python -m benchmarks.eval.benchmark_duplex_serving report "$@" --output $OUT/$NAME/serving.json > $OUT/$NAME/SERVING.md 2> $OUT/$NAME/serving-report.log
  echo "SERVING $NAME exit=$?"
}
for S in minicpmo qwen3omni cascade; do
  RUNS=(--run $FDB/runs/$S/repeat-1/recording/shard-0)
  for LEVEL_DIR in $(ls -d $R/serving/$S/c*/concurrency-* 2>/dev/null | sort -t- -k2 -n); do RUNS+=(--run $LEVEL_DIR); done
  report $S "${RUNS[@]}"
  cp $FDB/runs/$S/RESULTS.md $OUT/$S/RESULTS.md
  cp $FDB/runs/$S/repeat-1/listening/summary.json $OUT/$S/listening-summary.json
  cp $FDB/runs/$S/repeat-1/sample-ids.txt $OUT/$S/v15-sample-ids.txt
  cp $FDB/runs/$S/repeat-1/v10/sample-ids.txt $OUT/$S/v10-sample-ids.txt
  python -c "import json,sys; m=json.load(open(sys.argv[1])); print(json.dumps({k: m[k] for k in ('profile','server','config') if k in m}, indent=1))" \
    $FDB/runs/$S/repeat-1/recording/shard-0/manifest.json > $OUT/$S/recording-manifest.json
done
# note (luojiaxuan): the MiniCPM-o levels rerun by quiet.sh while no other system was serving.
QUIET=()
for LEVEL_DIR in $(ls -d $R/serving/minicpmo-quiet/c*/concurrency-* | sort -t- -k2 -n); do QUIET+=(--run $LEVEL_DIR); done
report minicpmo-quiet "${QUIET[@]}"
cp $R/logs/commands.log $R/logs/commands-servers.log $R/logs/revisions.txt $R/logs/pip-freeze-*.txt \
  $R/logs/host-load.log $R/logs/user-cpu-pressure.log $OUT/
cp $R/servers.sh $R/bench.sh $R/quiet.sh $R/collect.sh $OUT/
cp $R/priv/examples/streaming_cascade/profiles/qwen3-asr-qwen3-tts-customvoice-bench/launch.yaml $OUT/cascade-profile.yaml
cp $R/priv/examples/qwen3_omni/session_h200.yaml $R/priv/examples/full_duplex/minicpmo.yaml $OUT/
{
  for REF in /data/cache/huggingface/hub/models--*/refs/main; do echo "$(echo $REF | sed 's|.*/models--||; s|/refs/main||; s|--|/|') $(cat $REF)"; done
  echo "MiniCPM-o local copy 503e754207c94da6bb26850b4469f367c9ea3582"
  echo "judge $(cat $FDB/models/Qwen3.8-27B.revision)"
  echo "dataset v1.5 $(cat $FDB/dataset/v1.5.revision)"
  echo "dataset v1.0 $(cat $FDB/dataset/v1.0.revision)"
} > $OUT/model-and-data-revisions.txt
echo "COLLECT_DONE"
