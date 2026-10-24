#!/bin/bash
# note (luojiaxuan): the one-GPU streaming cascade (Qwen3-ASR, Qwen3-4B, Qwen3-TTS
# CustomVoice) of the private main, on high ports, until the container is stopped.
# $1 run directory.
set -uo pipefail
R=$1
export HF_HOME=/data/cache/huggingface PYTHONPATH=$R/cascade-src:$R/pyshim CUDA_VISIBLE_DEVICES=0
cd $R/cascade-src
step() {
  local name=$1; shift
  local start=$SECONDS
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code seconds=$((SECONDS - start))"
  return $code
}
step cascade-pip pip install -e . && \
step cascade-pip-extra pip install websockets httpx && \
step cascade-sox bash -c "apt-get update -qq && apt-get install -y -qq sox" && \
step cascade-tts-deps bash -c "pip install --no-deps sox einops && pip install --no-deps qwen-tts==0.1.1" && step cascade-models python -c "from huggingface_hub import snapshot_download
for model in ('Qwen/Qwen3-4B-Instruct-2507', 'Qwen/Qwen3-ASR-1.7B', 'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice'):
    print(model, snapshot_download(model))" || exit 1
sgl-omni serve --config examples/streaming_cascade/profiles/qwen3-asr-qwen3-tts-customvoice-bench/launch.yaml \
  --enable-realtime --host 127.0.0.1 --port 28765 > $R/logs/cascade-server.log 2>&1 &
SERVER=$!
START=$SECONDS
# note (luojiaxuan): another tenant's server may answer a port on this host network, so
# the cascade is up only when /v1/models names this profile.
until curl -sf http://127.0.0.1:28765/v1/models | grep -q customvoice-bench; do
  if ! kill -0 $SERVER 2>/dev/null || (( SECONDS - START > 2400 )); then echo "CASCADE_FAILED"; exit 1; fi
  sleep 10
done
echo "CASCADE_UP after $((SECONDS - START)) s"
wait $SERVER
echo "CASCADE_EXIT $?"
