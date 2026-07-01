# RADAR 🎯 — Kubernetes Visual Dashboard

RADAR is a local Kubernetes dashboard that connects directly to your cluster via `kubectl`.
No cluster-side installation needed — it runs entirely on your laptop.

---

## What is RADAR?

RADAR gives you a live visual UI of everything running inside your Kubernetes cluster.
Instead of running multiple `kubectl` commands to understand what's happening,
RADAR shows you the full picture in one browser tab.

---

## What RADAR shows

| View | What you see |
|---|---|
| Topology | Visual graph of how all K8s resources connect — pods, service, ingress, configmap, hpa |
| Resources | Table of every resource in your namespace with live status |
| Timeline | Real-time cluster events — pod crashes, image pulls, restarts |
| Logs | Stream logs from any pod directly in the browser |

---

## Why we use RADAR

- Visually verify manifests are structurally correct before the image exists
- See exactly why a pod is failing without running multiple kubectl commands
- Confirm service → ingress → pod connections are wired correctly
- Monitor HPA scaling decisions in real time
- Stream pod logs without remembering pod names

---

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/skyhook-io/radar/main/install.sh | bash
```

Verify installation:

```bash
radar version
```

---

## Launch RADAR

```bash
kubectl radar
```

Opens your browser automatically at:

```
http://localhost:9280
```

---

## Filter to HiveBox namespace

Once RADAR opens, filter by namespace `hivebox` to see only HiveBox resources:

```
hivebox namespace
├── 2 pods          ← your app instances
├── service         ← stable internal name for pods
├── ingress         ← routes external HTTP traffic in
├── configmap       ← holds senseBox IDs env var
└── hpa             ← autoscales pods based on CPU
```

---

## How RADAR fits in the HiveBox workflow

```
kubectl apply -f k8s/
        ↓
kubectl radar
        ↓
Browser opens at localhost:9280
        ↓
Filter by hivebox namespace
        ↓
Topology view shows all resources connected
        ↓
Timeline view shows real-time events
        ↓
Logs view streams pod output directly
```

---

## RADAR vs kubectl commands

| Task | Without RADAR | With RADAR |
|---|---|---|
| See all resources | kubectl get all -n hivebox | One topology view |
| Check pod logs | kubectl logs pod/hivebox-xxx -n hivebox | Click pod in browser |
| Debug failing pod | kubectl describe pod/hivebox-xxx | Timeline view shows events |
| Monitor HPA | kubectl get hpa -n hivebox --watch | Live resources view |
| Verify ingress wiring | kubectl describe ingress -n hivebox | Topology graph |

---

## Notes

- RADAR is a local-only tool — it never runs in CI/CD
- It connects to whatever cluster `kubectl` is currently pointing to
- Use `kubectl config current-context` to verify you are pointed at `kind-hivebox`
- RADAR has no cluster-side components — uninstalling it leaves your cluster untouched

---

## For more Infromation check https://github.com/skyhook-io/radar
