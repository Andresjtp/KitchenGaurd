# 🚀 KitchenGuard - AWS ECS Fargate Deployment Guide

## Complete Guide for Deploying to AWS ECS with Fargate

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Pre-Deployment Setup](#pre-deployment-setup)
5. [Local Testing](#local-testing)
6. [AWS Deployment Steps](#aws-deployment-steps)
7. [Post-Deployment](#post-deployment)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Cost Estimation](#cost-estimation)

---

## Overview

This deployment uses:
- **AWS ECS Fargate**: Serverless container orchestration
- **Application Load Balancer**: Traffic distribution and routing
- **AWS VPC**: Isolated network with public/private subnets
- **AWS RDS PostgreSQL**: Existing database (already configured)
- **AWS Secrets Manager**: Secure credential storage
- **AWS CloudWatch**: Logging and monitoring
- **Terraform**: Infrastructure as Code

---

## Prerequisites

### Required Tools
```bash
# 1. AWS CLI (v2)
aws --version
# If not installed: https://aws.amazon.com/cli/

# 2. Docker
docker --version
# If not installed: https://docs.docker.com/get-docker/

# 3. Terraform
terraform --version
# If not installed: https://developer.hashicorp.com/terraform/downloads

# 4. Git
git --version
```

### AWS Account Requirements
- ✅ AWS Account with Administrator access
- ✅ AWS CLI configured with credentials
- ✅ Existing RDS PostgreSQL database (✅ You have this!)
- ✅ Budget: ~$100-150/month for production setup

### Verify AWS Configuration
```bash
aws sts get-caller-identity
# Should show your Account ID, UserId, and ARN
```

---

## Architecture

### High-Level Architecture
```
Internet
   ↓
Application Load Balancer (Public Subnets)
   ↓
ECS Services (Private Subnets)
   ├── API Gateway (2 tasks)
   ├── Auth Service (2 tasks)
   └── Inventory Service (2 tasks)
   ↓
AWS RDS PostgreSQL (kitchenguard-db)
```

### Network Architecture
- **VPC**: 10.0.0.0/16
- **Public Subnets**: 3 subnets across 3 AZs (for ALB)
- **Private Subnets**: 3 subnets across 3 AZs (for ECS tasks)
- **NAT Gateways**: 3 (one per AZ for high availability)
- **Service Discovery**: Private DNS namespace for inter-service communication

---

## Pre-Deployment Setup

### Step 1: Configure AWS Credentials
```bash
aws configure
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: us-east-2
# Default output format: json
```

### Step 2: Set Environment Variables
```bash
export AWS_REGION=us-east-2
export PROJECT_NAME=kitchenguard
export ENVIRONMENT=prod
```

### Step 3: Generate JWT Secret
```bash
# Generate a strong random JWT secret
openssl rand -base64 32
# Save this - you'll need it for Terraform variables
```

### Step 4: Prepare Terraform Variables
```bash
cd aws-infrastructure/terraform

# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**terraform.tfvars** (update these values):
```hcl
aws_region = "us-east-2"
environment = "prod"

rds_endpoint = "kitchenguard-db.cxike2u26m31.us-east-2.rds.amazonaws.com"
db_user      = "KG_Admin"
db_password  = "13Torr0123"  # Your actual RDS password

jwt_secret_key = "paste-the-generated-secret-from-step-3"

container_cpu    = 256
container_memory = 512

desired_count_auth      = 2
desired_count_inventory = 2
desired_count_gateway   = 2

ecr_image_tag = "latest"
```

---

## Local Testing

Before deploying to AWS, test containers locally:

### Step 1: Create Environment File
```bash
# In project root
cp .env.example .env

# Edit with your RDS credentials
nano .env
```

**.env**:
```env
DB_HOST=kitchenguard-db.cxike2u26m31.us-east-2.rds.amazonaws.com
DB_PORT=5432
DB_USER=KG_Admin
DB_PASSWORD=13Torr0123
AUTH_DB_NAME=kitchenguard_auth
INVENTORY_DB_NAME=kitchenguard_inventory
JWT_SECRET_KEY=your-jwt-secret-here
```

### Step 2: Build and Test with Docker Compose
```bash
# Build all images
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up

# In another terminal, test the services
curl http://localhost:8000/health    # API Gateway
curl http://localhost:8007/health    # Auth Service
curl http://localhost:8001/health    # Inventory Service

# Test registration
curl -X POST http://localhost:8007/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "fullName": "Test User",
    "restaurantName": "Test Restaurant",
    "restaurantType": "Fine Dining",
    "userPosition": "Manager"
  }'

# Stop services
docker-compose -f docker-compose.prod.yml down
```

---

## AWS Deployment Steps

### Phase 1: Create ECR Repositories and Push Images

#### Step 1: Initialize Terraform (Create ECR only)
```bash
cd aws-infrastructure/terraform

# Initialize Terraform
terraform init

# Preview ECR resources
terraform plan -target=aws_ecr_repository.auth_service \
               -target=aws_ecr_repository.inventory_service \
               -target=aws_ecr_repository.api_gateway

# Create ECR repositories
terraform apply -target=aws_ecr_repository.auth_service \
                -target=aws_ecr_repository.inventory_service \
                -target=aws_ecr_repository.api_gateway \
                -auto-approve
```

#### Step 2: Build and Push Docker Images
```bash
cd ../..  # Back to project root

# Run the build and push script
./scripts/build-and-push.sh us-east-2 v1.0.0

# This will:
# - Build Docker images for all services
# - Tag images with version and 'latest'
# - Push to ECR
```

**Expected Output:**
```
========================================
KitchenGuard - Build and Push to ECR
========================================

✅ AWS Account ID: 123456789012
✅ Successfully logged in to ECR
✅ Auth Service pushed successfully
✅ Inventory Service pushed successfully
✅ API Gateway pushed successfully

Image URLs:
  Auth:      123456789012.dkr.ecr.us-east-2.amazonaws.com/kitchenguard-auth:v1.0.0
  Inventory: 123456789012.dkr.ecr.us-east-2.amazonaws.com/kitchenguard-inventory:v1.0.0
  Gateway:   123456789012.dkr.ecr.us-east-2.amazonaws.com/kitchenguard-gateway:v1.0.0
```

### Phase 2: Deploy Infrastructure

#### Step 1: Review Terraform Plan
```bash
cd aws-infrastructure/terraform

# See what will be created
terraform plan

# Review:
# - VPC and networking (subnets, NAT gateways, route tables)
# - Security groups
# - Application Load Balancer
# - ECS cluster
# - ECS task definitions
# - ECS services
# - CloudWatch log groups
# - Secrets Manager secrets
```

#### Step 2: Deploy Infrastructure
```bash
# Apply Terraform configuration
terraform apply

# Review the plan and type 'yes' when prompted
# This will take 10-15 minutes
```

**Resources Created:**
- ✅ VPC with 3 public and 3 private subnets
- ✅ Internet Gateway and 3 NAT Gateways
- ✅ Application Load Balancer
- ✅ 3 Target Groups
- ✅ ECS Cluster
- ✅ 3 ECS Services with Fargate tasks
- ✅ Service Discovery namespace
- ✅ Security Groups
- ✅ CloudWatch Log Groups
- ✅ Secrets Manager secrets

#### Step 3: Get Outputs
```bash
# Get the ALB URL
terraform output alb_dns_name

# Get all outputs
terraform output
```

Save the ALB DNS name - this is your application URL!

### Phase 3: Verify Deployment

#### Check Service Status
```bash
# Get cluster name
CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)

# Check all services
aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services kitchenguard-auth-service kitchenguard-inventory-service kitchenguard-api-gateway \
  --region us-east-2

# Check running tasks
aws ecs list-tasks --cluster $CLUSTER_NAME --region us-east-2
```

#### Test the Application
```bash
# Get the ALB URL
ALB_URL=$(terraform output -raw alb_dns_name)

# Test health endpoints
curl http://$ALB_URL/health          # API Gateway
curl http://$ALB_URL/auth/health     # Auth Service (if routed)
curl http://$ALB_URL/inventory/health # Inventory Service (if routed)

# Test registration
curl -X POST http://$ALB_URL/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "produser",
    "email": "prod@example.com",
    "password": "securepass123",
    "fullName": "Production User",
    "restaurantName": "My Restaurant",
    "restaurantType": "Fine Dining",
    "userPosition": "Manager"
  }'
```

---

## Post-Deployment

### 1. Set Up Custom Domain (Optional)

#### Register Domain in Route 53
```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name kitchenguard.com \
  --caller-reference $(date +%s)
```

#### Request SSL Certificate
```bash
# Request certificate
aws acm request-certificate \
  --domain-name kitchenguard.com \
  --domain-name *.kitchenguard.com \
  --validation-method DNS \
  --region us-east-2
```

#### Add DNS Record
```bash
# Get ALB Zone ID and DNS name
terraform output alb_zone_id
terraform output alb_dns_name

# Create Route 53 alias record
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_HOSTED_ZONE_ID \
  --change-batch file://dns-record.json
```

**dns-record.json:**
```json
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "api.kitchenguard.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "YOUR_ALB_ZONE_ID",
        "DNSName": "YOUR_ALB_DNS_NAME",
        "EvaluateTargetHealth": false
      }
    }
  }]
}
```

### 2. Enable HTTPS

Update `alb.tf` to uncomment the HTTPS listener:
```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:us-east-2:ACCOUNT_ID:certificate/CERT_ID"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_gateway.arn
  }
}
```

Apply changes:
```bash
terraform apply
```

### 3. Update Frontend

Update React frontend to use the ALB URL:

**frontend/.env.production:**
```env
REACT_APP_API_URL=http://your-alb-dns-name.us-east-2.elb.amazonaws.com
# Or with custom domain:
REACT_APP_API_URL=https://api.kitchenguard.com
```

Build and deploy frontend to S3 + CloudFront (separate guide).

---

## Monitoring & Maintenance

### View Logs
```bash
# Auth Service logs
aws logs tail /ecs/kitchenguard-auth-service --follow --region us-east-2

