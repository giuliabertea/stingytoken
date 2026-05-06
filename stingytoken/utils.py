"""Token estimation and text truncation utilities."""


def estimate_tokens(text: str) -> int:
    """Rough token estimate: word count × 1.3, rounded to nearest int."""
    return round(len(text.split()) * 1.3)


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text at a word boundary so estimate_tokens(result) <= max_tokens."""
    if estimate_tokens(text) <= max_tokens:
        return text

    words = text.split()
    lo, hi = 0, len(words)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if round(mid * 1.3) <= max_tokens:
            lo = mid
        else:
            hi = mid - 1

    if lo == 0:
        return "..."
    return " ".join(words[:lo]) + "..."
