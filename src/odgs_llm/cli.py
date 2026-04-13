"""
ODGS LLM Bridge CLI — `odgs-llm` command line interface.

Usage:
    odgs-llm compile   <file>      Compile regulation text to ODGS rules
    odgs-llm drift     <dir>       Check definitions for staleness
    odgs-llm conflicts <file>      Detect rule conflicts
    odgs-llm narrate   <file>      Narrate an S-Cert
    odgs-llm discover  <file>      Discover bindings from catalog metadata
    odgs-llm health                Check provider connectivity
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="odgs-llm",
    help="LLM Bridge for the Open Data Governance Standard (ODGS v6.0)",
    no_args_is_help=True,
)
console = Console()


def _get_bridge(provider: Optional[str], model: Optional[str]):
    from odgs_llm.bridge import OdgsLlmBridge

    return OdgsLlmBridge(provider=provider, model=model)


@app.command()
def compile(
    file: Path = typer.Argument(..., help="Path to regulation text file"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model name"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Compile regulation text into ODGS rule JSON."""
    text = file.read_text(encoding="utf-8")
    bridge = _get_bridge(provider, model)

    with console.status("[bold green]Compiling regulation..."):
        rules = bridge.compile_regulation(text)

    result = json.dumps(rules, indent=2)
    if output:
        output.write_text(result, encoding="utf-8")
        console.print(f"[green]✓[/green] Wrote {len(rules)} rules to {output}")
    else:
        console.print_json(result)


@app.command()
def drift(
    directory: Path = typer.Argument(..., help="Path to definitions directory"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    threshold: int = typer.Option(90, "--threshold", "-t", help="Staleness threshold in days"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Check definition files for semantic drift."""
    bridge = _get_bridge(provider, model)

    with console.status("[bold yellow]Scanning for drift..."):
        warnings = bridge.check_drift(str(directory), threshold_days=threshold)

    result = json.dumps(warnings, indent=2)
    if output:
        output.write_text(result, encoding="utf-8")
        console.print(f"[green]✓[/green] Wrote {len(warnings)} warnings to {output}")
    else:
        console.print_json(result)

    if warnings:
        console.print(
            Panel(
                f"[yellow]{len(warnings)} drift warnings detected[/yellow]",
                title="⚠ Drift Report",
            )
        )


@app.command()
def conflicts(
    file: Path = typer.Argument(..., help="Path to rules JSON file"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Detect semantic conflicts across ODGS rules."""
    rules = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(rules, list):
        rules = rules.get("rules", [])

    bridge = _get_bridge(provider, model)

    with console.status("[bold red]Detecting conflicts..."):
        conflicts_found = bridge.detect_conflicts(rules)

    result = json.dumps(conflicts_found, indent=2)
    if output:
        output.write_text(result, encoding="utf-8")
        console.print(f"[green]✓[/green] Wrote {len(conflicts_found)} conflicts to {output}")
    else:
        console.print_json(result)


@app.command()
def narrate(
    file: Path = typer.Argument(..., help="Path to S-Cert JSON file"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    audience: str = typer.Option("executive", "--audience", "-a", help="executive|legal|technical"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Narrate an S-Cert as a human-readable report."""
    scert = json.loads(file.read_text(encoding="utf-8"))
    bridge = _get_bridge(provider, model)

    with console.status("[bold blue]Generating narrative..."):
        narrative = bridge.narrate_audit(scert, audience=audience)

    if output:
        output.write_text(narrative, encoding="utf-8")
        console.print(f"[green]✓[/green] Wrote narrative to {output}")
    else:
        console.print(narrative)


@app.command()
def discover(
    file: Path = typer.Argument(..., help="Path to catalog metadata JSON"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    metrics: Optional[Path] = typer.Option(None, "--metrics", help="Path to existing metrics JSON"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
):
    """Discover physical data bindings from catalog metadata."""
    catalog = json.loads(file.read_text(encoding="utf-8"))
    metrics_data = None
    if metrics:
        metrics_data = json.loads(metrics.read_text(encoding="utf-8"))

    bridge = _get_bridge(provider, model)

    with console.status("[bold magenta]Discovering bindings..."):
        bindings = bridge.discover_bindings(catalog, metrics=metrics_data)

    result = json.dumps(bindings, indent=2)
    if output:
        output.write_text(result, encoding="utf-8")
        console.print(f"[green]✓[/green] Wrote bindings to {output}")
    else:
        console.print_json(result)


@app.command()
def health(
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
):
    """Check LLM provider connectivity."""
    try:
        bridge = _get_bridge(provider, model)
        ok = bridge.provider.health_check()
        if ok:
            console.print(
                Panel(
                    f"[green]✓ Provider '{bridge.provider.name}' is reachable[/green]",
                    title="Health Check",
                )
            )
        else:
            console.print("[red]✗ Provider health check failed[/red]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from odgs_llm import __version__

    console.print(f"odgs-llm-bridge v{__version__}")


if __name__ == "__main__":
    app()
