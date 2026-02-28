# Jenkins CI/CD Setup Guide

## Overview
This guide sets up a complete CI/CD pipeline using Jenkins to automatically build, push, and deploy your microservices to AWS EKS.

---

## Prerequisites

1. **Jenkins Server** (EC2 instance or local)
2. **Docker** installed on Jenkins server
3. **AWS CLI** configured on Jenkins server
4. **kubectl** installed on Jenkins server
5. **Git** repository for your code

---

## Part 1: Jenkins Server Setup

### Option A: Deploy Jenkins on EC2

**1. Launch EC2 Instance:**
- AMI: Amazon Linux 2
- Instance Type: t3.medium (minimum)
- Security Group: Open ports 8080 (Jenkins), 22 (SSH)

**2. Install Jenkins:**
```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@<EC2-IP>

# Install Java
sudo yum update -y
sudo yum install java-11-amazon-corretto -y

# Install Jenkins
sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key
sudo yum install jenkins -y
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Get initial admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**3. Install Docker:**
```bash
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker jenkins
sudo usermod -aG docker ec2-user
sudo systemctl restart jenkins
```

**4. Install AWS CLI:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**5. Install kubectl:**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

**6. Configure AWS Credentials:**
```bash
sudo su - jenkins
aws configure
# Enter AWS Access Key ID
# Enter AWS Secret Access Key
# Region: ap-south-1
# Output: json
exit
```

---

## Part 2: Jenkins Configuration

### Step 1: Access Jenkins
1. Open browser: `http://<JENKINS-SERVER-IP>:8080`
2. Enter initial admin password
3. Install suggested plugins
4. Create admin user

### Step 2: Install Required Plugins
1. Go to: **Manage Jenkins** → **Manage Plugins** → **Available**
2. Install:
   - Docker Pipeline
   - AWS Steps
   - Kubernetes CLI
   - Git
   - Pipeline
3. Restart Jenkins

### Step 3: Configure AWS Credentials
1. Go to: **Manage Jenkins** → **Manage Credentials**
2. Click **(global)** → **Add Credentials**
3. Kind: **AWS Credentials**
4. ID: `aws-credentials`
5. Add your AWS Access Key and Secret Key
6. Click **OK**

### Step 4: Configure EKS Access
```bash
# On Jenkins server as jenkins user
sudo su - jenkins
aws eks update-kubeconfig --name microservices-cluster --region ap-south-1
kubectl get nodes
exit
```

---

## Part 3: Create Jenkins Pipeline

### Step 1: Create New Pipeline Job
1. Click **New Item**
2. Name: `microservices-cicd`
3. Type: **Pipeline**
4. Click **OK**

### Step 2: Configure Pipeline
1. **General** section:
   - ✅ GitHub project
   - Project URL: `https://github.com/your-username/your-repo`

2. **Build Triggers**:
   - ✅ GitHub hook trigger for GITScm polling
   - ✅ Poll SCM: `H/5 * * * *` (every 5 minutes)

3. **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `https://github.com/your-username/your-repo.git`
   - Credentials: Add your GitHub credentials
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`

4. Click **Save**

---

## Part 4: Setup GitHub Webhook (Optional)

### For Automatic Builds on Git Push

1. Go to your GitHub repository
2. **Settings** → **Webhooks** → **Add webhook**
3. Payload URL: `http://<JENKINS-IP>:8080/github-webhook/`
4. Content type: `application/json`
5. Events: **Just the push event**
6. Click **Add webhook**

---

## Part 5: Run the Pipeline

### Manual Trigger
1. Go to your pipeline job
2. Click **Build Now**
3. Watch the build progress in **Console Output**

### Automatic Trigger
- Push code to GitHub
- Jenkins automatically detects changes
- Pipeline runs automatically

---

## Pipeline Stages Explained

### 1. **Checkout**
- Pulls latest code from Git repository
- Gets commit hash for tagging

### 2. **Build Docker Images**
- Builds all 5 microservices in parallel
- Tags with commit hash and 'latest'

### 3. **Push to ECR**
- Logs into AWS ECR
- Pushes all images with both tags

### 4. **Deploy to EKS**
- Updates kubeconfig
- Restarts all deployments
- Waits for rollout completion

### 5. **Verify Deployment**
- Shows pod status
- Shows service status

---

## Monitoring & Troubleshooting

### View Build Logs
```
Jenkins Dashboard → Job → Build Number → Console Output
```

### Check Jenkins Logs
```bash
sudo tail -f /var/log/jenkins/jenkins.log
```

### Test Docker Access
```bash
sudo su - jenkins
docker ps
docker build --help
```

### Test AWS Access
```bash
sudo su - jenkins
aws sts get-caller-identity
aws ecr describe-repositories --region ap-south-1
```

### Test kubectl Access
```bash
sudo su - jenkins
kubectl get nodes
kubectl get pods
```

---

## Pipeline Workflow

```
Code Push → GitHub
    ↓
GitHub Webhook → Jenkins
    ↓
Jenkins Pipeline Triggered
    ↓
1. Checkout Code
    ↓
2. Build Docker Images (Parallel)
    ├── Auth Service
    ├── Gateway Service
    ├── Converter Service
    ├── Notification Service
    └── Frontend
    ↓
3. Push to ECR
    ↓
4. Deploy to EKS
    ├── Restart Deployments
    └── Wait for Rollout
    ↓
5. Verify Deployment
    ↓
✅ Success / ❌ Failure Notification
```

---

## Best Practices

1. **Use Git Branches:**
   - `main` → Production
   - `develop` → Staging
   - `feature/*` → Development

2. **Add Tests:**
   - Unit tests before build
   - Integration tests after deployment

3. **Notifications:**
   - Email on build failure
   - Slack integration

4. **Rollback Strategy:**
   - Keep previous image tags
   - Quick rollback command

5. **Security:**
   - Use Jenkins credentials store
   - Rotate AWS keys regularly
   - Scan Docker images

---

## Advanced Features (Optional)

### Add Slack Notifications
```groovy
post {
    success {
        slackSend color: 'good', message: "Build Successful: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
    }
    failure {
        slackSend color: 'danger', message: "Build Failed: ${env.JOB_NAME} ${env.BUILD_NUMBER}"
    }
}
```

### Add Email Notifications
```groovy
post {
    failure {
        emailext (
            subject: "Build Failed: ${env.JOB_NAME}",
            body: "Build ${env.BUILD_NUMBER} failed",
            to: "team@example.com"
        )
    }
}
```

### Add Testing Stage
```groovy
stage('Test') {
    steps {
        sh 'pytest tests/'
    }
}
```

---

## Cleanup

### Stop Jenkins
```bash
sudo systemctl stop jenkins
```

### Remove Jenkins
```bash
sudo yum remove jenkins -y
```

---

## Cost Optimization

- Use **t3.medium** for Jenkins (can be stopped when not in use)
- Use **Spot Instances** for Jenkins server
- Schedule builds during off-peak hours
- Clean up old Docker images regularly

---

## Support

For issues:
1. Check Jenkins console output
2. Verify AWS credentials
3. Check kubectl access
4. Review Docker permissions
5. Check security group rules

---

**Your CI/CD pipeline is ready!** 🚀

Every code push will automatically:
1. Build Docker images
2. Push to ECR
3. Deploy to EKS
4. Verify deployment

Happy deploying! 🎉
