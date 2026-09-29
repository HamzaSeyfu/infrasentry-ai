# NetworkPolicy failure scenario

This scenario isolates the network layer while keeping the application and Service healthy.

The baseline `infrasentry-echo` Pods stay Ready, the Service still has endpoints, and Kubernetes DNS still resolves the Service. A deny-all ingress NetworkPolicy then prevents the diagnostic Pod from reaching the application.

## Reproduce

```bash
kubectl apply -f lab/manifests/healthy.yaml
kubectl apply -f lab/manifests/network-policy.yaml
kubectl wait --for=condition=Ready pod/infrasentry-net-debug --timeout=60s

kubectl get pods
kubectl get service infrasentry-echo
kubectl get endpointslices -l kubernetes.io/service-name=infrasentry-echo
kubectl exec infrasentry-net-debug -- nslookup infrasentry-echo.default.svc.cluster.local
kubectl exec infrasentry-net-debug -- wget -T 3 -qO- http://infrasentry-echo:80
```

Expected evidence:

- application Pods remain Ready;
- the Service still exposes ready endpoints;
- DNS resolution succeeds;
- the HTTP request times out or fails because ingress traffic is denied.

This makes the incident useful for distinguishing service discovery failures from network-policy enforcement.

## Restore

```bash
kubectl delete networkpolicy deny-infrasentry-echo-ingress
kubectl exec infrasentry-net-debug -- wget -T 3 -qO- http://infrasentry-echo:80
```

## Reset

```bash
kubectl delete -f lab/manifests/network-policy.yaml --ignore-not-found
```

> The cluster network plugin must enforce Kubernetes NetworkPolicy for the denial to take effect.
