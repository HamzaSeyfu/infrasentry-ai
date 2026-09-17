from __future__ import annotations

import json

from typer.testing import CliRunner

from infrasentry.cli import app

runner = CliRunner()


def test_investigate_json_file(tmp_path) -> None:
    incident_file = tmp_path / "incident.json"
    incident_file.write_text(
        json.dumps(
            {
                "incident": "API cannot reach database",
                "evidence": [
                    {
                        "key": "dns_resolution",
                        "status": "fail",
                        "summary": "Database name does not resolve",
                        "details": {"hostname": "db.internal"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["investigate", str(incident_file), "--json"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["incident"] == "API cannot reach database"
    assert report["diagnosis"]["title"] == "DNS resolution failure"
    assert report["evidence"][0]["details"]["hostname"] == "db.internal"


def test_investigate_rejects_invalid_evidence_status(tmp_path) -> None:
    incident_file = tmp_path / "invalid.json"
    incident_file.write_text(
        json.dumps(
            {
                "incident": "Broken application",
                "evidence": [
                    {
                        "key": "pod_status",
                        "status": "probably",
                        "summary": "Ambiguous state",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["investigate", str(incident_file)])

    assert result.exit_code == 2
    assert "Invalid incident file" in result.stderr


def test_investigate_rejects_malformed_json(tmp_path) -> None:
    incident_file = tmp_path / "broken.json"
    incident_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(app, ["investigate", str(incident_file)])

    assert result.exit_code == 2
    assert "Invalid incident file" in result.stderr
