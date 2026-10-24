"""Round-robin shard lists of every v1.0 sample and v1.5 pair, one file per GPU."""
import sys
from pathlib import Path

root, out, gpus = Path(sys.argv[1]), Path(sys.argv[2]), [int(g) for g in sys.argv[3].split(",")]
out.mkdir(parents=True, exist_ok=True)
for name in ("v1.0", "v1.5"):
    ids = sorted(
        f"{subset.name}/{sample.name}"
        for subset in (root / name).iterdir() if subset.is_dir()
        for sample in subset.iterdir() if sample.is_dir() and sample.name.isdigit()
    )
    shards = {gpu: ids[index::len(gpus)] for index, gpu in enumerate(gpus)}
    for gpu, chunk in shards.items():
        (out / f"{name.replace('.', '')}-g{gpu}.txt").write_text("".join(f"{line}\n" for line in chunk))
    print(name, len(ids), {gpu: len(chunk) for gpu, chunk in shards.items()})
