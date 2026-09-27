# InfraSentry failure lab

This lab creates a small local Kubernetes environment for reproducing incidents without cloud services or paid APIs.

## Requirements

- Docker
- `kind`
- `kubectl`

## Create the cluster and healthy baseline

```bash
kind create cluster --name infrasentry --config lab/kind-config.yaml
kubectl apply -f lab/manifests/healthy.yaml
kubectl -n infrasentry-lab rollout status deployment/echo --timeout=90s
kubectl -n infrasentry-lab get pods,svc,endpointslices
```

The `echo` Deployment exposes a tiny HTTP endpoint through the `echo` Service. Wait for the Deployment to become available before injecting a failure.

## Reproduce a Service selector mismatch

```bash
kubectl apply -f lab/manifests/service-selector-mismatch.yaml
kubectl -n infrasentry-lab get service echo -o yaml
kubectl -n infrasentry-lab get endpointslices -l kubernetes.io/service-name=echo
```

The broken Service selects `app=echo-broken` while the healthy Pod is labelled `app=echo`. The workload therefore remains healthy, but the Service has no ready endpoints. This is a useful deterministic incident for InfraSentry's Service/EndpointSlice evidence collector.

Restore the healthy Service with:

```bash
kubectl apply -f lab/manifests/healthy.yaml
```

## Tear down

```bash
kind delete cluster --name infrasentry
```
