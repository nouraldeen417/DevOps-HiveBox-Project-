# K8s Cluster Setup — Ansible Playbooks

Ansible project to prepare, verify, and install a full Kubernetes tooling stack.

## What it installs

| Component | Namespace | Purpose |
|---|---|---|
| **Nginx Ingress** | `ingress-nginx` | Ingress controller |
| **kube-prometheus-stack** | `monitoring` | Prometheus + Grafana + Alertmanager |
| **Loki Stack** | `monitoring` | Log aggregation (Loki + Promtail) |
| **Argo CD** | `argocd` | GitOps continuous delivery |

---

## Project Structure

```
k8s-ansible/
├── ansible.cfg               # Ansible settings
├── requirements.yml          # Galaxy collections
├── install.yml               # Main install playbook
├── uninstall.yml             # Full uninstall playbook
├── group_vars/
│   └── all.yml               # ← ALL variables live here
├── inventory/
│   └── hosts.ini             # Your cluster hosts
└── roles/
    ├── preflight/            # Cluster health checks
    ├── helm/                 # Helm binary install/remove
    ├── nginx-ingress/        # Nginx Ingress Controller
    ├── monitoring/           # kube-prometheus-stack
    ├── loki/                 # Loki + Promtail
    └── argo/                 # Argo CD
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
```

### 3. Edit variables (optional)
```bash
# group_vars/all.yml
# Toggle components on/off, change passwords, versions, etc.
```

### 4. Run the install
```bash
ansible-playbook -i inventory/hosts.ini install.yml
```

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

# Only run preflight checks (nothing installed)
ansible-playbook install.yml \
  -e "install_helm=false install_nginx_ingress=false install_monitoring=false install_loki=false install_argo=false"
```

---

## Uninstall

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
# Grafana (user: admin, password: from group_vars/all.yml → grafana_admin_password)
kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring

# Argo CD (user: admin, password: printed at end of install)
kubectl port-forward svc/argo-cd-server 8080:80 -n argocd

# Prometheus
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring
```

---

## Key Variables (`group_vars/all.yml`)

| Variable | Default | Description |
|---|---|---|
| `install_helm` | `true` | Install Helm binary |
| `install_nginx_ingress` | `true` | Install Nginx Ingress Controller |
| `install_monitoring` | `true` | Install Prometheus + Grafana |
| `install_loki` | `true` | Install Loki + Promtail |
| `install_argo` | `true` | Install Argo CD |
| `grafana_admin_password` | `admin` | **Change this in production!** |
| `helm_version` | `v3.14.4` | Helm binary version |
| `nginx_ingress_service_type` | `LoadBalancer` | `LoadBalancer` or `NodePort` |
| `prometheus_retention` | `7d` | How long Prometheus keeps data |
| `kubeconfig_path` | `/etc/kubernetes/admin.conf` | Path on master node |

---

## Preflight Checks

The `preflight` role always runs first and verifies:
- Required tools are present (`kubectl`, `curl`)
- kubeconfig exists
- Kubernetes version meets minimum (`1.26.0`)
- All nodes are in `Ready` state
- No `kube-system` pods are crashing