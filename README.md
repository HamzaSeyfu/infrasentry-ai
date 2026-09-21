# InfraSentry AI

**Local-first incident investigation for Kubernetes applications.**

InfraSentry AI collects technical evidence from a cluster, validates it, builds a structured incident report, and helps identify likely root causes and remediation paths. The project is designed around a simple principle: **facts first, inference second**.

## Why this project

Production incidents are rarely caused by a single obvious signal. Engineers often need to inspect pod state, events, logs, services, DNS, configuration, and network connectivity before they can form a useful hypothesis.

InfraSentry shortens that loop by turning raw operational signals into a reproducible diagnostic workflow.

## What is implemented

- Structured incident and evidence model
- Input validation for incident payloads
- Deterministic diagnosis engine
- Human-readable and JSON reports
- CLI workflow for local investigation
- Test suite for core diagnosis behavior
- Packaging through `pyproject.toml`
- Architecture prepared for Kubernetes evidence collection and AI-assisted reasoning

## Example

Given evidence such as:

```json
{
  "incident": "API cannot reach database",
  "evidence": [
    {
      "key": "dns_resolution",
      "status": "fail",
      "summary": "Database name does not resolve",
      "details": {"hostname": "db.internal"}
    }
  ]
}
```

Run:

```bash
infrasentry investigate incident.json
```

or request machine-readable output:

```bash
infrasentry investigate incident.json --json
```

## Engineering principles

- **Evidence before inference**: deterministic collectors establish facts before any AI layer is involved.
- **Local-first**: the core tool remains useful without paid external APIs.
- **Reproducibility**: incidents and failure scenarios should be replayable.
- **Testability**: diagnoses should be verifiable through explicit evidence.
- **Small reviewable increments**: each capability is designed to remain understandable and maintainable.

## Architecture direction

The project is evolving toward four layers:

1. **Collectors**: Kubernetes and infrastructure evidence gathering.
2. **Diagnosis engine**: deterministic rules and structured reasoning.
3. **Interfaces**: CLI and API.
4. **AI assistance**: local RAG and optional agentic reasoning over evidence and runbooks.

## Roadmap

- v0.1: core evidence and diagnosis model
- v0.2: Kubernetes collector
- v0.3: reproducible incident scenarios
- v0.4: CLI and API
- v0.5: local RAG over runbooks
- v0.6: local agentic investigation through Ollama
- v0.7: observability integrations
- v0.8: evaluation and regression framework
- v1.0: documented end-to-end platform

See [ROADMAP.md](ROADMAP.md) for the detailed plan.

## Stack

Python · Kubernetes · CLI tooling · testing · structured diagnostics · local AI/RAG roadmap

## Repository layout

- `src/` — application code
- `tests/` — automated tests
- `.github/` — repository automation
- `ROADMAP.md` — implementation roadmap
- `AUTONOMY.md` — project development constraints and operating principles

---

**Status:** active development. The current focus is building the deterministic investigation core before adding AI-assisted reasoning.
