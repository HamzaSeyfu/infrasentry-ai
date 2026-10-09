# NetworkPolicy failure scenario

This scenario keeps the application and Service healthy while ingress traffic is blocked by a NetworkPolicy. It uses the existing `echo` Deployment and Service in the `infrasentry-lab` namespace.

## Requirements

Use the cluster from [README.md](README.md), with **kind v0.25.0 or newer** and its default kindnet CNI. Kind v0.24.0 introduced NetworkPolicy enforcement, but v0.25.0 includes a related DNS fix. Older clusters or custom CNIs without NetworkPolicy enforcement can accept the policy without blocking traffic. Check `kind version` and recreate an old cluster if needed.

## Reproduce and compare

Start from the healthy baseline (restore it first if another lab scenario changed the Service):

```bash
kubectl apply -f lab/manifests/healthy.yaml
kubectl apply -f lab/manifests/network-debug.yaml
kubectl -n infrasentry-lab rollout status deployment/echo --timeout=90s
kubectl -n infrasentry-lab wait --for=condition=Ready pod/infrasentry-net-debug --timeout=90s
kubectl -n infrasentry-lab exec infrasentry-net-debug -- nslookup echo.infrasentry-lab.svc.cluster.local
kubectl -n infrasentry-lab exec infrasentry-net-debug -- wget -T 5 -qO- http://echo:80
```

The DNS lookup and HTTP request should **both succeed** before the fault is injected. Then:

```bash
kubectl apply -f lab/manifests/network-policy.yaml
kubectl -n infrasentry-lab get pods,svc
kubectl -n infrasentry-lab get endpointslices -l kubernetes.io/service-name=echo
kubectl -n infrasentry-lab exec infrasentry-net-debug -- nslookup echo.infrasentry-lab.svc.cluster.local
kubectl -n infrasentry-lab exec infrasentry-net-debug -- wget -T 5 -qO- http://echo:80
```

After a few seconds for policy propagation, the **last command must fail** while the application Pods remain Ready, the Service has endpoints, and DNS still resolves. If HTTP still succeeds, NetworkPolicy enforcement is not active; do not count the scenario as reproduced.

For an automated success/failure/recovery check against an existing cluster:

```bash
bash lab/scripts/check-network-policy.sh
```

## Restore

```bash
kubectl delete -f lab/manifests/network-policy.yaml --ignore-not-found
kubectl -n infrasentry-lab exec infrasentry-net-debug -- wget -T 5 -qO- http://echo:80
kubectl delete -f lab/manifests/network-debug.yaml --ignore-not-found
```

The HTTP request should succeed again after policy propagation. No paid services or LLM API are required.
