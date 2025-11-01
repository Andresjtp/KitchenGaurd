# Terraform Configuration for KitchenGuard ECS Fargate Deployment

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Store Terraform state in S3
  # backend "s3" {
  #   bucket = "kitchenguard-terraform-state"
  #   key    = "prod/terraform.tfstate"
  #   region = "us-east-2"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt = true
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "KitchenGuard"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