# Inventory Service logs
aws logs tail /ecs/kitchenguard-inventory-service --follow --region us-east-2

# API Gateway logs
aws logs tail /ecs/kitchenguard-api-gateway --follow --region us-east-2

# Filter logs
aws logs filter-log-events \
  --log-group-name /ecs/kitchenguard-auth-service \
  --filter-pattern "ERROR" \
  --region us-east-2
```

### Scale Services
```bash
# Update desired count in terraform.tfvars
desired_count_auth = 4  # Scale up to 4 tasks

# Apply changes
terraform apply
```

### Update Application
```bash
# 1. Build and push new images
./scripts/build-and-push.sh us-east-2 v1.0.1

# 2. Update Terraform variables
# Edit terraform.tfvars: ecr_image_tag = "v1.0.1"

# 3. Apply changes
terraform apply

# OR force new deployment without changing tag
./scripts/update-ecs-services.sh
```

### Set Up CloudWatch Alarms
```bash
# CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name kitchenguard-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=kitchenguard-auth-service Name=ClusterName,Value=kitchenguard-cluster-prod

# Memory utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name kitchenguard-high-memory \
  --alarm-description "Alert when memory exceeds 80%" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=kitchenguard-auth-service Name=ClusterName,Value=kitchenguard-cluster-prod
