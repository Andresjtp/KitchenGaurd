# 🍽️ KitchenGuard

A **microservices-based** web application that helps restaurants track inventory, predict orders with AI, and detect unusual usage to reduce losses.

## 🏗️ Microservices Architecture

```
kitchenguard/
├── microservices/
│   ├── api-gateway/         # Entry point, routing, auth
│   ├── inventory-service/   # Product & stock management
│   ├── notification-service/# Alerts & messaging
│   └── analytics-service/   # Data analysis & reporting
├── frontend/                # React web application
├── docker-compose.yml       # Container orchestration
├── start-microservices.sh   # Development startup script
└── stop-services.sh         # Service shutdown script
```

### 🚀 **Service Architecture**
- **API Gateway** (Port 8000): Routes requests, handles auth, rate limiting
- **Inventory Service** (Port 8001): CRUD operations for products and stock
- **Notification Service** (Port 8005): Alerts, messaging, and notifications
- **Analytics Service** (Port 8006): Data analysis, reporting, dashboards
- **Frontend** (Port 3000): React UI consuming microservices via API Gateway

## Features

### Phase 1: Inventory Tracking ✅
- **Inventory Management**: Track products with stock levels, costs, and supplier information
- **CRUD Operations**: Add, view, update, and delete inventory items
- **Real-time Updates**: Live inventory tracking with stock adjustments
- **Database**: SQLite database for lightweight, efficient storage

### Phase 2: AI Order Prediction (Coming Soon)
- Predict future orders based on historical data
- Machine learning algorithms for demand forecasting
- Integration with inventory levels for automated reordering

### Phase 3: Usage Anomaly Detection (Coming Soon)
- Detect unusual usage patterns
- Alert system for potential losses or theft
- Analytics dashboard for usage insights

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Quick Start (Recommended)

1. **Start All Microservices:**
   ```bash
   ./start-microservices.sh
   ```

2. **Access the Application:**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000

3. **Stop All Services:**
   ```bash
   ./stop-services.sh
   ```

### Manual Setup

If you prefer to start services individually:

1. **Start Inventory Service:**
   ```bash
   cd microservices/inventory-service
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python app.py  # Runs on port 8001
   ```

2. **Start Notification Service:**
   ```bash
   cd microservices/notification-service
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python app.py  # Runs on port 8005
   ```

3. **Start Analytics Service:**
   ```bash
   cd microservices/analytics-service
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python app.py  # Runs on port 8006
   ```

4. **Start API Gateway:**
   ```bash
   cd microservices/api-gateway
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python app.py  # Runs on port 8000
   ```

5. **Start Frontend:**
   ```bash
   cd frontend
   npm install
   npm start  # Runs on port 3000
   ```

## 🔌 API Endpoints

### Authentication
All API requests require an API key header:
```bash
-H "X-API-Key: kitchenguard-api-key"
```

### Inventory Management (via API Gateway)
- `GET /api/inventory` - List all products
- `POST /api/inventory` - Add new product
- `PUT /api/inventory/{id}` - Update product
- `DELETE /api/inventory/{id}` - Delete product
- `GET /api/inventory/low-stock` - Get low stock items

### Service Health Checks
- `GET /health` - API Gateway health
- Direct service health: ports 8001, 8005, 8006

### 🛠️ Example API Usage

**Get all inventory:**
```bash
curl -H "X-API-Key: kitchenguard-api-key" \
  http://localhost:8000/api/inventory
```

**Add a new product:**
```bash
curl -X POST \
  -H "X-API-Key: kitchenguard-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomatoes",
    "category": "Produce", 
    "current_stock": 50,
    "unit_cost": 2.99,
    "supplier": "Fresh Farm Co"
  }' \
  http://localhost:8000/api/inventory
```

**Get analytics dashboard:**
```bash
curl -H "X-API-Key: kitchenguard-api-key" \
  http://localhost:8000/api/analytics/dashboard
```

## Database Schema

### Products Table
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    current_stock INTEGER DEFAULT 0,
    unit_cost REAL,
    supplier TEXT
);
```

## 🛠️ Technology Stack

### **Microservices Architecture**
- **API Gateway**: Flask + Request Routing + Authentication
- **Service Discovery**: Automatic service registration
- **Inter-Service Communication**: REST APIs + Event Publishing
- **Load Balancing**: Round-robin (extensible to multiple instances)

### **Backend Services**
- **Languages**: Python (Flask)
- **Database**: SQLite (per service) + PostgreSQL (production ready)
- **Caching**: In-memory + Redis (production ready)
- **Message Queue**: Event-based communication

### **Frontend**
- **Framework**: React (JavaScript)
- **HTTP Client**: Axios with API Gateway integration
- **Styling**: CSS3
- **Authentication**: API Key based

### **DevOps & Deployment**
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Docker Compose (Kubernetes ready)
- **Monitoring**: Health checks + Service registry
- **Development**: Hot reload + Automated startup scripts

## Development Roadmap

- [x] Basic project structure
- [x] SQLite database setup
- [x] Flask API with CRUD operations
- [x] React frontend with inventory table
- [x] Add/Update/Delete functionality
- [ ] User authentication
- [ ] Advanced filtering and search
- [ ] Export functionality
- [ ] Mobile responsiveness improvements
- [ ] AI-powered order prediction
- [ ] Anomaly detection system

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please open an issue on GitHub.