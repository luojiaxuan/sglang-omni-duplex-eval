#!/usr/bin/env bash
# note (luojiaxuan): Log SoulX-Duplug (turn_log.py) and the Silero + Smart Turn detector (eou_log.py) on the FDB pause
# and turn-taking subsets, for sweep.py. SoulX runs PER_GPU shards on each granted GPU: English on the
# first half of the GPUs, Chinese on the second half. eou_log.py runs EOU_SHARDS processes on GPU 0.
# Usage: bash turn_sweep.sh <run_dir> <out_dir> <seed> [per_gpu] [eou_shards]
set -euo pipefail
RUN=$1
OUT=$2
SEED=$3
PER_GPU=${4:-3}
EOU_SHARDS=${5:-16}
SRC=$RUN/src/benchmarks/cascade_replay
export HF_HOME=/data/cache/huggingface MODELSCOPE_CACHE=/data/cache/modelscope
export PYTHONPATH="$SRC/pyshim${PYTHONPATH:+:$PYTHONPATH}"
IFS=, read -r -a GPUS <<<"$CUDA_VISIBLE_DEVICES"
HALF=$((${#GPUS[@]} / 2))
EN=("$RUN/data/fdb/v1.0/candor_turn_taking" "$RUN/data/fdb/v1.0/candor_pause_handling" "$RUN/data/fdb/v1.0/synthetic_pause_handling")
ZH=("$RUN/data/fdb-zh/Full-Duplex-Bench-zh/turn_taking" "$RUN/data/fdb-zh/Full-Duplex-Bench-zh/pause_handling")
mkdir -p "$OUT/logs"

pids=()
for lang in en zh; do
  if [ $lang = en ]; then data=("${EN[@]}"); g0=0; else data=("${ZH[@]}"); g0=$HALF; fi
  n=$((HALF * PER_GPU))
  for k in $(seq 0 $((n - 1))); do
    gpu=${GPUS[$((g0 + k / PER_GPU))]}
    (cd "$RUN/turn-$lang" && CUDA_VISIBLE_DEVICES=$gpu OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
      "$RUN/turn-venv/bin/python" "$SRC/turn_log.py" --data "${data[@]}" --out "$OUT/soulx" --shard "$k/$n" --seed "$SEED" \
      >"$OUT/logs/soulx-$lang-$k.log" 2>&1) &
    pids+=($!)
  done
done
for k in $(seq 0 $((EOU_SHARDS - 1))); do
  CUDA_VISIBLE_DEVICES=${GPUS[0]} OMP_NUM_THREADS=1 SGLANG_OMNI_SMART_TURN_MODEL_PATH="$RUN/smart-turn" \
    /opt/sglang/bin/python3 "$SRC/eou_log.py" --data "${EN[@]}" "${ZH[@]}" --out "$OUT/eou" --shard "$k/$EOU_SHARDS" \
    >"$OUT/logs/eou-$k.log" 2>&1 &
  pids+=($!)
done
fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
echo "TURN_SWEEP_DONE fail=$fail"
exit $fail
