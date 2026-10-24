#!/bin/bash
# note (luojiaxuan): one-time setup inside the task container; $1 is the run directory.
set -euo pipefail
R=$1
export HF_HOME=/data/cache/huggingface FDB_WORK=$R/fdb PYTHONPATH=$R/src:$R/pyshim CUDA_VISIBLE_DEVICES=0
cd $R/src
pip install -e . > $R/logs/pip.log 2>&1
echo PIP_DONE
python $R/setup_v15.py > $R/logs/setup.log 2>&1
grep -E '^MODEL_(PATH|REVISION)' $R/logs/setup.log
echo SETUP_DONE
