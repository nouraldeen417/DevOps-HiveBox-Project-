# Local Testing Runbook

The full local workflow, start to finish — spinning up a clean cluster,
installing everything, and tearing it down again. **Order matters**:
namespace, TLS, and secrets must exist *before* ArgoCD's first sync, or the
app pods will fail with `CreateContainerConfigError`/`Secret Not Found` the
moment ArgoCD tries to deploy them (see `docs/gitops.md`'s Operational Note
— this is that exact timing issue, made concrete as a runbook).

## 1. Start the cluster
```bash
kind create cluster --config k8s/kind-config.yaml
```

## 2. Install cluster tooling via Ansible
```bash
cd Ansible/
ansible-playbook -i inventory/hosts.ini install.yml
cd ..
```
Installs Nginx Ingress, Prometheus/Grafana, Loki, and ArgoCD — see
`docs/ansible.md`.

## 3. Pre-requisites: namespace, TLS, and secrets

Everything ArgoCD will expect to already exist, created manually so nothing
sensitive goes through Git:

```bash
# Application namespace
kubectl create namespace hivebox

# Self-signed TLS cert covering localhost + hivebox.local
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:hivebox.local,DNS:*.local,IP:127.0.0.1"

kubectl create secret tls hivebox-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n hivebox

# MinIO credentials (same secret referenced in docs/helm.md and docs/kustomize.md)
kubectl create secret generic minio-credentials \
  --from-literal=username='minioadmin' \
  --from-literal=password='minioadmin' \
  -n hivebox
```

The `hivebox-tls` secret name matches `ingress.tlsSecret` in the Helm
chart's `values.yaml`; `minio-credentials` matches what both the app
Deployment and the Kustomize-deployed MinIO instance expect (see
`docs/helm.md`).

## 4. Stateful dependencies (Kustomize)
```bash
kubectl apply -k k8s/infrastructure/overlays/local/
```
Deploys Valkey + MinIO — see `docs/kustomize.md`.

## 5. Hand off to GitOps
```bash
kubectl apply -f gitops/hivebox-application.yaml
kubectl get pods -n hivebox -w
```
From here, ArgoCD takes over — pulls the chart from `main`, syncs it into
`hivebox`, and keeps it self-healing (see `docs/gitops.md`'s Sync Policy
section).

Optional: a throwaway debug pod for testing in-cluster connectivity to app
services:
```bash
kubectl run debug \
  --image=curlimages/curl \
  --rm -it \
  --restart=Never \
  -n hivebox \
  -- sh
```

## 6. Grafana dashboards
```bash
kubectl apply -k dashboards/
```
Applies the Grafana dashboard ConfigMaps documented in `docs/kustomize.md`
— note this lives in its own top-level `dashboards/` directory, separate
from `k8s/infrastructure/`.

## 7. Access the UIs

```bash
# ArgoCD — get the auto-generated admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
kubectl port-forward svc/argocd-server 8080:80 -n argocd
# → http://localhost:8080, user: admin

# Grafana
kubectl port-forward svc/monitoring-stack-grafana 3000:80 -n monitoring
# → http://localhost:3000, user: admin / password: admin (see docs/ansible.md note on this being hardcoded)
```

## 8. Tear down at end of day
```bash
kind delete cluster
```
Guarantees the next run starts from a fully clean state.