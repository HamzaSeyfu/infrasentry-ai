# NetworkPolicy scenario

This scenario keeps the demo Pods, Service, endpoints and cluster DNS healthy while a NetworkPolicy deliberately isolates the demo workload from the diagnostic client.

The cluster CNI must enforce Kubernetes NetworkPolicy. If the local KIND setup does not enforce policies, install a NetworkPolicy-capable CNI before running this scenario.

## Reproduce

```bash
kubectl apply -f lab/manifests/healthy.yaml
kubectl apply -f lab/manifests/network-policy.yaml
kubectl wait --for=condition=Ready pod/infrasentry-client --timeout=60s
kubectl get endpointslices -l kubernetes.io/service-name=infrasentry-demo
kubectl exec infrasentry-client -- nslookup infrasentry-demo.default.svc
kubectl exec infrasentry-client -- wget -T 3 -qO- http://infrasentry-demo.default.svc
```

With policy enforcement enabled, DNS still resolves and the Service still has ready endpoints, while the HTTP request from the client times out. That makes the failure distinguishable from DNS and Service-selector incidents.

## Restore

```bash
kubectl delete networkpolicy isolate-infrasentry-demo --ignore-not-found
kubectl exec infrasentry-client -- wget -T 3 -qO- http://infrasentry-demo.default.svc
```

## Reset

```bash
kubectl delete -f lab/manifests/network-policy.yaml --ignore-not-found
```
