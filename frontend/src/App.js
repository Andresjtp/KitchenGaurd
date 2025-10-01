import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';
const API_KEY = 'kitchenguard-api-key';

function App() {
  const [products, setProducts] = useState([]);
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

  // Configure axios defaults
  const axiosConfig = {
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    }
  };

  // Fetch inventory data
  const fetchInventory = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/inventory`, axiosConfig);
      setProducts(response.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch inventory data. Make sure the microservices are running.');
      console.error('Error fetching inventory:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

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

  return (
    <div className="App">
      <div className="header">
        <h1>🍽️ KitchenGuard</h1>
        <p>Restaurant Inventory Management System</p>
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
          <h3 style={{ padding: '20px', margin: '0', backgroundColor: '#34495e', color: 'white' }}>
            Current Inventory
          </h3>
          
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