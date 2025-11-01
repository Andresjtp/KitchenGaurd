#!/bin/bash

# Update ECS Services with new Docker images
# Usage: ./update-ecs-services.sh [cluster-name] [region]

set -e

# Configuration
CLUSTER_NAME="${1:-kitchenguard-cluster-prod}"
AWS_REGION="${2:-us-east-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KitchenGuard - Update ECS Services${NC}"
echo -e "${GREEN}========================================${NC}"

# Service names
SERVICES=("kitchenguard-auth-service" "kitchenguard-inventory-service" "kitchenguard-api-gateway")

for SERVICE in "${SERVICES[@]}"; do
    echo -e "\n${YELLOW}Updating service: $SERVICE${NC}"
    
    # Force new deployment
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE \
        --force-new-deployment \
        --region $AWS_REGION
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Service $SERVICE update initiated${NC}"
    else
        echo -e "${RED}Failed to update service $SERVICE${NC}"
    fi
done

echo -e "\n${YELLOW}Waiting for services to stabilize...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"

for SERVICE in "${SERVICES[@]}"; do
    echo -e "\n${YELLOW}Waiting for $SERVICE...${NC}"
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services $SERVICE \
        --region $AWS_REGION
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}$SERVICE is stable${NC}"
    else
        echo -e "${RED}$SERVICE failed to stabilize${NC}"
    fi
done

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All services updated successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nCheck service status:"
echo -e "  aws ecs describe-services --cluster $CLUSTER_NAME --services ${SERVICES[*]} --region $AWS_REGION"
echo -e "\nView logs:"
echo -e "  aws logs tail /ecs/kitchenguard-auth-service --follow --region $AWS_REGION"
echo -e "  aws logs tail /ecs/kitchenguard-inventory-service --follow --region $AWS_REGION"
echo -e "  aws logs tail /ecs/kitchenguard-api-gateway --follow --region $AWS_REGION"
