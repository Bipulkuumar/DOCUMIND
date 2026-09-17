import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { BrainCircuit, Lock, Mail, User, ArrowRight } from "lucide-react";

export const Register = () => {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, fullName);
      navigate("/");
    } catch (err) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--bg-main)",
        padding: "1rem",
      }}
    >
      <div
        className="card"
        style={{
          width: "100%",
          maxWidth: "420px",
          padding: "2.5rem",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "0.75rem",
              background: "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              margin: "0 auto 1rem",
            }}
          >
            <BrainCircuit size={28} />
          </div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "700", color: "#fff" }}>Create an Account</h2>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Get started with your document RAG platform
          </p>
        </div>

        {error && (
          <div
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#f87171",
              padding: "0.75rem 1rem",
              borderRadius: "0.375rem",
              fontSize: "0.875rem",
              marginBottom: "1.5rem",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: "500", color: "#e2e8f0", marginBottom: "0.375rem" }}>
              Full Name
            </label>
            <div style={{ position: "relative" }}>
              <User size={18} color="#64748b" style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)" }} />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                style={{
                  width: "100%",
                  padding: "0.625rem 0.75rem 0.625rem 2.5rem",
                  backgroundColor: "#0f172a",
                  border: "1px solid var(--border-color)",
                  borderRadius: "0.375rem",
                  color: "#fff",
                  fontSize: "0.875rem",
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: "500", color: "#e2e8f0", marginBottom: "0.375rem" }}>
              Email Address
            </label>
            <div style={{ position: "relative" }}>
              <Mail size={18} color="#64748b" style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)" }} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                style={{
                  width: "100%",
                  padding: "0.625rem 0.75rem 0.625rem 2.5rem",
                  backgroundColor: "#0f172a",
                  border: "1px solid var(--border-color)",
                  borderRadius: "0.375rem",
                  color: "#fff",
                  fontSize: "0.875rem",
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.875rem", fontWeight: "500", color: "#e2e8f0", marginBottom: "0.375rem" }}>
              Password
            </label>
            <div style={{ position: "relative" }}>
              <Lock size={18} color="#64748b" style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)" }} />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                style={{
                  width: "100%",
                  padding: "0.625rem 0.75rem 0.625rem 2.5rem",
                  backgroundColor: "#0f172a",
                  border: "1px solid var(--border-color)",
                  borderRadius: "0.375rem",
                  color: "#fff",
                  fontSize: "0.875rem",
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: "100%", justifyContent: "center", padding: "0.75rem", marginTop: "0.5rem" }}
          >
            {loading ? "Creating account..." : "Register Now"}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem", color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "#3b82f6", fontWeight: "500" }}>
            Sign in here
          </Link>
        </div>
      </div>
    </div>
  );
};
