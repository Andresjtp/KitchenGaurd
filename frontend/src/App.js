import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AuthWrapper } from './components/Auth';

const API_BASE_URL = 'http://localhost:8000/api';
const API_KEY = 'kitchenguard-api-key';

function App() {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [inventoryData, setInventoryData] = useState({ kitchen: [], bar: [], combined: [] });
  const [currentView, setCurrentView] = useState('combined'); // 'kitchen', 'bar', or 'combined'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    current_stock: 0,
    unit_cost: 0,
    supplier: ''
  });

  // Check for existing authentication on app load
  useEffect(() => {
    const checkAuthStatus = () => {
      const storedUser = localStorage.getItem('kitchenguard_user');
      const storedToken = localStorage.getItem('kitchenguard_token');
      
      if (storedUser && storedToken) {
        try {
          const userData = JSON.parse(storedUser);
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Error parsing stored user data:', error);
          localStorage.removeItem('kitchenguard_user');
          localStorage.removeItem('kitchenguard_token');
        }
      }
      setAuthLoading(false);
    };

    checkAuthStatus();
  }, []);

  // Authentication handlers
  const handleAuthSuccess = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('kitchenguard_user');
    localStorage.removeItem('kitchenguard_token');
    setUser(null);
    setIsAuthenticated(false);
    setProducts([]);
  };

  // Configure axios defaults
  const axiosConfig = {
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    }
  };

  // Fetch inventory data
  const fetchInventory = async () => {
    if (!user?.id) {
      setError('User ID not available');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/inventory/user/${user.id}`, axiosConfig);
      
      if (response.data.combined || response.data.kitchen || response.data.bar) {
        setInventoryData(response.data);
        setProducts(response.data.combined || []);
      } else {
        // Handle case where response is just an array
        setProducts(response.data);
        setInventoryData({ 
          kitchen: response.data.filter(item => item.type === 'kitchen') || [],
          bar: response.data.filter(item => item.type === 'bar') || [],
          combined: response.data 
        });
      }
      setError('');
    } catch (err) {
      setError('Failed to fetch inventory data. Make sure the microservices are running.');
      console.error('Error fetching inventory:', err);
      setProducts([]);
      setInventoryData({ kitchen: [], bar: [], combined: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user?.id) {
      fetchInventory();
    }
  }, [isAuthenticated, user?.id]);

  // Handle inventory view switching
  const handleViewChange = (view) => {
    setCurrentView(view);
    switch(view) {
      case 'kitchen':
        setProducts(inventoryData.kitchen || []);
        break;
      case 'bar':
        setProducts(inventoryData.bar || []);
        break;
      case 'combined':
      default:
        setProducts(inventoryData.combined || []);
        break;
    }
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'current_stock' || name === 'unit_cost' ? Number(value) : value
    }));
  };

  // Add new product
  const handleAddProduct = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE_URL}/inventory`, formData, axiosConfig);
      setFormData({
        name: '',
        category: '',
        current_stock: 0,
        unit_cost: 0,
        supplier: ''
      });
      setShowForm(false);
      fetchInventory();
    } catch (err) {
      setError('Failed to add product');
      console.error('Error adding product:', err);
    }
  };

  // Delete product
  const handleDeleteProduct = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        await axios.delete(`${API_BASE_URL}/inventory/${productId}`, axiosConfig);
        fetchInventory();
      } catch (err) {
        setError('Failed to delete product');
        console.error('Error deleting product:', err);
      }
    }
  };

  // Update stock (simple increment/decrement for now)
  const updateStock = async (productId, currentStock, change) => {
    const newStock = Math.max(0, currentStock + change);
    try {
      await axios.put(`${API_BASE_URL}/inventory/${productId}`, {
        current_stock: newStock
      }, axiosConfig);
      fetchInventory();
    } catch (err) {
      setError('Failed to update stock');
      console.error('Error updating stock:', err);
    }
  };

  // Show loading screen while checking authentication
  if (authLoading) {
    return (
      <div className="App">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading KitchenGuard...</p>
        </div>
      </div>
    );
  }

  // Show authentication screen if not logged in
  if (!isAuthenticated) {
    return <AuthWrapper onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="App">
      <div className="header">
        <h1>🍽️ KitchenGuard</h1>
        <p>Restaurant Inventory Management System</p>
        <div className="user-info">
          <div className="user-details">
            <span className="user-name">Welcome, {user?.fullName}</span>
            <span className="user-restaurant">{user?.restaurantName} • {user?.userPosition}</span>
          </div>
          <button 
            className="btn btn-logout"
            onClick={handleLogout}
            title="Logout"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="container">
        {error && <div className="error">{error}</div>}

        <div style={{ marginBottom: '20px' }}>
          <button 
            className="btn btn-primary"
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? 'Cancel' : 'Add New Product'}
          </button>
          <button 
            className="btn btn-success"
            onClick={fetchInventory}
            style={{ marginLeft: '10px' }}
          >
            Refresh Inventory
          </button>
        </div>

        {showForm && (
          <div className="form-container">
            <h3>Add New Product</h3>
            <form onSubmit={handleAddProduct}>
              <div className="form-group">
                <label>Product Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="form-control"
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Category</label>
                <input
                  type="text"
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className="form-control"
                  placeholder="e.g., Produce, Dairy, Meat"
                />
              </div>
              
              <div className="form-group">
                <label>Current Stock</label>
                <input
                  type="number"
                  name="current_stock"
                  value={formData.current_stock}
                  onChange={handleInputChange}
                  className="form-control"
                  min="0"
                />
              </div>
              
              <div className="form-group">
                <label>Unit Cost ($)</label>
                <input
                  type="number"
                  name="unit_cost"
                  value={formData.unit_cost}
                  onChange={handleInputChange}
                  className="form-control"
                  step="0.01"
                  min="0"
                />
              </div>
              
              <div className="form-group">
                <label>Supplier</label>
                <input
                  type="text"
                  name="supplier"
                  value={formData.supplier}
                  onChange={handleInputChange}
                  className="form-control"
                />
              </div>
              
              <button type="submit" className="btn btn-success">
                Add Product
              </button>
            </form>
          </div>
        )}

        <div className="inventory-table">
          <div style={{ backgroundColor: '#34495e', color: 'white', padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: '0' }}>
              Current Inventory
              {currentView === 'kitchen' && ' - Kitchen'}
              {currentView === 'bar' && ' - Bar'}
              {currentView === 'combined' && ' - All Items'}
            </h3>
            <div className="inventory-tabs">
              <button 
                className={`btn ${currentView === 'combined' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleViewChange('combined')}
                style={{ marginRight: '5px', fontSize: '14px', padding: '6px 12px' }}
              >
                All ({inventoryData.combined?.length || 0})
              </button>
              <button 
                className={`btn ${currentView === 'kitchen' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleViewChange('kitchen')}
                style={{ marginRight: '5px', fontSize: '14px', padding: '6px 12px' }}
              >
                Kitchen ({inventoryData.kitchen?.length || 0})
              </button>
              <button 
                className={`btn ${currentView === 'bar' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => handleViewChange('bar')}
                style={{ fontSize: '14px', padding: '6px 12px' }}
              >
                Bar ({inventoryData.bar?.length || 0})
              </button>
            </div>
          </div>
          
          {loading ? (
            <div className="loading">Loading inventory...</div>
          ) : products.length === 0 ? (
            <div className="loading">No products in inventory. Add some products to get started!</div>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Product Name</th>
                  <th>Type</th>
                  <th>Category</th>
                  <th>Current Stock</th>
                  <th>Unit Cost</th>
                  <th>Total Value</th>
                  <th>Supplier</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map(product => (
                  <tr key={product.id}>
                    <td>{product.id}</td>
                    <td>{product.name}</td>
                    <td>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: '4px', 
                        fontSize: '12px',
                        backgroundColor: product.type === 'kitchen' ? '#27ae60' : '#8e44ad',
                        color: 'white'
                      }}>
                        {product.type === 'kitchen' ? '🍽️ Kitchen' : '🍸 Bar'}
                      </span>
                    </td>
                    <td>{product.category}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <button 
                          className="btn"
                          style={{ fontSize: '12px', padding: '4px 8px', backgroundColor: '#95a5a6', color: 'white' }}
                          onClick={() => updateStock(product.id, product.current_stock, -1)}
                        >
                          -
                        </button>
                        <span style={{ minWidth: '30px', textAlign: 'center' }}>
                          {product.current_stock}
                        </span>
                        <button 
                          className="btn"
                          style={{ fontSize: '12px', padding: '4px 8px', backgroundColor: '#95a5a6', color: 'white' }}
                          onClick={() => updateStock(product.id, product.current_stock, 1)}
                        >
                          +
                        </button>
                      </div>
                    </td>
                    <td>${product.unit_cost.toFixed(2)}</td>
                    <td>${(product.current_stock * product.unit_cost).toFixed(2)}</td>
                    <td>{product.supplier}</td>
                    <td>
                      <button 
                        className="btn btn-danger"
                        onClick={() => handleDeleteProduct(product.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;