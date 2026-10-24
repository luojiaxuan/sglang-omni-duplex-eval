#!/bin/bash
# note (luojiaxuan): local watchdog for the recordings; exits with a reason on
# completion, a missing container, a Traceback, low memory or stalled progress.
# Progress is the sum of the recorders' finished-session counts; KIND (mcpo or
# qwen) picks the logs and the per-GPU completion markers.
RC=$1; CTR=$2; KIND=$3; H=/Users/luojiaxuan/.claude/skills/radix-gpu-nodes/scripts/radix_node.py
# note (luojiaxuan): the runbook logs finished-session counts; the bare record CLI
# logs nothing until it exits, so its progress is the session WAVs it has written.
PROGRESS=$([ "$KIND" = qwen ] && echo "find \$R/rec -name 'output*.wav' | wc -l" || echo "for f in \$R/logs/mcpo-generate-g*.log; do grep -o 'finished sessions: [0-9]*' \$f | grep -o '[0-9]*\$' | paste -sd+ | bc; done | paste -sd+ | bc")
STALE_S=600; last_count=-1; last_change=$(date +%s)
while true; do
  out=$(python3 $H ssh --receipt "$RC" -- "
    R=/data/luojiaxuan/home/runs/20261014-fdb
    echo container=\$(podman ps --filter name=$CTR --format '{{.Status}}' | head -1)
    echo wavs=\$($PROGRESS)
    echo done=\$(grep -h -c -E '^(MCPO|QWEN)_G[0-9]+_DONE' \$R/logs/driver-$KIND-*.log 2>/dev/null | paste -sd+ | bc)
    echo tracebacks=\$(grep -l Traceback \$R/logs/*.log 2>/dev/null | tr '\n' ' ')
    echo mem_avail_pct=\$(free | awk '/Mem:/ {printf \"%d\", \$7*100/\$2}')
    echo gpu_util=\$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | paste -sd,)
  " 2>&1)
  now=$(date +%s); echo "$(date -u +%H:%MZ) $(echo "$out" | tr '\n' ' ')"
  container=$(echo "$out" | sed -n 's/^container=//p'); count=$(echo "$out" | sed -n 's/^wavs=//p')
  done_n=$(echo "$out" | sed -n 's/^done=//p'); tb=$(echo "$out" | sed -n 's/^tracebacks=//p'); mem=$(echo "$out" | sed -n 's/^mem_avail_pct=//p')
  [ -z "$container" ] && { echo "ALERT container gone"; exit 2; }
  [ -n "$tb" ] && { echo "ALERT traceback in $tb"; exit 3; }
  [ -n "$mem" ] && [ "$mem" -lt 15 ] && { echo "ALERT memory $mem%"; exit 4; }
  [ "${done_n:-0}" -ge 8 ] && { echo "ALL_DONE"; exit 0; }
  if [ "$count" != "$last_count" ]; then last_count=$count; last_change=$now; fi
  [ $((now - last_change)) -gt $STALE_S ] && { echo "ALERT no new recording for $STALE_S s"; exit 5; }
  sleep 300
done
