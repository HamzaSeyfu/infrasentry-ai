# InfraSentry AI

> Turn application outages into actionable diagnoses.

InfraSentry AI is a local-first incident investigation tool for Kubernetes applications. It collects technical evidence from the cluster, builds a structured incident report, and helps identify the most likely root cause and remediation.

## Why this project exists

When an application fails, engineers often have to inspect pod state, events, logs, services, DNS, configuration, and network connectivity before they can even form a useful hypothesis. InfraSentry aims to shorten that investigation loop.

The first versions deliberately avoid relying on an LLM for raw facts. Deterministic collectors gather evidence first. AI is added later as an optional reasoning and explanation layer.

## Project principles

- Local-first and usable without paid AI APIs
- Evidence before inference
- Reproducible failure scenarios
- Testable diagnoses
- Small, reviewable increments
- Useful without AI, better with AI

## Diagnose a JSON incident

InfraSentry can run its deterministic diagnosis engine against evidence stored in a JSON file:

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

Human-readable report:

```bash
infrasentry investigate incident.json
```

Machine-readable report, including the diagnosis:

```bash
infrasentry investigate incident.json --json
```

Input is validated before diagnosis. Evidence status must be `ok`, `fail`, or `unknown`.

## Initial roadmap

- v0.1: core evidence and diagnosis model
- v0.2: Kubernetes collector
- v0.3: reproducible incident scenarios
- v0.4: CLI and API
- v0.5: local RAG over runbooks
- v0.6: local agentic investigation through Ollama
- v0.7: observability integrations
- v0.8: evaluation and regression framework
- v1.0: documented end-to-end platform

See `ROADMAP.md` for the detailed plan.
