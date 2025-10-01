#!/bin/bash

# KitchenGuard Microservices Startup Script
echo "🚀 Starting KitchenGuard Microservices..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Port $1 is already in use${NC}"
        return 1
    else
        return 0
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local service_path=$2
    local port=$3
    
    echo -e "${BLUE}Starting $service_name on port $port...${NC}"
    
    if ! check_port $port; then
        echo -e "${YELLOW}Skipping $service_name - port $port is busy${NC}"
        return 1
    fi
    
    cd "$service_path"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment for $service_name...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Start the service in background
    python app.py > "$service_name.log" 2>&1 &
    local pid=$!
    
    # Store PID for later cleanup
    echo $pid > "$service_name.pid"
    
    echo -e "${GREEN}✅ $service_name started (PID: $pid)${NC}"
    cd - > /dev/null
    
    # Wait a moment for service to start
    sleep 2
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 is required but not installed${NC}"
    exit 1
fi

# Check if Node.js is installed (for frontend)
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is required but not installed${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs

echo -e "${BLUE}Checking prerequisites...${NC}"

# Start services in dependency order
echo -e "${BLUE}Starting backend microservices...${NC}"

# 1. Start Inventory Service (core service)
start_service "inventory-service" "./microservices/inventory-service" 8001

# 2. Start Notification Service
start_service "notification-service" "./microservices/notification-service" 8005

# 3. Start Analytics Service
start_service "analytics-service" "./microservices/analytics-service" 8006

# 4. Start API Gateway (depends on other services)
start_service "api-gateway" "./microservices/api-gateway" 8000

# 5. Start Frontend
echo -e "${BLUE}Starting frontend...${NC}"
if check_port 3000; then
    cd frontend
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install > /dev/null 2>&1
    fi
    
    # Start React development server
    BROWSER=none npm start > frontend.log 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > frontend.pid
    
    echo -e "${GREEN}✅ Frontend started (PID: $frontend_pid)${NC}"
    cd - > /dev/null
else
    echo -e "${YELLOW}Skipping frontend - port 3000 is busy${NC}"
fi

echo ""
echo -e "${GREEN}🎉 KitchenGuard Microservices are starting up!${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo "  🌐 API Gateway:     http://localhost:8000"
echo "  📦 Inventory:       http://localhost:8001"
echo "  🔔 Notifications:   http://localhost:8005"
echo "  📊 Analytics:       http://localhost:8006"
echo "  🖥️  Frontend:        http://localhost:3000"
echo ""
echo -e "${BLUE}Health Checks:${NC}"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8001/health"
echo "  curl http://localhost:8005/health"
echo "  curl http://localhost:8006/health"
echo ""
echo -e "${BLUE}API Examples:${NC}"
echo "  # Get inventory (requires API key)"
echo "  curl -H 'X-API-Key: kitchenguard-api-key' http://localhost:8000/api/inventory"
echo ""
echo "  # Add product"
echo "  curl -X POST -H 'X-API-Key: kitchenguard-api-key' -H 'Content-Type: application/json' \\"
echo "    -d '{\"name\":\"Tomatoes\",\"category\":\"Produce\",\"current_stock\":50,\"unit_cost\":2.99}' \\"
echo "    http://localhost:8000/api/inventory"
echo ""
echo -e "${YELLOW}To stop all services, run: ./stop-services.sh${NC}"
echo -e "${YELLOW}Logs are available in each service directory${NC}"

# Wait for user to press Ctrl+C
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all services...${NC}"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all services...${NC}"
    
    # Stop all services
    for service in api-gateway inventory-service notification-service analytics-service frontend; do
        if [ -f "$service.pid" ] || [ -f "microservices/*/$service.pid" ] || [ -f "frontend/$service.pid" ]; then
            pid_file=$(find . -name "$service.pid" 2>/dev/null | head -1)
            if [ -f "$pid_file" ]; then
                pid=$(cat "$pid_file")
                if kill -0 $pid 2>/dev/null; then
                    kill $pid
                    echo -e "${GREEN}✅ Stopped $service (PID: $pid)${NC}"
                fi
                rm "$pid_file"
            fi
        fi
    done
    
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Keep script running
wait