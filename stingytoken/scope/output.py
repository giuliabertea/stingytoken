"""Rich table display and context manifest writing for scope results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

_console = Console()


def print_results(ranked: list[dict[str, Any]]) -> None:
    """Print ranked file results as a rich table with score-based color coding."""
    table = Table(title="Scope Results", show_lines=False)
    table.add_column("Rank", style="bold", justify="right", no_wrap=True)
    table.add_column("Score", justify="right", no_wrap=True)
    table.add_column("File")
    table.add_column("Est. Tokens", justify="right", no_wrap=True)

    for i, file in enumerate(ranked, start=1):
        score: float = file["score"]
        tokens: int = file["token_estimate"]
        path: str = file["path"]

        if score >= 0.3:
            style = "green"
        elif score >= 0.1:
            style = "yellow"
        else:
            style = "dim"

        table.add_row(str(i), f"{score:.3f}", path, str(tokens), style=style)

    _console.print(table)


def write_context_file(ranked: list[dict[str, Any]], root: Path) -> Path:
    """Write .stingytoken-context listing relative paths of ranked files."""
    out = root / ".stingytoken-context"
    out.write_text("\n".join(f["path"] for f in ranked) + "\n", encoding="utf-8")
    return out
