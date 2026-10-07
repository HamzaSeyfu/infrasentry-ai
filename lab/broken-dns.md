# Broken DNS failure scenario

This scenario isolates DNS resolution from application health. The baseline application and Service remain unchanged while two diagnostic Pods provide a control and a deliberately broken resolver.

## Reproduce

```bash
kubectl apply -f lab/manifests/healthy.yaml
kubectl apply -f lab/manifests/broken-dns.yaml
kubectl wait --for=condition=Ready pod/infrasentry-dns-control --timeout=60s
kubectl wait --for=condition=Ready pod/infrasentry-dns-broken --timeout=60s

kubectl exec infrasentry-dns-control -- nslookup infrasentry-echo.default.svc.cluster.local
kubectl exec infrasentry-dns-broken -- nslookup infrasentry-echo.default.svc.cluster.local
```

Expected evidence:

- the application Pods remain Ready;
- the Service and its endpoints remain healthy;
- the control Pod resolves the Service through cluster DNS;
- the broken Pod fails resolution because it uses the documentation-only address `192.0.2.53` as its resolver.

Using a per-Pod DNS configuration keeps the failure deterministic without damaging CoreDNS for the whole KIND cluster.

## Restore

Delete the broken diagnostic Pods and recreate them from the manifest whenever the scenario is needed again.

```bash
kubectl delete -f lab/manifests/broken-dns.yaml --ignore-not-found
```
