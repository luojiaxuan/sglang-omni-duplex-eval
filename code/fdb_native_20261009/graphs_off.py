"""Run a script or module with the NeMo CUDA-graph transducer decoder disabled.

NeMo 3.0 graph decoding truncates Parakeet transcripts (sglang-omni#2666). Every
ASRModel loaded through restore_from or from_pretrained gets the same decoding
change as that fix, then the target runs unchanged.

usage: graphs_off.py script.py [args...] | graphs_off.py -m module [args...]
"""

import runpy
import sys

from nemo.collections.asr.models import ASRModel


def disable_graph_decoder(model):
    decoding = dict(model.cfg.decoding)
    decoding["greedy"] = {**decoding["greedy"], "use_cuda_graph_decoder": False}
    model.change_decoding_strategy(decoding)
    return model


def wrap(name):
    original = getattr(ASRModel, name).__func__

    def load(cls, *args, **kwargs):
        return disable_graph_decoder(original(cls, *args, **kwargs))

    setattr(ASRModel, name, classmethod(load))


wrap("restore_from")
wrap("from_pretrained")
if sys.argv[1] == "-m":
    sys.argv = sys.argv[2:]
    runpy.run_module(sys.argv[0], run_name="__main__", alter_sys=True)
else:
    sys.argv = sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")
