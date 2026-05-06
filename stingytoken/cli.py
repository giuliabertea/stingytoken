"""stingytoken CLI entry point."""

from __future__ import annotations

from pathlib import Path

import click
import pyperclip
from rich.console import Console
from rich.panel import Panel

from stingytoken import __version__
from stingytoken.compress import rewrite_prompt
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
        f"\n[dim]Scanned {len(files)} files | "
        f"Est. tokens saved: [bold]{saved:,}[/bold] "
        f"({total_tokens:,} -> {ranked_tokens:,})[/dim]"
    )


@cli.command()
@click.argument("query")
@click.option("--backend", "-b", default=None, type=click.Choice(["ollama", "openai"]))
@click.option("--model", "-m", default=None)
@click.option("--copy", "-c", is_flag=True, help="Copy result to clipboard")
def compress(query: str, backend: str | None, model: str | None, copy: bool) -> None:
    """Compress a prompt via a local LLM backend."""
    config = load_config()
    if backend is not None:
        config.compress.backend = backend
    if model is not None:
        config.compress.model = model

    try:
        result = rewrite_prompt(query, config)
    except RuntimeError as exc:
        _console.print(f"[red]{exc}[/red]")
        raise SystemExit(1)

    _console.print(Panel(result["rewritten"], border_style="green", title="Rewritten prompt"))
    _console.print(
        f"Original: ~{result['original_tokens']} tokens  →  "
        f"Rewritten: ~{result['rewritten_tokens']} tokens  "
        f"({result['savings_pct']}% reduction)"
    )

    if copy:
        pyperclip.copy(result["rewritten"])
        _console.print("✓ Copied to clipboard")


@cli.command()
@click.argument("query")
@click.option("--max-files", "-n", default=None, type=int)
@click.option("--backend", "-b", default=None, type=click.Choice(["ollama", "openai"]))
@click.option("--model", "-m", default=None)
@click.option("--copy", "-c", is_flag=True)
@click.option("--root", "-r", default=".", type=click.Path(exists=True))
def prep(
    query: str,
    max_files: int | None,
    backend: str | None,
    model: str | None,
    copy: bool,
    root: str,
) -> None:
    """Scan repo and compress prompt in one step."""
    config = load_config()
    if max_files is not None:
        config.scope.max_files = max_files
    if backend is not None:
        config.compress.backend = backend
    if model is not None:
        config.compress.model = model

    root_path = Path(root).resolve()

    with _console.status("📁 Scanning repo..."):
        files = scan_repo(root_path, config)
        total_scanned = len(files)
        ranked = rank_files(files, query, config.scope.max_files)

    try:
        with _console.status("✍️  Compressing prompt..."):
            result = rewrite_prompt(query, config)
    except RuntimeError as exc:
        _console.print(f"[red]{exc}[/red]")
        raise SystemExit(1)

    paths = [f["path"] for f in ranked]
    savings_pct = result["savings_pct"]

    panel_content = "\n".join([
        "📁 Context files:",
        *[f"  {p}" for p in paths],
        "",
        "✍️  Optimized prompt:",
        result["rewritten"],
        "",
        f"Tokens saved: ~{savings_pct}% on prompt | Context: {len(ranked)} files instead of {total_scanned}",
    ])
    _console.print(Panel(panel_content))

    if copy:
        combined = "# Context files\n" + "\n".join(paths) + "\n\n# Prompt\n" + result["rewritten"]
        pyperclip.copy(combined)
