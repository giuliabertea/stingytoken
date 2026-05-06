from __future__ import annotations

from stingytoken.compress.backends import get_backend
from stingytoken.compress.templates import COMPRESSION_SYSTEM_PROMPT
from stingytoken.utils import estimate_tokens


def rewrite_prompt(prompt: str, config) -> dict:
    backend = get_backend(config)
    original_tokens = estimate_tokens(prompt)
    rewritten = backend.complete(COMPRESSION_SYSTEM_PROMPT, prompt).strip()
    rewritten_tokens = estimate_tokens(rewritten)
    savings_pct = round((1 - rewritten_tokens / original_tokens) * 100) if original_tokens > 0 else 0
    return {
        "original": prompt,
        "rewritten": rewritten,
        "original_tokens": original_tokens,
        "rewritten_tokens": rewritten_tokens,
        "savings_pct": savings_pct,
    }
