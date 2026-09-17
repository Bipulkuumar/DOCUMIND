import React, { useState, useEffect, useRef } from "react";
import { chatAPI, conversationAPI } from "../services/api";
import {
  MessageSquare,
  Plus,
  Send,
  Trash2,
  FileText,
  Sparkles,
  AlertTriangle,
  BookOpen,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export const Chat = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [showSourcesMap, setShowSourcesMap] = useState({});

  const messagesEndRef = useRef(null);

  const fetchConversations = async () => {
    try {
      const res = await conversationAPI.list({ size: 50 });
      setConversations(res.data.items);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (activeConvId) {
      loadConversationDetail(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const loadConversationDetail = async (id) => {
    try {
      const res = await conversationAPI.getDetail(id);
      setMessages(res.data.messages);
    } catch (err) {
      console.error("Failed to load conversation history:", err);
    }
  };

  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await conversationAPI.delete(id);
      setConversations(conversations.filter((c) => c.id !== id));
      if (activeConvId === id) {
        handleNewChat();
      }
    } catch (err) {
      alert("Failed to delete conversation: " + err.message);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    const userMsgText = input.trim();
    setInput("");
    setSending(true);

    // Optimistically append user message to UI
    const tempUserMsg = {
      id: "temp-" + Date.now(),
      role: "user",
      content: userMsgText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await chatAPI.sendMessage({
        conversation_id: activeConvId,
        message: userMsgText,
      });

      const responseData = res.data;
      if (!activeConvId) {
        setActiveConvId(responseData.conversation_id);
        fetchConversations();
      }

      const tempAssistantMsg = {
        id: responseData.message_id,
        role: "assistant",
        content: responseData.answer,
        citations: responseData.citations,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempAssistantMsg]);
    } catch (err) {
      const errorMsg = {
        id: "err-" + Date.now(),
        role: "assistant",
        content: "Error processing query: " + (err.message || "Failed to generate answer."),
        citations: [],
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  const toggleSources = (msgId) => {
    setShowSourcesMap((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div
      style={{
        display: "flex",
        height: "calc(100vh - 128px)",
        gap: "1.5rem",
        overflow: "hidden",
      }}
    >
      {/* Sidebar - Conversations */}
      <div
        className="card"
        style={{
          width: "280px",
          display: "flex",
          flexDirection: "column",
          padding: "1rem",
        }}
      >
        <button onClick={handleNewChat} className="btn-primary" style={{ width: "100%", justifyContent: "center", marginBottom: "1rem" }}>
          <Plus size={18} /> New Conversation
        </button>

        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.375rem" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "600", paddingLeft: "0.5rem" }}>
            Chat History
          </span>
          {conversations.length === 0 ? (
            <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", padding: "0.5rem" }}>
              No previous chats.
            </div>
          ) : (
            conversations.map((c) => {
              const isActive = activeConvId === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => setActiveConvId(c.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.625rem 0.75rem",
                    borderRadius: "0.5rem",
                    cursor: "pointer",
                    backgroundColor: isActive ? "rgba(59, 130, 246, 0.15)" : "transparent",
                    color: isActive ? "#fff" : "var(--text-muted)",
                    fontSize: "0.875rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", overflow: "hidden" }}>
                    <MessageSquare size={16} color={isActive ? "#3b82f6" : "var(--text-muted)"} />
                    <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{c.title}</span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteConversation(e, c.id)}
                    style={{ background: "none", color: "var(--text-muted)", padding: "0.25rem" }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="card" style={{ flex: 1, display: "flex", flexDirection: "column", padding: "1.25rem" }}>
        {/* Messages List */}
        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "1.25rem", paddingRight: "0.5rem" }}>
          {messages.length === 0 && !sending ? (
            <div style={{ textAlign: "center", margin: "auto", maxWidth: "420px", color: "var(--text-muted)" }}>
              <Sparkles size={40} color="#3b82f6" style={{ margin: "0 auto 1rem" }} />
              <h3 style={{ fontSize: "1.125rem", color: "#fff", fontWeight: "600" }}>DocuMind Document Assistant</h3>
              <p style={{ fontSize: "0.875rem", marginTop: "0.5rem" }}>
                Ask any question grounded in your uploaded documents. Answers will include verifiable source citations.
              </p>
            </div>
          ) : (
            messages.map((m) => {
              const isUser = m.role === "user";
              const showSrc = showSourcesMap[m.id];
              return (
                <div
                  key={m.id}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: isUser ? "flex-end" : "flex-start",
                  }}
                >
                  {/* Message Bubble */}
                  <div
                    style={{
                      maxWidth: "80%",
                      padding: "1rem 1.25rem",
                      borderRadius: isUser ? "1rem 1rem 0.25rem 1rem" : "1rem 1rem 1rem 0.25rem",
                      backgroundColor: isUser ? "#2563eb" : "#0f172a",
                      color: "#fff",
                      border: isUser ? "none" : "1px solid var(--border-color)",
                      fontSize: "0.9375rem",
                      lineHeight: 1.6,
                      whiteSpace: "pre-wrap",
                    }}
                  >
                    {m.content}
                  </div>

                  {/* Sources Citation Section */}
                  {!isUser && m.citations && m.citations.length > 0 && (
                    <div style={{ marginTop: "0.625rem", maxWidth: "80%" }}>
                      <button
                        onClick={() => toggleSources(m.id)}
                        style={{
                          background: "none",
                          color: "#60a5fa",
                          fontSize: "0.75rem",
                          fontWeight: "600",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.375rem",
                          cursor: "pointer",
                        }}
                      >
                        <BookOpen size={14} />
                        {m.citations.length} Source Citation{m.citations.length > 1 ? "s" : ""}
                        {showSrc ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>

                      {showSrc && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginTop: "0.5rem" }}>
                          {m.citations.map((c, idx) => (
                            <div
                              key={idx}
                              style={{
                                backgroundColor: "rgba(15, 23, 42, 0.9)",
                                border: "1px solid rgba(59, 130, 246, 0.3)",
                                borderRadius: "0.5rem",
                                padding: "0.75rem",
                                fontSize: "0.75rem",
                              }}
                            >
                              <div style={{ display: "flex", justifyContent: "space-between", color: "#3b82f6", fontWeight: "600", marginBottom: "0.25rem" }}>
                                <span>📄 {c.document_name}</span>
                                <span>Score: {(c.similarity * 100).toFixed(1)}%</span>
                              </div>
                              <div style={{ color: "var(--text-muted)", marginBottom: "0.375rem" }}>
                                Page: {c.page || "N/A"} • Section: {c.section || "General"}
                              </div>
                              <div style={{ color: "#cbd5e1", fontStyle: "italic" }}>"{c.snippet}"</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}

          {sending && (
            <div style={{ alignSelf: "flex-start", backgroundColor: "#0f172a", padding: "0.75rem 1.25rem", borderRadius: "1rem", border: "1px solid var(--border-color)", color: "var(--text-muted)", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Sparkles size={16} color="#3b82f6" /> DocuMind is searching vector index and generating completion...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSend} style={{ marginTop: "1rem", display: "flex", gap: "0.75rem" }}>
          <input
            type="text"
            required
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            style={{
              flex: 1,
              padding: "0.875rem 1rem",
              backgroundColor: "#0f172a",
              border: "1px solid var(--border-color)",
              borderRadius: "0.5rem",
              color: "#fff",
              fontSize: "0.9375rem",
            }}
          />
          <button type="submit" disabled={sending} className="btn-primary" style={{ padding: "0 1.25rem" }}>
            <Send size={18} /> Send
          </button>
        </form>
      </div>
    </div>
  );
};
