# EKS Python Microservices Deployment Guide

Complete step-by-step guide to deploy video-to-audio converter microservices on AWS EKS.

## Project Overview

This application converts MP4 videos to MP3 audio files using microservices architecture:
- **Auth Service**: User authentication (PostgreSQL)
- **Gateway Service**: API gateway for uploads/downloads (MongoDB)
- **Converter Service**: Video to audio conversion (RabbitMQ)
- **Notification Service**: Email notifications

---

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **kubectl** installed
4. **Helm** installed
5. **Docker** installed
6. **Terraform** installed

---

## Part 1: Infrastructure Setup with Terraform

### Step 1: Configure AWS CLI

```bash
aws configure
# Enter AWS Access Key ID
# Enter AWS Secret Access Key
# Region: ap-south-1
# Output format: json
```

### Step 2: Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Wait 15-20 minutes for infrastructure creation.

**What gets created:**
- VPC with public/private subnets
- EKS cluster (Kubernetes 1.28)
- Node group (2x t3.small instances)
- IAM roles and policies
- Security groups with required ports
- ECR repositories for all services
- EBS CSI driver addon

### Step 3: Configure kubectl

```bash
aws eks update-kubeconfig --name microservices-cluster --region ap-south-1
kubectl get nodes
```

Verify nodes are in "Ready" state.

---

## Part 2: Deploy Databases and Message Queue

### Step 4: Deploy MongoDB

```bash
cd "d:\Projects of Devops\EKS-Python-Microservice-Project\microservices-python-app\Helm_charts\MongoDB"
helm install mongo .
```

Wait for pod to be ready:
```bash
kubectl get pods
```

**Note:** MongoDB automatically creates `mp3s` and `videos` databases with user `nasi`.

### Step 5: Deploy PostgreSQL

```bash
cd ..\Postgres
helm install postgres .
```

**Initialize Database:**

```bash
# Get pod name
kubectl get pods

# Copy init.sql to pod
kubectl cp init.sql postgres-deploy-<pod-id>:/tmp/init.sql

# Execute SQL
kubectl exec -it postgres-deploy-<pod-id> -- psql -U nasi -d authdb -f /tmp/init.sql
```

### Step 6: Deploy RabbitMQ

```bash
cd ..\RabbitMQ
helm install rabbitmq .
```

**Create Queues:**

```bash
kubectl exec -it rabbitmq-0 -- rabbitmqadmin declare queue name=video durable=true
kubectl exec -it rabbitmq-0 -- rabbitmqadmin declare queue name=mp3 durable=true
```

**Verify queues:**
```bash
kubectl exec -it rabbitmq-0 -- rabbitmqctl list_queues
```

---

## Part 3: Build and Push Docker Images

### Step 7: Login to ECR

```bash
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 754307962192.dkr.ecr.ap-south-1.amazonaws.com
```

### Step 8: Build and Push All Services

```bash
cd "d:\Projects of Devops\EKS-Python-Microservice-Project\microservices-python-app\src"

# Auth Service
cd auth-service
docker build -t auth-service .
docker tag auth-service:latest 754307962192.dkr.ecr.ap-south-1.amazonaws.com/auth-service:latest
docker push 754307962192.dkr.ecr.ap-south-1.amazonaws.com/auth-service:latest

# Gateway Service
cd ..\gateway-service
docker build -t gateway-service .
docker tag gateway-service:latest 754307962192.dkr.ecr.ap-south-1.amazonaws.com/gateway-service:latest
docker push 754307962192.dkr.ecr.ap-south-1.amazonaws.com/gateway-service:latest

# Converter Service
cd ..\converter-service
docker build -t converter-service .
docker tag converter-service:latest 754307962192.dkr.ecr.ap-south-1.amazonaws.com/converter-service:latest
docker push 754307962192.dkr.ecr.ap-south-1.amazonaws.com/converter-service:latest

# Notification Service
cd ..\notification-service
docker build -t notification-service .
docker tag notification-service:latest 754307962192.dkr.ecr.ap-south-1.amazonaws.com/notification-service:latest
docker push 754307962192.dkr.ecr.ap-south-1.amazonaws.com/notification-service:latest
```

---

## Part 4: Update Deployment Manifests

### Step 9: Update Image URLs

