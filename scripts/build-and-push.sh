#!/bin/bash

# Build and Push Docker Images to AWS ECR
# Usage: ./build-and-push.sh [region] [tag]

set -e

# Configuration
AWS_REGION="${1:-us-east-2}"
IMAGE_TAG="${2:-latest}"
PROJECT_NAME="kitchenguard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KitchenGuard - Build and Push to ECR${NC}"
echo -e "${GREEN}========================================${NC}"

# Get AWS Account ID
echo -e "\n${YELLOW}Getting AWS Account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Could not get AWS Account ID. Make sure AWS CLI is configured.${NC}"
    exit 1
fi
echo -e "${GREEN}AWS Account ID: $AWS_ACCOUNT_ID${NC}"

# ECR Repository URLs
AUTH_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-auth"
INVENTORY_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-inventory"
GATEWAY_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-gateway"

# Login to ECR
echo -e "\n${YELLOW}Logging in to Amazon ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to login to ECR${NC}"
    exit 1
fi
echo -e "${GREEN}Successfully logged in to ECR${NC}"

# Build and push Auth Service
echo -e "\n${YELLOW}Building Auth Service...${NC}"
cd microservices/auth-service
docker build --platform linux/amd64 -t $PROJECT_NAME-auth:$IMAGE_TAG .
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to build auth service${NC}"
    exit 1
fi
docker tag $PROJECT_NAME-auth:$IMAGE_TAG $AUTH_REPO:$IMAGE_TAG
docker tag $PROJECT_NAME-auth:$IMAGE_TAG $AUTH_REPO:latest

echo -e "${YELLOW}Pushing Auth Service to ECR...${NC}"
docker push $AUTH_REPO:$IMAGE_TAG
docker push $AUTH_REPO:latest
echo -e "${GREEN}Auth Service pushed successfully${NC}"
cd ../..

# Build and push Inventory Service
echo -e "\n${YELLOW}Building Inventory Service...${NC}"
cd microservices/inventory-service
docker build --platform linux/amd64 -t $PROJECT_NAME-inventory:$IMAGE_TAG .
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to build inventory service${NC}"
    exit 1
fi
docker tag $PROJECT_NAME-inventory:$IMAGE_TAG $INVENTORY_REPO:$IMAGE_TAG
docker tag $PROJECT_NAME-inventory:$IMAGE_TAG $INVENTORY_REPO:latest

echo -e "${YELLOW}Pushing Inventory Service to ECR...${NC}"
docker push $INVENTORY_REPO:$IMAGE_TAG
docker push $INVENTORY_REPO:latest
echo -e "${GREEN}Inventory Service pushed successfully${NC}"
cd ../..

# Build and push API Gateway
echo -e "\n${YELLOW}Building API Gateway...${NC}"
cd microservices/api-gateway
docker build --platform linux/amd64 -t $PROJECT_NAME-gateway:$IMAGE_TAG .
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to build API gateway${NC}"
    exit 1
fi
docker tag $PROJECT_NAME-gateway:$IMAGE_TAG $GATEWAY_REPO:$IMAGE_TAG
docker tag $PROJECT_NAME-gateway:$IMAGE_TAG $GATEWAY_REPO:latest

echo -e "${YELLOW}Pushing API Gateway to ECR...${NC}"
docker push $GATEWAY_REPO:$IMAGE_TAG
docker push $GATEWAY_REPO:latest
echo -e "${GREEN}API Gateway pushed successfully${NC}"
cd ../..

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All images built and pushed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nImage URLs:"
echo -e "  Auth:      ${AUTH_REPO}:${IMAGE_TAG}"
echo -e "  Inventory: ${INVENTORY_REPO}:${IMAGE_TAG}"
echo -e "  Gateway:   ${GATEWAY_REPO}:${IMAGE_TAG}"
echo -e "\nNext steps:"
echo -e "  1. Deploy infrastructure: cd aws-infrastructure/terraform && terraform apply"
echo -e "  2. Update ECS services: ./scripts/update-ecs-services.sh"
