from __future__ import annotations

from kubernetes import client, config

from infrasentry.models import Evidence, EvidenceStatus


def load_kubernetes_config() -> None:
    """Load local kubeconfig, falling back to in-cluster credentials."""
    try:
        config.load_kube_config()
    except config.ConfigException:
        config.load_incluster_config()


def collect_pod_evidence(
    namespace: str,
    pod_name: str,
    core_api: client.CoreV1Api | None = None,
) -> list[Evidence]:
    """Collect deterministic health evidence for one Kubernetes Pod."""
    if core_api is None:
        load_kubernetes_config()
        core_api = client.CoreV1Api()

    pod = core_api.read_namespaced_pod(name=pod_name, namespace=namespace)
    statuses = pod.status.container_statuses or []
    restart_count = sum(status.restart_count or 0 for status in statuses)
    ready = bool(statuses) and all(bool(status.ready) for status in statuses)
    phase = pod.status.phase or "Unknown"

    phase_status = EvidenceStatus.OK if phase == "Running" else EvidenceStatus.FAIL
    readiness_status = EvidenceStatus.OK if ready else EvidenceStatus.FAIL
    restart_status = EvidenceStatus.OK if restart_count == 0 else EvidenceStatus.FAIL

    return [
        Evidence(
            key="pod_phase",
            status=phase_status,
            summary=f"Pod {namespace}/{pod_name} phase is {phase}",
            details={"namespace": namespace, "pod": pod_name, "phase": phase},
        ),
        Evidence(
            key="pod_readiness",
            status=readiness_status,
            summary=(
                f"All containers in {namespace}/{pod_name} are ready"
                if ready
                else f"One or more containers in {namespace}/{pod_name} are not ready"
            ),
            details={"namespace": namespace, "pod": pod_name, "ready": ready},
        ),
        Evidence(
            key="pod_restarts",
            status=restart_status,
            summary=f"Pod {namespace}/{pod_name} has {restart_count} container restart(s)",
            details={"namespace": namespace, "pod": pod_name, "restart_count": restart_count},
        ),
    ]
