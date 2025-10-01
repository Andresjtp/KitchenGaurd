#!/bin/bash

# KitchenGuard Microservices Stop Script
echo "🛑 Stopping KitchenGuard Microservices..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop service by PID file
stop_service_by_pid() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            echo -e "${GREEN}✅ Stopped $service_name (PID: $pid)${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name was not running${NC}"
        fi
        rm "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
    fi
}

# Function to stop service by port
stop_service_by_port() {
    local service_name=$1
    local port=$2
    
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        kill $pid
        echo -e "${GREEN}✅ Stopped $service_name on port $port (PID: $pid)${NC}"
    else
        echo -e "${YELLOW}⚠️  No service running on port $port${NC}"
    fi
}

echo -e "${YELLOW}Stopping services by PID files...${NC}"

# Stop services by PID files
stop_service_by_pid "API Gateway" "./microservices/api-gateway/api-gateway.pid"
stop_service_by_pid "Inventory Service" "./microservices/inventory-service/inventory-service.pid"
stop_service_by_pid "Notification Service" "./microservices/notification-service/notification-service.pid"
stop_service_by_pid "Analytics Service" "./microservices/analytics-service/analytics-service.pid"
stop_service_by_pid "Frontend" "./frontend/frontend.pid"

echo ""
echo -e "${YELLOW}Stopping services by ports (fallback)...${NC}"

# Stop services by ports (fallback)
stop_service_by_port "API Gateway" 8000
stop_service_by_port "Inventory Service" 8001
stop_service_by_port "Notification Service" 8005
stop_service_by_port "Analytics Service" 8006
stop_service_by_port "Frontend" 3000

echo ""
echo -e "${YELLOW}Cleaning up log files...${NC}"

# Clean up log files (optional)
find . -name "*.log" -type f -delete 2>/dev/null && echo -e "${GREEN}✅ Cleaned up log files${NC}"

echo ""
echo -e "${GREEN}🎉 All KitchenGuard services have been stopped!${NC}"