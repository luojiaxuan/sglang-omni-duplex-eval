#!/bin/bash
# usage: sweep_serve.sh <gpu> <port>; one Qwen3-Omni half-duplex realtime server, colocated on one H200
export SGLANG_OMNI_QWEN_REALTIME_BACKEND=runtime
export SGLANG_OMNI_SMART_TURN_MODEL_PATH=/data/models/smart-turn-v3
export PYTHONPATH=/data/pyshim HF_HOME=/data/cache/huggingface CUDA_VISIBLE_DEVICES=$1
cd /data/runs/20261010-sweep/server
exec python -m sglang_omni.cli serve --config examples/configs/qwen3_omni_colocated_h200.yaml \
  --model-path /data/models/qwen3-omni-30b --colocate --enable-realtime --host 127.0.0.1 --port $2
