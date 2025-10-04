import React, { useState } from 'react';
import './Auth.css';

const Register = ({ onSwitchToLogin, onRegister }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Personal Information (Step 1)
    fullName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    // Restaurant Information (Step 2)
    restaurantName: '',
    restaurantType: '',
    userPosition: '',
    // Inventory Lists (Step 3)
    kitchenProduceList: [],
    barProduceList: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // File upload states
  const [kitchenFile, setKitchenFile] = useState(null);
  const [barFile, setBarFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState({
    kitchen: '',
    bar: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const validateStep1 = () => {
    if (!formData.fullName.trim()) {
      return 'Full name is required';
    }
    if (!formData.username.trim()) {
      return 'Username is required';
    }
    if (!formData.email.trim()) {
      return 'Email is required';
    }
    if (!formData.email.includes('@')) {
      return 'Please enter a valid email address';
    }
    if (formData.password.length < 6) {
      return 'Password must be at least 6 characters long';
    }
    if (formData.password !== formData.confirmPassword) {
      return 'Passwords do not match';
    }
    return null;
  };

  const validateStep2 = () => {
    if (!formData.restaurantName.trim()) {
      return 'Restaurant name is required';
    }
    if (!formData.restaurantType.trim()) {
      return 'Restaurant type is required';
    }
    if (!formData.userPosition.trim()) {
      return 'Your position/title is required';
    }
    return null;
  };

  const validateStep3 = () => {
    // Step 3 is optional - users can skip adding produce lists
    return null;
  };

  const handleNextStep = (e) => {
    e.preventDefault();
    
    let validationError = null;
    
    if (currentStep === 1) {
      validationError = validateStep1();
    } else if (currentStep === 2) {
      validationError = validateStep2();
    }
    
    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    setCurrentStep(currentStep + 1);
  };

  const handlePrevStep = () => {
    setCurrentStep(currentStep - 1);
    setError('');
  };

  const parseCSVFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target.result;
          const lines = text.split('\n').filter(line => line.trim());
          const items = [];
          
          // Skip header row if it exists
          const startIndex = lines[0]?.toLowerCase().includes('name') || 
                            lines[0]?.toLowerCase().includes('item') || 
                            lines[0]?.toLowerCase().includes('product') ? 1 : 0;
          
          for (let i = startIndex; i < lines.length; i++) {
            const columns = lines[i].split(',').map(col => col.trim().replace(/"/g, ''));
            if (columns[0]) {
              items.push({
                name: columns[0],
                category: columns[1] || 'General',
                supplier: columns[2] || '',
                unitCost: parseFloat(columns[3]) || 0,
                unit: columns[4] || 'each'
              });
            }
          }
          resolve(items);
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  };

  const handleFileUpload = async (file, area) => {
    if (!file) return;
    
    setUploadStatus(prev => ({ ...prev, [area]: 'Processing...' }));
    
    try {
      const items = await parseCSVFile(file);
      
      setFormData(prev => ({
        ...prev,
        [`${area}ProduceList`]: items
      }));
      
      setUploadStatus(prev => ({ 
        ...prev, 
        [area]: `✅ ${items.length} items loaded` 
      }));
    } catch (error) {
      setUploadStatus(prev => ({ 
        ...prev, 
        [area]: '❌ Error processing file' 
      }));
      console.error('File processing error:', error);
    }
  };

  const handleFileChange = (e, area) => {
    const file = e.target.files[0];
    if (file) {
      if (area === 'kitchen') {
        setKitchenFile(file);
      } else {
        setBarFile(file);
      }
      handleFileUpload(file, area);
    }
  };

  const removeFile = (area) => {
    if (area === 'kitchen') {
      setKitchenFile(null);
    } else {
      setBarFile(null);
    }
    setFormData(prev => ({
      ...prev,
      [`${area}ProduceList`]: []
    }));
    setUploadStatus(prev => ({ ...prev, [area]: '' }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateStep3();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Call the parent component's register handler
      await onRegister({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        fullName: formData.fullName,
        restaurantName: formData.restaurantName,
        restaurantType: formData.restaurantType,
        userPosition: formData.userPosition,
        kitchenProduceList: formData.kitchenProduceList,
        barProduceList: formData.barProduceList
      });
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="logo">
            🍽️ KitchenGuard
          </div>
          <h2>Create Your Account</h2>
          <p>Let's start with your personal information</p>
          <div className="step-indicator">
            <span className="step active">1</span>
            <span className="step-divider"></span>
            <span className="step">2</span>
            <span className="step-divider"></span>
            <span className="step">3</span>
          </div>
        </div>

        <form onSubmit={handleNextStep} className="auth-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="fullName">Full Name *</label>
            <input
              type="text"
              id="fullName"
              name="fullName"
              value={formData.fullName}
              onChange={handleInputChange}
              placeholder="Your full name"
              disabled={loading}
              autoComplete="name"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="username">Username *</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="Choose a username"
                disabled={loading}
                autoComplete="username"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email Address *</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="your.email@restaurant.com"
                disabled={loading}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Create a password (min 6 chars)"
                disabled={loading}
                autoComplete="new-password"
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password *</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="Confirm your password"
                disabled={loading}
                autoComplete="new-password"
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="auth-button primary"
            disabled={loading}
          >
            Continue to Restaurant Info →
          </button>
        </form>

        <div className="auth-divider">
          <span>Already have an account?</span>
        </div>

        <button 
          type="button" 
          className="auth-button secondary"
          onClick={onSwitchToLogin}
        >
          Sign In Instead
        </button>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="logo">
            🍽️ KitchenGuard
          </div>
          <h2>Restaurant Information</h2>
          <p>Tell us about your establishment</p>
          <div className="step-indicator">
            <span className="step completed">✓</span>
            <span className="step-divider"></span>
            <span className="step active">2</span>
            <span className="step-divider"></span>
            <span className="step">3</span>
          </div>
        </div>

        <form onSubmit={handleNextStep} className="auth-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="restaurantName">Restaurant Name *</label>
            <input
              type="text"
              id="restaurantName"
              name="restaurantName"
              value={formData.restaurantName}
              onChange={handleInputChange}
              placeholder="Your restaurant or business name"
              disabled={loading}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="restaurantType">Restaurant Type *</label>
              <select
                id="restaurantType"
                name="restaurantType"
                value={formData.restaurantType}
                onChange={handleInputChange}
                disabled={loading}
              >
                <option value="">Select restaurant type</option>
                <option value="fine-dining">Fine Dining</option>
                <option value="casual-dining">Casual Dining</option>
                <option value="fast-food">Fast Food</option>
                <option value="fast-casual">Fast Casual</option>
                <option value="cafe">Café</option>
                <option value="bakery">Bakery</option>
                <option value="pizzeria">Pizzeria</option>
                <option value="steakhouse">Steakhouse</option>
                <option value="seafood">Seafood</option>
                <option value="italian">Italian</option>
                <option value="mexican">Mexican</option>
                <option value="asian">Asian</option>
                <option value="indian">Indian</option>
                <option value="mediterranean">Mediterranean</option>
                <option value="american">American</option>
                <option value="vegetarian">Vegetarian/Vegan</option>
                <option value="bar-grill">Bar & Grill</option>
                <option value="food-truck">Food Truck</option>
                <option value="catering">Catering</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="userPosition">Your Position *</label>
              <select
                id="userPosition"
                name="userPosition"
                value={formData.userPosition}
                onChange={handleInputChange}
                disabled={loading}
              >
                <option value="">Select your role</option>
                <option value="owner">Owner</option>
                <option value="general-manager">General Manager</option>
                <option value="kitchen-manager">Kitchen Manager</option>
                <option value="assistant-manager">Assistant Manager</option>
                <option value="head-chef">Head Chef</option>
                <option value="sous-chef">Sous Chef</option>
                <option value="inventory-manager">Inventory Manager</option>
                <option value="purchasing-manager">Purchasing Manager</option>
                <option value="shift-supervisor">Shift Supervisor</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="button-group">
            <button 
              type="button" 
              className="auth-button secondary"
              onClick={handlePrevStep}
              disabled={loading}
            >
              ← Back
            </button>
            
            <button 
              type="submit" 
              className="auth-button primary"
              disabled={loading}
            >
              Continue to Inventory Setup →
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="auth-container">
      <div className="auth-card inventory-setup-card">
        <div className="auth-header">
          <div className="logo">
            🍽️ KitchenGuard
          </div>
          <h2>Inventory Setup</h2>
          <p>Upload your produce lists to set up your inventory tracking</p>
          <div className="step-indicator">
            <span className="step completed">✓</span>
            <span className="step-divider"></span>
            <span className="step completed">✓</span>
            <span className="step-divider"></span>
            <span className="step active">3</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="inventory-sections">
            {/* Kitchen Produce Section */}
            <div className="inventory-section">
              <div className="section-header">
                <h3>🍳 Kitchen Produce</h3>
                <p>Upload your kitchen ingredients and supplies list</p>
              </div>
              
              <div className="file-upload-area">
                <input
                  type="file"
                  id="kitchen-file"
                  accept=".csv,.xlsx,.xls,.txt"
                  onChange={(e) => handleFileChange(e, 'kitchen')}
                  style={{ display: 'none' }}
                />
                
                {!kitchenFile ? (
                  <label htmlFor="kitchen-file" className="file-upload-label">
                    <div className="upload-icon">📁</div>
                    <div className="upload-text">
                      <strong>Upload Kitchen Inventory List</strong>
                      <p>Excel (.xlsx) or CSV file from your spreadsheet</p>
                    </div>
                  </label>
                ) : (
                  <div className="file-uploaded">
                    <div className="file-info">
                      <span className="file-name">📄 {kitchenFile.name}</span>
                      <span className="file-status">{uploadStatus.kitchen}</span>
                    </div>
                    <button 
                      type="button" 
                      className="remove-file-btn"
                      onClick={() => removeFile('kitchen')}
                    >
                      ×
                    </button>
                  </div>
                )}
              </div>

              {formData.kitchenProduceList.length > 0 && (
                <div className="preview-items">
                  <p><strong>Preview:</strong> {formData.kitchenProduceList.slice(0, 3).map(item => item.name).join(', ')}
                  {formData.kitchenProduceList.length > 3 && ` +${formData.kitchenProduceList.length - 3} more`}</p>
                </div>
              )}
            </div>

            {/* Bar Produce Section */}
            <div className="inventory-section">
              <div className="section-header">
                <h3>🍸 Bar Supplies</h3>
                <p>Upload your bar inventory and supplies list</p>
              </div>
              
              <div className="file-upload-area">
                <input
                  type="file"
                  id="bar-file"
                  accept=".csv,.xlsx,.xls,.txt"
                  onChange={(e) => handleFileChange(e, 'bar')}
                  style={{ display: 'none' }}
                />
                
                {!barFile ? (
                  <label htmlFor="bar-file" className="file-upload-label">
                    <div className="upload-icon">📁</div>
                    <div className="upload-text">
                      <strong>Upload Bar Inventory List</strong>
                      <p>Excel (.xlsx) or CSV file from your spreadsheet</p>
                    </div>
                  </label>
                ) : (
                  <div className="file-uploaded">
                    <div className="file-info">
                      <span className="file-name">📄 {barFile.name}</span>
                      <span className="file-status">{uploadStatus.bar}</span>
                    </div>
                    <button 
                      type="button" 
                      className="remove-file-btn"
                      onClick={() => removeFile('bar')}
                    >
                      ×
                    </button>
                  </div>
                )}
              </div>

              {formData.barProduceList.length > 0 && (
                <div className="preview-items">
                  <p><strong>Preview:</strong> {formData.barProduceList.slice(0, 3).map(item => item.name).join(', ')}
                  {formData.barProduceList.length > 3 && ` +${formData.barProduceList.length - 3} more`}</p>
                </div>
              )}
            </div>
          </div>

          <div className="file-format-info">
            <h4>📋 File Format Guide</h4>
            <p><strong>What file type?</strong> Upload an Excel file (.xlsx) or CSV file from your spreadsheet program</p>
            <p><strong>Required columns:</strong> <code>Name, Category, Supplier, Unit Cost, Unit</code></p>
            <p><strong>Example row:</strong> <code>Tomatoes, Produce, Fresh Food Inc, 2.99, lb</code></p>
            <p><strong>How to create:</strong> Use Excel, Google Sheets, or Numbers to create your list, then save/export as CSV</p>
          </div>

          <div className="button-group">
            <button 
              type="button" 
              className="auth-button secondary"
              onClick={handlePrevStep}
              disabled={loading}
            >
              ← Back
            </button>
            
            <button 
              type="submit" 
              className="auth-button primary"
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Complete Registration'}
            </button>
          </div>

          <div className="skip-notice">
            <p><em>Upload your inventory lists to get started with automated tracking</em></p>
          </div>
        </form>
      </div>
    </div>
  );

  return currentStep === 1 ? renderStep1() : currentStep === 2 ? renderStep2() : renderStep3();
};

export default Register;