Update the `image:` field in these files with your ECR URLs:

**Files to update:**
- `src/auth-service/manifest/deployment.yaml`
- `src/gateway-service/manifest/gateway-deploy.yaml`
- `src/converter-service/manifest/converter-deploy.yaml`
- `src/notification-service/manifest/notification-deploy.yaml`

Change from:
```yaml
image: nasi101/gateway
```

To:
```yaml
image: 754307962192.dkr.ecr.ap-south-1.amazonaws.com/gateway-service:latest
```

### Step 10: Configure Email Notifications

**Setup Gmail App Password:**
1. Google Account → Security → 2-Step Verification (enable)
2. Search "App passwords" → Generate new
3. Copy 16-character password

**Encode credentials:**
```bash
echo -n "your-email@gmail.com" | base64
echo -n "your-app-password" | base64
```

**Update secret:**
Edit `src/notification-service/manifest/secret.yaml` with base64 encoded values.

---

## Part 5: Deploy Microservices

### Step 11: Deploy All Services

```bash
# Auth Service
cd "d:\Projects of Devops\EKS-Python-Microservice-Project\microservices-python-app\src\auth-service\manifest"
kubectl apply -f .

# Gateway Service
cd ..\..\gateway-service\manifest
kubectl apply -f .

# Converter Service
cd ..\..\converter-service\manifest
kubectl apply -f .

# Notification Service
cd ..\..\notification-service\manifest
kubectl apply -f .
```

### Step 12: Verify Deployment

```bash
kubectl get all
kubectl get pods
```

All pods should be in "Running" state.

---

## Part 6: Test the Application

### Step 13: Access the Application

Since nodes don't have public IPs, use port-forward:

```bash
kubectl port-forward svc/gateway 8080:8002
```

### Step 14: Test APIs

**Login:**
```bash
curl -X POST http://localhost:8080/login -u <email>:<password>
```

Copy JWT token from response.

**Upload Video:**
```bash
curl -X POST -F 'file=@d:\Projects of Devops\EKS-Python-Microservice-Project\microservices-python-app\assets\video.mp4' -H 'Authorization: Bearer <JWT-TOKEN>' http://localhost:8080/upload
```

Check email for file ID.

