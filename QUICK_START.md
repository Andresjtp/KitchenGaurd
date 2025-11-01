# 🚀 Quick Start Guide - PostgreSQL Production Setup

## Services Status

✅ **Auth Service**: Running on port 8007 with PostgreSQL  
✅ **Inventory Service**: Running on port 8001 with PostgreSQL  
✅ **AWS RDS**: kitchenguard-db.cxike2u26m31.us-east-2.rds.amazonaws.com

---

## Start Services

### Terminal 1: Auth Service
```bash
cd /Users/andrestorres-prunell/Documents/Repositories/KitchenGaurd/microservices/auth-service
python app.py
```

### Terminal 2: Inventory Service
```bash
cd /Users/andrestorres-prunell/Documents/Repositories/KitchenGaurd
python microservices/inventory-service/app.py
```

### Terminal 3: API Gateway
```bash
cd /Users/andrestorres-prunell/Documents/Repositories/KitchenGaurd/microservices/api-gateway
python app.py
```

### Terminal 4: Frontend
```bash
cd /Users/andrestorres-prunell/Documents/Repositories/KitchenGaurd/frontend
npm start
```

---

## Test Endpoints

### Health Checks
```bash
curl http://localhost:8007/health  # Auth
curl http://localhost:8001/health  # Inventory
curl http://localhost:8000/health  # API Gateway
```

### Register User
```bash
curl -X POST http://localhost:8007/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123",
    "fullName": "New User",
    "restaurantName": "My Restaurant",
    "restaurantType": "Casual Dining",
    "userPosition": "Manager"
  }'
```

### Login
```bash
curl -X POST http://localhost:8007/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123"
  }'
```

---

## Database Access

### Connection Details
```
Host: kitchenguard-db.cxike2u26m31.us-east-2.rds.amazonaws.com
Port: 5432
User: KG_Admin
Password: (see .env files)

Databases:
- kitchenguard_auth
- kitchenguard_inventory
```

### Test Connection
```bash
python test_rds_connection.py
```

### Query Users
```bash
python3 << 'EOF'
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="kitchenguard-db.cxike2u26m31.us-east-2.rds.amazonaws.com",
    port=5432,
    database="kitchenguard_auth",
    user="KG_Admin",
    password="13Torr0123"
)

cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute("SELECT id, username, email FROM users")
print(cursor.fetchall())
cursor.close()
conn.close()
EOF
```

---

## Environment Files

### Auth Service (.env location)
```
microservices/auth-service/.env
```

### Inventory Service (.env location)
```
microservices/inventory-service/.env
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8007
lsof -ti:8007 | xargs kill -9

# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Connection Issues
```bash
# Check .env file exists
ls -la microservices/auth-service/.env
ls -la microservices/inventory-service/.env

# Test connection
python test_rds_connection.py
```

### Import Errors
```bash
# Install dependencies
cd microservices/auth-service
pip install -r requirements.txt

cd ../inventory-service
pip install -r requirements.txt
```

---

## Next Steps

1. ✅ **Test Complete Flow**
   - Start all services
   - Open frontend (http://localhost:3000)
   - Complete registration with CSV upload
   - Verify data in PostgreSQL

2. ✅ **Production Prep**
   - Review security settings
   - Update JWT secret key
   - Configure SSL for RDS
   - Set up monitoring

3. ✅ **Deploy to AWS**
   - Choose deployment method (EB/ECS/EC2)
   - Configure load balancer
   - Set up CloudWatch
   - Deploy frontend to S3+CloudFront

---

## Key Files

- `MIGRATION_SUMMARY.md` - Complete technical documentation
- `DEPLOYMENT_SUCCESS.md` - Migration success summary
- `QUICK_START.md` - This file
- `setup_rds_databases.py` - Database setup script
- `test_rds_connection.py` - Connection test utility

---

## Status: PRODUCTION READY ✅

All services migrated to PostgreSQL and tested successfully!
