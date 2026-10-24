#!/bin/bash
# note (luojiaxuan): Qwen3-TTS CustomVoice and Base from private main in one container. $1 run directory.
set -uo pipefail
R=$1
export HF_HOME=/data/cache/huggingface PYTHONPATH=$R/priv
cd $R/priv
pip install -e . > $R/logs/pip.log 2>&1 || exit 1
(apt-get update -qq && apt-get install -y -qq sox) > $R/logs/sox.log 2>&1
pip install --no-deps sox einops > $R/logs/deps.log 2>&1 && pip install --no-deps qwen-tts==0.1.1 >> $R/logs/deps.log 2>&1 || exit 1
sgl-omni serve --model-path Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --config examples/configs/qwen3_tts_1_7b_customvoice.yaml --host 127.0.0.1 --port 28305 --mem-fraction-static 0.25 > $R/logs/cv.log 2>&1 &
sgl-omni serve --model-path Qwen/Qwen3-TTS-12Hz-1.7B-Base --config examples/configs/qwen3_tts_1_7b.yaml --host 127.0.0.1 --port 28306 --mem-fraction-static 0.25 > $R/logs/base.log 2>&1 &
wait
