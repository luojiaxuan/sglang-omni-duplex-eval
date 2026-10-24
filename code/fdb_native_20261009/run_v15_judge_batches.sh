#!/bin/bash
# usage: run_v15_judge_batches.sh <cap_usd> <already_spent_usd>
# Runs the official v1.5 behavior judge in batches sized so that incurred spend
# plus the worst case of every request in the next batch stays under the cap.
# The key reaches only the judge process, through SSH stdin.
set -euo pipefail
cd /Users/luojiaxuan/Downloads/S2S_omni
R=results/radix/20261009T183431Z-hyper01
H=/Users/luojiaxuan/.claude/skills/radix-gpu-nodes/scripts/radix_node.py
cap=$1; prior=$2
until python3 $H ssh --receipt $R -- 'grep -q V15_PREPARED $HOME/runs/20261009-fdb/logs/post-v15.log' 2>/dev/null; do sleep 30; done
while true; do
  stats=$(python3 $H ssh --receipt $R -- 'cd $HOME/runs/20261009-fdb/ref-v15/scores && python3 - <<PY
import glob, json
reqs = glob.glob("**/judge/request.json", recursive=True)
spent, pending, longest = 0.0, 0, 0
for r in reqs:
    longest = max(longest, len(open(r).read()))
    res = r.replace("request.json", "result.json")
    try:
        doc = json.load(open(res))
    except FileNotFoundError:
        pending += 1
        continue
    for a in doc.get("attempts", []):
        u = ((a.get("response") or {}).get("usage")) or {}
        spent += u.get("prompt_tokens", 0) * 2.5e-6 + u.get("completion_tokens", 0) * 10e-6
print(len(reqs), pending, round(spent, 4), longest)
PY')
  read -r total pending spent longest <<< "$stats"
  # note (luojiaxuan): worst case per request is its prompt (about 3 characters per token for compact JSON) plus gpt-4o's 16384-token output limit.
  n=$(python3 -c "b=$longest/3*2.5e-6+16384*10e-6; print(int(($cap-$prior-$spent)/b))")
  echo "$(TZ=America/Los_Angeles date '+%H:%M PT') requests=$total pending=$pending v15_spent=$spent next_batch=$n"
  if [ "$pending" = 0 ]; then echo JUDGE_DONE; exit 0; fi
  if [ "$n" -lt 1 ]; then echo BUDGET_STOP; exit 0; fi
  python3 $H ssh --receipt $R -- "podman exec -i sglang-omni-jaxan-1 bash -c 'read -r OPENAI_API_KEY; export OPENAI_API_KEY; cd /data/runs/20261009-fdb && PYTHONPATH=/data/runs/20261009-fdb/src score-venv/bin/python -m benchmarks.eval.benchmark_duplex_reference judge --reference-source fdb-src --tree model=ref-v15/audio --out ref-v15/scores --judge gpt-4o-2024-08-06 --limit $n >> logs/judge-v15.log 2>&1'" < <(tr -d '[:space:]' < ~/openai_key.txt; echo)
done
