from types import SimpleNamespace

from infrasentry.kubernetes_collector import collect_pod_evidence
from infrasentry.models import EvidenceStatus


class FakeCoreApi:
    def __init__(self, phase="Running", ready=True, restarts=0):
        self.pod = SimpleNamespace(
            status=SimpleNamespace(
                phase=phase,
                container_statuses=[
                    SimpleNamespace(ready=ready, restart_count=restarts),
                ],
            )
        )

    def read_namespaced_pod(self, name, namespace):
        return self.pod


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