```

---

## Troubleshooting

### Services Not Starting

**Check task status:**
```bash
aws ecs describe-tasks \
  --cluster kitchenguard-cluster-prod \
  --tasks $(aws ecs list-tasks --cluster kitchenguard-cluster-prod --query 'taskArns[0]' --output text) \
  --region us-east-2
```

**Common issues:**
1. **Image pull errors**: Verify ECR repository permissions
2. **Health check failures**: Check application logs
3. **Database connection errors**: Verify security groups allow traffic from ECS to RDS

### Health Check Failures

**View task logs:**
```bash
# Get task ID
TASK_ID=$(aws ecs list-tasks --cluster kitchenguard-cluster-prod --service-name kitchenguard-auth-service --query 'taskArns[0]' --output text | cut -d'/' -f3)

# View logs
aws logs get-log-events \
  --log-group-name /ecs/kitchenguard-auth-service \
  --log-stream-name ecs/auth-service/$TASK_ID \
  --region us-east-2
```

### Database Connection Issues

**Update RDS security group:**
```bash
# Get ECS security group ID
ECS_SG=$(terraform output -json | jq -r '.ecs_tasks_sg_id.value')

# Add inbound rule to RDS security group
aws ec2 authorize-security-group-ingress \
  --group-id YOUR_RDS_SECURITY_GROUP_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $ECS_SG \
  --region us-east-2
