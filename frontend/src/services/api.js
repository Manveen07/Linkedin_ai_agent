import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (credentials) => api.post('/api/users/login', credentials),
  register: (userData) => api.post('/api/users/register', userData),
  getCurrentUser: () => api.get('/api/users/me'),
};

export const contentAPI = {
  generateContent: (data) => api.post('/api/content/generate', data),
  saveDraft: (data) => api.post('/api/content/save-draft', data),
  getDrafts: () => api.get('/api/content/drafts'),
  getTopicSuggestions: (industry) => api.get(`/api/content/suggestions/${industry}`),
  schedulePost: (data) => api.post('/api/content/schedule-post', data),
  suggestImprovements: (data) => api.post('/api/content/improve', data)
};

export const linkedinAPI = {
  connectLinkedIn: () => api.get('/api/linkedin/connect'),
  publishPost: (data) => api.post('/api/linkedin/publish', data),
  getConnectionStatus: () => api.get('/api/linkedin/status'),
  exchangeCodeForToken: (code) => api.post('/api/linkedin/exchange-token', { code }), // ← This line
  disconnectLinkedIn: () => api.post('/api/linkedin/disconnect')
};


export const analyticsAPI = {
  getDashboard: () => api.get('/api/analytics/dashboard'),
  getPostAnalytics: (postId) => api.get(`/api/analytics/post/${postId}`),
  updatePostAnalytics: (postId, data) => api.post(`/api/analytics/update/${postId}`, data),
  getPerformanceTrends: (days = 30) => api.get(`/api/analytics/performance-trends?days=${days}`),
};


export default api;
