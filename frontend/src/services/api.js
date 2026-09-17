import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach Authorization Bearer token to outgoing requests if logged in
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("documind_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Global response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token on 401 Unauthorized
      localStorage.removeItem("documind_token");
      if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        window.location.href = "/login";
      }
    }
    const errorPayload = error.response?.data?.error || {
      code: "NETWORK_ERROR",
      message: error.message || "Failed to communicate with API server.",
    };
    return Promise.reject(errorPayload);
  }
);

export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  getMe: () => api.get("/auth/me"),
};

export const documentAPI = {
  upload: (formData) => api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }),
  list: (params) => api.get("/documents", { params }),
  getDetail: (id) => api.get(`/documents/${id}`),
  delete: (id) => api.delete(`/documents/${id}`),
  getChunks: (id) => api.get(`/documents/${id}/chunks`),
};

export const searchAPI = {
  search: (payload) => api.post("/search", payload),
};

export const chatAPI = {
  sendMessage: (payload) => api.post("/chat", payload),
};

export const conversationAPI = {
  list: (params) => api.get("/conversations", { params }),
  getDetail: (id) => api.get(`/conversations/${id}`),
  delete: (id) => api.delete(`/conversations/${id}`),
};

export const systemAPI = {
  health: () => api.get("/health"),
  metrics: () => api.get("/metrics"),
};
