import React, { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("documind_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await authAPI.getMe();
        setUser(res.data);
      } catch (err) {
        console.error("Session restoration failed:", err);
        localStorage.removeItem("documind_token");
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    fetchCurrentUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password });
    const newToken = res.data.access_token;
    localStorage.setItem("documind_token", newToken);
    setToken(newToken);
    const userRes = await authAPI.getMe();
    setUser(userRes.data);
    return userRes.data;
  };

  const register = async (email, password, fullName) => {
    await authAPI.register({ email, password, full_name: fullName });
    return await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem("documind_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
