pipeline {
    agent any
    
    environment {
        AWS_REGION = 'ap-south-1'
        AWS_ACCOUNT_ID = '754307962192'
        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        EKS_CLUSTER_NAME = 'microservices-cluster'
        GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Building commit: ${GIT_COMMIT_SHORT}"
            }
        }
        
        stage('Build Docker Images') {
            parallel {
                stage('Auth Service') {
                    steps {
                        script {
                            dir('microservices-python-app/src/auth-service') {
                                sh """
                                    docker build -t auth-service:${GIT_COMMIT_SHORT} .
                                    docker tag auth-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/auth-service:${GIT_COMMIT_SHORT}
                                    docker tag auth-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/auth-service:latest
                                """
                            }
                        }
                    }
                }
                
                stage('Gateway Service') {
                    steps {
                        script {
                            dir('microservices-python-app/src/gateway-service') {
                                sh """
                                    docker build -t gateway-service:${GIT_COMMIT_SHORT} .
                                    docker tag gateway-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/gateway-service:${GIT_COMMIT_SHORT}
                                    docker tag gateway-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/gateway-service:latest
                                """
                            }
                        }
                    }
                }
                
                stage('Converter Service') {
                    steps {
                        script {
                            dir('microservices-python-app/src/converter-service') {
                                sh """
                                    docker build -t converter-service:${GIT_COMMIT_SHORT} .
                                    docker tag converter-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/converter-service:${GIT_COMMIT_SHORT}
                                    docker tag converter-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/converter-service:latest
                                """
                            }
                        }
                    }
                }
                
                stage('Notification Service') {
                    steps {
                        script {
                            dir('microservices-python-app/src/notification-service') {
                                sh """
                                    docker build -t notification-service:${GIT_COMMIT_SHORT} .
                                    docker tag notification-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/notification-service:${GIT_COMMIT_SHORT}
                                    docker tag notification-service:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/notification-service:latest
                                """
                            }
                        }
                    }
                }
                
                stage('Frontend') {
                    steps {
                        script {
                            dir('microservices-python-app/src/frontend') {
                                sh """
                                    docker build -t frontend:${GIT_COMMIT_SHORT} .
                                    docker tag frontend:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/frontend:${GIT_COMMIT_SHORT}
                                    docker tag frontend:${GIT_COMMIT_SHORT} ${ECR_REGISTRY}/frontend:latest
                                """
                            }
                        }
                    }
                }
            }
        }
        
        stage('Push to ECR') {
            steps {
                script {
                    sh """
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        
                        docker push ${ECR_REGISTRY}/auth-service:${GIT_COMMIT_SHORT}
                        docker push ${ECR_REGISTRY}/auth-service:latest
                        
                        docker push ${ECR_REGISTRY}/gateway-service:${GIT_COMMIT_SHORT}
                        docker push ${ECR_REGISTRY}/gateway-service:latest
                        
                        docker push ${ECR_REGISTRY}/converter-service:${GIT_COMMIT_SHORT}
                        docker push ${ECR_REGISTRY}/converter-service:latest
                        
                        docker push ${ECR_REGISTRY}/notification-service:${GIT_COMMIT_SHORT}
                        docker push ${ECR_REGISTRY}/notification-service:latest
                        
                        docker push ${ECR_REGISTRY}/frontend:${GIT_COMMIT_SHORT}
                        docker push ${ECR_REGISTRY}/frontend:latest
                    """
                }
            }
        }
        
        stage('Deploy to EKS') {
            steps {
                script {
                    sh """
                        aws eks update-kubeconfig --name ${EKS_CLUSTER_NAME} --region ${AWS_REGION}
                        
                        kubectl rollout restart deployment auth
                        kubectl rollout restart deployment gateway
                        kubectl rollout restart deployment converter
                        kubectl rollout restart deployment notification
                        kubectl rollout restart deployment frontend
                        
                        kubectl rollout status deployment auth
                        kubectl rollout status deployment gateway
                        kubectl rollout status deployment converter
                        kubectl rollout status deployment notification
                        kubectl rollout status deployment frontend
                    """
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    sh """
                        kubectl get pods
                        kubectl get svc
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Pipeline completed successfully!"
            echo "Deployed commit: ${GIT_COMMIT_SHORT}"
        }
        failure {
            echo "❌ Pipeline failed!"
        }
        always {
            sh 'docker system prune -f'
        }
    }
}
