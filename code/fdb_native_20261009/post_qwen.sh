#!/bin/bash
# usage: post_qwen.sh; after v1.5 recording, replaces the Nemotron servers with a Qwen3.8-27B judge on GPU 0 and runs the non-official judge passes
set -euo pipefail
cd /data/runs/20261009-fdb
REV=1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
until [ "$(grep -l DONE logs/supervise-v15-s*.log 2>/dev/null | wc -l)" = 4 ]; do sleep 30; done
until grep -q "Fetching 32 files: 100%" /data/logs/qwen-dl.log; do sleep 30; done
grep -rh "^$REV" /data/models/qwen38-27b/.cache/huggingface/download/*.metadata | head -1 | grep -q "$REV"
for p in $(pgrep -f "^bash -c /data/runs/20261009-fdb/serve.s[h]"); do
  pkill -TERM -P $p || true
  kill $p || true
done
sleep 20
cmd="python -m sglang.launch_server --model-path /data/models/qwen38-27b --served-model-name qwen3.8-27b --host 127.0.0.1 --port 30000 --mem-fraction-static 0.85 --context-length 32768"
PYTHONPATH=/data/pyshim CUDA_VISIBLE_DEVICES=0 HF_HOME=/data/cache/huggingface $cmd > logs/serve-qwen.log 2>&1 &
mkdir -p judge
python - <<PY
import json, sglang
json.dump({"command": "CUDA_VISIBLE_DEVICES=0 $cmd", "runtime": f"sglang {sglang.__version__}", "model_id": "Qwen/Qwen3.8-27B",
           "model_revision": "$REV", "precision": "bf16", "gpu": "1x H200",
           "image": "docker.io/hongccc/sglang-omni@sha256:ebe4239e29a764ee3a2806385c061c5fd438a26f01458e503d3822dcba5790df"},
          open("judge/qwen-launch.json", "w"), indent=1)
PY
sha=$(sha256sum judge/qwen-launch.json | cut -d" " -f1)
cat > judge/qwen-judge-config.json <<JSON
{"model_id": "Qwen/Qwen3.8-27B", "model_revision": "$REV", "tokenizer_id": "Qwen/Qwen3.8-27B", "tokenizer_revision": "$REV",
 "served_model": "qwen3.8-27b", "precision": "bf16", "enable_thinking": false, "seeds": [1, 2, 3],
 "decoding": {"temperature": 0.0, "top_p": 1.0, "top_k": -1, "min_p": 0.0, "repetition_penalty": 1.0, "max_tokens": 512},
 "server_launch_receipt": "qwen-launch.json", "server_launch_receipt_sha256": "$sha"}
JSON
until curl -sf http://127.0.0.1:30000/v1/models > /dev/null; do sleep 10; done
echo QWEN_READY
until grep -q V10_NOGRAPH_ASR_DONE logs/v10-nograph.log 2>/dev/null; do sleep 20; done
rm -rf ref-v10/qwen-interrupt && mkdir -p ref-v10/qwen-interrupt
for d in ref-v10/export-nograph/synthetic_user_interruption/*/; do
  id=$(basename $d)
  mkdir -p ref-v10/qwen-interrupt/$id
  cp $d/output.json $d/interrupt.json ref-v10/qwen-interrupt/$id/
done
python run_v10_interruption_local_judge.py --root-dir ref-v10/qwen-interrupt --upstream fdb-src/v1_v1.5/evaluation/eval_user_interruption.py \
  --base-url http://127.0.0.1:30000/v1 --served-model qwen3.8-27b --ledger judge/ledger-v10-qwen.jsonl --log judge/v10-interruption-qwen.log
echo V10_QWEN_DONE
until grep -q V15_PREPARED logs/post-v15.log; do sleep 30; done
export PYTHONPATH=/data/runs/20261009-fdb/src CUSTOM_JUDGE_API_KEY=local
PY=/data/runs/20261009-fdb/score-venv/bin/python
$PY -m benchmarks.eval.benchmark_duplex_reference custom-judge --reference-source fdb-src --tree model=ref-v15/audio --source-scores ref-v15/scores --out ref-v15/custom-qwen --judge-config judge/qwen-judge-config.json --base-url http://127.0.0.1:30000/v1
$PY -m benchmarks.eval.benchmark_duplex_reference custom-summarize --reference-source fdb-src --tree model=ref-v15/audio --source-scores ref-v15/scores --out ref-v15/custom-qwen --judge-config judge/qwen-judge-config.json
echo V15_QWEN_DONE
