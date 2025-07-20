import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const flowsAPI = {
  // Get flows with filters
  getFlows: (params = {}) => api.get('/api/flows/', { params }),
  
  // Get flow by ID
  getFlow: (id) => api.get(`/api/flows/${id}/`),
  
  // Get flow summary
  getSummary: (params = {}) => api.get('/api/flows/summary/', { params }),
  
  // Get recent flows
  getRecent: (params = {}) => api.get('/api/flows/recent/', { params }),
  
  // Get top talkers
  getTopTalkers: (params = {}) => api.get('/api/flows/top-talkers/', { params }),
  
  // Get protocol distribution
  getProtocols: (params = {}) => api.get('/api/flows/protocols/', { params }),
  
  // Get bandwidth data
  getBandwidth: (params = {}) => api.get('/api/flows/bandwidth/', { params }),
  
  // Get geographic distribution
  getGeographic: (params = {}) => api.get('/api/flows/geographic/', { params }),
  
  // Get real-time flows
  getRealtime: (params = {}) => api.get('/api/flows/realtime/', { params }),
};

export const statisticsAPI = {
  // Get statistics
  getStatistics: (params = {}) => api.get('/api/statistics/', { params }),
};

export const alertsAPI = {
  // Get alerts
  getAlerts: (params = {}) => api.get('/api/alerts/', { params }),
  
  // Acknowledge alert
  acknowledgeAlert: (id) => api.post(`/api/alerts/${id}/acknowledge/`),
};

export const interfacesAPI = {
  // Get network interfaces
  getInterfaces: () => api.get('/api/interfaces/'),
};

export default api;