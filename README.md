# Visitor Counter Web Application (Flask + Redis)

A learning project demonstrating containerization, Kubernetes deployment, self-healing, horizontal autoscaling, a simulated hybrid deployment, and cost optimization.

## Architecture

```text
Browser
   |
NodePort / Cloud Load Balancer
   |
Kubernetes Service
   |
Flask Pods (2 to 6 replicas) ---- Redis Service ---- Redis Pod
   |
/health and /ready probes

Separate environment:
Private/local Kubernetes cluster <---- application image/manifests ----> Public/simulated cluster
```

## Requirements
- Python 3.12 (only needed for local development)
- Docker Desktop with Docker Compose
- Kubernetes cluster (Docker Desktop Kubernetes, Minikube, or kind)
- `kubectl`
- Metrics Server installed for HPA CPU metrics

## Run locally with Docker Compose
```bash
docker compose up --build
```
Open http://localhost:5000. Refresh the page to increase the visitor count.
Stop:
```bash
docker compose down
```

## Build and deploy to Kubernetes
Build the image:
```bash
docker build -t visitor-counter:1.0 .
```
For Minikube, load the image:
```bash
minikube image load visitor-counter:1.0
```
For kind, load the image:
```bash
kind load docker-image visitor-counter:1.0
```
Apply manifests:
```bash
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/web.yaml
kubectl get pods,services
```
Open the app:
- Minikube: `minikube service visitor-web`
- Docker Desktop: http://localhost:30080 (if NodePort is exposed by your setup)

## Demonstrate self-healing
```bash
kubectl get pods
kubectl delete pod <one-visitor-web-pod-name>
kubectl get pods -w
```
Record the deleted Pod and its replacement in screenshots. Kubernetes Deployment should restore the desired replica count.

## Configure and test HPA
Metrics Server must be installed and working:
```bash
kubectl top nodes
kubectl top pods
kubectl apply -f k8s/hpa.yaml
kubectl get hpa
```
Generate load from another terminal (requires `hey`):
```bash
hey -z 3m -c 50 http://<CLUSTER-IP-OR-NODE-IP>:30080/
```
Watch scaling:
```bash
kubectl get hpa -w
kubectl get deployment visitor-web -w
```
The HPA target is 50% CPU, with a minimum of 2 and maximum of 6 replicas. Actual scaling depends on CPU usage, Metrics Server, available capacity and workload. Save actual output/screenshots; do not assume it will always reach 6.

## Hybrid deployment demonstration (two simulated environments)
This is a simulation unless you have a real private cluster and public cloud account. Create two independent local clusters (for example, two kind clusters):
```bash
kind create cluster --name private-demo
kind create cluster --name public-demo
kind load docker-image visitor-counter:1.0 --name private-demo
kind load docker-image visitor-counter:1.0 --name public-demo
```
Deploy the same manifests to both contexts:
```bash
kubectl --context kind-private-demo apply -f k8s/
kubectl --context kind-public-demo apply -f k8s/
```
Check each:
```bash
kubectl --context kind-private-demo get pods
kubectl --context kind-public-demo get pods
```
Failover simulation: stop or delete the private demo cluster:
```bash
kind delete cluster --name private-demo
```
Then verify the public-demo cluster still runs:
```bash
kubectl --context kind-public-demo get pods
```
This demonstrates service continuity in a second environment, but it is not automatic production failover. Real failover also needs replicated data, health-based DNS/load balancing, secrets/network configuration and tested recovery procedures.

## Cost optimization techniques
1. Multi-stage/small base image and no-cache pip installation reduce container image size.
2. CPU/memory requests and limits right-size resource allocation.
3. HPA scales replicas between 2 and 6 based on CPU demand.
4. Remove unused clusters, disks, load balancers and idle resources after testing.
5. Use budget alerts and monitoring; select lower-cost storage tiers for old backups.

Record measured values:
| Metric | Before | After |
|---|---:|---:|
| Docker image size | Measure with `docker image ls` | Measure after rebuild |
| Web replicas during idle | Record actual value | HPA minimum: 2 |
| CPU/memory allocation | Record old settings | Requests: 100m CPU, 128Mi; limits: 500m CPU, 256Mi |
| Monthly cloud cost | From provider calculator/bill | From provider calculator/bill |

Do not enter invented measurements. Image size and cloud cost depend on the environment and usage.

## Screenshots to capture
1. `docker compose ps` and browser page running locally.
2. `kubectl get pods,svc` showing Redis and two web replicas.
3. Pod deletion and replacement (`kubectl get pods -w`).
4. `kubectl get hpa` and deployment replica count during load.
5. Both cluster contexts running, then public cluster after private cluster is stopped.
6. Docker image size and cost comparison evidence.

## Important notes
- Redis in this demonstration uses one replica and is not highly available. For production, use managed Redis or a properly configured highly available Redis deployment.
- The visitor count is stored in Redis. The sample Redis Deployment has no persistent volume; configure persistent storage and backups if data durability is required.
- For a real public cloud deployment, push the image to a registry and replace `visitor-counter:1.0` with the full registry image path.
