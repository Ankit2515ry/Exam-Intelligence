// src/api/apiService.js
import API from './axiosInstance';

// 1. AUTHENTICATION SERVICE (Mapped to /auth/auth/ paths due to combined prefixes)
export const authService = {
  // POST /auth/auth/signup
  signup: async (userData) => {
    const response = await API.post('/auth/auth/signup', {
      name: userData.name,
      email: userData.email,
      password: userData.password
    });
    return response.data;
  },

  // POST /auth/auth/login
  login: async (credentials) => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email); 
    formData.append('password', credentials.password);

    const response = await API.post('/auth/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data; 
  }
};

// 2. UPLOAD SERVICE (Crucial: Make sure this is completely outside authService!)
export const uploadService = {
  // POST /api/upload
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await API.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // GET /api/documents
  getDocuments: async () => {
    const response = await API.get('/api/documents');
    return response.data;
  },

  // DELETE /api/delete/{document_uuid}
  deleteDocument: async (documentUuid) => {
    const response = await API.delete(`/api/delete/${documentUuid}`);
    return response.data;
  },

  viewPdf: async (documentUuid) => {

    const response = await API.get(
      `/api/view/${documentUuid}`,
      {
        responseType: "blob"
      }
    );

    const pdfUrl = URL.createObjectURL(
      response.data
    );

    window.open(pdfUrl, "_blank");
  }

};

// 3. CHAT SERVICE
export const chatService = {
  // POST /api/chat
  sendMessage: async (question, documentUuid = null) => {
    const payload = {
      question: question,
      top_k: 5,
      document_id: documentUuid || null 
    };
    const response = await API.post('/api/chat', payload);
    return response.data; 
  }
};

