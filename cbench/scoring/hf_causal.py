from __future__ import annotations

from dataclasses import dataclass
import math
import time
from pathlib import Path
from typing import Any

from cbench.data.loaders import decode_utf8
from cbench.data.manifest import ManifestEntry, resolve_entry_path
from cbench.metrics import DocumentScore
from cbench.scoring.windows import make_windows


@dataclass(frozen=True)
class HFDocumentResult:
    score: DocumentScore
    token_count: int
    scored_tokens: int
    unscored_initial_tokens: int


class HFCausalScorer:
    def __init__(self, model_name: str, *, device: str | None = None, dtype: str | None = None) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ModuleNotFoundError as exc:
            raise RuntimeError("Hugging Face scoring requires the 'hf' extra: pip install -e '.[hf]'") from exc

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        model_kwargs: dict[str, Any] = {}
        if dtype:
            model_kwargs["torch_dtype"] = getattr(torch, dtype)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
        if device:
            self.model.to(device)
        self.model.eval()
        self.model_name = model_name

    def score_bytes(
        self,
        raw: bytes,
        *,
        max_context_tokens: int,
        target_chunk_tokens: int,
        allow_invalid_utf8: bool = False,
        use_bos: bool = False,
    ) -> tuple[float, int, int, int]:
        text = decode_utf8(raw, allow_invalid_utf8=allow_invalid_utf8)
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        unscored_initial_tokens = 0
        if use_bos:
            bos_id = self.tokenizer.bos_token_id
            if bos_id is None:
                raise ValueError("use_bos=True requested, but tokenizer has no bos_token_id")
            token_ids = [bos_id] + token_ids
        else:
            unscored_initial_tokens = 1 if token_ids else 0

        windows = make_windows(token_ids, max_context_tokens, target_chunk_tokens)
        bits = 0.0
        scored_tokens = 0
        device = next(self.model.parameters()).device
        with self.torch.no_grad():
            for window in windows:
                input_ids = window.context_ids + window.target_ids
                if len(input_ids) < 2:
                    continue
                context_len = len(window.context_ids)
                tensor = self.torch.tensor([input_ids], dtype=self.torch.long, device=device)
                logits = self.model(tensor).logits[0]
                logprobs = self.torch.nn.functional.log_softmax(logits, dim=-1)
                for offset, target_id in enumerate(window.target_ids):
                    input_position = context_len + offset
                    prediction_position = input_position - 1
                    if prediction_position < 0:
                        continue
                    bits += float(-logprobs[prediction_position, target_id].item() / math.log(2.0))
                    scored_tokens += 1
        if scored_tokens == 0:
            raise ValueError("document produced no scorable tokens; use a longer document or enable BOS scoring")
        visible_token_count = len(token_ids) - (1 if use_bos else 0)
        return bits, visible_token_count, scored_tokens, unscored_initial_tokens

    def score_entry(
        self,
        entry: ManifestEntry,
        manifest_path: str | Path,
        *,
        max_context_tokens: int,
        target_chunk_tokens: int,
        allow_invalid_utf8: bool = False,
        use_bos: bool = False,
    ) -> HFDocumentResult:
        if entry.mode != "streaming" or not entry.path:
            raise ValueError(f"{entry.id}: HF scorer supports streaming entries only")
        raw = resolve_entry_path(entry.path, manifest_path).read_bytes()
        bits, token_count, scored_tokens, unscored_initial_tokens = self.score_bytes(
            raw,
            max_context_tokens=max_context_tokens,
            target_chunk_tokens=target_chunk_tokens,
            allow_invalid_utf8=allow_invalid_utf8,
            use_bos=use_bos,
        )
        score = DocumentScore(id=entry.id, domain=entry.domain, bits=bits, bytes=len(raw), token_count=token_count)
        return HFDocumentResult(
            score=score,
            token_count=token_count,
            scored_tokens=scored_tokens,
            unscored_initial_tokens=unscored_initial_tokens,
        )


def score_hf_entries(
    model_name: str,
    entries: list[ManifestEntry],
    manifest_path: str | Path,
    *,
    max_context_tokens: int,
    target_chunk_tokens: int,
    allow_invalid_utf8: bool = False,
    use_bos: bool = False,
    device: str | None = None,
) -> tuple[list[HFDocumentResult], dict[str, float | int | None]]:
    started = time.perf_counter()
    scorer = HFCausalScorer(model_name, device=device)
    results = [
        scorer.score_entry(
            entry,
            manifest_path,
            max_context_tokens=max_context_tokens,
            target_chunk_tokens=target_chunk_tokens,
            allow_invalid_utf8=allow_invalid_utf8,
            use_bos=use_bos,
        )
        for entry in entries
    ]
    elapsed = time.perf_counter() - started
    total_scored = sum(result.scored_tokens for result in results)
    return results, {
        "wall_time_seconds": elapsed,
        "peak_vram_gb": None,
        "peak_ram_gb": None,
        "tokens_per_second": total_scored / elapsed if elapsed > 0 else None,
        "estimated_cost_usd": None,
        "api_calls": None,
        "reasoning_tokens": None,
    }
