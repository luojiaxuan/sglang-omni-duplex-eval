#!/bin/bash
# usage: wait_h200.sh; polls the two H200 nodes every 5 minutes and assigns a lease when at least 2 GPUs are free
cd /Users/luojiaxuan/Downloads/S2S_omni
H=/Users/luojiaxuan/.claude/skills/radix-gpu-nodes/scripts/radix_node.py
for i in $(seq 1 72); do
  pick=$(~/.local/bin/radix machines list --json 2>/dev/null | python3 -c "
import json, sys
raw = sys.stdin.read(); d = json.loads(raw[raw.index('{'):])
alias = {'node-radixark-16-0001': 'hyper01', 'node-radixark-16-0000': 'hyper00'}
best = None
for m in d['machines']:
    mid = m.get('id') or m.get('machine_id')
    if mid in alias and m.get('status') != 'offline':
        free = m['total_gpus'] - m['gpus_allocated']
        if best is None or free > best[1]: best = (alias[mid], free)
print(best[0], best[1])")
  set -- $pick
  echo "$(TZ=America/Los_Angeles date '+%H:%M PT') best=$1 free=$2"
  if [ "${2:-0}" -ge 2 ]; then
    n=2; [ "$2" -ge 4 ] && n=4
    R=results/radix/$(date -u +%Y%m%dT%H%M%SZ)-$1
    python3 $H assign --node $1 --gpus $n --duration 3h --receipt $R 2>&1 | tail -4
    echo "ASSIGNED $R"
    exit 0
  fi
  sleep 300
done
echo "GAVE UP after 6 hours"
