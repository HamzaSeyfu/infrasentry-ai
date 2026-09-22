from types import SimpleNamespace

from infrasentry.kubernetes_collector import (
    collect_container_logs,
    collect_pod_events,
    collect_pod_evidence,
)
from infrasentry.models import EvidenceStatus


class FakeCoreApi:
    def __init__(self, phase="Running", ready=True, restarts=0, events=None):
        self.pod = SimpleNamespace(
            status=SimpleNamespace(
                phase=phase,
                container_statuses=[
                    SimpleNamespace(ready=ready, restart_count=restarts),
                ],
            ),
            spec=SimpleNamespace(
                containers=[SimpleNamespace(name="api"), SimpleNamespace(name="sidecar")]
            ),
        )
        self.events = events or []

    def read_namespaced_pod(self, name, namespace):
        return self.pod

    def list_namespaced_event(self, namespace, field_selector):
        assert field_selector.startswith("involvedObject.name=")
        return SimpleNamespace(items=self.events)

    def read_namespaced_pod_log(
        self, name, namespace, container, tail_lines, timestamps
    ):
        return f"2026-09-20T08:00:00Z {container} started"


def test_collects_healthy_pod_evidence():
    evidence = collect_pod_evidence("default", "api", FakeCoreApi())

    assert [item.key for item in evidence] == [
        "pod_phase",
        "pod_readiness",
        "pod_restarts",
    ]
    assert all(item.status == EvidenceStatus.OK for item in evidence)
    assert evidence[2].details["restart_count"] == 0


def test_marks_unready_restarting_pod_as_failed():
    evidence = collect_pod_evidence(
        "production",
        "api-123",
        FakeCoreApi(phase="Running", ready=False, restarts=4),
    )

    by_key = {item.key: item for item in evidence}
    assert by_key["pod_phase"].status == EvidenceStatus.OK
    assert by_key["pod_readiness"].status == EvidenceStatus.FAIL
    assert by_key["pod_restarts"].status == EvidenceStatus.FAIL
    assert by_key["pod_restarts"].details["restart_count"] == 4


def test_marks_non_running_pod_phase_as_failed():
    evidence = collect_pod_evidence(
        "default",
        "worker",
        FakeCoreApi(phase="Pending", ready=False),
    )

    assert evidence[0].status == EvidenceStatus.FAIL
    assert evidence[0].details["phase"] == "Pending"


def test_collects_warning_events_as_failed_evidence():
    events = [
        SimpleNamespace(
            type="Warning",
            reason="BackOff",
            message="Back-off restarting failed container",
            count=3,
        ),
        SimpleNamespace(type="Normal", reason="Pulled", message="Image pulled", count=1),
    ]
    evidence = collect_pod_events("default", "api", FakeCoreApi(events=events))

    assert evidence.status == EvidenceStatus.FAIL
    assert evidence.details["events"][0]["reason"] == "BackOff"
    assert "1 warning" in evidence.summary


def test_collects_container_logs_with_a_bounded_tail():
    evidence = collect_container_logs("default", "api", FakeCoreApi(), tail_lines=25)

    assert evidence.status == EvidenceStatus.OK
    assert evidence.details["tail_lines"] == 25
    assert set(evidence.details["logs"]) == {"api", "sidecar"}
    assert "api started" in evidence.details["logs"]["api"]
