// frontend/src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
      return Promise.reject({
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR'
      });
    }

    // Handle specific HTTP status codes
    const status = error.response?.status;
    const data = error.response?.data;

    switch (status) {
      case 401:
        // Unauthorized - but DON'T auto-logout for now
        console.warn('Authentication error (401):', data?.detail);
        // TEMPORARY: Don't redirect to login
        // localStorage.removeItem('authToken');
        // if (window.location.pathname !== '/login') {
        //   window.location.href = '/login';
        // }
        break;
      
      case 403:
        // Forbidden
        console.error('Access forbidden:', data?.detail);
        break;
      
      case 404:
        // Not found
        console.error('Resource not found:', data?.detail);
        break;
      
      case 429:
        // Rate limited
        console.error('Rate limited:', data?.detail);
        break;
      
      case 500:
        // Server error
        console.error('Server error:', data?.detail);
        break;
      
      default:
        console.error('API error:', error.message);
    }

    return Promise.reject({
      message: data?.detail || data?.message || 'An error occurred',
      code: data?.code || `HTTP_${status}`,
      status,
      data: data
    });
  }
);

// Generic API methods
export const apiMethods = {
  // Health check
  healthCheck: () => api.get('/health').then(res => res.data),

  // System info
  getSystemInfo: () => api.get('/info').then(res => res.data),

  // System status
  getSystemStatus: () => api.get('/status').then(res => res.data),

  // Test CORS
  testCors: () => api.get('/test-cors').then(res => res.data),
};

// Auth API methods
export const authAPI = {
  // Login
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    return api.post('/api/v1/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then(response => response.data);
  },

  // OTP Registration Flow - Step 1: Request OTP - FIXED ENDPOINT
  register: (userData) => {
    return api.post('/api/v1/auth/register/request-otp', userData).then(res => {
      const data = res.data;
      if (!data.success) {
        throw new Error(data.message || 'Failed to send OTP');
      }
      return data;
    });
  },

  // OTP Registration Flow - Step 2: Verify OTP - NEW METHOD NAME
  verifyRegistrationOTP: (verifyData) => {
    return api.post('/api/v1/auth/register/verify-otp', verifyData).then(res => {
      const data = res.data;
      if (!data.success) {
        throw new Error(data.message || 'OTP verification failed');
      }
      return data;
    });
  },

  // OTP Registration Flow - Step 3: Complete Registration
  completeRegistration: (userData) => {
    return api.post('/api/v1/auth/register/complete', userData).then(res => {
      const data = res.data;
      if (!data.success) {
        throw new Error(data.message || 'Registration failed');
      }
      return data;
    });
  },

  // Check email existence
  checkEmail: (email) => {
    return api.post('/api/v1/auth/check-email', { email }).then(res => res.data);
  },

  // Get current user
  getCurrentUser: () => {
    return api.get('/api/v1/auth/me').then(res => res.data);
  },

  // Update profile
  updateProfile: (userData) => {
    return api.put('/api/v1/auth/me', userData).then(res => res.data);
  },

  // Request password reset
  requestPasswordReset: (email) => {
    return api.post('/api/v1/auth/request-password-reset', { email }).then(response => response.data);
  },

  // Reset password
  resetPassword: (token, newPassword) => {
    return api.post('/api/v1/auth/reset-password', { token, new_password: newPassword }).then(response => response.data);
  },

  // Verify email
  verifyEmail: (token) => {
    return api.post('/api/v1/auth/verify-email', { token }).then(response => response.data);
  },

  // Refresh token
  refreshToken: (refreshToken) => {
    return api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }).then(response => response.data);
  },

  // Logout
  logout: () => {
    return api.post('/api/v1/auth/logout').then(response => response.data);
  },

  // General OTP verification (for other purposes)
  verifyGeneralOTP: (email, otp) => {
    return api.post('/api/v1/auth/verify-otp', { email, otp }).then(response => response.data);
  },

  // Resend OTP
  resendOTP: (email) => {
    return api.post('/api/v1/auth/resend-otp', { email }).then(response => response.data);
  },

  // ✅ TEMPORARY ALIAS - Remove this once all code is updated
  verifyOTP: function(verifyData) {
    console.warn('⚠️ verifyOTP is deprecated, use verifyRegistrationOTP instead');
    return this.verifyRegistrationOTP(verifyData);
  }
};
// News API methods
export const newsAPI = {
  // Text prediction
  predictText: (textData) => {
    return api.post('/api/v1/news/predict', textData).then(response => response.data);
  },

  // URL prediction
  predictUrl: (urlData) => {
    return api.post('/api/v1/news/predict-url', urlData).then(response => response.data);
  },

  // Get task status
  getTaskStatus: (taskId) => {
    return api.get(`/api/v1/news/task-status/${taskId}`).then(response => response.data);
  },

  // Get news stats
  getStats: () => {
    return api.get('/api/v1/news/stats').then(response => response.data);
  },

  // Get recent news
  getRecentNews: () => {
    return api.get('/api/v1/news/recent').then(response => response.data);
  },

  // Submit feedback
  submitFeedback: (feedbackData) => {
    return api.post('/api/v1/news/feedback', feedbackData).then(response => response.data);
  },

  // Get prediction history
  getPredictionHistory: (limit = 10, offset = 0) => {
    return api.get(`/api/v1/news/history?limit=${limit}&offset=${offset}`).then(response => response.data);
  }
};

