from __future__ import annotations

from kubernetes import client, config

from infrasentry.models import Evidence, EvidenceStatus


def load_kubernetes_config() -> None:
    """Load local kubeconfig, falling back to in-cluster credentials."""
    try:
        config.load_kube_config()
    except config.ConfigException:
        config.load_incluster_config()


def _core_api(core_api: client.CoreV1Api | None) -> client.CoreV1Api:
    if core_api is not None:
        return core_api
    load_kubernetes_config()
    return client.CoreV1Api()


def collect_pod_evidence(
    namespace: str,
    pod_name: str,
    core_api: client.CoreV1Api | None = None,
) -> list[Evidence]:
    """Collect deterministic health evidence for one Kubernetes Pod."""
    core_api = _core_api(core_api)
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


def collect_pod_events(
    namespace: str,
    pod_name: str,
    core_api: client.CoreV1Api | None = None,
) -> Evidence:
    """Collect recent Kubernetes events attached to a Pod."""
    core_api = _core_api(core_api)
    response = core_api.list_namespaced_event(
        namespace=namespace,
        field_selector=f"involvedObject.name={pod_name}",
    )
    events = response.items or []
    warnings = [event for event in events if event.type == "Warning"]
    details = [
        {
            "type": event.type,
            "reason": event.reason,
            "message": event.message,
            "count": event.count or 1,
        }
        for event in events
    ]
    return Evidence(
        key="pod_events",
        status=EvidenceStatus.FAIL if warnings else EvidenceStatus.OK,
        summary=(
            f"Pod {namespace}/{pod_name} has {len(warnings)} warning event(s)"
            if warnings
            else f"Pod {namespace}/{pod_name} has no warning events"
        ),
        details={"namespace": namespace, "pod": pod_name, "events": details},
    )


def collect_container_logs(
    namespace: str,
    pod_name: str,
    core_api: client.CoreV1Api | None = None,
    tail_lines: int = 100,
) -> Evidence:
    """Collect bounded recent logs for every container in a Pod."""
    core_api = _core_api(core_api)
    pod = core_api.read_namespaced_pod(name=pod_name, namespace=namespace)
    containers = [container.name for container in (pod.spec.containers or [])]
    logs = {
        name: core_api.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=name,
            tail_lines=tail_lines,
            timestamps=True,
        )
        for name in containers
    }
    return Evidence(
        key="container_logs",
        status=EvidenceStatus.OK,
        summary=f"Collected recent logs from {len(containers)} container(s) in {namespace}/{pod_name}",
        details={
            "namespace": namespace,
            "pod": pod_name,
            "tail_lines": tail_lines,
            "logs": logs,
        },
    )
