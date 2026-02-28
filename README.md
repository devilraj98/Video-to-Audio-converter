# EKS Python Microservices - Video to MP3 Converter

A complete production-ready microservices application deployed on AWS EKS that converts video files to MP3 audio format.

## 🎯 Project Overview

This project demonstrates a full-stack microservices architecture with:
- **5 Microservices**: Auth, Gateway, Converter, Notification, Frontend
- **Infrastructure as Code**: Terraform for AWS resources
- **Container Orchestration**: Kubernetes (EKS)
- **CI/CD**: Jenkins pipeline
- **Databases**: MongoDB, PostgreSQL
- **Message Queue**: RabbitMQ
- **Web UI**: Flask-based frontend

## 🏗️ Architecture

```
User → Frontend (Web UI)
         ↓
    Gateway Service
         ↓
    Auth Service (PostgreSQL)
         ↓
    MongoDB (Videos/MP3s)
         ↓
    RabbitMQ (Message Queue)
         ↓
    Converter Service
         ↓
    Notification Service (Email)
```

## 🚀 Features

- ✅ User authentication with JWT
- ✅ Video upload via web interface
- ✅ Automatic video to MP3 conversion
- ✅ Email notification with download link
- ✅ MP3 download from web UI
- ✅ Scalable microservices architecture
- ✅ Infrastructure as Code with Terraform
- ✅ CI/CD pipeline with Jenkins
- ✅ Production-ready Kubernetes deployment

## 📁 Project Structure

```
EKS-Python-Microservice-Project/
├── microservices-python-app/
│   ├── src/
│   │   ├── auth-service/
│   │   ├── gateway-service/
│   │   ├── converter-service/
│   │   ├── notification-service/
│   │   └── frontend/
│   └── Helm_charts/
│       ├── MongoDB/
│       ├── Postgres/
│       └── RabbitMQ/
├── terraform/
│   ├── provider.tf
│   ├── vpc.tf
│   ├── eks.tf
│   ├── ecr.tf
│   └── ...
├── jenkins/
│   └── JENKINS-SETUP.md
├── Jenkinsfile
├── DEPLOYMENT-GUIDE.md
└── README.md
```

## 🛠️ Technology Stack

**Backend:**
- Python 3.10
- Flask
- PostgreSQL
- MongoDB
- RabbitMQ

**Infrastructure:**
- AWS EKS (Kubernetes)
- AWS ECR (Container Registry)
- Terraform
- Helm

**CI/CD:**
- Jenkins
- Docker

## 📋 Prerequisites

- AWS Account
- AWS CLI configured
- Docker installed
- kubectl installed
- Helm installed
- Terraform installed
- Git

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/YOUR-USERNAME/EKS-Python-Microservice-Project.git
cd EKS-Python-Microservice-Project
```

### 2. Deploy Infrastructure
```bash
cd terraform
terraform init
terraform apply
```

### 3. Configure kubectl
```bash
aws eks update-kubeconfig --name microservices-cluster --region ap-south-1
```

### 4. Deploy Databases
```bash
cd ../microservices-python-app/Helm_charts
helm install mongo MongoDB/
helm install postgres Postgres/
helm install rabbitmq RabbitMQ/
```

### 5. Build and Push Docker Images
```bash
# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

# Build and push all services
cd ../src
# (See DEPLOYMENT-GUIDE.md for detailed commands)
```

### 6. Deploy Microservices
```bash
kubectl apply -f auth-service/manifest/
kubectl apply -f gateway-service/manifest/
kubectl apply -f converter-service/manifest/
kubectl apply -f notification-service/manifest/
kubectl apply -f frontend/manifest/
```

### 7. Access Application
```bash
kubectl get svc frontend
# Open the LoadBalancer URL in browser
```

## 📖 Documentation

- **[DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md)** - Complete deployment instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[jenkins/JENKINS-SETUP.md](jenkins/JENKINS-SETUP.md)** - CI/CD pipeline setup

## 🔧 Configuration

### Update Credentials

**PostgreSQL & MongoDB:**
- Edit `Helm_charts/Postgres/values.yaml`
- Edit `Helm_charts/MongoDB/values.yaml`

**Email Notifications:**
- Edit `src/notification-service/manifest/secret.yaml`
- Add Gmail app password

**AWS Region:**
- Update `terraform/terraform.tfvars`

## 🧪 Testing

**Login:**
```bash
curl -X POST http://<FRONTEND-URL>/login -u email:password
```

**Upload Video:**
- Use web UI at `http://<FRONTEND-URL>`
- Login with credentials
- Upload MP4 file
- Check email for file ID
- Download MP3

## 📊 Monitoring

```bash
# Check pods
kubectl get pods

# Check logs
kubectl logs -l app=gateway

# Check services
kubectl get svc

# Check resource usage
kubectl top nodes
kubectl top pods
```

## 🔒 Security

- Secrets stored in Kubernetes Secrets
- JWT-based authentication
- AWS IAM roles for EKS
- Private subnets for nodes
- Security groups configured

## 💰 Cost Estimate

**Monthly cost (ap-south-1):**
- EKS Cluster: ~$73
- 2x t3.small nodes: ~$30
- NAT Gateways: ~$66
- EBS volumes: ~$4
- **Total: ~$173/month**

## 🧹 Cleanup

```bash
# Delete Kubernetes resources
kubectl delete -f src/*/manifest/
helm uninstall mongo postgres rabbitmq

# Destroy infrastructure
cd terraform
terraform destroy
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 👤 Author

**Your Name**
- GitHub: [@your-username](https://github.com/your-username)
- LinkedIn: [Your Profile](https://linkedin.com/in/your-profile)

## 🙏 Acknowledgments

- AWS EKS Documentation
- Kubernetes Documentation
- Flask Documentation
- Terraform Documentation

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check DEPLOYMENT-GUIDE.md for troubleshooting
- Review Jenkins setup guide for CI/CD issues

---

**⭐ Star this repo if you find it helpful!**

Made with ❤️ for DevOps learning
