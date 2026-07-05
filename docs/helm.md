# Helm Chart

Deploys the HiveBox app itself (Deployment, Service, Ingress, HPA, ConfigMap,
ServiceMonitor) — chart name **`hivebox`**, located at
`k8s/app/helm/hivebox/`.

**This is not an umbrella chart.** Helm's scope here is deliberately limited
to the app and its version — monitoring (Prometheus/Grafana/Loki) and Nginx
Ingress are installed separately via Ansible (see
[`docs/ansible.md`](./ansible.md)), specifically to keep Helm's dependency
surface small and avoid the complexity of managing unrelated infrastructure
through the same chart. Valkey/MinIO (the app's direct infra dependencies)
are deployed via Kustomize — see [`docs/kustomize.md`](./kustomize.md).

> Note: `k8s/app/app.old/` contains an earlier set of raw (non-Helm)
> manifests for the app, superseded by this chart. Worth confirming it can
> be deleted rather than left in the repo as dead weight.


## `values.yaml`

| Key | Default | Purpose |
|---|---|---|
| `replicaCount` | `2` | Initial pod count (HPA can scale beyond this) |
| `app.name` / `app.version` | `hivebox` / `0.0.2` | Injected into the ConfigMap as `APP_VERSION` |
| `image.repository` / `.tag` / `.pullPolicy` | GHCR image, `0.0.2`, `Always` | Container image |
| `service.port` / `.targetPort` | `80` / `5000` | Service exposes `80`, forwards to the app's `5000` |
| `ingress.host` / `.tlsSecret` | `hivebox.local` / `hivebox-tls` | Ingress hostname + TLS secret name (cert is provisioned outside Helm — see architecture notes) |
| `resources.requests` / `.limits` | `100m/128Mi` – `250m/256Mi` | Pod resource bounds |
| `hpa.minReplicas` / `.maxReplicas` / `.cpuUtilization` | `2` / `5` / `70%` | Autoscaling target |
| `config.senseboxIds`, `.valkeyHost`, `.valkeyPort`, `.minioEndpoint`, `.minioBucket` | — | App config, rendered into the `hivebox-config` ConfigMap |
| `metrics.enabled` | `true` | Toggles the `ServiceMonitor` |

## Templates

| Template | What it does |
|---|---|
| `deployment.yaml` | Runs the app container; non-root pod security context; env vars from `hivebox-config` ConfigMap plus MinIO credentials from a Secret (see below); liveness probe on `/version`, readiness probe on `/readyz` (`initialDelaySeconds: 60`, `failureThreshold: 10` — generous, to tolerate slow first cache population) |
| `service.yaml` | ClusterIP-style Service, `service.port` → `service.targetPort` |
| `ingress.yaml` | nginx ingress, forces TLS redirect, single host + TLS secret |
| `hpa.yaml` | `autoscaling/v2` HPA, scales on CPU utilization |
| `configmap.yaml` | Renders `config.*` values into env vars (`SENSEBOX_IDS`, `VALKEY_HOST`, `VALKEY_PORT`, `MINIO_ENDPOINT`, `MINIO_BUCKET`, `APP_VERSION`) |
| `servicemonitor.yaml` | Only rendered if `metrics.enabled`; tells Prometheus to scrape `/metrics` every `30s` |

## Secrets — Manual Creation (Intentional)

`MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` are **deliberately absent** from
`values.yaml` and every template. The Deployment pulls them from a Kubernetes
Secret (`minio-credentials`) via `secretKeyRef` instead — this Secret is
created **manually, out-of-band**, specifically so real MinIO credentials
never get committed to Git (values files, Helm releases, and ArgoCD's
Git-tracked state all stay secret-free).

Create it once, before installing the chart (or before ArgoCD syncs it):

```bash
kubectl create secret generic minio-credentials \
  --namespace hivebox \
  --from-literal=username=<minio-access-key> \
  --from-literal=password=<minio-secret-key>
```

This same Secret name/keys are also referenced by the Kustomize-deployed
MinIO instance itself (see `docs/kustomize.md`), so it only needs to be
created **once per namespace** — both the app and MinIO read from it.

> If this Secret doesn't exist before the pod starts, expect
> `CreateContainerConfigError` on the app pod.

## Known Issues (flagged — not corrected here)

These are noted for awareness only; not fixed in this doc pass since the
plan is to correct them manually:

- **Duplicate `securityContext` in `deployment.yaml`** — `runAsNonRoot` /
  `runAsUser` appear at both pod level and container level, with `# add this`
  comments suggesting a leftover duplicate rather than an intentional
  override.
- **`servicemonitor.yaml` selector is hardcoded to `app: hivebox`**, unlike
  every other template which uses `{{ .Release.Name }}`. If the chart is
  ever installed under a different release name, the ServiceMonitor's
  selector won't match the pod labels.