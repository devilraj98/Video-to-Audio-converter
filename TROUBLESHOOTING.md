# Troubleshooting Guide

Complete troubleshooting guide for common issues encountered during deployment and operation of the EKS Python Microservices project.

---

## Table of Contents

1. [Infrastructure Issues](#infrastructure-issues)
2. [Kubernetes Issues](#kubernetes-issues)
3. [Database Issues](#database-issues)
4. [Application Issues](#application-issues)
5. [CI/CD Issues](#cicd-issues)
6. [Cleanup Issues](#cleanup-issues)

---

## Infrastructure Issues

### Issue 1: Terraform Apply Fails - ECR Permission Denied

**Error:**
```
Error: creating ECR Repository: AccessDeniedException
```

**Solution:**
Add ECR permissions to your IAM user:
```bash
# Attach policy via AWS CLI
aws iam attach-user-policy --user-name YOUR-USER --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
```

Or in AWS Console:
- IAM → Users → Your User → Add permissions → AmazonEC2ContainerRegistryFullAccess

---

### Issue 2: Kubernetes Version Mismatch

**Error:**
```
Error: Unsupported Kubernetes minor version update from 1.29 to 1.28
```

**Solution:**
Update Terraform to match current cluster version:
```bash
# Check current cluster version
aws eks describe-cluster --name microservices-cluster --region ap-south-1 --query 'cluster.version'

# Update terraform/variables.tf
# Change: default = "1.28" to default = "1.29"

terraform apply
```

---

### Issue 3: Node Group Creation Fails - AMI Not Supported

**Error:**
```
Error: Requested AMI for this version 1.28 is not supported
```

**Solution:**
Add explicit AMI type in `terraform/eks.tf`:
```hcl
resource "aws_eks_node_group" "main" {
  # ... other config
  ami_type = "AL2_x86_64"
}
```

---

## Kubernetes Issues

### Issue 4: Pods in Pending State - "Too many pods"

**Error:**
```
0/2 nodes are available: 2 Too many pods
```

**Solutions:**

**Option 1: Scale Down Replicas (Quick Fix)**
```bash
kubectl scale deployment converter --replicas=2
kubectl scale deployment auth --replicas=1
kubectl scale deployment gateway --replicas=1
kubectl scale deployment notification --replicas=1
```

**Option 2: Increase Node Count**
```bash
# Edit terraform/terraform.tfvars
node_desired_size = 3

# Apply changes
cd terraform
terraform apply
```

**Option 3: Use Larger Instance Type**
```bash
# Edit terraform/terraform.tfvars
node_instance_type = "t3.medium"

terraform apply
```

---

### Issue 5: kubectl Connection Failed

**Error:**
```
error: You must be logged in to the server (the server has asked for the client to provide credentials)
```

**Solution:**
```bash
# Update kubeconfig
aws eks update-kubeconfig --name microservices-cluster --region ap-south-1

# Verify connection
kubectl get nodes

# If still fails, check AWS credentials
aws sts get-caller-identity
```

---

### Issue 6: Pods CrashLoopBackOff

**Diagnosis:**
```bash
kubectl get pods
kubectl logs <pod-name>
kubectl describe pod <pod-name>
```

**Common Causes & Solutions:**

**A. Database Connection Failed**
```bash
# Check if database pods are running
kubectl get pods | grep -E "mongo|postgres"

# Verify connection strings in configmaps
kubectl get configmap gateway-configmap -o yaml
```

**B. Wrong Credentials**
```bash
# Update secrets
kubectl delete secret auth-secret
kubectl apply -f src/auth-service/manifest/secret.yaml

# Restart deployment
kubectl rollout restart deployment auth
```

---

### Issue 7: RabbitMQ Queue Not Found

**Error:**
```
pika.exceptions.ChannelClosedByBroker: (404, "NOT_FOUND - no queue 'mp3'")
```

**Solution:**
```bash
# Create missing queues
kubectl exec -it rabbitmq-0 -- rabbitmqadmin declare queue name=video durable=true
kubectl exec -it rabbitmq-0 -- rabbitmqadmin declare queue name=mp3 durable=true

# Verify queues exist
kubectl exec -it rabbitmq-0 -- rabbitmqctl list_queues

# Restart affected services
kubectl rollout restart deployment converter
kubectl rollout restart deployment notification
```

---

## Database Issues

### Issue 8: PostgreSQL Authentication Failed

**Error:**
```
psycopg2.OperationalError: FATAL: role "nasi" does not exist
```

**Solution:**
```bash
# Check PostgreSQL values
kubectl get configmap auth-configmap -o yaml
kubectl get secret auth-secret -o yaml

# Ensure credentials match in:
# 1. Helm_charts/Postgres/values.yaml
# 2. src/auth-service/manifest/configmap.yaml
# 3. src/auth-service/manifest/secret.yaml

# Redeploy PostgreSQL
helm uninstall postgres
cd Helm_charts/Postgres
helm install postgres .

# Reinitialize database
kubectl cp init.sql postgres-deploy-<pod-id>:/tmp/init.sql
kubectl exec -it postgres-deploy-<pod-id> -- psql -U YOUR-USER -d authdb -f /tmp/init.sql

# Restart auth service
kubectl rollout restart deployment auth
```

---

### Issue 9: MongoDB Authentication Failed

**Error:**
```
pymongo.errors.OperationFailure: Authentication failed
```

**Solution:**
```bash
# Check MongoDB credentials match in:
# 1. Helm_charts/MongoDB/values.yaml
# 2. src/gateway-service/manifest/configmap.yaml
# 3. src/converter-service/manifest/configmap.yaml

# Update configmaps with correct credentials
kubectl apply -f src/gateway-service/manifest/configmap.yaml
kubectl apply -f src/converter-service/manifest/configmap.yaml

# Restart services
kubectl rollout restart deployment gateway
kubectl rollout restart deployment converter
```

---

### Issue 10: Database Not Initialized

**Error:**
```
relation "auth_user" does not exist
```

**Solution:**
```bash
# Get PostgreSQL pod name
kubectl get pods | grep postgres

# Copy and execute init.sql
kubectl cp Helm_charts/Postgres/init.sql postgres-deploy-<pod-id>:/tmp/init.sql
kubectl exec -it postgres-deploy-<pod-id> -- psql -U YOUR-USER -d authdb -f /tmp/init.sql

# Verify table exists
kubectl exec -it postgres-deploy-<pod-id> -- psql -U YOUR-USER -d authdb -c "\dt"
```

---

## Application Issues

### Issue 11: Login Returns 500 Error

**Error:**
```
500 Internal Server Error
```

**Diagnosis:**
```bash
# Check auth service logs
kubectl logs -l app=auth --tail=50

# Check gateway service logs
kubectl logs -l app=gateway --tail=50
```

**Common Causes:**

**A. User Doesn't Exist**
```bash
# Check users in database
kubectl exec -it postgres-deploy-<pod-id> -- psql -U YOUR-USER -d authdb -c "SELECT email FROM auth_user;"

# Use correct email/password from init.sql
```

**B. Database Connection Issue**
- See [Issue 8](#issue-8-postgresql-authentication-failed)

---

### Issue 12: Upload Returns 500 Error

**Error:**
```
NameError: name 'unauth_count' is not defined
```

**Solution:**
This was a code issue. Ensure you're using the fixed version:
```bash
# Rebuild and push gateway service
cd src/gateway-service
docker build -t gateway-service .
docker tag gateway-service:latest <ACCOUNT-ID>.dkr.ecr.ap-south-1.amazonaws.com/gateway-service:latest
docker push <ACCOUNT-ID>.dkr.ecr.ap-south-1.amazonaws.com/gateway-service:latest

# Restart deployment
kubectl rollout restart deployment gateway
```

---

### Issue 13: Email Notification Not Received

**Error:**
```
smtplib.SMTPAuthenticationError: Username and Password not accepted
```

**Solutions:**

**A. Remove Spaces from App Password**
```yaml
# In src/notification-service/manifest/secret.yaml
# Wrong: "vrtw ojpv tgsh pcet"
# Correct: "vrtwojpvtgshpcet"
```

**B. Generate New App Password**
1. Google Account → Security → 2-Step Verification (enable)
2. Search "App passwords" → Generate new
3. Copy 16-character password (remove spaces)
4. Update secret.yaml
5. Apply and restart:
```bash
kubectl apply -f src/notification-service/manifest/secret.yaml
kubectl rollout restart deployment notification
```

---

### Issue 14: Cannot Access Frontend - No Public IP

**Error:**
Nodes don't have public IPs, can't access services via NodePort.

**Solutions:**

**Option 1: Port Forward (Development)**
```bash
kubectl port-forward svc/frontend 8080:80
# Access: http://localhost:8080
```

**Option 2: Use LoadBalancer (Production)**
```bash
# Frontend service already uses LoadBalancer
kubectl get svc frontend

# Wait for EXTERNAL-IP (AWS LoadBalancer DNS)
# Access via: http://<EXTERNAL-IP>
```

**Option 3: Use Ingress Controller**
```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
```

---

## CI/CD Issues

### Issue 15: Jenkins Cannot Connect to EKS

**Error:**
```
error: You must be logged in to the server
```

**Solution:**
```bash
# On Jenkins server as jenkins user
sudo su - jenkins
aws configure
aws eks update-kubeconfig --name microservices-cluster --region ap-south-1
kubectl get nodes
exit
```

---

### Issue 16: Jenkins Docker Permission Denied

**Error:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```bash
# Add jenkins user to docker group
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
sudo systemctl restart docker
```

---

### Issue 17: ECR Login Failed in Jenkins

**Error:**
```
Error response from daemon: login attempt failed with status: 400 Bad Request
```

**Solution:**
```bash
# Use this format in Jenkinsfile
sh """
    aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin ${ECR_REGISTRY}
"""
```

---

## Cleanup Issues

### Issue 18: Terraform Destroy Fails - ECR Not Empty

**Error:**
```
Error: ECR Repository not empty, consider using force_delete
```

**Solution:**
```bash
# Delete all images from ECR
aws ecr batch-delete-image --repository-name auth-service --region ap-south-1 --image-ids imageTag=latest
aws ecr batch-delete-image --repository-name gateway-service --region ap-south-1 --image-ids imageTag=latest
aws ecr batch-delete-image --repository-name converter-service --region ap-south-1 --image-ids imageTag=latest
aws ecr batch-delete-image --repository-name notification-service --region ap-south-1 --image-ids imageTag=latest
aws ecr batch-delete-image --repository-name frontend --region ap-south-1 --image-ids imageTag=latest

# Then destroy
terraform destroy
```

---

### Issue 19: Terraform Destroy Fails - Subnet Dependencies

**Error:**
```
Error: subnet has dependencies and cannot be deleted
```

**Solution:**
```bash
# Delete LoadBalancers first
kubectl delete svc frontend

# Wait 2-3 minutes for AWS to clean up

# Delete remaining network interfaces
# AWS Console → EC2 → Network Interfaces → Delete all in your VPC

# Then destroy
terraform destroy
```

---

### Issue 20: Cannot Delete VPC - Dependencies Exist

**Solution:**
```bash
# 1. Delete all Kubernetes resources
kubectl delete all --all

# 2. Uninstall Helm charts
helm uninstall mongo postgres rabbitmq

# 3. Delete LoadBalancers (AWS Console)
# EC2 → Load Balancers → Delete

# 4. Wait 5 minutes

# 5. Delete Network Interfaces (AWS Console)
# EC2 → Network Interfaces → Delete all

# 6. Run terraform destroy
terraform destroy -auto-approve
```

---

## General Troubleshooting Commands

### Check Pod Status
```bash
kubectl get pods
kubectl get pods -o wide
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl logs <pod-name> --previous
```

### Check Services
```bash
kubectl get svc
kubectl describe svc <service-name>
```

### Check ConfigMaps and Secrets
```bash
kubectl get configmap
kubectl get configmap <name> -o yaml
kubectl get secret
kubectl get secret <name> -o yaml
```

### Check Events
```bash
kubectl get events --sort-by='.lastTimestamp'
kubectl get events --field-selector involvedObject.name=<pod-name>
```

### Check Resource Usage
```bash
kubectl top nodes
kubectl top pods
```

### Restart Deployments
```bash
kubectl rollout restart deployment <name>
kubectl rollout status deployment <name>
```

### Debug Pod Issues
```bash
# Execute shell in pod
kubectl exec -it <pod-name> -- sh

# Test connectivity
kubectl exec -it <pod-name> -- ping mongodb
kubectl exec -it <pod-name> -- nslookup mongodb
```

---

## Quick Reference

### Credential Locations

**PostgreSQL:**
- Values: `Helm_charts/Postgres/values.yaml`
- ConfigMap: `src/auth-service/manifest/configmap.yaml`
- Secret: `src/auth-service/manifest/secret.yaml`

**MongoDB:**
- Values: `Helm_charts/MongoDB/values.yaml`
- ConfigMap: `src/gateway-service/manifest/configmap.yaml`
- ConfigMap: `src/converter-service/manifest/configmap.yaml`

**Email:**
- Secret: `src/notification-service/manifest/secret.yaml`

### Service Ports

- Frontend: 80 (LoadBalancer)
- Gateway: 8080 (NodePort 30002)
- Auth: 5000 (NodePort 30006)
- PostgreSQL: 5432 (NodePort 30003)
- MongoDB: 27017 (NodePort 30005)
- RabbitMQ: 15672 (NodePort 30004)

### Common kubectl Commands

```bash
# Get all resources
kubectl get all

# Delete all resources
kubectl delete all --all

# Force delete pod
kubectl delete pod <pod-name> --force --grace-period=0

# Get pod logs with follow
kubectl logs -f <pod-name>

# Scale deployment
kubectl scale deployment <name> --replicas=3

# Update image
kubectl set image deployment/<name> <container>=<new-image>
```

---

## Getting Help

If you encounter an issue not covered here:

1. **Check logs**: `kubectl logs <pod-name>`
2. **Check events**: `kubectl get events`
3. **Describe resource**: `kubectl describe <resource> <name>`
4. **Check AWS Console**: Verify resources exist
5. **Open GitHub Issue**: Include logs and error messages

---

## Preventive Measures

1. **Always verify credentials match** across all configuration files
2. **Check resource limits** before scaling up
3. **Monitor costs** regularly in AWS Cost Explorer
4. **Keep backups** of working configurations
5. **Test in staging** before production changes
6. **Use version control** for all configuration changes
7. **Document custom changes** for team reference

---

**Last Updated:** 2024

For more help, refer to:
- [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)
- [jenkins/JENKINS-SETUP.md](jenkins/JENKINS-SETUP.md)
- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
