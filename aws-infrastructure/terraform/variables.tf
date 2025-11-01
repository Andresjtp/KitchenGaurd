# Variables for KitchenGuard Infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "kitchenguard"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-2a", "us-east-2b", "us-east-2c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  type        = string
  default     = "kitchenguard-db.cxike2u26m31.us-east-2.rds.amazonaws.com"
}

variable "db_user" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "container_cpu" {
  description = "CPU units for containers (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Memory for containers in MB"
  type        = number
  default     = 512
}

variable "desired_count_auth" {
  description = "Desired number of auth service tasks"
  type        = number
  default     = 2
}

variable "desired_count_inventory" {
  description = "Desired number of inventory service tasks"
  type        = number
  default     = 2
}

variable "desired_count_gateway" {
  description = "Desired number of api gateway tasks"
  type        = number
  default     = 2
}

variable "ecr_image_tag" {
  description = "ECR image tag to deploy"
  type        = string
  default     = "latest"
}
