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


def _discovery_api(
    discovery_api: client.DiscoveryV1Api | None,
) -> client.DiscoveryV1Api:
    if discovery_api is not None:
        return discovery_api
    load_kubernetes_config()
    return client.DiscoveryV1Api()


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


def collect_service_evidence(
    namespace: str,
    service_name: str,
    core_api: client.CoreV1Api | None = None,
    discovery_api: client.DiscoveryV1Api | None = None,
) -> list[Evidence]:
    """Inspect a Service and its EndpointSlices without guessing cluster state."""
    core_api = _core_api(core_api)
    discovery_api = _discovery_api(discovery_api)

    service = core_api.read_namespaced_service(name=service_name, namespace=namespace)
    selector = service.spec.selector or {}
    ports = [
        {
            "name": port.name,
            "port": port.port,
            "target_port": port.target_port,
            "protocol": port.protocol,
        }
        for port in (service.spec.ports or [])
    ]

    slices = discovery_api.list_namespaced_endpoint_slice(
        namespace=namespace,
        label_selector=f"kubernetes.io/service-name={service_name}",
    ).items or []

    endpoint_count = 0
    ready_endpoint_count = 0
    addresses: list[str] = []
    for endpoint_slice in slices:
        for endpoint in endpoint_slice.endpoints or []:
            endpoint_count += 1
            addresses.extend(endpoint.addresses or [])
            conditions = endpoint.conditions
            if conditions is None or conditions.ready is not False:
                ready_endpoint_count += 1

    service_status = EvidenceStatus.OK if selector and ports else EvidenceStatus.FAIL
    endpoint_status = (
        EvidenceStatus.OK if ready_endpoint_count > 0 else EvidenceStatus.FAIL
    )

    return [
        Evidence(
            key="service_configuration",
            status=service_status,
            summary=(
                f"Service {namespace}/{service_name} has a selector and {len(ports)} port(s)"
                if service_status == EvidenceStatus.OK
                else f"Service {namespace}/{service_name} is missing a selector or ports"
            ),
            details={
                "namespace": namespace,
                "service": service_name,
                "selector": selector,
                "ports": ports,
            },
        ),
        Evidence(
            key="service_endpoints",
            status=endpoint_status,
            summary=(
                f"Service {namespace}/{service_name} has {ready_endpoint_count} ready endpoint(s)"
                if ready_endpoint_count
                else f"Service {namespace}/{service_name} has no ready endpoints"
            ),
            details={
                "namespace": namespace,
                "service": service_name,
                "endpoint_slices": len(slices),
                "endpoint_count": endpoint_count,
                "ready_endpoint_count": ready_endpoint_count,
                "addresses": addresses,
            },
        ),
    ]
