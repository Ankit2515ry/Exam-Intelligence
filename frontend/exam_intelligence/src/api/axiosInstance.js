// src/api/axiosInstance.js
import axios from 'axios';

const API = axios.create({
// Dynamically loads from your frontend .env file
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: Automatically attaches the token from localStorage to ALL requests
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('userToken');
  if (token) {
    // This MUST match exactly what FastAPI's get_current_user expects (Bearer + token)
    config.headers.Authorization = `Bearer ${token}`; 
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default API;