# AWS Configuration
aws_region = "ap-south-1"

# EKS Cluster Configuration
cluster_name    = "microservices-cluster"
cluster_version = "1.29"

# Node Group Configuration
node_instance_type = "t3.small"
node_desired_size  = 2
node_min_size      = 1
node_max_size      = 3
node_disk_size     = 20