**Download MP3:**
```bash
curl --output video.mp3 -X GET -H 'Authorization: Bearer <JWT-TOKEN>' "http://localhost:8080/download?fid=<FILE-ID>"
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Pods in Pending State - "Too many pods"

**Problem:** `0/2 nodes are available: 2 Too many pods`

**Root Cause:** Not enough resources (CPU/Memory) on nodes to schedule all pods.

**Solutions:**

**Option 1: Scale Down Replicas (Quick Fix)**
```bash
kubectl scale deployment converter --replicas=2
kubectl scale deployment auth --replicas=1
kubectl scale deployment gateway --replicas=1
kubectl scale deployment notification --replicas=1
```

**Option 2: Increase Node Count (Recommended)**
```bash
# Update Terraform
cd terraform
# Edit terraform.tfvars: node_desired_size = 3
terraform apply
```

**Option 3: Use Larger Instance Type**
```bash
# Edit terraform.tfvars: node_instance_type = "t3.medium"
terraform apply
# Note: Requires node group recreation
```

**Option 4: Enable Cluster Autoscaler**
```bash
# Install cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Edit deployment to add cluster name
kubectl -n kube-system edit deployment cluster-autoscaler
# Add: --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/microservices-cluster
```

**Option 5: Reduce Resource Requests**

Add resource limits to deployments:
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

**Option 6: Use Spot Instances (Cost Optimization)**

Update node group in Terraform to use spot instances:
```hcl
capacity_type = "SPOT"
instance_types = ["t3.small", "t3a.small", "t2.small"]
```

---

#### Issue 2: RabbitMQ Queue Not Found

**Problem:** `pika.exceptions.ChannelClosedByBroker: (404, "NOT_FOUND - no queue 'mp3'")`

**Solution:**
```bash
kubectl exec -it rabbitmq-0 -- rabbitmqadmin declare queue name=video durable=true
kubectl exec -it rabbitmq-0 -- rabbitmqadmin declare queue name=mp3 durable=true
kubectl rollout restart deployment notification
kubectl rollout restart deployment converter
```

---

#### Issue 3: Cannot Access Services (No Public IP)

**Problem:** Nodes in private subnets have no public IPs.

**Solutions:**

**Option 1: Port Forward (Development)**
```bash
kubectl port-forward svc/gateway 8080:8002
# Access: http://localhost:8080
```

**Option 2: Create LoadBalancer Service**
```bash
# Change service type from NodePort to LoadBalancer
kubectl patch svc gateway -p '{"spec":{"type":"LoadBalancer"}}'
kubectl get svc gateway  # Get external DNS
```

**Option 3: Use Ingress Controller**
```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
helm install aws-load-balancer-controller eks/aws-load-balancer-controller -n kube-system
```

**Option 4: Deploy Nodes in Public Subnets**

Update Terraform `eks.tf`:
```hcl
subnet_ids = aws_subnet.public[*].id  # Instead of private
```

---

#### Issue 4: ECR Login Failed

**Problem:** `Error response from daemon: login attempt failed with status: 400 Bad Request`

**Solution:**
```bash
# Use CMD instead of PowerShell
cmd
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 754307962192.dkr.ecr.ap-south-1.amazonaws.com
```

---

#### Issue 5: Database Connection Failed

**Problem:** Pods can't connect to PostgreSQL/MongoDB

**Solutions:**

1. **Check service names match configmap:**
```bash
kubectl get svc
# Verify service names: mongodb, db (postgres)
```

2. **Check credentials:**
```bash
kubectl get configmap gateway-configmap -o yaml
kubectl get secret auth-secret -o yaml
```

3. **Test connection from pod:**
```bash
kubectl exec -it gateway-<pod-id> -- sh
ping mongodb
ping db
```

---

### General Troubleshooting Commands

**Check Pod Logs:**
```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous  # Previous crashed container
```

**Describe Pod:**
```bash
kubectl describe pod <pod-name>
```

**Check Events:**
```bash
kubectl get events --sort-by='.lastTimestamp'
kubectl get events --field-selector involvedObject.name=<pod-name>
```

**Restart Deployment:**
```bash
kubectl rollout restart deployment <deployment-name>
```

**Check Resource Usage:**
```bash
kubectl top nodes
kubectl top pods
```

**Check Services:**
```bash
kubectl get svc
kubectl describe svc <service-name>
```

**Check Node Capacity:**
```bash
kubectl describe nodes
```

---

## Cleanup

### Delete Kubernetes Resources
```bash
kubectl delete -f <manifest-folder>
helm uninstall mongo
helm uninstall postgres
helm uninstall rabbitmq
```

### Destroy Infrastructure
```bash
cd terraform
terraform destroy
```

---

## Important Notes

1. **Database Credentials:**
   - PostgreSQL: User: `nasi`, Password: `cnd2023`
   - MongoDB: User: `nasi`, Password: `nasi1234`

2. **Ports:**
   - Gateway: 30002
   - PostgreSQL: 30003
   - RabbitMQ: 30004
   - MongoDB: 30005
   - Auth: 30006

3. **Region:** ap-south-1 (Mumbai)

4. **Instance Type:** t3.small (2 nodes)

5. **No Public IPs:** Nodes are in private subnets, use `kubectl port-forward` for access

6. **Resource Constraints:** With t3.small nodes, scale down replicas:
   ```bash
   kubectl scale deployment converter --replicas=2
   kubectl scale deployment auth --replicas=1
   kubectl scale deployment gateway --replicas=1
   kubectl scale deployment notification --replicas=1
   ```

---

## Cost Estimate (ap-south-1)

- EKS Cluster: ~$73/month
- 2x t3.small nodes: ~$30/month
- NAT Gateways: ~$66/month
- EBS volumes: ~$4/month
- **Total: ~$173/month**

---

## Architecture

```
User → Gateway Service (NodePort 30002)
         ↓
    Auth Service (validates JWT)
         ↓
    MongoDB (stores videos/mp3s)
         ↓
    RabbitMQ (queues: video, mp3)
         ↓
    Converter Service (converts video to mp3)
         ↓
    Notification Service (sends email with file ID)
```

---

## Support

For issues:
1. Check pod logs
2. Verify all services are running
3. Check security groups
4. Verify database connections
5. Check RabbitMQ queues

---

**Deployment completed successfully!** 🎉
