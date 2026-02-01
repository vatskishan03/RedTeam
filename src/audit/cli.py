from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from audit.flows import run_fix, run_pipeline, run_scan, run_verify, run_report
from audit.tools.openai_client import OpenAIClient

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


def _get_client() -> OpenAIClient:
    load_dotenv()
    client = OpenAIClient()
    if not client.available:
        console.print(f"[yellow]OpenAI client unavailable:[/yellow] {client.error}")
        console.print("Falling back to heuristic mode.")
    return client


def _print_findings(findings) -> None:
    table = Table(title="Findings")
    table.add_column("ID")
    table.add_column("Severity")
    table.add_column("Title")
    table.add_column("Location")
    for f in findings:
        table.add_row(f.id, f.severity, f.title, f"{f.file}:{f.line}")
    console.print(table)


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Path to codebase"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
    heuristic: bool = typer.Option(False, "--heuristic"),
):
    client = _get_client()
    run_paths, findings, _ = run_scan(
        path, client, run_id=run_id, use_heuristics=heuristic or not client.available
    )
    console.print(f"Run: {run_paths.root}")
    _print_findings(findings)


@app.command()
def fix(
    path: Path = typer.Argument(..., help="Path to codebase"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
    autofix: bool = typer.Option(False, "--autofix"),
    heuristic: bool = typer.Option(False, "--heuristic"),
):
    client = _get_client()
    run_paths, findings, patches = run_fix(
        path,
        client,
        run_id=run_id,
        autofix=autofix,
        use_heuristics=heuristic or not client.available,
    )
    console.print(f"Run: {run_paths.root}")
    _print_findings(findings)
    console.print(f"Patches generated: {len(patches)}")


@app.command()
def verify(
    path: Path = typer.Argument(..., help="Path to codebase"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
):
    client = _get_client()
    run_paths, decisions, verification, _ = run_verify(path, client, run_id=run_id)
    console.print(f"Run: {run_paths.root}")
    for result in verification:
        console.print(f"{result.name} exit {result.exit_code}")
    for decision in decisions:
        console.print(f"{decision.id}: {decision.status} - {decision.reason}")


@app.command()
def report(
    path: Path = typer.Argument(..., help="Path to codebase"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
):
    client = _get_client()
    run_paths = run_report(path, client, run_id=run_id)
    console.print(f"Report written: {run_paths.report}")


@app.command(name="run")
def run_all(
    path: Path = typer.Argument(..., help="Path to codebase"),
    run_id: Optional[str] = typer.Option(None, "--run-id"),
    autofix: bool = typer.Option(False, "--autofix"),
    heuristic: bool = typer.Option(False, "--heuristic"),
    baseline: bool = typer.Option(True, "--baseline/--no-baseline"),
    reattack: bool = typer.Option(True, "--reattack/--no-reattack"),
):
    client = _get_client()
    run_paths = run_pipeline(
        path,
        client,
        run_id=run_id,
        autofix=autofix,
        use_heuristics=heuristic or not client.available,
        baseline=baseline,
        reattack=reattack,
    )
    console.print(f"Run complete: {run_paths.root}")
    console.print(f"Report: {run_paths.report}")
