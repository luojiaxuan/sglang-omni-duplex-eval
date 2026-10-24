#!/usr/bin/env bash
# Score a replay output directory for one FDB task (smooth_turn_taking or pause_handling).
#   en: official FDB v1 scripts (Parakeet ASR)   zh: SoulX dialogue-system eval scripts (Paraformer)
# Usage: bash score.sh <run_dir> <out_dir> <en|zh> <gpu_index> <task>
set -euo pipefail
RUN=$1
OUT=$2
LANG_=$3
IFS=, read -r -a GPUS <<<"$CUDA_VISIBLE_DEVICES"
export CUDA_VISIBLE_DEVICES=${GPUS[$4]}
export HF_HOME=/data/cache/huggingface MODELSCOPE_CACHE=/data/cache/modelscope
if [ "$LANG_" = en ]; then
  PY=$RUN/eval-venv/bin/python
  CODE=$RUN/fdb-code/v1_v1.5
  (cd "$CODE/get_transcript" && $PY asr.py --root_dir "$OUT" --task default)
else
  PY=$RUN/turn-venv/bin/python
  CODE=$RUN/turn-eval/dialogue_system/eval
  (cd "$CODE/get_transcript" && $PY asr_zh.py --root_dir "$OUT" --task full)
fi
(cd "$CODE/evaluation" && $PY evaluate.py --task "$5" --root_dir "$OUT") | tail -n 5
