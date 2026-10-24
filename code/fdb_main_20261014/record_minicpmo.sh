#!/bin/bash
# note (luojiaxuan): the runbook's generate, asr and judge for one shard on GPU $1.
set -uo pipefail
K=$1; R=/data/runs/20261014-fdb
export PYTHONPATH=$R/src:$R/pyshim HF_HOME=/data/cache/huggingface FDB_WORK=$R/fdb CUDA_VISIBLE_DEVICES=$K
unset GPU SERVER_PORT JUDGE_PORT
cd $R/src
RUN=minicpmo-g$K
python -m benchmarks.duplex.fdb generate --run-name $RUN --v15-sample-ids-file $R/shards/v15-g$K.txt --v10-sample-ids-file $R/shards/v10-g$K.txt > $R/logs/mcpo-generate-g$K.log 2>&1; echo "generate g$K exit $?"
python -m benchmarks.duplex.fdb asr --run-name $RUN > $R/logs/mcpo-asr-g$K.log 2>&1; echo "asr g$K exit $?"
python -m benchmarks.duplex.fdb judge --run-name $RUN > $R/logs/mcpo-judge-g$K.log 2>&1; echo "judge g$K exit $?"
echo "MCPO_G${K}_DONE"
