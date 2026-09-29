# Missing Secret scenario

This scenario reproduces a common Kubernetes configuration failure: a Pod references a Secret that does not exist.

## Reproduce

```bash
kubectl apply -f lab/manifests/missing-secret.yaml
kubectl get pods
kubectl describe pod -l app=infrasentry-secret-demo
kubectl get events --sort-by=.lastTimestamp
```

The Pod should remain unable to start and Kubernetes should report that `infrasentry-demo-secret` cannot be found. This gives InfraSentry deterministic Pod status and event evidence to inspect.

## Restore

```bash
kubectl create secret generic infrasentry-demo-secret --from-literal=token=demo
kubectl rollout status deployment/infrasentry-secret-demo
kubectl get pods -l app=infrasentry-secret-demo
```

## Reset

```bash
kubectl delete deployment infrasentry-secret-demo --ignore-not-found
kubectl delete secret infrasentry-demo-secret --ignore-not-found
```
