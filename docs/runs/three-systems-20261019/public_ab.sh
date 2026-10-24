#!/bin/bash
# note (luojiaxuan): MiniCPM-o served by public main (the client's own checkout) with the
# runbook's H200 settings on the bench container's GPU, then levels 8 (warm-up), 16 and 24
# with the same client command as quiet.sh, to separate the server code and config from
# the hardware in the private main capacity.
set -uo pipefail
R=/data/runs/20261019-three; FDB=$R/fdb; PORT=28098; STARTUP_LIMIT_S=1200
export HF_HOME=/data/cache/huggingface FDB_WORK=$FDB CUDA_VISIBLE_DEVICES=0 PYTHONPATH=$R/src:$R/pyshim
cd $R/src
SERVER_SHA=$(git rev-parse HEAD)
SERVE=(python -m sglang_omni.cli serve --model-path $FDB/models/MiniCPM-o-4_5 --variant session --max_sessions 40 --enable-realtime --host 127.0.0.1 --port $PORT)
printf "%s\tsrv-minicpmo-public\tcd %q && env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONPATH=%q CUDA_VISIBLE_DEVICES=0" "$(date -u +%FT%TZ)" "$PWD" "$PYTHONPATH" >> $R/logs/commands-servers.log; printf " %q" "${SERVE[@]}" >> $R/logs/commands-servers.log; printf "\n" >> $R/logs/commands-servers.log
OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 "${SERVE[@]}" > $R/logs/srv-minicpmo-public.log 2>&1 &
SERVER=$!
START=$SECONDS
until curl -sf http://127.0.0.1:$PORT/v1/models | grep -q MiniCPM; do
  if ! kill -0 $SERVER 2>/dev/null || (( SECONDS - START > STARTUP_LIMIT_S )); then echo "SERVER_FAILED"; exit 1; fi
  sleep 10
done
echo "SERVER_UP after $((SECONDS - START)) s"
for LEVEL in 8 16 24; do
  CMD=(python -m benchmarks.eval.benchmark_duplex_serving sweep --dataset v1.5 --concurrency $LEVEL --output $R/serving/minicpmo-public/c$LEVEL -- --profile minicpmo-native-pr2377 --url ws://127.0.0.1:$PORT/v1/realtime --model openbmb/MiniCPM-o-4_5 --model-revision 503e754207c94da6bb26850b4469f367c9ea3582 --server-revision $SERVER_SHA --dataset-root $FDB/dataset/v1.5 --dataset-revision "$(cat $FDB/dataset/v1.5.revision)" --timeout 90 --max-per-subset 16)
  printf "%s\tminicpmo-public-c%s\tcd %q &&" "$(date -u +%FT%TZ)" $LEVEL "$PWD" >> $R/logs/commands.log; printf " %q" "${CMD[@]}" >> $R/logs/commands.log; printf "\n" >> $R/logs/commands.log
  "${CMD[@]}" > $R/logs/minicpmo-public-c$LEVEL.log 2>&1
  echo "LEVEL_DONE c$LEVEL exit $?"
done
kill $SERVER; wait $SERVER
echo PUBLIC_AB_DONE
