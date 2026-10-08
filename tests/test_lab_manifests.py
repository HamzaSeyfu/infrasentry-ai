from pathlib import Path

import yaml



MANIFESTS = Path(__file__).resolve().parents[1] / "lab" / "manifests"


def load_resources(name: str) -> list[dict]:
    with (MANIFESTS / name).open(encoding="utf-8") as stream:
        return list(yaml.safe_load_all(stream))


def test_network_policy_targets_the_real_healthy_workload():
    baseline = load_resources("healthy.yaml")
    deployment = next(item for item in baseline if item["kind"] == "Deployment")
    service = next(item for item in baseline if item["kind"] == "Service")
    policy, = load_resources("network-policy.yaml")
    debug, = load_resources("network-debug.yaml")

    namespace = deployment["metadata"]["namespace"]
    app_labels = deployment["spec"]["template"]["metadata"]["labels"]
    service_selector = service["spec"]["selector"]
    policy_selector = policy["spec"]["podSelector"]["matchLabels"]

    assert namespace == "infrasentry-lab"
    assert service["metadata"]["namespace"] == namespace
    assert policy["metadata"]["namespace"] == namespace
    assert debug["metadata"]["namespace"] == namespace
    assert all(app_labels.get(key) == value for key, value in service_selector.items())
    assert all(app_labels.get(key) == value for key, value in policy_selector.items())
    assert policy["kind"] == "NetworkPolicy"
    assert policy["spec"]["policyTypes"] == ["Ingress"]
    assert policy["spec"]["ingress"] == []
    assert debug["metadata"]["labels"] != app_labels
