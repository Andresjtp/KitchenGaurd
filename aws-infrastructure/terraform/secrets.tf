# AWS Secrets Manager for sensitive data

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "kitchenguard/jwt-secret-${var.environment}"
  description             = "JWT secret key for KitchenGuard"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-jwt-secret"
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret_key
}

resource "aws_secretsmanager_secret" "db_user" {
  name                    = "kitchenguard/db-user-${var.environment}"
  description             = "Database username for KitchenGuard"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-db-user"
  }
}

resource "aws_secretsmanager_secret_version" "db_user" {
  secret_id     = aws_secretsmanager_secret.db_user.id
  secret_string = var.db_user
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "kitchenguard/db-password-${var.environment}"
  description             = "Database password for KitchenGuard"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}
