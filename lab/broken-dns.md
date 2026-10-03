# Broken DNS scenario

This lab isolates DNS failure from application health. A control Pod uses normal Kubernetes DNS while a second diagnostic Pod uses an intentionally non-working resolver configuration. The application Pods and Service remain healthy, so the failed lookup is attributable to DNS rather than workload readiness or Service endpoints.

## Expected evidence

- application Pods remain Ready;
- the Service keeps ready endpoints;
- the control Pod resolves the Service name;
- the broken-DNS Pod cannot resolve the same Service name;
- no paid API or external cloud service is involved.

The manifest and reproduction commands belong in the same scenario change so the failure remains deterministic and reversible.
