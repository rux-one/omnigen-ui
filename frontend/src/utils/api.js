import axios from 'axios';

// Base API configuration
// Use the environment variable for the backend URL or fall back to default
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor for API calls
apiClient.interceptors.request.use(
  config => {
    // You can add authentication headers here if needed in the future
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
apiClient.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    const errorResponse = {
      status: error.response?.status || 500,
      message: error.response?.data?.message || 'An unexpected error occurred',
      error: error.response?.data?.error || 'Error',
      path: error.response?.data?.path || '',
      originalError: error
    };
    
    // Log the error for debugging
    console.error('API Error:', errorResponse);
    
    return Promise.reject(errorResponse);
  }
);

// API service class
class ApiService {
  // Health check
  static async healthCheck() {
    return apiClient.get('/health');
  }
  
  // Image upload
  static async uploadImage(file, onUploadProgress) {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress
    });
  }
  
  // List input images
  static async getInputImages() {
    return apiClient.get('/images/input');
  }
  
  // List output images
  static async getOutputImages() {
    return apiClient.get('/images/output');
  }
  
  // Delete input image
  static async deleteInputImage(filename) {
    return apiClient.delete(`/images/input/${filename}`);
  }
  
  // Delete output image
  static async deleteOutputImage(filename) {
    return apiClient.delete(`/images/output/${filename}`);
  }
  
  // Execute script
  static async executeScript(params) {
    return apiClient.post('/execute', params);
  }
  
  // Get script status
  static async getScriptStatus(processId) {
    return apiClient.get(`/status/${processId}`);
  }
  
  // Cancel script
  static async cancelScript(processId) {
    return apiClient.post(`/cancel/${processId}`);
  }
}

export default ApiService;
