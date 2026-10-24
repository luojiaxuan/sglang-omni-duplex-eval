#!/bin/bash
# note (luojiaxuan): the 4B cascade of private main with the Vivian anchor, one GPU, serving until
# the container stops. $1 run directory.
set -uo pipefail
R=$1
export HF_HOME=/data/cache/huggingface PYTHONPATH=$R/priv:$R/pyshim
cd $R/priv
step() {
  local name=$1; shift
  printf '%s\t%s\tcd %q && env HF_HOME=%q PYTHONPATH=%q' "$(date -u +%FT%TZ)" "$name" "$PWD" "$HF_HOME" "$PYTHONPATH" >> $R/logs/commands-servers.log
  printf ' %q' "$@" >> $R/logs/commands-servers.log; printf '\n' >> $R/logs/commands-servers.log
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code"
  return $code
}
step srv-pip pip install -e . && \
step srv-pip-extra pip install websockets httpx && \
step srv-sox bash -c "apt-get update -qq && apt-get install -y -qq sox" && \
step srv-tts-deps bash -c "pip install --no-deps sox einops && pip install --no-deps qwen-tts==0.1.1" && \
step srv-models python -c "from huggingface_hub import snapshot_download
for model in ('Qwen/Qwen3-4B-Instruct-2507', 'Qwen/Qwen3-ASR-1.7B', 'Qwen/Qwen3-TTS-12Hz-1.7B-Base'):
    print(model, snapshot_download(model))" || exit 1
step srv-cascade-xvector-launch bash -c "sgl-omni serve --config examples/streaming_cascade/profiles/qwen3-asr-qwen3-tts-vivian-xvector-bench/launch.yaml --enable-realtime --host 127.0.0.1 --port 28865 > $R/logs/srv-cascade-xvector.log 2>&1 &"
START=$SECONDS
until curl -sf http://127.0.0.1:28865/v1/models | grep -qi "vivian-xvector-bench"; do
  if (( SECONDS - START > 2400 )); then echo "SERVER_FAILED"; exit 1; fi
  sleep 15
done
echo "SERVER_UP after $((SECONDS - START)) s"
sleep infinity
