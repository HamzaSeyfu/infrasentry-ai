# Broken DNS failure scenario

The `echo` Deployment and Service remain healthy in `infrasentry-lab`. Two diagnostic Pods use the same BusyBox image: a control Pod uses cluster DNS, while a broken Pod deliberately points to the documentation-only resolver address `192.0.2.53`. CoreDNS and other workloads are not modified.

## Reproduce

Use the existing KIND cluster described in [README.md](README.md). Restore the baseline first if another scenario changed the Service:

```bash
kubectl apply -f lab/manifests/healthy.yaml
kubectl apply -f lab/manifests/broken-dns.yaml
kubectl -n infrasentry-lab rollout status deployment/echo --timeout=90s
kubectl -n infrasentry-lab wait --for=condition=Ready pod/infrasentry-dns-control --timeout=90s
kubectl -n infrasentry-lab wait --for=condition=Ready pod/infrasentry-dns-broken --timeout=90s
kubectl -n infrasentry-lab get svc echo
kubectl -n infrasentry-lab get endpointslices -l kubernetes.io/service-name=echo
kubectl -n infrasentry-lab exec infrasentry-dns-control -- nslookup echo.infrasentry-lab.svc.cluster.local
kubectl -n infrasentry-lab exec infrasentry-dns-broken -- nslookup echo.infrasentry-lab.svc.cluster.local
```

The **control lookup succeeds**. The **broken lookup fails** because its resolver is unreachable; the per-Pod DNS timeout and attempts are bounded to avoid a long hang. The final command returning nonzero is expected.

To prove the network path and application still work, reach the Service **by ClusterIP** from the broken Pod:

```bash
SERVICE_IP=$(kubectl -n infrasentry-lab get svc echo -o jsonpath='{.spec.clusterIP}')
kubectl -n infrasentry-lab exec infrasentry-dns-broken -- wget -T 5 -qO- "http://${SERVICE_IP}:80"
```

The ClusterIP request should succeed. Together these observations distinguish DNS failure from a dead Pod, missing endpoints, or a network-policy block.

## Automated verification and cleanup

```bash
bash lab/scripts/check-broken-dns.sh
```

The script verifies successful control DNS, failed target DNS, and successful target HTTP by IP. It deletes the two diagnostic Pods when finished.

For manual cleanup:

```bash
kubectl delete -f lab/manifests/broken-dns.yaml --ignore-not-found
```

No paid API or cloud account is required.
