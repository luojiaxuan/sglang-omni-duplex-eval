#!/bin/bash
# usage: sweep_monitor.sh; polls the turn-detection sweep every 5 minutes
cd /Users/luojiaxuan/Downloads/S2S_omni
R=$(cat /private/tmp/claude-501/-Users-luojiaxuan-Downloads-S2S-omni/d929e068-e502-4614-a422-100edee8e07f/scratchpad/receipt_sweep)
H=/Users/luojiaxuan/.claude/skills/radix-gpu-nodes/scripts/radix_node.py
while true; do
  out=$(python3 $H ssh --receipt $R -- 'S=$HOME/runs/20261010-sweep; echo state=$(podman inspect -f "{{.State.Status}}" sglang-omni-jaxan-1 2>&1); for a in vad500 vad800 vad1200 semmed; do f=$S/rec/$a/run.json; if [ -f $f ]; then python3 -c "
import json,os,time; d=json.load(open(\"$f\")); v=d[\"summary\"][\"variants\"]; print(\"$a\", d[\"status\"], \"pass=%d fail=%d err=%d inv=%d pend=%d stale=%ds\" % (v[\"pass\"], v[\"fail\"], v[\"error\"], v[\"invalid\"], v[\"pending\"], time.time()-os.path.getmtime(\"$f\")))"; else echo "$a waiting: $(tail -c 120 $S/logs/arm-$a.log | tr "\n" " ")"; fi; done; echo tracebacks=$(grep -l Traceback $S/logs/serve-*.log $S/logs/arm-*.log 2>/dev/null | wc -l); free | awk "/Mem:/{printf \"mem_avail=%d%%\\n\", \$7*100/\$2}"; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader | tr "\n" ";"' 2>&1)
  echo "== $(TZ=America/Los_Angeles date '+%H:%M PT')"; echo "$out"
  if ! echo "$out" | grep -q 'state=running'; then echo "ALERT container"; exit 1; fi
  if echo "$out" | grep -qE 'stale=([6-9][0-9][0-9]|[0-9]{4,})s'; then echo "ALERT stale"; exit 1; fi
  if [ "$(echo "$out" | grep -cE '^(vad500|vad800|vad1200|semmed) (complete|finished|done)')" = 4 ]; then echo "ALL DONE"; exit 0; fi
  sleep 300
done
