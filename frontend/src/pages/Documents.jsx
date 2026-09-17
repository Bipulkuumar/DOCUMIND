import React, { useState, useEffect } from "react";
import { documentAPI } from "../services/api";
import {
  Upload,
  FileText,
  Trash2,
  Eye,
  CheckCircle2,
  Clock,
  AlertCircle,
  X,
  FileCode,
  Layers,
} from "lucide-react";

export const Documents = () => {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedDocChunks, setSelectedDocChunks] = useState(null);
  const [inspectingDoc, setInspectingDoc] = useState(null);

  const fetchDocuments = async () => {
    try {
      const res = await documentAPI.list({ size: 50 });
      setDocs(res.data.items);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Auto-refresh processing status every 4 seconds
    const interval = setInterval(() => {
      fetchDocuments();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError("");
    setSuccess("");
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      await documentAPI.upload(formData);
      setSuccess(`File '${file.name}' uploaded successfully. Background ingestion started.`);
      await fetchDocuments();
    } catch (err) {
      setError(err.message || "Failed to upload file.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to delete '${filename}'? This will delete all extracted chunks and vectors.`)) {
      return;
    }
    try {
      await documentAPI.delete(id);
      setDocs(docs.filter((d) => d.id !== id));
      if (inspectingDoc?.id === id) {
        setInspectingDoc(null);
        setSelectedDocChunks(null);
      }
    } catch (err) {
      alert("Failed to delete document: " + err.message);
    }
  };

  const handleInspectChunks = async (doc) => {
    setInspectingDoc(doc);
    try {
      const res = await documentAPI.getChunks(doc.id);
      setSelectedDocChunks(res.data.chunks);
    } catch (err) {
      alert("Failed to fetch chunks: " + err.message);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.75rem", fontWeight: "700", color: "#fff" }}>
          Document Management
        </h2>
        <p style={{ color: "var(--text-muted)", marginTop: "0.25rem" }}>
          Upload, parse, chunk, and index unstructured documents into PostgreSQL pgvector.
        </p>
      </div>

      {/* Upload Box */}
      <div
        className="card"
        style={{
          border: "2px dashed var(--border-color)",
          textAlign: "center",
          padding: "2.5rem 1.5rem",
          marginBottom: "2rem",
          backgroundColor: "rgba(30, 41, 59, 0.4)",
        }}
      >
        <div
          style={{
            width: "56px",
            height: "56px",
            borderRadius: "50%",
            backgroundColor: "rgba(59, 130, 246, 0.15)",
            color: "#3b82f6",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 1rem",
          }}
        >
          <Upload size={28} />
        </div>
        <h3 style={{ fontSize: "1.125rem", fontWeight: "600", color: "#fff", marginBottom: "0.25rem" }}>
          Upload Document for RAG Ingestion
        </h3>
        <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
          Supported file formats: PDF, DOCX, TXT, Markdown (Max file size: 25MB)
        </p>

        <label className="btn-primary" style={{ cursor: "pointer", display: "inline-flex" }}>
          {uploading ? "Processing & Uploading..." : "Choose File to Upload"}
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileUpload}
            disabled={uploading}
            style={{ display: "none" }}
          />
        </label>

        {error && (
          <div style={{ marginTop: "1rem", color: "#f87171", fontSize: "0.875rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.375rem" }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}
        {success && (
          <div style={{ marginTop: "1rem", color: "#34d399", fontSize: "0.875rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.375rem" }}>
            <CheckCircle2 size={16} /> {success}
          </div>
        )}
      </div>

      {/* Document List Table */}
      <div className="card">
        <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#fff", marginBottom: "1rem" }}>
          Uploaded Documents ({docs.length})
        </h3>

        {loading ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Loading documents...</div>
        ) : docs.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
            No documents found. Use the upload box above to ingest your first file.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)" }}>
                  <th style={{ padding: "0.75rem" }}>Filename</th>
                  <th style={{ padding: "0.75rem" }}>Type</th>
                  <th style={{ padding: "0.75rem" }}>Size</th>
                  <th style={{ padding: "0.75rem" }}>Status</th>
                  <th style={{ padding: "0.75rem" }}>Uploaded At</th>
                  <th style={{ padding: "0.75rem", textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((doc) => (
                  <tr key={doc.id} style={{ borderBottom: "1px solid rgba(51, 65, 85, 0.5)" }}>
                    <td style={{ padding: "0.875rem 0.75rem", fontWeight: "500", color: "#fff" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <FileText size={18} color="#3b82f6" />
                        {doc.filename}
                      </div>
                    </td>
                    <td style={{ padding: "0.75rem", textTransform: "uppercase", color: "var(--text-muted)", fontSize: "0.75rem" }}>
                      {doc.file_type}
                    </td>
                    <td style={{ padding: "0.75rem", color: "var(--text-muted)" }}>
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td style={{ padding: "0.75rem" }}>
                      <span className={`badge badge-${doc.status.toLowerCase()}`}>{doc.status}</span>
                    </td>
                    <td style={{ padding: "0.75rem", color: "var(--text-muted)" }}>
                      {new Date(doc.created_at).toLocaleString()}
                    </td>
                    <td style={{ padding: "0.75rem", textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: "0.5rem" }}>
                        <button
                          onClick={() => handleInspectChunks(doc)}
                          className="btn-secondary"
                          style={{ padding: "0.375rem 0.625rem", fontSize: "0.75rem" }}
                          title="View Chunks"
                        >
                          <Layers size={14} /> Chunks
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          className="btn-danger"
                          style={{ padding: "0.375rem 0.625rem", fontSize: "0.75rem" }}
                          title="Delete Document"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chunks Inspector Modal */}
      {inspectingDoc && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(15, 23, 42, 0.85)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: "1rem",
          }}
        >
          <div
            className="card"
            style={{
              width: "100%",
              maxWidth: "800px",
              maxHeight: "85vh",
              display: "flex",
              flexDirection: "column",
              padding: "1.5rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem", paddingBottom: "0.75rem", borderBottom: "1px solid var(--border-color)" }}>
              <div>
                <h3 style={{ fontSize: "1.125rem", fontWeight: "600", color: "#fff" }}>
                  Chunks Inspector: {inspectingDoc.filename}
                </h3>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  Extracted vector windows & layout metadata
                </span>
              </div>
              <button onClick={() => setInspectingDoc(null)} style={{ background: "none", color: "var(--text-muted)" }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "1rem" }}>
              {!selectedDocChunks ? (
                <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Loading chunks...</div>
              ) : selectedDocChunks.length === 0 ? (
                <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>No chunks generated for this document yet.</div>
              ) : (
                selectedDocChunks.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      backgroundColor: "#0f172a",
                      border: "1px solid var(--border-color)",
                      borderRadius: "0.5rem",
                      padding: "1rem",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", fontSize: "0.75rem", color: "#94a3b8" }}>
                      <span style={{ fontWeight: "600", color: "#3b82f6" }}>Chunk #{c.chunk_index}</span>
                      <span>Page: {c.page_number || "N/A"} • Section: {c.section || "General"} • {c.token_count} tokens</span>
                    </div>
                    <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.8125rem", color: "#e2e8f0", fontFamily: "inherit" }}>
                      {c.content}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
