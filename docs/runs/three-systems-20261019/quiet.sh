#!/bin/bash
# note (luojiaxuan): MiniCPM-o levels 16, 20 and 24 again once the other systems were done.
set -uo pipefail
R=/data/runs/20261019-three; FDB=$R/fdb
export HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0 JUDGE=qwen PYTHONPATH=$R/src:$R/pyshim
cd $R/src
for LEVEL in 16 20 24; do
  CMD=(python -m benchmarks.eval.benchmark_duplex_serving sweep --dataset v1.5 --concurrency $LEVEL --output $R/serving/minicpmo-quiet/c$LEVEL -- --profile minicpmo-native-pr2377 --url ws://127.0.0.1:28097/v1/realtime --model openbmb/MiniCPM-o-4_5 --model-revision 503e754207c94da6bb26850b4469f367c9ea3582 --server-revision 3dd888e02ac44fd64414241fc9ea55ab80a22adc --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 --max-per-subset 16)
  printf "%s\tminicpmo-quiet-c%s\tcd %q &&" "$(date -u +%FT%TZ)" $LEVEL "$PWD" >> $R/logs/commands.log; printf " %q" "${CMD[@]}" >> $R/logs/commands.log; printf "\n" >> $R/logs/commands.log
  "${CMD[@]}" > $R/logs/minicpmo-quiet-c$LEVEL.log 2>&1
  echo "LEVEL_DONE c$LEVEL exit $?"
done
echo QUIET_DONE