// Model API methods
export const modelAPI = {
  // Get available datasets
  getDatasets: () => {
    return api.get('/api/v1/models/datasets/').then(response => response.data);
  },

  // Start training
  startTraining: (trainingData) => {
    return api.post('/api/v1/models/train', trainingData).then(response => response.data);
  },

  // Get training progress
  getTrainingProgress: (trainingId) => {
    return api.get(`/api/v1/models/training/${trainingId}/progress`).then(response => response.data);
  },

  // Stop training
  stopTraining: (trainingId) => {
    return api.post(`/api/v1/models/training/${trainingId}/stop`).then(response => response.data);
  },

  // Get training history
  getTrainingHistory: (limit = 10, offset = 0) => {
    return api.get(`/api/v1/models/history?limit=${limit}&offset=${offset}`).then(response => response.data);
  },

  // Deploy model
  deployModel: (modelId) => {
    return api.post(`/api/v1/models/${modelId}/deploy`).then(response => response.data);
  },

  // Download model
  downloadModel: (modelId) => {
    return api.get(`/api/v1/models/${modelId}/download`, { 
      responseType: 'blob' 
    }).then(response => response.data);
  },

  // Get model info
  getModelInfo: (modelId) => {
    return api.get(`/api/v1/models/${modelId}`).then(response => response.data);
  }
};

// Dataset API methods
export const datasetAPI = {
  // Get user datasets
  getMy: () => {
    return api.get('/api/v1/datasets/my').then(res => res.data);
  },

  // Get public datasets
  getPublic: () => {
    return api.get('/api/v1/datasets/public').then(res => res.data);
  },

  // Upload dataset
  upload: (formData) => {
    return api.post('/api/v1/datasets/upload', formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
      },
    }).then(res => res.data);
  },

  // Delete dataset
  delete: (id) => {
    return api.delete(`/api/v1/datasets/${id}`).then(res => res.data);
  },

  // Preview dataset
  preview: (id, limit = 5) => {
    return api.get(`/api/v1/datasets/${id}/preview?limit=${limit}`).then(res => res.data);
  },

  // Download dataset
  download: (id) => {
    return api.get(`/api/v1/datasets/${id}/download`, { 
      responseType: 'blob' 
    }).then(res => res.data);
  },

  // Get dataset info
  getInfo: (id) => {
    return api.get(`/api/v1/datasets/${id}`).then(res => res.data);
  },

  // Update dataset
  update: (id, data) => {
    return api.put(`/api/v1/datasets/${id}`, data).then(res => res.data);
  }
};

