#!/bin/bash
# usage: sweep_record.sh <arm> <port> '<turn_detection json>'; records candor_pause_handling and candor_turn_taking against one server
set -euo pipefail
S=/data/runs/20261010-sweep
cd $S/harness
export PYTHONPATH=$S/harness
python -m benchmarks.eval.benchmark_duplex_v10 record \
  --dataset-root $S/data/fdb/v1.0 --url ws://127.0.0.1:$2/v1/realtime --output $S/rec/$1 \
  --server-revision 8d03145ebc45210511d6ef824262ebfad80671ef --model Qwen/Qwen3-Omni-30B-A3B-Instruct \
  --model-revision 26291f793822fb6be9555850f06dfe95f2d7e695 --profile qwen3-omni-half-duplex \
  --runtime docker.io/hongccc/sglang-omni@sha256:ebe4239e29a764ee3a2806385c061c5fd438a26f01458e503d3822dcba5790df \
  --dataset-revision "HF gavinlaw/sglang-omni-fdb-v1-v15-source@1ece9dbb32585acfb61b9dd04f77d9ff784e6b76" \
  --turn-detection "$3" --timeout 230 \
  $(for sub in candor_pause_handling candor_turn_taking; do for d in $S/data/fdb/v1.0/$sub/*/; do printf -- '--sample-id %s/%s ' $sub $(basename $d); done; done)
echo RECORD_DONE
