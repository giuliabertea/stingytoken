"""Layered TOML configuration loader for stingytoken."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_DEFAULTS: dict[str, Any] = {
    "scope": {
        "max_files": 12,
        "extensions": [".py", ".ts", ".js", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb", ".php"],
        "ignore": ["node_modules", "dist", ".venv", "__pycache__", ".git", "build", "coverage"],
        "write_context": False,
    },
    "compress": {
        "backend": "ollama",
        "model": "mistral",
        "max_output_tokens": 120,
        "temperature": 0.2,
    },
}


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return {}


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = {k: dict(v) if isinstance(v, dict) else v for k, v in base.items()}
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = {**result[key], **value}
        else:
            result[key] = value
    return result


def load_config() -> SimpleNamespace:
    """Load config from defaults, ~/.stingytokenrc, and .stingytoken.toml (last wins)."""
    merged = {k: dict(v) for k, v in _DEFAULTS.items()}
    merged = _merge(merged, _load_toml(Path.home() / ".stingytokenrc"))
    merged = _merge(merged, _load_toml(Path.cwd() / ".stingytoken.toml"))

    return SimpleNamespace(
        scope=SimpleNamespace(**merged["scope"]),
        compress=SimpleNamespace(**merged["compress"]),
    )