// Admin API methods
export const adminAPI = {
  // Get detailed stats
  getDetailedStats: () => {
    return api.get('/api/v1/admin/stats/detailed').then(response => response.data);
  },

  // Retrain model
  retrainModel: () => {
    return api.post('/api/v1/admin/models/retrain').then(response => response.data);
  },

  // List models
  listModels: () => {
    return api.get('/api/v1/admin/models/list').then(response => response.data);
  },

  // Refresh data
  refreshData: () => {
    return api.post('/api/v1/admin/data/refresh').then(response => response.data);
  },

  // Get system logs
  getSystemLogs: (limit = 100) => {
    return api.get(`/api/v1/admin/logs?limit=${limit}`).then(response => response.data);
  },

  // Get user management
  getUsers: (limit = 50, offset = 0) => {
    return api.get(`/api/v1/admin/users?limit=${limit}&offset=${offset}`).then(response => response.data);
  },

  // Update user status
  updateUserStatus: (userId, status) => {
    return api.put(`/api/v1/admin/users/${userId}`, { is_active: status }).then(response => response.data);
  },

  // Get admin dashboard stats
  getDashboardStats: () => {
    return api.get('/api/v1/admin/stats/dashboard').then(response => response.data);
  }
};

// User API methods
export const userAPI = {
  // Get user stats
  getStats: () => {
    return api.get('/api/v1/user/stats').then(res => res.data);
  },

  // Get user profile
  getProfile: () => {
    return api.get('/api/v1/user/profile').then(res => res.data);
  },

  // Update user profile
  updateProfile: (profileData) => {
    return api.put('/api/v1/user/profile', profileData).then(res => res.data);
  },

  // Get user activity
  getActivity: (limit = 10, offset = 0) => {
    return api.get(`/api/v1/user/activity?limit=${limit}&offset=${offset}`).then(res => res.data);
  },

  // Change password
  changePassword: (passwordData) => {
    return api.post('/api/v1/user/change-password', passwordData).then(res => res.data);
  },

  // Get user preferences
  getPreferences: () => {
    return api.get('/api/v1/user/preferences').then(res => res.data);
  },

  // Update user preferences
  updatePreferences: (preferences) => {
    return api.put('/api/v1/user/preferences', preferences).then(res => res.data);
  }
};

// Utility functions
export const apiUtils = {
  // Check if error is a specific type
  isNetworkError: (error) => error.code === 'NETWORK_ERROR',
  
  // Check if error is authentication error
  isAuthError: (error) => error.status === 401,
  
  // Get error message
  getErrorMessage: (error) => {
    if (typeof error === 'string') return error;
    if (error.message) return error.message;
    if (error.detail) return error.detail;
    return 'An unexpected error occurred';
  },

  // Handle API response
  handleResponse: (response) => {
    if (response.success) {
      return response.data;
    } else {
      throw new Error(response.error || 'Request failed');
    }
  },

  // Download file helper
  downloadFile: (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // Format file size
  formatFileSize: (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  // Validate email
  validateEmail: (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },

  // Get auth token
  getToken: () => {
    return localStorage.getItem('authToken');
  },

  // Set auth token
  setToken: (token) => {
    localStorage.setItem('authToken', token);
  },

  // Remove auth token
  removeToken: () => {
    localStorage.removeItem('authToken');
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('authToken');
  }
};

// Legacy functions for backward compatibility
export const getUserStats = () => userAPI.getStats();
export const getRecentNews = () => newsAPI.getRecentNews();

// Legacy news prediction (for backward compatibility)
export const predictNews = async (text) => {
  const response = await api.post('/api/v1/news/predict', { text });
  return response.data;
};

// Test connection function
export const testConnection = async () => {
  try {
    const response = await api.get('/health');
    return { connected: true, data: response.data };
  } catch (error) {
    return { connected: false, error: apiUtils.getErrorMessage(error) };
  }
};

// Batch request helper
export const batchRequests = (requests) => {
  return Promise.all(requests);
};

// Retry mechanism for failed requests
export const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
};

export default api;