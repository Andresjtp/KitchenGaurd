# Outputs

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "auth_service_name" {
  description = "Name of the auth service"
  value       = aws_ecs_service.auth_service.name
}

output "inventory_service_name" {
  description = "Name of the inventory service"
  value       = aws_ecs_service.inventory_service.name
}

output "api_gateway_service_name" {
  description = "Name of the API gateway service"
  value       = aws_ecs_service.api_gateway.name
}

output "service_discovery_namespace" {
  description = "Service discovery namespace"
  value       = aws_service_discovery_private_dns_namespace.main.name
}

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value = {
    auth_service      = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}-auth"
    inventory_service = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}-inventory"
    api_gateway       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}-gateway"
  }
}

output "application_url" {
  description = "URL to access the application"
  value       = "http://${aws_lb.main.dns_name}"
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value = {
    auth_service      = aws_cloudwatch_log_group.auth_service.name
    inventory_service = aws_cloudwatch_log_group.inventory_service.name
    api_gateway       = aws_cloudwatch_log_group.api_gateway.name
  }
}
