# GitOps — ArgoCD

ArgoCD manages continuous deployment of the **app only** (the Helm chart at
`k8s/app/helm/hivebox`) — it does not manage infrastructure (Valkey/MinIO,
deployed via Kustomize) or cluster tooling (monitoring, ingress, deployed
via Ansible — see `docs/ansible.md`). Those stay outside GitOps scope by
design, consistent with Helm's scope being limited to the app itself (see
`docs/helm.md`).

ArgoCD itself is installed into the `argocd` namespace via the Ansible
`argo` role.

## Application Manifest

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: hivebox
  namespace: argocd   # ArgoCD Applications must live in the argocd namespace
spec:
  project: default

  source:
    repoURL: 'https://github.com/nouraldeen417/DevOps-HiveBox-Project-.git'
    targetRevision: main
    path: k8s/app/helm/hivebox
    helm:
      valueFiles:
        - values.yaml

  destination:
    server: 'https://kubernetes.default.svc'   # the cluster ArgoCD itself runs on
    namespace: hivebox

  syncPolicy:
    automated:
      prune: true      # auto-delete resources removed from Git
      selfHeal: true    # auto-revert manual kubectl changes back to Git state
    syncOptions:
      - CreateNamespace=true
```

## What this does

- **Source:** watches the `main` branch of the repo, pointed at the Helm
  chart's path, reading `values.yaml` for configuration.
- **Destination:** deploys into the `hivebox` namespace on ArgoCD's own
  cluster (`https://kubernetes.default.svc` — the in-cluster API endpoint,
  used since ArgoCD is running on the same KIND cluster it's managing).
- **Sync policy — fully automated GitOps:**
  - `prune: true` — if a resource is removed from the chart/values in Git,
    ArgoCD deletes it from the cluster on the next sync.
  - `selfHeal: true` — if someone manually `kubectl edit`s a live resource,
    ArgoCD reverts it back to match Git on the next reconciliation loop.
    Combined, these two mean **Git is the only real source of truth** — any
    drift, in either direction, gets corrected automatically.
  - `CreateNamespace=true` — the `hivebox` namespace is created automatically
    on first sync if it doesn't already exist.

## Operational Note — Secret Timing

Because `selfHeal`/`prune` make this fully automated, ArgoCD will
happily sync and mark the Application `Synced` even if the app pods can't
actually start. Specifically: the `minio-credentials` Secret (see
`docs/helm.md`) is **not** part of the Helm chart and isn't managed by
ArgoCD — it must exist in the `hivebox` namespace *before* ArgoCD's first
sync, or the app pods will sit in `CreateContainerConfigError` while ArgoCD
itself reports the sync as successful (sync status and pod health are
separate signals here — worth checking pod health directly, not just sync
status, after a first deploy to a fresh namespace).

See [`docs/runbook.md`](./runbook.md) for the full local testing workflow,
start to finish.