# ECS Cluster and Services

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster-${var.environment}"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "auth_service" {
  name              = "/ecs/${var.project_name}-auth-service"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-auth-logs"
  }
}

resource "aws_cloudwatch_log_group" "inventory_service" {
  name              = "/ecs/${var.project_name}-inventory-service"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-inventory-logs"
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/ecs/${var.project_name}-api-gateway"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-gateway-logs"
  }
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-ecs-task-execution-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for Secrets Manager
resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "${var.project_name}-ecs-secrets-policy"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:kitchenguard/*"
        ]
      }
    ]
  })
}

# ECS Task Role (for application permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-ecs-task-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Service Discovery Namespace
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "kitchenguard-internal"
  description = "Service discovery for KitchenGuard microservices"
  vpc         = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-service-discovery-${var.environment}"
  }
}

# Service Discovery for Auth Service
resource "aws_service_discovery_service" "auth_service" {
  name = "auth-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

# Service Discovery for Inventory Service
resource "aws_service_discovery_service" "inventory_service" {
  name = "inventory-service"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}
