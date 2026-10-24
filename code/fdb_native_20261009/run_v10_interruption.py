"""Run the pinned upstream FDB v1.0 user-interruption evaluator under a spend cap.

The upstream eval_user_interruption(root_dir, client) is imported unchanged
(its SHA-256 is checked) and handed a client whose chat.completions.create
first checks that incurred spend plus the worst case of the next request stays
under the cap, then records every request and response in a JSONL ledger.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

from openai import OpenAI

UPSTREAM_SHA256 = "e701c14579c1477577b262265cfff75b28ac2e057beee5ba82572afa2a35963a"
# note (luojiaxuan): USD per token for gpt-4-turbo; the worst case assumes the model's 4096-token output limit because upstream sets no max_tokens.
PRICE_IN, PRICE_OUT, MAX_OUT = 10e-6, 30e-6, 4096


class BudgetExceeded(RuntimeError):
    pass


class LedgerCompletions:
    def __init__(self, client: OpenAI, ledger: Path, cap_usd: float) -> None:
        self.client, self.ledger, self.cap_usd = client, ledger, cap_usd
        self.spent = sum(json.loads(line)["cost_usd"] for line in ledger.open()) if ledger.exists() else 0.0

    def create(self, **request):
        prompt_chars = sum(len(m["content"]) for m in request["messages"])
        # note (luojiaxuan): one token per two characters over-estimates English prompts, keeping the bound conservative.
        bound = prompt_chars / 2 * PRICE_IN + MAX_OUT * PRICE_OUT
        if self.spent + bound > self.cap_usd:
            raise BudgetExceeded(f"spent {self.spent:.4f} + bound {bound:.4f} > cap {self.cap_usd}")
        started = time.time()
        response = self.client.chat.completions.create(**request)
        usage = response.usage
        cost = usage.prompt_tokens * PRICE_IN + usage.completion_tokens * PRICE_OUT
        self.spent += cost
        with self.ledger.open("a") as f:
            f.write(json.dumps({
                "started": started,
                "requested_model": request["model"],
                "returned_model": response.model,
                "seed": request.get("seed"),
                "messages_sha256": hashlib.sha256(json.dumps(request["messages"]).encode()).hexdigest(),
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "cost_usd": cost,
                "content": response.choices[0].message.content,
            }) + "\n")
        return response


class LedgerClient:
    def __init__(self, completions: LedgerCompletions) -> None:
        self.chat = type("Chat", (), {"completions": completions})()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True, help="evaluation/eval_user_interruption.py")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--cap-usd", type=float, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    digest = hashlib.sha256(args.upstream.read_bytes()).hexdigest()
    if digest != UPSTREAM_SHA256:
        raise SystemExit(f"upstream evaluator hash {digest} differs from the pinned one")
    spec = importlib.util.spec_from_file_location("eval_user_interruption", args.upstream)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    completions = LedgerCompletions(OpenAI(api_key=os.environ["OPENAI_API_KEY"]), args.ledger, args.cap_usd)
    with args.log.open("w") as log, contextlib.redirect_stdout(log):
        module.eval_user_interruption(str(args.root_dir), LedgerClient(completions))
    print(f"spent {completions.spent:.4f} USD; log {args.log}", file=sys.stderr)


if __name__ == "__main__":
    main()
