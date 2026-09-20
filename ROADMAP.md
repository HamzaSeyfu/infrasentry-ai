# Roadmap

InfraSentry's goal is simple: turn an application outage into an actionable diagnosis.

## v0.1 — Core diagnosis engine

- [x] Define evidence and diagnosis domain models
- [x] Implement deterministic rule-based diagnosis
- [x] Add CLI demo command
- [x] Add unit tests
- [x] Add CI quality gate
- [x] Add JSON incident input
- [x] Add confidence scoring based on evidence completeness

## v0.2 — Kubernetes evidence collector

- [x] Kubernetes client integration
- [x] Pod status, restart count and readiness collection
- [x] Events and container logs
- [ ] Service/endpoints inspection
- [ ] DNS/connectivity checks

## v0.3 — Reproducible failure lab

- [ ] KIND demo cluster
- [ ] Healthy baseline application
- [ ] Broken DNS scenario
- [ ] Missing Secret scenario
- [ ] Service selector mismatch scenario
- [ ] NetworkPolicy scenario

## v0.4 — Interfaces

- [ ] Stable CLI investigation command
- [ ] FastAPI service
- [ ] Structured JSON reports

## v0.5 — Local knowledge

- [ ] Markdown runbook ingestion
- [ ] Local embeddings/vector retrieval
- [ ] Evidence-linked runbook suggestions

## v0.6 — Local AI reasoning

- [ ] Ollama provider
- [ ] Structured model outputs
- [ ] Tool-aware investigation planner
- [ ] No paid API required

## v0.7+ — Reliability

- [ ] Prometheus integration
- [ ] Evaluation dataset
- [ ] Regression testing for diagnoses
- [ ] Security-oriented incident scenarios
- [ ] End-to-end documentation
