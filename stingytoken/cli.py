"""stingytoken CLI entry point."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from stingytoken import __version__
from stingytoken.config import load_config
from stingytoken.scope import print_results, rank_files, scan_repo, write_context_file
from stingytoken.utils import estimate_tokens

_console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="stingytoken")
def cli() -> None:
    """Reduce GitHub Copilot token usage via semantic context pruning."""


@cli.command()
@click.argument("query")
@click.option("--max-files", "-n", default=None, type=int, help="Max files to return.")
@click.option("--write-context", "-w", is_flag=True, help="Write .stingytoken-context file.")
@click.option("--root", "-r", default=".", type=click.Path(exists=True), help="Repository root.")
def scope(query: str, max_files: int | None, write_context: bool, root: str) -> None:
    """Scan repo and rank files by relevance to QUERY."""
    config = load_config()
    if max_files is not None:
        config.scope.max_files = max_files

    root_path = Path(root).resolve()
    files = scan_repo(root_path, config)
    total_tokens = sum(f["token_estimate"] for f in files)

    ranked = rank_files(files, query, config.scope.max_files)
    print_results(ranked)

    if write_context:
        ctx_path = write_context_file(ranked, root_path)
        _console.print(f"[bold]Context file written:[/bold] {ctx_path}")

    ranked_tokens = sum(f["token_estimate"] for f in ranked)
    saved = total_tokens - ranked_tokens
    _console.print(
        f"\n[dim]Scanned {len(files)} files · "
        f"Est. tokens saved: [bold]{saved:,}[/bold] "
        f"({total_tokens:,} → {ranked_tokens:,})[/dim]"
    )


@cli.command()
def compress() -> None:
    """Compress prompt context via a local LLM backend."""
    _console.print("Not implemented yet")


@cli.command()
def prep() -> None:
    """Prepare and assemble context for Copilot."""
    _console.print("Not implemented yet")
