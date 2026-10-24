#!/usr/bin/env bash
# note (luojiaxuan): Replay one SoulX decision rule (margin, wait) end to end on the turn-taking and pause
# subsets of one language and score both with the official scripts. Needs the LLM and TTS servers of
# serve.sh; starts N turn servers on TURN_GPU (ordinal) at PORT..PORT+N-1 and stops them afterwards.
# Usage: bash turn_point.sh <run_dir> <en|zh> <margin> <wait> <direct 1|0> <n_servers> <port_base> <out_root>
set -euo pipefail
RUN=$1
LANG_=$2
MARGIN=$3
WAIT=$4
DIRECT=$5
N=$6
PORT=$7
OUT=$8
SRC=$RUN/src/benchmarks/cascade_replay
TAG=$LANG_-m$MARGIN-w$WAIT$([ "$DIRECT" = 0 ] && echo -eos || true)
if [ "$LANG_" = en ]; then
  SETS=("fdb/v1.0/candor_turn_taking:smooth_turn_taking" "fdb/v1.0/candor_pause_handling:pause_handling")
else
  SETS=("fdb-zh/Full-Duplex-Bench-zh/turn_taking:smooth_turn_taking" "fdb-zh/Full-Duplex-Bench-zh/pause_handling:pause_handling")
fi

TURN_MARGIN=$MARGIN TURN_WAIT=$WAIT TURN_DIRECT=$DIRECT TURN_PORT_BASE=$PORT bash "$SRC/serve.sh" "$RUN" "$LANG_" "$N" turn
urls=()
for k in $(seq 0 $((N - 1))); do
  urls+=("ws://127.0.0.1:$((PORT + k))/turn")
  for _ in $(seq 120); do grep -q "Application startup complete" "$RUN/logs/turn-$TAG-$k.log" && break; sleep 5; done
  grep -q "Application startup complete" "$RUN/logs/turn-$TAG-$k.log"
done

for s in "${SETS[@]}"; do
  data=${s%%:*}
  task=${s##*:}
  out=$OUT/$TAG/$(basename "$data")
  /opt/sglang/bin/python3 "$SRC/replay.py" --data "$RUN/data/$data" --out "$out" --lang "$LANG_" --mode turn \
    --concurrency "$N" --turn-urls "${urls[@]}" >"$RUN/logs/point-$TAG-$(basename "$data").log" 2>&1
  bash "$SRC/score.sh" "$RUN" "$out" "$LANG_" "${TURN_GPU:-0}" "$task" >"$out.score.log" 2>&1
done
for k in $(seq 0 $((N - 1))); do kill "$(cat "$RUN/logs/turn-$TAG-$k.pid")"; done
echo "TURN_POINT_DONE $TAG"
