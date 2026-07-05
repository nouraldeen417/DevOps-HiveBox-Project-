# Kustomize Infrastructure + Local KIND Cluster

Deploys the app's direct infrastructure dependencies (Valkey, MinIO) at
`k8s/infrastructure/`. Kept separate from the Helm chart (which is scoped
only to the app itself — see [`docs/helm.md`](./helm.md)) rather than as
part of any umbrella chart. This file also covers the KIND config used to
run everything locally (`k8s/kind-config.yaml`), since it's the cluster
these manifests target.

## Layout

```
k8s/infrastructure/
├── base/
│   ├── kustomization.yaml     → references valkey/{deployment,service}.yaml,
│   │                             minio/{deployment,service}.yaml
│   ├── valkey/
│   └── minio/
└── overlays/
    └── local/
        └── kustomization.yaml → references ../../base   (active overlay)
```

A simple base + overlay structure — currently the overlay just points back
at base with no patches, which is fine for a single-environment setup but
worth knowing if a second environment (e.g. staging) gets added later, since
that's where overlay patches would start doing actual work.

## Valkey

- `Deployment`: namespace `hivebox`, 1 replica, `valkey/valkey:8`, non-root
  pod + container security context (`runAsNonRoot`, `runAsUser: 1000`,
  `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`).
  Requests `100m`/`64Mi`, limits `200m`/`128Mi`.
- `Service`: ClusterIP, port `6379`.
- No persistent volume — Valkey here is pure cache, so this is expected and
  fine (losing cache on restart just means the next `/temperature` call
  re-fetches live).

## MinIO

- `Deployment`: namespace `hivebox`, 1 replica, `minio/minio:latest`, runs
  `server /data`, same non-root security posture as Valkey. Requests
  `100m`/`128Mi`, limits `300m`/`256Mi`. Reads `MINIO_ACCESS_KEY` /
  `MINIO_SECRET_KEY` from the same `minio-credentials` Secret used by the
  Helm-deployed app (see [`docs/helm.md`](./helm.md) for the manual
  creation command — only needs to be created once per namespace).
- `Service`: ClusterIP, port `9000`.


## Grafana Dashboards (auto-loaded via Kustomize + sidecar)

Lives in its own top-level `dashboards/` directory (separate from
`k8s/infrastructure/`) — applied with `kubectl apply -k dashboards/` (see
`docs/gitops.md`'s local testing cheat sheet).

```yaml
# dashboards/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: monitoring

configMapGenerator:
  - name: grafana-dashboard-hivebox-app
    files:
      - ./app-dashboard.json
    options:
      labels:
        grafana_dashboard: "1"

  - name: grafana-dashboard-k8s-cluster
    files:
      - ./k8s-dashboard.json
    options:
      labels:
        grafana_dashboard: "1"

generatorOptions:
  disableNameSuffixHash: true
```

Turns the two dashboard JSON files (HiveBox app dashboard, Kubernetes
cluster dashboard) into ConfigMaps, each labeled `grafana_dashboard: "1"`.
This label is what makes them get picked up automatically — Grafana's
sidecar (enabled in the `monitoring` Ansible role's values template,
`sidecar.dashboards.label: grafana_dashboard`, `searchNamespace: ALL`)
watches for ConfigMaps carrying that exact label across the cluster and
loads them into Grafana without any manual import step.

Two things worth understanding about this file specifically:
- **`namespace: monitoring`** — these ConfigMaps must land in the same
  namespace the sidecar is actually watching (or in any namespace, since
  the sidecar's `searchNamespace` is set to `ALL` — but matching the
  monitoring stack's own namespace here is still the clearer convention).
- **`disableNameSuffixHash: true`** — normally Kustomize appends a content
  hash to generated ConfigMap names (e.g. `grafana-dashboard-hivebox-app-a1b2c3`)
  so any change forces a new object and a rolling update. That's disabled
  here on purpose: the sidecar discovers dashboards by **label**, not by a
  specific ConfigMap name, so a stable name avoids unnecessary object churn
  in the GitOps diff on every sync, at the cost of Kubernetes not
  automatically forcing anything to "notice" a content change — the sidecar
  is what's responsible for re-polling and picking up edits instead.

## Namespace Coupling (implicit, not enforced)

Every manifest here hardcodes the `hivebox` namespace, and the Helm chart's
`config.valkeyHost: valkey` / `config.minioEndpoint: minio:9000` are plain
short service names — which only resolve correctly if the Helm release is
installed into that **same** `hivebox` namespace. Nothing at the chart or
Kustomize level enforces this; it's a manual convention to get right at
deploy time, not something that would fail loudly if missed until pods
can't resolve Valkey/MinIO.

## KIND Cluster (`kind-config.yaml`)

Local Kubernetes cluster used to run all of the above during development
and CI e2e testing.

- Single control-plane node.
- Node is labeled `ingress-ready=true` via a `kubeadmConfigPatches` init
  patch — this is what allows Ingress-Nginx to actually schedule and serve
  from this node.
- `extraPortMappings` bind container ports `80` and `443` to the same ports
  on the host machine, so the Ingress is reachable directly at
  `http://hivebox.local` / `https://hivebox.local` from outside the KIND
  container, without any `kubectl port-forward` needed.

### Running it locally
```bash
kind create cluster --config k8s/kind-config.yaml

# Deploy infra (Valkey + MinIO)
kubectl apply -k k8s/infrastructure/overlays/local/

# Create the shared secret before installing the Helm release
kubectl create secret generic minio-credentials \
  --namespace hivebox \
  --from-literal=username=<minio-access-key> \
  --from-literal=password=<minio-secret-key>

# Then install/upgrade the Helm chart (app only) into the same namespace
helm upgrade --install hivebox k8s/app/helm/hivebox -n hivebox
```