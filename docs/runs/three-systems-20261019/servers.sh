#!/bin/bash
# note (luojiaxuan): the three systems of the private main, one H200 each, on high ports:
# MiniCPM-o native full duplex, Qwen3-Omni as a turn-based Session node, and the streaming
# cascade; they serve until the container is stopped. $1 run directory.
set -uo pipefail
R=$1
export HF_HOME=/data/cache/huggingface PYTHONPATH=$R/priv:$R/pyshim
cd $R/priv
step() {
  local name=$1; shift
  local start=$SECONDS
  "$@" > $R/logs/$name.log 2>&1
  local code=$?
  echo "STEP $name exit=$code seconds=$((SECONDS - start))"
  return $code
}
step srv-pip pip install -e . && \
step srv-pip-extra pip install websockets httpx && \
step srv-sox bash -c "apt-get update -qq && apt-get install -y -qq sox" && \
step srv-tts-deps bash -c "pip install --no-deps sox einops && pip install --no-deps qwen-tts==0.1.1" && \
step srv-models python -c "from huggingface_hub import snapshot_download
print(snapshot_download('openbmb/MiniCPM-o-4_5', revision='503e754207c94da6bb26850b4469f367c9ea3582'))
for model in ('Qwen/Qwen3-Omni-30B-A3B-Instruct', 'Qwen/Qwen3-4B-Instruct-2507', 'Qwen/Qwen3-ASR-1.7B', 'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice'):
    print(model, snapshot_download(model))" || exit 1
MINICPMO=$(python -c "from huggingface_hub import snapshot_download; print(snapshot_download('openbmb/MiniCPM-o-4_5', revision='503e754207c94da6bb26850b4469f367c9ea3582'))")
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 python -m sglang_omni.cli serve --model-path $MINICPMO \
  --variant session --max_sessions 40 --enable-realtime --host 127.0.0.1 --port 28097 > $R/logs/srv-minicpmo.log 2>&1 &
CUDA_VISIBLE_DEVICES=1 sgl-omni serve --config examples/qwen3_omni/session_h200.yaml \
  --enable-realtime --host 127.0.0.1 --port 28965 > $R/logs/srv-qwen3omni.log 2>&1 &
CUDA_VISIBLE_DEVICES=2 sgl-omni serve --config examples/streaming_cascade/profiles/qwen3-asr-qwen3-tts-customvoice-bench/launch.yaml \
  --enable-realtime --host 127.0.0.1 --port 28865 > $R/logs/srv-cascade.log 2>&1 &
START=$SECONDS
# note (luojiaxuan): another tenant may answer a port on this host network, so a server is up
# only when /v1/models names its model or profile.
for pair in "28097 MiniCPM-o" "28965 qwen3.omni" "28865 customvoice-bench"; do
  set -- $pair
  until curl -sf http://127.0.0.1:$1/v1/models | grep -qi "$2"; do
    if (( SECONDS - START > 3600 )); then echo "SERVER_FAILED $2"; exit 1; fi
    sleep 15
  done
  echo "SERVER_UP $2 after $((SECONDS - START)) s"
done
wait
echo "SERVERS_EXIT"
