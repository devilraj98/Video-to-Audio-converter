output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "ecr_repositories" {
  description = "ECR repository URLs"
  value = {
    auth_service         = aws_ecr_repository.auth_service.repository_url
    gateway_service      = aws_ecr_repository.gateway_service.repository_url
    converter_service    = aws_ecr_repository.converter_service.repository_url
    notification_service = aws_ecr_repository.notification_service.repository_url
    frontend             = aws_ecr_repository.frontend.repository_url
  }
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}"
}

output "node_security_group_id" {
  description = "Security group ID for nodes"
  value       = aws_security_group.node_group.id
}
