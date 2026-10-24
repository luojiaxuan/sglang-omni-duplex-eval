#!/bin/bash
# usage: gated_v10.sh; the #2331 gated v1.0 diagnostic per shard on GPU 3, with graph decoding disabled
cd /data/runs/20261009-fdb
PY=/data/runs/20261009-fdb/score-venv/bin/python
export PYTHONPATH=/data/runs/20261009-fdb/src HF_HOME=/data/cache/huggingface
rm -rf gated-v10 && mkdir -p gated-v10
for k in 0 1 2 3; do
  CUDA_VISIBLE_DEVICES=3 $PY graphs_off.py -m benchmarks.eval.benchmark_duplex_v10 transcribe --run rec/v10-nemotron-s$k-p1 --output gated-v10/asr-s$k --model-path /data/models/parakeet/parakeet-tdt-0.6b-v2.nemo --device cuda > logs/gated-asr-s$k.log 2>&1 \
    && $PY -m benchmarks.eval.benchmark_duplex_v10 score --run rec/v10-nemotron-s$k-p1 --output gated-v10/score-s$k --transcripts gated-v10/asr-s$k --backchannel-reference fdb-src/v1_v1.5/evaluation/icc_gt_distribution.json > logs/gated-score-s$k.log 2>&1 \
    && echo "GATED s$k done"
done
echo GATED_ALL_DONE
