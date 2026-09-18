from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from infrasentry.models import Evidence, EvidenceStatus, IncidentInput, IncidentReport
from infrasentry.report import build_report

app = typer.Typer(help="Turn application outages into actionable diagnoses.")
console = Console()
error_console = Console(stderr=True)


def _print_report(report: IncidentReport) -> None:
    table = Table(title="InfraSentry evidence")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Observation")
    for item in report.evidence:
        table.add_row(item.key, item.status.value.upper(), item.summary)
    console.print(table)
    console.print(f"\n[bold]Diagnosis:[/bold] {report.diagnosis.title}")
    console.print(f"[bold]Root cause:[/bold] {report.diagnosis.probable_root_cause}")
    console.print(f"[bold]Remediation:[/bold] {report.diagnosis.remediation}")
    console.print(f"[bold]Confidence:[/bold] {report.diagnosis.confidence:.0%}")
    completeness = report.evidence_completeness
    console.print(
        f"[bold]Evidence completeness:[/bold] {completeness.score:.0%} "
        f"({completeness.observed}/{completeness.total} observed)"
    )


@app.command()
def investigate(
    incident_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="JSON file containing an incident and its evidence.",
        ),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print the complete incident report as JSON."),
    ] = False,
) -> None:
    """Diagnose an incident described by a JSON evidence file."""
    try:
        payload = json.loads(incident_file.read_text(encoding="utf-8"))
        incident = IncidentInput.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        error_console.print(f"[bold red]Invalid incident file:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc

    report = build_report(incident.incident, incident.evidence)
    if json_output:
        console.print_json(report.model_dump_json())
    else:
        _print_report(report)


@app.command()
def demo() -> None:
    """Run a deterministic DNS-failure demonstration."""
    evidence = [
        Evidence(
            key="target_service",
            status=EvidenceStatus.OK,
            summary="PostgreSQL Service exists",
        ),
        Evidence(
            key="dns_resolution",
            status=EvidenceStatus.FAIL,
            summary="Database hostname cannot be resolved",
            details={"hostname": "db.internal"},
        ),
        Evidence(
            key="tcp_connectivity",
            status=EvidenceStatus.FAIL,
            summary="Connection cannot be established because hostname lookup fails",
        ),
    ]
    _print_report(build_report("API cannot connect to PostgreSQL", evidence))


if __name__ == "__main__":
    app()
