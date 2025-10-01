# 🍽️ KitchenGuard

A web-based application that helps restaurants track inventory, predict orders with AI, and detect unusual usage to reduce losses.

## Project Structure

```
kitchenguard/
├── backend/ (Flask/FastAPI code)
│   ├── app.py
│   ├── models.py
│   ├── database.db
│   └── requirements.txt
├── frontend/ (React code)
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   └── index.css
│   ├── public/
│   │   └── index.html
│   └── package.json
└── README.md
```

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

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask application:
   ```bash
   python app.py
   ```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Inventory Management
- `GET /inventory` - List all products
- `POST /inventory` - Add new product
- `PUT /inventory/{id}` - Update product
- `DELETE /inventory/{id}` - Delete product
- `GET /health` - Health check

### Example API Usage

**Add a new product:**
```bash
curl -X POST http://localhost:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tomatoes",
    "category": "Produce",
    "current_stock": 50,
    "unit_cost": 2.99,
    "supplier": "Fresh Farm Co"
  }'
```

**Get all inventory:**
```bash
curl http://localhost:5000/inventory
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

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: React (JavaScript)
- **Database**: SQLite
- **Styling**: CSS3
- **HTTP Client**: Axios
- **CORS**: Flask-CORS

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