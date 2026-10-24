#!/bin/bash
# note (luojiaxuan): two replicas of the Qwen3.8-27B cascade from private main, one GPU each,
# serving until the container stops. $1 run directory.
set -uo pipefail
R=$1
export HF_HOME=/data/cache/huggingface PYTHONPATH=$R/priv
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
for model in ('Qwen/Qwen3.8-27B', 'Qwen/Qwen3-ASR-1.7B', 'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice'):
    print(model, snapshot_download(model))" || exit 1
for r in 0 1; do
  step srv-cascade27b-r$r-launch bash -c "CUDA_VISIBLE_DEVICES=$r sgl-omni serve --config examples/streaming_cascade/profiles/qwen3-asr-qwen3.8-27b-customvoice-bench-r$r/launch.yaml --enable-realtime --host 127.0.0.1 --port $((28870 + r)) > $R/logs/srv-cascade27b-r$r.log 2>&1 &"
done
START=$SECONDS
for r in 0 1; do
  until curl -sf http://127.0.0.1:$((28870 + r))/v1/models | grep -qi "27b-customvoice-bench-r$r"; do
    if (( SECONDS - START > 2400 )); then echo "SERVER_FAILED r$r"; exit 1; fi
    sleep 15
  done
  echo "SERVER_UP r$r after $((SECONDS - START)) s"
done
sleep infinity
