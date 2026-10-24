#!/bin/bash
# usage: post_v15.sh; once all v1.5 shards finish: v1.5 reference phases (GPU 1), v1.0 upstream re-ASR without graph decoding (GPU 2), v1.0 gated diagnostic (GPU 3)
cd /data/runs/20261009-fdb
until [ "$(grep -l DONE logs/supervise-v15-s*.log 2>/dev/null | wc -l)" = 4 ]; do sleep 30; done
PY=/data/runs/20261009-fdb/score-venv/bin/python
OFF=/data/runs/20261009-fdb/graphs_off.py
NEMO=/data/models/parakeet/parakeet-tdt-0.6b-v2.nemo
export HF_HOME=/data/cache/huggingface
(
  set -e
  E=/data/runs/20261009-fdb/ref-v10/export-nograph
  L=/data/runs/20261009-fdb/ref-v10/logs-nograph
  rm -rf $E && mkdir -p $E $L
  for d in ref-v10/export/*/*/; do
    t=$E/${d#ref-v10/export/}
    mkdir -p $t
    cp $d/output.wav $t/
    for a in pause.json turn_taking.json interrupt.json; do
      if [ -f $d/$a ]; then cp $d/$a $t/; fi
    done
  done
  cd fdb-src/v1_v1.5/get_transcript
  for sub in synthetic_pause_handling candor_pause_handling candor_turn_taking icc_backchannel; do
    CUDA_VISIBLE_DEVICES=2 $PY $OFF asr.py --root_dir $E/$sub > $L/asr-$sub.log 2>&1
  done
  CUDA_VISIBLE_DEVICES=2 $PY $OFF asr.py --root_dir $E/synthetic_user_interruption --task user_interruption > $L/asr-synthetic_user_interruption.log 2>&1
  echo V10_NOGRAPH_ASR_DONE
  cd ../evaluation
  CUDA_VISIBLE_DEVICES= $PY evaluate.py --task pause_handling --root_dir $E/synthetic_pause_handling > $L/eval-synthetic_pause_handling.log 2>&1
  CUDA_VISIBLE_DEVICES= $PY evaluate.py --task pause_handling --root_dir $E/candor_pause_handling > $L/eval-candor_pause_handling.log 2>&1
  CUDA_VISIBLE_DEVICES= $PY evaluate.py --task smooth_turn_taking --root_dir $E/candor_turn_taking > $L/eval-candor_turn_taking.log 2>&1
  CUDA_VISIBLE_DEVICES= $PY evaluate.py --task backchannel --root_dir $E/icc_backchannel > $L/eval-icc_backchannel.log 2>&1
  echo V10_NOGRAPH_SCORED
) > logs/v10-nograph.log 2>&1 &
(
  export PYTHONPATH=/data/runs/20261009-fdb/src
  mkdir -p gated-v10
  for k in 0 1 2 3; do
    CUDA_VISIBLE_DEVICES=3 $PY $OFF -m benchmarks.eval.benchmark_duplex_v10 transcribe --run rec/v10-nemotron-s$k-p1 --output gated-v10/asr-s$k --model-path $NEMO --device cuda > logs/gated-asr-s$k.log 2>&1 \
      && $PY -m benchmarks.eval.benchmark_duplex_v10 score --run rec/v10-nemotron-s$k-p1 --output gated-v10/score-s$k --transcripts gated-v10/asr-s$k --backchannel-reference fdb-src/v1_v1.5/evaluation/icc_gt_distribution.json > logs/gated-score-s$k.log 2>&1 \
      && echo "GATED s$k done"
  done
) > logs/gated-v10.log 2>&1 &
set -e
export PYTHONPATH=/data/runs/20261009-fdb/src
runs=()
for d in rec/v15-nemotron-s*-p*; do runs+=(--run "$d"); done
ref=(--reference-source fdb-src --tree model=ref-v15/audio --out ref-v15/scores)
$PY -m benchmarks.eval.benchmark_duplex_reference export --engine sglang --trace-format realtime-pcm16-v1 "${runs[@]}" --dataset-root /data/data/fdb/v1.5 --out ref-v15/audio
CUDA_VISIBLE_DEVICES=1 $PY -m benchmarks.eval.benchmark_duplex_reference asr "${ref[@]}" --nemo $NEMO --nemo-sha256 d99e39955c9d3d0350d8fb7c75e40c64a2b2eaeb003883d7c941fd2e8747b28c --device cuda
CUDA_VISIBLE_DEVICES= $PY -m benchmarks.eval.benchmark_duplex_reference timing "${ref[@]}" --audio-loader soundfile
$PY -m benchmarks.eval.benchmark_duplex_reference prepare-judge "${ref[@]}"
$PY -m benchmarks.eval.benchmark_duplex_reference summarize "${ref[@]}"
echo V15_PREPARED
wait
echo ALL_POST_DONE
