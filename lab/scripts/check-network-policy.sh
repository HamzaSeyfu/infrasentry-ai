#!/usr/bin/env bash
# Integration smoke test: requires an existing kind cluster with NetworkPolicy enforcement.
set -euo pipefail

ns=infrasentry-lab
policy=lab/manifests/network-policy.yaml

cleanup() {
  kubectl delete -f "$policy" --ignore-not-found >/dev/null || true
  kubectl delete -f lab/manifests/network-debug.yaml --ignore-not-found >/dev/null || true
}
trap cleanup EXIT

kubectl apply -f lab/manifests/healthy.yaml
kubectl apply -f lab/manifests/network-debug.yaml
kubectl -n "$ns" rollout status deployment/echo --timeout=120s
kubectl -n "$ns" wait --for=condition=Ready pod/infrasentry-net-debug --timeout=90s

probe() {
  kubectl -n "$ns" exec infrasentry-net-debug -- wget -T 3 -qO- http://echo:80 >/dev/null 2>&1
}

echo "Checking healthy baseline..."
probe || { echo "Baseline HTTP connectivity failed before policy injection" >&2; exit 1; }
kubectl -n "$ns" exec infrasentry-net-debug -- nslookup echo.infrasentry-lab.svc.cluster.local >/dev/null

echo "Injecting ingress-deny NetworkPolicy..."
kubectl apply -f "$policy"
blocked=false
for _ in $(seq 1 12); do
  if probe; then
    sleep 2
  else
    blocked=true
    break
  fi
done
if [ "$blocked" != true ]; then
  echo "HTTP still works: NetworkPolicy was not enforced" >&2
  exit 1
fi

kubectl -n "$ns" rollout status deployment/echo --timeout=30s
kubectl -n "$ns" exec infrasentry-net-debug -- nslookup echo.infrasentry-lab.svc.cluster.local >/dev/null
kubectl -n "$ns" get endpointslices -l kubernetes.io/service-name=echo

echo "Removing policy and checking recovery..."
kubectl delete -f "$policy"
recovered=false
for _ in $(seq 1 12); do
  if probe; then
    recovered=true
    break
  fi
  sleep 2
done
if [ "$recovered" != true ]; then
  echo "HTTP did not recover after deleting the policy" >&2
  exit 1
fi
echo "PASS: healthy -> blocked by NetworkPolicy -> recovered"
