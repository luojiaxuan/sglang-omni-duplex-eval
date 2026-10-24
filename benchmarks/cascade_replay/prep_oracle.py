# SPDX-License-Identifier: Apache-2.0
"""Write oracle_text.txt for each sample: offline ASR of input.wav up to the annotated turn end.

Runs in the turn-detector environment (funasr): SenseVoice-Small for English, Paraformer-large for
Chinese, matching the external ASR the turn detector uses for each language.
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

ASR_MODEL = {
    "en": "iic/SenseVoiceSmall",
    "zh": "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--lang", choices=["en", "zh"], required=True)
    args = ap.parse_args()

    model = AutoModel(model=ASR_MODEL[args.lang], device="cuda", disable_pbar=True, disable_update=True)
    for d in sorted(p for p in args.data.iterdir() if (p / "input.wav").exists()):
        audio, sr = sf.read(d / "input.wav", dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
        if sr != 16000:
            audio = soxr.resample(audio, sr, 16000).astype(np.float32)
        end = json.loads((d / "turn_taking.json").read_text())[0]["timestamp"][0]
        kwargs = {"language": "en", "use_itn": True} if args.lang == "en" else {}
        res = model.generate(input=audio[: int(end * 16000)], **kwargs)
        if args.lang == "en":
            text = rich_transcription_postprocess(res[0]["text"])
        else:
            text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", res[0]["text"])
        (d / "oracle_text.txt").write_text(text.strip() + "\n")
        print(d.name, text.strip())


if __name__ == "__main__":
    main()
