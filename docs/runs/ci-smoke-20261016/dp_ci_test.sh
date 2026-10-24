#!/bin/bash
# note (luojiaxuan): runs the CI smoke test file the way the Omni CI stage does, on the
# container's two GPUs with CUDA_VISIBLE_DEVICES unset, timing each part.
set -uo pipefail
R=$1
cd $R/src
start=$SECONDS
pip install -e . > $R/logs/pip.log 2>&1
echo "PIP exit=$? seconds=$((SECONDS - start))"
( while true; do nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits >> $R/logs/gpu.log; sleep 2; done ) &
SAMPLER=$!
start=$SECONDS
env -u CUDA_VISIBLE_DEVICES OMNI_CI_HOME=$R/ci-home HF_HOME=/data/cache/huggingface PYTHONPATH=$R/src:$R/pyshim \
  python -m pytest tests/test_model/test_minicpmo_fdb_ci.py -v -s -x > $R/logs/pytest.log 2>&1
echo "PYTEST exit=$? seconds=$((SECONDS - start))"
kill $SAMPLER
for gpu in 0 1; do echo "PEAK_GPU$gpu $(awk -F', ' -v g=$gpu '$1==g{print $2}' $R/logs/gpu.log | sort -n | tail -1) MiB"; done
