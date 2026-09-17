import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { documentAPI, conversationAPI, systemAPI } from "../services/api";
import {
  FileText,
  CheckCircle2,
  Clock,
  MessageSquare,
  Upload,
  Search,
  ArrowRight,
  Database,
  Cpu,
  Layers,
} from "lucide-react";

export const Dashboard = () => {
  const [docs, setDocs] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [docsRes, convsRes, metricsRes] = await Promise.all([
          documentAPI.list({ size: 5 }),
          conversationAPI.list({ size: 5 }),
          systemAPI.metrics(),
        ]);
        setDocs(docsRes.data.items);
        setConversations(convsRes.data.items);
        setMetrics(metricsRes.data);
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    };
    loadDashboardData();
  }, []);

  const totalDocs = docs.length;
  const readyDocs = docs.filter((d) => d.status === "READY").length;
  const processingDocs = docs.filter((d) => d.status === "PROCESSING" || d.status === "UPLOADED").length;
  const totalConvs = conversations.length;

  return (
    <div>
      {/* Header Banner */}
      <div style={{ marginBottom: "2rem" }}>
        <h2 style={{ fontSize: "1.75rem", fontWeight: "700", color: "#fff" }}>
          Document Intelligence Dashboard
        </h2>
        <p style={{ color: "var(--text-muted)", marginTop: "0.25rem" }}>
          Overview of ingested documents, semantic vector embeddings, and active RAG sessions.
        </p>
      </div>

      {/* Metric Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1.25rem",
          marginBottom: "2rem",
        }}
      >
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: "500" }}>
              Total Documents
            </span>
            <div style={{ padding: "0.5rem", borderRadius: "0.5rem", backgroundColor: "rgba(59, 130, 246, 0.15)", color: "#3b82f6" }}>
              <FileText size={20} />
            </div>
          </div>
          <div style={{ fontSize: "1.875rem", fontWeight: "700", color: "#fff", marginTop: "0.75rem" }}>
            {totalDocs}
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: "500" }}>
              Ready for RAG
            </span>
            <div style={{ padding: "0.5rem", borderRadius: "0.5rem", backgroundColor: "rgba(16, 185, 129, 0.15)", color: "#10b981" }}>
              <CheckCircle2 size={20} />
            </div>
          </div>
          <div style={{ fontSize: "1.875rem", fontWeight: "700", color: "#fff", marginTop: "0.75rem" }}>
            {readyDocs}
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: "500" }}>
              Processing Jobs
            </span>
            <div style={{ padding: "0.5rem", borderRadius: "0.5rem", backgroundColor: "rgba(245, 158, 11, 0.15)", color: "#f59e0b" }}>
              <Clock size={20} />
            </div>
          </div>
          <div style={{ fontSize: "1.875rem", fontWeight: "700", color: "#fff", marginTop: "0.75rem" }}>
            {processingDocs}
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontWeight: "500" }}>
              Active Conversations
            </span>
            <div style={{ padding: "0.5rem", borderRadius: "0.5rem", backgroundColor: "rgba(139, 92, 246, 0.15)", color: "#8b5cf6" }}>
              <MessageSquare size={20} />
            </div>
          </div>
          <div style={{ fontSize: "1.875rem", fontWeight: "700", color: "#fff", marginTop: "0.75rem" }}>
            {totalConvs}
          </div>
        </div>
      </div>

      {/* Quick Action Banner */}
      <div
        className="card"
        style={{
          background: "linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%)",
          border: "1px solid rgba(59, 130, 246, 0.3)",
          marginBottom: "2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "1.5rem",
        }}
      >
        <div>
          <h3 style={{ fontSize: "1.125rem", fontWeight: "600", color: "#fff" }}>
            Ask Questions Grounded in Your Documents
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
            Upload PDFs, DOCX, TXT, or Markdown files and query them with verifiable source citations.
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <Link to="/documents" className="btn-primary">
            <Upload size={18} /> Upload File
          </Link>
          <Link to="/chat" className="btn-secondary">
            <MessageSquare size={18} /> Start Chat
          </Link>
        </div>
      </div>

      {/* Content Layout Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "1.5rem" }}>
        {/* Recent Documents */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#fff" }}>Recent Documents</h3>
            <Link to="/documents" style={{ fontSize: "0.875rem", color: "#3b82f6", display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              View all <ArrowRight size={14} />
            </Link>
          </div>

          {docs.length === 0 ? (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)", fontSize: "0.875rem" }}>
              No documents uploaded yet. Upload a PDF, DOCX, TXT, or MD file to get started.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {docs.map((d) => (
                <div
                  key={d.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.75rem 1rem",
                    backgroundColor: "#0f172a",
                    border: "1px solid var(--border-color)",
                    borderRadius: "0.5rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <FileText size={18} color="#3b82f6" />
                    <div>
                      <div style={{ fontSize: "0.875rem", fontWeight: "500", color: "#fff" }}>{d.filename}</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {(d.file_size / 1024).toFixed(1)} KB • {new Date(d.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  <span className={`badge badge-${d.status.toLowerCase()}`}>{d.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* System & Architecture Info */}
        <div className="card">
          <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#fff", marginBottom: "1.25rem" }}>
            Engine Architecture
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", fontSize: "0.875rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <Database size={18} color="#10b981" />
              <div>
                <div style={{ color: "#fff", fontWeight: "500" }}>PostgreSQL + pgvector</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>Cosine similarity vector index</div>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <Cpu size={18} color="#8b5cf6" />
              <div>
                <div style={{ color: "#fff", fontWeight: "500" }}>Embedding Engine</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>BAAI/bge-small-en-v1.5 (384-dim)</div>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <Layers size={18} color="#3b82f6" />
              <div>
                <div style={{ color: "#fff", fontWeight: "500" }}>Chunking Strategy</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>800 tokens window / 120 overlap</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
