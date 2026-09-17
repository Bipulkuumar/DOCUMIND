import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  FileText,
  Search,
  MessageSquare,
  LogOut,
  BrainCircuit,
  ShieldCheck,
  User as UserIcon,
} from "lucide-react";

export const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { label: "Dashboard", path: "/", icon: LayoutDashboard },
    { label: "Documents", path: "/documents", icon: FileText },
    { label: "Semantic Search", path: "/search", icon: Search },
    { label: "Document Chat", path: "/chat", icon: MessageSquare },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: "var(--bg-main)" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "260px",
          backgroundColor: "var(--bg-sidebar)",
          borderRight: "1px solid var(--border-color)",
          display: "flex",
          flexDirection: "column",
          padding: "1.5rem 1rem",
        }}
      >
        {/* Brand Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "2rem", paddingLeft: "0.5rem" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "0.5rem",
              background: "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
            }}
          >
            <BrainCircuit size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: "1.125rem", fontWeight: "700", color: "#fff", lineHeight: 1.2 }}>DocuMind</h1>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>RAG Intelligence Platform</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.375rem" }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                  padding: "0.625rem 0.875rem",
                  borderRadius: "0.5rem",
                  fontSize: "0.875rem",
                  fontWeight: isActive ? "600" : "400",
                  color: isActive ? "#fff" : "var(--text-muted)",
                  backgroundColor: isActive ? "rgba(59, 130, 246, 0.15)" : "transparent",
                  borderLeft: isActive ? "3px solid #3b82f6" : "3px solid transparent",
                  transition: "all 0.15s ease",
                }}
              >
                <Icon size={18} color={isActive ? "#3b82f6" : "var(--text-muted)"} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* System Health Badge */}
        <div
          style={{
            backgroundColor: "rgba(30, 41, 59, 0.5)",
            border: "1px solid var(--border-color)",
            borderRadius: "0.5rem",
            padding: "0.75rem",
            marginBottom: "1rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <ShieldCheck size={18} color="#10b981" />
          <div style={{ fontSize: "0.75rem" }}>
            <div style={{ color: "#fff", fontWeight: "500" }}>pgvector Engine</div>
            <div style={{ color: "var(--accent-green)" }}>Healthy & Active</div>
          </div>
        </div>

        {/* User Footer */}
        {user && (
          <div
            style={{
              paddingTop: "1rem",
              borderTop: "1px solid var(--border-color)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", overflow: "hidden" }}>
              <div
                style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "50%",
                  backgroundColor: "#334155",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#94a3b8",
                  flexShrink: 0,
                }}
              >
                <UserIcon size={16} />
              </div>
              <div style={{ overflow: "hidden" }}>
                <div style={{ fontSize: "0.8125rem", fontWeight: "600", color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {user.full_name || user.email}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {user.email}
                </div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              style={{
                background: "none",
                color: "var(--text-muted)",
                padding: "0.375rem",
                borderRadius: "0.375rem",
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
        <header
          style={{
            height: "64px",
            borderBottom: "1px solid var(--border-color)",
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 2rem",
            position: "sticky",
            top: 0,
            zIndex: 10,
          }}
        >
          <div style={{ fontSize: "1rem", fontWeight: "600", color: "#fff" }}>
            DocuMind Workspace
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span className="badge badge-ready">
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#10b981" }}></span>
              PostgreSQL + pgvector
            </span>
          </div>
        </header>

        <div style={{ padding: "2rem", flex: 1 }}>{children}</div>
      </main>
    </div>
  );
};
