# 🚀 AWS ECS Fargate Deployment - Quick Start Checklist

## Pre-Deployment Checklist

- [ ] **AWS CLI installed and configured**
  ```bash
  aws configure
  aws sts get-caller-identity
  ```

- [ ] **Docker installed**
  ```bash
  docker --version
  ```

- [ ] **Terraform installed**
  ```bash
  terraform --version
  ```

- [ ] **Generate JWT Secret**
  ```bash
  openssl rand -base64 32
  # Save this value!
  ```

- [ ] **Create terraform.tfvars**
  ```bash
  cd aws-infrastructure/terraform
  cp terraform.tfvars.example terraform.tfvars
  nano terraform.tfvars
  # Update: rds_endpoint, db_user, db_password, jwt_secret_key
  ```

---

## Deployment Steps

### Phase 1: Test Locally
- [ ] **Build images**
  ```bash
  docker-compose -f docker-compose.prod.yml build
  ```

- [ ] **Test locally**
  ```bash
  docker-compose -f docker-compose.prod.yml up
  # Test: curl http://localhost:8000/health
  ```

- [ ] **Stop containers**
  ```bash
  docker-compose -f docker-compose.prod.yml down
  ```

### Phase 2: Create ECR Repositories
- [ ] **Initialize Terraform**
  ```bash
  cd aws-infrastructure/terraform
  terraform init
  ```

- [ ] **Create ECR repos**
  ```bash
  terraform apply -target=aws_ecr_repository.auth_service \
                  -target=aws_ecr_repository.inventory_service \
                  -target=aws_ecr_repository.api_gateway \
                  -auto-approve
  ```

### Phase 3: Build and Push Images
- [ ] **Build and push to ECR**
  ```bash
  cd ../..  # Back to project root
  ./scripts/build-and-push.sh us-east-2 v1.0.0
  ```

- [ ] **Verify images in ECR**
  ```bash
  aws ecr describe-images --repository-name kitchenguard-auth --region us-east-2
  aws ecr describe-images --repository-name kitchenguard-inventory --region us-east-2
  aws ecr describe-images --repository-name kitchenguard-gateway --region us-east-2
  ```

### Phase 4: Deploy Infrastructure
- [ ] **Review Terraform plan**
  ```bash
  cd aws-infrastructure/terraform
  terraform plan
  ```

- [ ] **Apply infrastructure**
  ```bash
  terraform apply
  # Type 'yes' when prompted
  # Wait 10-15 minutes
  ```

- [ ] **Get ALB URL**
  ```bash
  terraform output alb_dns_name
  # Save this URL!
  ```

### Phase 5: Verify Deployment
- [ ] **Check ECS services**
  ```bash
  aws ecs list-services --cluster kitchenguard-cluster-prod --region us-east-2
  ```

- [ ] **Check running tasks**
  ```bash
  aws ecs list-tasks --cluster kitchenguard-cluster-prod --region us-east-2
  ```

- [ ] **Test health endpoints**
  ```bash
  ALB_URL=$(terraform output -raw alb_dns_name)
  curl http://$ALB_URL/health
  ```

- [ ] **Test registration**
  ```bash
  curl -X POST http://$ALB_URL/register \
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
  ```

---

## Post-Deployment

### Monitoring Setup
- [ ] **View logs**
  ```bash
  aws logs tail /ecs/kitchenguard-auth-service --follow --region us-east-2
  ```

- [ ] **Set up CloudWatch alarms** (optional)
  ```bash
  # See AWS_ECS_DEPLOYMENT_GUIDE.md for alarm commands
  ```

### Frontend Update
- [ ] **Update frontend environment**
  ```bash
  cd frontend
  echo "REACT_APP_API_URL=http://YOUR_ALB_URL" > .env.production
  ```

- [ ] **Build frontend**
  ```bash
  npm run build
  ```

- [ ] **Deploy to S3 + CloudFront** (separate guide needed)

### Optional Enhancements
- [ ] **Set up custom domain** (Route 53)
- [ ] **Enable HTTPS** (ACM Certificate)
- [ ] **Configure auto-scaling**
- [ ] **Set up CI/CD** (GitHub Actions)
- [ ] **Add WAF rules** (security)

---

## Quick Commands Reference

### View Service Status
```bash
CLUSTER=kitchenguard-cluster-prod
aws ecs describe-services --cluster $CLUSTER --services kitchenguard-auth-service --region us-east-2
```

### Force New Deployment
```bash
./scripts/update-ecs-services.sh
```

### Scale Services
```bash
# Edit terraform.tfvars: desired_count_auth = 4
terraform apply
```

### View Logs
```bash
aws logs tail /ecs/kitchenguard-auth-service --follow --region us-east-2
aws logs tail /ecs/kitchenguard-inventory-service --follow --region us-east-2
aws logs tail /ecs/kitchenguard-api-gateway --follow --region us-east-2
```

### Rollback
```bash
# Update image tag in terraform.tfvars to previous version
ecr_image_tag = "v1.0.0"  # Previous version
terraform apply
```

---

## Troubleshooting Quick Fixes

### Services not starting
```bash
# Check task status
aws ecs describe-tasks --cluster kitchenguard-cluster-prod --tasks TASK_ID --region us-east-2

# View task logs
aws logs get-log-events --log-group-name /ecs/kitchenguard-auth-service --log-stream-name STREAM_NAME --region us-east-2
```

### Health check failures
```bash
# Check application logs
aws logs tail /ecs/kitchenguard-auth-service --follow --region us-east-2

# Verify database connectivity
aws ec2 describe-security-groups --group-ids SG_ID --region us-east-2
```

### Database connection errors
```bash
# Add ECS security group to RDS security group
ECS_SG=$(terraform output -json | jq -r '.ecs_tasks_sg_id.value')
aws ec2 authorize-security-group-ingress \
  --group-id RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $ECS_SG \
  --region us-east-2
```

---

## Cost Optimization Tips

1. **Reduce NAT Gateways**: Use 1 instead of 3 (saves ~$64/month)
2. **Lower task count**: Use 1 task per service for dev (saves ~$24/month)
3. **Smaller instance sizes**: Use 128 CPU / 256 MB for less traffic
4. **CloudWatch Logs retention**: Set to 3 days instead of 7

---

## Success Criteria

✅ All 3 ECR repositories created  
✅ All 3 Docker images pushed to ECR  
✅ VPC and networking infrastructure deployed  
✅ Application Load Balancer accessible  
✅ 6 ECS tasks running (2 per service)  
✅ Health endpoints returning 200 OK  
✅ Registration endpoint working  
✅ CloudWatch logs streaming  

---

## Estimated Time

- **Pre-deployment setup**: 15 minutes
- **Local testing**: 10 minutes
- **ECR setup**: 5 minutes
- **Build and push images**: 10 minutes
- **Infrastructure deployment**: 15 minutes
- **Testing and verification**: 10 minutes

**Total**: ~65 minutes

---

## Need Help?

- See full guide: `AWS_ECS_DEPLOYMENT_GUIDE.md`
- Check logs: `aws logs tail /ecs/kitchenguard-auth-service --follow --region us-east-2`
- Terraform docs: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- AWS ECS docs: https://docs.aws.amazon.com/ecs/

---

**Status: READY TO DEPLOY** ✅

All files prepared. Start with Pre-Deployment Checklist!
