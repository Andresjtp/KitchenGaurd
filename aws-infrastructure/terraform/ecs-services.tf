# ECS Services for KitchenGuard

# Get AWS Account ID
data "aws_caller_identity" "current" {}

# Auth Service Task Definition
resource "aws_ecs_task_definition" "auth_service" {
  family                   = "${var.project_name}-auth-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "auth-service"
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}-auth:${var.ecr_image_tag}"
      cpu       = var.container_cpu
      memory    = var.container_memory
      essential = true

      portMappings = [
        {
          containerPort = 8007
          hostPort      = 8007
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "AUTH_PORT", value = "8007" },
        { name = "JWT_EXPIRATION_HOURS", value = "24" },
        { name = "DB_PORT", value = "5432" },
        { name = "DB_NAME", value = "kitchenguard_auth" },
        { name = "SERVICE_NAME", value = "auth-service" },
        { name = "DB_HOST", value = var.rds_endpoint }
      ]

      secrets = [
        {
          name      = "JWT_SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        },
        {
          name      = "DB_USER"
          valueFrom = aws_secretsmanager_secret.db_user.arn
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.auth_service.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c 'import requests; requests.get(\"http://localhost:8007/health\", timeout=2)' || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# Auth Service ECS Service
resource "aws_ecs_service" "auth_service" {
  name            = "${var.project_name}-auth-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.auth_service.arn
  desired_count   = var.desired_count_auth
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.auth_service.arn
    container_name   = "auth-service"
    container_port   = 8007
  }

  service_registries {
    registry_arn = aws_service_discovery_service.auth_service.arn
  }

  depends_on = [aws_lb_listener.http]
}

# Inventory Service Task Definition
resource "aws_ecs_task_definition" "inventory_service" {
  family                   = "${var.project_name}-inventory-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "inventory-service"
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}-inventory:${var.ecr_image_tag}"
      cpu       = var.container_cpu
      memory    = var.container_memory
      essential = true

      portMappings = [
        {
          containerPort = 8001
          hostPort      = 8001
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "INVENTORY_PORT", value = "8001" },
        { name = "DB_PORT", value = "5432" },
        { name = "DB_NAME", value = "kitchenguard_inventory" },
        { name = "SERVICE_NAME", value = "inventory-service" },
        { name = "DB_HOST", value = var.rds_endpoint }
      ]

      secrets = [
        {
          name      = "DB_USER"
          valueFrom = aws_secretsmanager_secret.db_user.arn
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.inventory_service.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c 'import requests; requests.get(\"http://localhost:8001/health\", timeout=2)' || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# Inventory Service ECS Service
resource "aws_ecs_service" "inventory_service" {
  name            = "${var.project_name}-inventory-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.inventory_service.arn
  desired_count   = var.desired_count_inventory
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.inventory_service.arn
    container_name   = "inventory-service"
    container_port   = 8001
  }

  service_registries {
    registry_arn = aws_service_discovery_service.inventory_service.arn
  }

  depends_on = [aws_lb_listener.http]
}

# API Gateway Task Definition
resource "aws_ecs_task_definition" "api_gateway" {
  family                   = "${var.project_name}-api-gateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "api-gateway"
      image     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.project_name}-gateway:${var.ecr_image_tag}"
      cpu       = var.container_cpu
      memory    = var.container_memory
      essential = true

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "GATEWAY_PORT", value = "8000" },
        { name = "AUTH_SERVICE_URL", value = "http://auth-service.kitchenguard-internal:8007" },
        { name = "INVENTORY_SERVICE_URL", value = "http://inventory-service.kitchenguard-internal:8001" },
        { name = "RATE_LIMIT_PER_MINUTE", value = "100" },
        { name = "CORS_ORIGINS", value = "*" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api_gateway.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c 'import requests; requests.get(\"http://localhost:8000/health\", timeout=2)' || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# API Gateway ECS Service
resource "aws_ecs_service" "api_gateway" {
  name            = "${var.project_name}-api-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api_gateway.arn
  desired_count   = var.desired_count_gateway
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api_gateway.arn
    container_name   = "api-gateway"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
}
