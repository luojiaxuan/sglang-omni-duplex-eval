#!/usr/bin/env bash
# Prepare a run directory inside a container of the SGLang base image pinned by docker/Dockerfile.
#   env   sglang-omni and its dependencies from <run_dir>/src (as docker/Dockerfile does, minus UCX
#         and the audar/cosyvoice extras)
#   turn  note (luojiaxuan): SoulX-Duplug turn detector in its own venv, with weights, one checkout per language
#         (English uses SenseVoice as the external ASR); Smart Turn v3.2 weights
#   data  FDB v1 (English) and SoulX Full-Duplex-Bench-zh (Chinese)
#   eval  official FDB scoring code (Parakeet ASR, NeMo venv) and SoulX's Chinese scoring scripts
# Usage: bash setup.sh <run_dir> [env|turn|data|eval|all]
set -euo pipefail
RUN=$1
STEP=${2:-all}
SOULX_SHA=a0b9063843df69619b087b95b74597b2176910b8
FDB_ZH_REV=f6e50e8f07f3d33d8b2e77b14df986d14c817ef2
FDB_V1_DRIVE=1DtoxMVO9_Y_nDs2peZtx3pw-U2qYgpd3
FDB_CODE_SHA=3e799c45
SOULX_EVAL_BRANCH=dialogue-system
export HF_HOME=/data/cache/huggingface MODELSCOPE_CACHE=/data/cache/modelscope UV_CACHE_DIR=/data/cache/uv
export UV_PYTHON_INSTALL_DIR=/data/cache/uv-python
PY=/opt/sglang/bin/python3

setup_env() {
  $PY -c 'import tomllib,sys; print("\n".join(tomllib.load(open(sys.argv[1], "rb"))["tool"]["uv"]["override-dependencies"]))' \
    "$RUN/src/pyproject.toml" >"$RUN/overrides.txt"
  uv pip install -q --python $PY --no-build-isolation --overrides "$RUN/overrides.txt" \
    -r "$RUN/src/pyproject.toml" descript-audiotools==0.7.2 descript-audio-codec==1.0.0
  uv pip install -q --python $PY --no-deps qwen-tts==0.1.1
  uv pip install -q --python $PY --no-deps --reinstall flashinfer-python==0.6.18
  uv pip uninstall -q --python $PY flashinfer-cubin flashinfer-jit-cache
  $PY -m pip install -q --no-deps -e "$RUN/src"
  $PY -m pip install -q aiohttp soxr soundfile gdown
}

setup_turn() {
  [ -d "$RUN/turn" ] || git clone -q https://github.com/Soul-AILab/SoulX-Duplug "$RUN/turn"
  git -C "$RUN/turn" checkout -q "$SOULX_SHA"
  uv venv -q --allow-existing "$RUN/turn-venv" --python 3.10
  uv pip install -q --python "$RUN/turn-venv/bin/python" \
    torch==2.6.0 torchaudio==2.6.0 transformers==4.52.1 peft==0.16.0 accelerate==1.9.0 \
    funasr==1.2.6 modelscope==1.28.2 omegaconf==2.3.0 pytorch-lightning==2.5.2 safetensors==0.4.5 \
    numpy==1.26.4 soxr==0.5.0.post1 soundfile==0.12.1 librosa==0.10.2 fastapi==0.115.3 \
    uvicorn==0.32.0 websockets==12.0 zhon==2.1.1 cn2an==0.5.23 jieba==0.42.1 pypinyin==0.55.0 \
    huggingface-hub==0.34.4 tiktoken==0.9.0 sentencepiece==0.2.0 hydra-core==1.3.2 \
    kaldiio==2.18.1 jaconv==0.4.0 editdistance==0.8.1 setproctitle==1.3.7
  uv pip install -q --python "$RUN/turn-venv/bin/python" pynini==2.1.6 importlib_resources \
    addict==2.4.0 simplejson==3.20.1 sortedcontainers==2.4.0 setuptools==78.1.1 datasets==3.1.0 \
    oss2==2.19.1 pillow==10.4.0 scipy==1.15.3 pandas==2.3.1 yapf==0.43.0 einops==0.8.1 \
    scikit-learn==1.7.1 requests==2.32.3 tqdm==4.67.1 pyyaml==6.0.2
  uv pip install -q --python "$RUN/turn-venv/bin/python" --no-deps WeTextProcessing==1.0.3
  "$RUN/turn-venv/bin/huggingface-cli" download Soul-AILab/SoulX-Duplug-0.6B \
    --local-dir "$RUN/turn/pretrained_models" >/dev/null
  for lang in en zh; do
    [ -d "$RUN/turn-$lang" ] && continue
    mkdir -p "$RUN/turn-$lang"
    for f in "$RUN/turn"/*; do
      if [ "$(basename "$f")" = pretrained_models ]; then ln -s "$f" "$RUN/turn-$lang/"; else cp -r "$f" "$RUN/turn-$lang/"; fi
    done
  done
  sed -i 's/^\(\s*\)model_name: paraformer/\1model_name: sensevoice\n\1language: en/' "$RUN/turn-en/config/config.yaml"
  "$RUN/turn-venv/bin/huggingface-cli" download pipecat-ai/smart-turn-v3 smart-turn-v3.2-gpu.onnx \
    --local-dir "$RUN/smart-turn" >/dev/null
}

setup_data() {
  mkdir -p "$RUN/data"
  "$RUN/turn-venv/bin/huggingface-cli" download Soul-AILab/SoulX-Duplug-Eval --repo-type dataset \
    --revision "$FDB_ZH_REV" --include Full-Duplex-Bench-zh.zip --local-dir "$RUN/data" >/dev/null
  unzip -q -o "$RUN/data/Full-Duplex-Bench-zh.zip" -d "$RUN/data/fdb-zh"
  $PY -m gdown -q --folder "$FDB_V1_DRIVE" -O "$RUN/data/fdb"
  for z in candor_turn_taking candor_pause_handling synthetic_pause_handling; do
    unzip -q -o "$RUN/data/fdb/v1.0/$z.zip" -d "$RUN/data/fdb/v1.0"
  done
}

setup_eval() {
  [ -d "$RUN/fdb-code" ] || git clone -q https://github.com/DanielLin94144/Full-Duplex-Bench "$RUN/fdb-code"
  git -C "$RUN/fdb-code" checkout -q "$FDB_CODE_SHA"
  [ -d "$RUN/turn-eval" ] || git clone -q -b "$SOULX_EVAL_BRANCH" --depth 1 \
    https://github.com/Soul-AILab/SoulX-Duplug "$RUN/turn-eval"
  uv venv -q --allow-existing "$RUN/eval-venv" --python 3.10
  uv pip install -q --python "$RUN/eval-venv/bin/python" "nemo_toolkit[asr]==2.4.0" torch==2.7.1 torchaudio==2.7.1 soundfile tqdm python-dotenv==1.1.1 openai==2.11.0
  # note (luojiaxuan): the Chinese scoring scripts run in the turn venv (Paraformer) and import openai too.
  uv pip install -q --python "$RUN/turn-venv/bin/python" python-dotenv==1.1.1 openai==2.11.0
}

case $STEP in
  env) setup_env ;;
  turn) setup_turn ;;
  data) setup_data ;;
  eval) setup_eval ;;
  all) setup_env; setup_turn; setup_data; setup_eval ;;
esac
echo "SETUP_DONE $STEP"
