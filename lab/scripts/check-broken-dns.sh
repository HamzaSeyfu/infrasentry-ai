#!/usr/bin/env bash
# Integration smoke test: requires an existing KIND cluster.
set -euo pipefail

ns=infrasentry-lab
manifest=lab/manifests/broken-dns.yaml

cleanup() {
  kubectl delete -f "$manifest" --ignore-not-found >/dev/null || true
}
trap cleanup EXIT

kubectl apply -f lab/manifests/healthy.yaml
kubectl apply -f "$manifest"
kubectl -n "$ns" rollout status deployment/echo --timeout=120s
kubectl -n "$ns" wait --for=condition=Ready pod/infrasentry-dns-control --timeout=90s
kubectl -n "$ns" wait --for=condition=Ready pod/infrasentry-dns-broken --timeout=90s

host=echo.infrasentry-lab.svc.cluster.local
echo "Checking control DNS..."
kubectl -n "$ns" exec infrasentry-dns-control -- nslookup "$host" >/dev/null

echo "Checking intentionally broken DNS..."
if kubectl -n "$ns" exec infrasentry-dns-broken -- sh -c "timeout 8 nslookup $host" >/dev/null 2>&1; then
  echo "Broken Pod unexpectedly resolved the Service" >&2
  exit 1
fi

service_ip=$(kubectl -n "$ns" get service echo -o jsonpath='{.spec.clusterIP}')
if [ -z "$service_ip" ] || [ "$service_ip" = None ]; then
  echo "Service does not have a ClusterIP" >&2
  exit 1
fi
echo "Checking HTTP by IP from the broken DNS Pod..."
kubectl -n "$ns" exec infrasentry-dns-broken -- wget -T 5 -qO- "http://$service_ip:80" >/dev/null
kubectl -n "$ns" get endpointslices -l kubernetes.io/service-name=echo

echo "PASS: control DNS works, target DNS fails, target HTTP by IP works"
