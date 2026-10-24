#!/usr/bin/env bash
# Start the LLM, the TTS and N turn-detector servers for one language. GPU placement is chosen
# with LLM_GPU / TTS_GPU / TURN_GPU (0 or 1: index into the two granted GPUs; default 0/1/0).
# LLM_MEM and TTS_MEM set the memory fractions when the LLM and TTS share a GPU; turn servers
# listen on TURN_PORT_BASE + k (default 8100). note (luojiaxuan): TURN_MARGIN / TURN_WAIT set the decision rule (see below).
# Usage: bash serve.sh <run_dir> <en|zh> [n_turn_servers] [all|models|turn]
set -euo pipefail
RUN=$1
LANG_=$2
NTURN=${3:-4}
WHAT=${4:-all}
export HF_HOME=/data/cache/huggingface MODELSCOPE_CACHE=/data/cache/modelscope
export PYTHONPATH="$RUN/src/benchmarks/cascade_replay/pyshim${PYTHONPATH:+:$PYTHONPATH}"
IFS=, read -r -a GPUS <<<"$CUDA_VISIBLE_DEVICES"
LLM_DEV=${GPUS[${LLM_GPU:-0}]}
TTS_DEV=${GPUS[${TTS_GPU:-1}]}
TURN_DEV=${GPUS[${TURN_GPU:-0}]}
LLM_MEM=${LLM_MEM:-0.5}
TTS_MEM=${TTS_MEM:-0.85}
TURN_PORT_BASE=${TURN_PORT_BASE:-8100}
mkdir -p "$RUN/logs"

if [ "$WHAT" != turn ]; then
CUDA_VISIBLE_DEVICES=$TTS_DEV nohup /opt/sglang/bin/sgl-omni serve \
  --model-path Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
  --config "$RUN/src/examples/configs/qwen3_tts_1_7b_customvoice.yaml" \
  --tts_engine.gpu_memory_fraction "$TTS_MEM" --vocoder.gpu_memory_fraction 0.05 \
  --host 127.0.0.1 --port 8000 >"$RUN/logs/tts.log" 2>&1 &
if [ "$LLM_DEV" = "$TTS_DEV" ]; then
  until curl -sf -o /dev/null 127.0.0.1:8000/health; do sleep 5; done
fi
CUDA_VISIBLE_DEVICES=$LLM_DEV nohup /opt/sglang/bin/python3 -m sglang.launch_server \
  --model-path Qwen/Qwen2.5-7B-Instruct --host 127.0.0.1 --port 30000 \
  --mem-fraction-static "$LLM_MEM" >"$RUN/logs/llm.log" 2>&1 &
fi
[ "$WHAT" = models ] && exit 0

# note (luojiaxuan): TURN_MARGIN is the logit lead <|user_complete|> needs over <|user_incomplete|> to reply at
# the first idle chunk, TURN_WAIT the further idle chunks after that decision before the fallback reply
# (SoulX defaults: 0 and 8).
# TURN_DIRECT=0 turns an argmax <|user_complete|> outside that decision into a wait, so replies only come
# at or after a pause (sweep.py's soulx-eos family).
TURN_MARGIN=${TURN_MARGIN:-0}
TURN_WAIT=${TURN_WAIT:-8}
TURN_DIRECT=${TURN_DIRECT:-1}
TURN_TAG=m$TURN_MARGIN-w$TURN_WAIT$([ "$TURN_DIRECT" = 0 ] && echo -eos || true)
TURN_DIR="$RUN/turn-$LANG_-$TURN_TAG"
if [ ! -d "$TURN_DIR" ]; then
  cp -r "$RUN/turn-$LANG_" "$TURN_DIR"
  sed -i "s/> logits\[-1, self.config.model_config.user_incomplete_token_id\]/& + ($TURN_MARGIN)/" "$TURN_DIR/service/model.py"
  sed -i "s/max_wait_num: 8/max_wait_num: $TURN_WAIT/" "$TURN_DIR/config/config.yaml"
  grep -q "user_incomplete_token_id\] + ($TURN_MARGIN)" "$TURN_DIR/service/model.py"
  grep -q "max_wait_num: $TURN_WAIT\$" "$TURN_DIR/config/config.yaml"
  if [ "$TURN_DIRECT" = 0 ]; then
    /opt/sglang/bin/python3 - "$TURN_DIR/service/model.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
old = """        else:
            # Update input_embeds for next turn (state token embedding)
"""
new = """        elif state == "<|user_complete|>":
            state = "<|user_incomplete|>"
            self.past_state["input_embeds"] = self.action_wait_embeds
        else:
            # Update input_embeds for next turn (state token embedding)
"""
assert s.count(old) == 1
open(p, "w").write(s.replace(old, new))
PY
  fi
fi
for k in $(seq 0 $((NTURN - 1))); do
  (cd "$TURN_DIR" && CUDA_VISIBLE_DEVICES=$TURN_DEV OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 nohup "$RUN/turn-venv/bin/uvicorn" server:app \
    --host 127.0.0.1 --port $((TURN_PORT_BASE + k)) --workers 1 >"$RUN/logs/turn-$LANG_-$TURN_TAG-$k.log" 2>&1 &
    echo $! >"$RUN/logs/turn-$LANG_-$TURN_TAG-$k.pid")
done