```

### High Costs

**Optimize costs:**
1. Reduce NAT Gateways (use 1 instead of 3): ~$32/month savings
2. Use Spot instances for non-critical tasks
3. Enable CloudWatch Logs retention limits
4. Use Reserved Capacity for consistent workloads

---

## Cost Estimation

### Monthly Costs (Production Setup)

#### Compute:
- **ECS Fargate** (6 tasks, 0.25 vCPU, 0.5 GB each):
  - Per task: ~$8/month
  - Total: 6 × $8 = **$48/month**

#### Networking:
- **Application Load Balancer**: **$16/month**
- **NAT Gateways** (3 × $32): **$96/month**
- **Data Transfer**: ~**$10/month**

#### Storage & Monitoring:
- **CloudWatch Logs** (7 days retention): **$5/month**
- **ECR Storage**: **$2/month**

#### Database:
- **RDS PostgreSQL** (existing): **$30/month** (already paid)

### Total: ~$177/month

### Cost Optimization Options:

**Option 1: Single NAT Gateway** (saves ~$64/month)
- Change `availability_zones` in terraform.tfvars to 1 AZ
- Total: **~$113/month**

**Option 2: Development Setup** (minimal costs)
- 1 task per service
- Single NAT Gateway
- Smaller instance sizes
- Total: **~$60/month**

---

## Next Steps

1. ✅ Deploy infrastructure
2. ✅ Test all endpoints
3. 🔄 Set up custom domain and SSL
4. 🔄 Deploy frontend to S3 + CloudFront
5. 🔄 Configure CI/CD pipeline (GitHub Actions)
6. 🔄 Set up monitoring and alerts
7. 🔄 Implement auto-scaling policies
8. 🔄 Add WAF for security

---

## Support & Resources

### Documentation
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Docker Documentation](https://docs.docker.com/)

### Useful Commands
```bash
# View all ECS services
aws ecs list-services --cluster kitchenguard-cluster-prod

# Describe a service
aws ecs describe-services --cluster kitchenguard-cluster-prod --services kitchenguard-auth-service

# View task definitions
aws ecs list-task-definitions --family-prefix kitchenguard

# Stop all tasks (for troubleshooting)
aws ecs update-service --cluster kitchenguard-cluster-prod --service kitchenguard-auth-service --desired-count 0

# Restart with new count
aws ecs update-service --cluster kitchenguard-cluster-prod --service kitchenguard-auth-service --desired-count 2
```

---

**Deployment Status: READY TO DEPLOY** ✅

All infrastructure code, scripts, and documentation are ready. Follow the steps above to deploy to AWS ECS Fargate!
