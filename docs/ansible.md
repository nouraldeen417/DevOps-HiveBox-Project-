# K8s Cluster Setup — Ansible Playbooks

Ansible project to prepare, verify, and install a full Kubernetes tooling stack.

## What it installs

| Component | Namespace | Install method | Purpose |
|---|---|---|---|
| **Nginx Ingress** | `ingress-nginx` | Raw manifest (`kubernetes.core.k8s`) | Ingress controller |
| **kube-prometheus-stack** | `monitoring` | Helm | Prometheus + Grafana + Alertmanager |
| **Loki Stack** | `monitoring` | Helm | Log aggregation (Loki + Promtail) |
| **Argo CD** | `argocd` | Helm | GitOps continuous delivery |

> Nginx Ingress is installed via a static, KIND-specific manifest applied
> directly, **not** via its Helm chart — the Helm chart doesn't reliably
> deploy on KIND (its admission-webhook job frequently fails to reach the
> API server in time). Uninstall mirrors this: it removes the same manifest
> rather than calling `helm uninstall`.

---

## Project Structure

```
k8s-ansible/
├── ansible.cfg                # Ansible settings
├── requirements.yml           # Galaxy collections
├── install.yml                # Main install playbook
├── uninstall.yml              # Full uninstall playbook
├── group_vars/
│   └── all.yml                # ← ALL variables live here (feature flags only)
├── inventory/
│   └── hosts.ini               # Your cluster hosts
└── roles/
    ├── cluster-verification/   # Cluster reachability + node health checks
    ├── helm/                   # Helm binary install/remove
    ├── nginx-ingress/          # Nginx Ingress Controller (raw manifest)
    ├── monitoring/             # kube-prometheus-stack
    ├── loki/                   # Loki + Promtail
    └── argo/                   # Argo CD
```

---

## Quick Start

### 1. Install required Ansible collections
```bash
ansible-galaxy collection install -r requirements.yml
```

### 2. Edit your inventory
```bash
# inventory/hosts.ini
# Set the IP/hostname and SSH user of your master node
# (for local KIND use, this stays as localhost under kind_control_plane)
```

### 3. Edit variables (optional)
```bash
# group_vars/all.yml
# Toggle components on/off
```

### 4. Run the install
```bash
ansible-playbook -i inventory/hosts.ini install.yml
```

Both `install.yml` and `uninstall.yml` run against `hosts: kind_control_plane`
(resolved to `localhost` in `inventory/hosts.ini`).

---

## Feature Flags

All flags are in `group_vars/all.yml`. You can also pass them at runtime with `-e`:

```bash
# Install everything (default)
ansible-playbook install.yml

# Skip monitoring and Argo CD
ansible-playbook install.yml -e "install_monitoring=false install_loki=false install_argo=false"

# Only install Helm and Nginx Ingress
ansible-playbook install.yml \
  -e "install_monitoring=false install_loki=false install_argo=false"

# Only run cluster verification (nothing installed)
ansible-playbook install.yml \
  -e "install_helm=false install_nginx_ingress=false install_monitoring=false install_loki=false install_argo=false"
```

---

## Uninstall

Components are removed in reverse order: Argo → Loki → Monitoring → Nginx → Helm.

```bash
# Remove everything
ansible-playbook uninstall.yml

# Remove only Argo CD
ansible-playbook uninstall.yml \
  -e "install_argo=true install_loki=false install_monitoring=false install_nginx_ingress=false install_helm=false"

# Remove monitoring stack (Prometheus + Grafana + Loki)
ansible-playbook uninstall.yml \
  -e "install_monitoring=true install_loki=true install_argo=false install_nginx_ingress=false install_helm=false"
```

---

## Access the UIs

After install, use `kubectl port-forward` to reach the UIs locally:

```bash
# Grafana (user: admin, password: admin — see note below)
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring

# Argo CD (user: admin, password: printed at end of install)
kubectl port-forward svc/argo-cd-server 8080:80 -n argocd

# Prometheus
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

> **Grafana admin password is currently hardcoded** to `admin` in
> `roles/monitoring/templates/kube-prometheus-values.yml.j2` — it is **not**
> yet exposed as a variable. Change it directly in that template (or promote
> it to a `group_vars/all.yml` variable) if you need something other than
> the default.

---

## Key Variables (`group_vars/all.yml`)

Currently, only feature-flag toggles exist here:

| Variable | Default | Description |
|---|---|---|
| `install_helm` | `true` | Install Helm binary |
| `install_nginx_ingress` | `true` | Install Nginx Ingress Controller |
| `install_monitoring` | `true` | Install Prometheus + Grafana |
| `install_loki` | `true` | Install Loki + Promtail |
| `install_argo` | `true` | Install Argo CD |

---

## Cluster Verification

The `cluster-verification` role always runs first and checks:
- The cluster's API is reachable (`kubectl`/kubeconfig resolves and responds)
- The cluster has at least one node

## Note on Grafana/Loki Datasource

The `monitoring` role runs before `loki` in the install order. Grafana's
`additionalDataSources` entry for Loki is added regardless of whether Loki
is actually up yet — this doesn't cause an error, since Grafana only
registers the datasource URL at that point and doesn't validate connectivity
until it's queried. The datasource-conflict issue this setup previously hit
(Grafana erroring over two datasources both marked default) is fixed via
`loki.isDefault: false` in the `loki` role's Helm values — that fix is
independent of install order.