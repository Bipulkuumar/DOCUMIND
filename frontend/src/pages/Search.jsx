import React, { useState } from "react";
import { searchAPI } from "../services/api";
import { Search as SearchIcon, Sliders, FileText, Layers, Tag } from "lucide-react";

export const Search = () => {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.0);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await searchAPI.search({
        query,
        top_k: Number(topK),
        similarity_threshold: Number(similarityThreshold),
      });
      setResults(res.data);
    } catch (err) {
      alert("Search error: " + (err.message || "Failed to execute search."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: "1.75rem", fontWeight: "700", color: "#fff" }}>
          Semantic Vector Search
        </h2>
        <p style={{ color: "var(--text-muted)", marginTop: "0.25rem" }}>
          Query your PostgreSQL pgvector index directly without LLM completion generation.
        </p>
      </div>

      {/* Search Bar & Controls */}
      <div className="card" style={{ marginBottom: "2rem" }}>
        <form onSubmit={handleSearch} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ position: "relative", flex: 1 }}>
              <SearchIcon size={20} color="#64748b" style={{ position: "absolute", left: "1rem", top: "50%", transform: "translateY(-50%)" }} />
              <input
                type="text"
                required
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. What is the annual leave and refund policy?"
                style={{
                  width: "100%",
                  padding: "0.875rem 1rem 0.875rem 3rem",
                  backgroundColor: "#0f172a",
                  border: "1px solid var(--border-color)",
                  borderRadius: "0.5rem",
                  color: "#fff",
                  fontSize: "1rem",
                }}
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary" style={{ padding: "0 1.5rem" }}>
              {loading ? "Searching..." : "Search Vectors"}
            </button>
          </div>

          {/* Search Hyperparameters */}
          <div style={{ display: "flex", gap: "2rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)", fontSize: "0.875rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <Sliders size={16} color="var(--text-muted)" />
              <label style={{ color: "var(--text-muted)" }}>Top K Results: <strong style={{ color: "#fff" }}>{topK}</strong></label>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(e.target.value)}
                style={{ accentColor: "#3b82f6" }}
              />
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <label style={{ color: "var(--text-muted)" }}>Similarity Threshold: <strong style={{ color: "#fff" }}>{similarityThreshold}</strong></label>
              <input
                type="range"
                min="0.0"
                max="0.9"
                step="0.05"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(e.target.value)}
                style={{ accentColor: "#3b82f6" }}
              />
            </div>
          </div>
        </form>
      </div>

      {/* Results Display */}
      {results && (
        <div>
          <div style={{ marginBottom: "1rem", color: "var(--text-muted)", fontSize: "0.875rem" }}>
            Found <strong style={{ color: "#fff" }}>{results.total_results}</strong> matching vector chunks for query: <em>"{results.query}"</em>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {results.results.map((res, idx) => (
              <div key={res.chunk_id || idx} className="card" style={{ backgroundColor: "#0f172a" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <FileText size={18} color="#3b82f6" />
                    <span style={{ fontWeight: "600", color: "#fff" }}>{res.document_name}</span>
                    <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                      • Page {res.page_number || "N/A"} • Section: {res.section || "General"}
                    </span>
                  </div>
                  <span
                    style={{
                      padding: "0.25rem 0.625rem",
                      borderRadius: "9999px",
                      fontSize: "0.75rem",
                      fontWeight: "700",
                      backgroundColor: "rgba(59, 130, 246, 0.15)",
                      color: "#60a5fa",
                      border: "1px solid rgba(59, 130, 246, 0.3)",
                    }}
                  >
                    Score: {(res.similarity * 100).toFixed(1)}%
                  </span>
                </div>

                <div style={{ fontSize: "0.875rem", color: "#e2e8f0", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                  {res.content}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
