"""Repository file scanner with .gitignore and config-based filtering."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pathspec

from stingytoken.utils import estimate_tokens

_MAX_FILE_BYTES = 500_000


def scan_repo(root: Path, config: Any) -> list[dict[str, Any]]:
    """Walk root, apply filters, and return sorted list of file records."""
    root = root.resolve()
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        spec = pathspec.PathSpec.from_lines("gitwildmatch", gitignore_path.read_text(encoding="utf-8").splitlines())
    else:
        spec = pathspec.PathSpec.from_lines("gitwildmatch", [])

    ignore_dirs: set[str] = set(config.scope.ignore)
    extensions: set[str] = set(config.scope.extensions)
    results: list[dict[str, Any]] = []

    for dirpath_str, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

        for filename in filenames:
            abs_path = Path(dirpath_str) / filename
            rel = abs_path.relative_to(root)
            rel_str = rel.as_posix()

            if abs_path.suffix not in extensions:
                continue
            if spec.match_file(rel_str):
                continue
            if abs_path.stat().st_size > _MAX_FILE_BYTES:
                continue

            try:
                content = abs_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            results.append({
                "path": rel_str,
                "abs_path": abs_path,
                "content": content,
                "token_estimate": estimate_tokens(content),
            })

    results.sort(key=lambda f: f["path"])
    return results
