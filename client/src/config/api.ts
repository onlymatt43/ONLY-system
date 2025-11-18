const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

export const api = {
  baseURL: API_BASE_URL,
  
  // Video endpoints with proper CORS
  videos: {
    stream: (id: string) => `${API_BASE_URL}/api/videos/stream/${id}`,
    list: () => `${API_BASE_URL}/api/videos`,
  },
  
  // Common headers
  headers: {
    'Content-Type': 'application/json',
  }
};
