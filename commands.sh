# /!/bin/bash
# This is an excellent, production-grade workflow. You have cleanly separated your platform infrastructure (Ansible), your stateful dependencies (Kustomize), your sensitive data (CLI Secrets), and your application lifecycle (ArgoCD/GitOps).

# Because ArgoCD is declarative and will try to deploy your application the second you apply its manifest, you **must** create the namespace, TLS certificates, and secrets *before* ArgoCD takes over. If you don't, ArgoCD will throw a "Secret Not Found" error and your pods will fail to start.

# Here is your exact, step-by-step local testing cheat sheet.

# 1. Start your local cluster (if destroyed)
kind create cluster --config k8s/kind-config.yaml

# 2. Run your master Ansible platform playbook
cd Ansible/
ansible-playbook -i inventory/hosts.ini install.yml

### **Phase 2: Pre-Requisites & Security**

# Create the destination namespace manually so you can inject your secure credentials *before* the application boots.

# 1. Create the application namespace
kubectl create namespace hivebox
cd .. 
# 2. Inject your local TLS Certificates
# (Run this from the directory where your tls.cert and tls.key are saved)
# Create a certificate that covers both localhost and hivebox.local
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:hivebox.local,DNS:*.local,IP:127.0.0.1"

# Create new secret with multi-host certificate
kubectl create secret tls hivebox-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n hivebox
# 3. Inject your Application Secrets manually
# (Replace with your actual keys for Django/DB/MinIO)
kubectl create secret generic minio-credentials \
  --from-literal=username='minioadmin' \
  --from-literal=password='minioadmin' \
  -n hivebox


### **Phase 3: Stateful Dependencies**

# Run Kustomize targeting your dependencies directory
# (Adjust the path to match where your kustomization.yaml lives)
kubectl apply -k k8s/infrastructure/overlays/local/

### **Phase 4: The GitOps Trigger**

# Apply your single ArgoCD Application manifest
kubectl apply -f gitops/hivebox-application.yaml

# Watch ArgoCD spin up your application in real-time
kubectl get pods -n hivebox -w
# run a debug pod if you want to test connectivity to your services from within the cluster
kubectl run debug \
  --image=curlimages/curl \
  --rm -it \
  --restart=Never \
  -n hivebox \
  -- sh


### **Phase 5: Accessing the Dashboards**
kubectl apply -k dashboards/ 
# Open your terminal multiplexer (or multiple tabs) to run these background port-forwards and access your UIs.

# **ArgoCD UI:**
# 1. Get the auto-generated ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

# 2. Port-forward the ArgoCD UI (Open http://localhost:8080)
kubectl port-forward svc/argocd-server 8080:80 -n argocd
# Username: admin
# Password: <from the command above>

# **Grafana UI:**

# Port-forward the Grafana UI (Open http://localhost:3000)
kubectl port-forward svc/monitoring-stack-grafana  3000:80 -n monitoring
# Username: admin
# Password: admin (as configured in your Ansible playbook)

### **Phase 6: The Quick Reset (End of Day)**

# When you are done testing and want to save CPU/RAM on your local machine, destroy the cluster completely. This guarantees your next test run is perfectly clean.

kind delete cluster
