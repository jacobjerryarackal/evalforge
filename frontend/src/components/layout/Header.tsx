import React from "react";
import { RefreshCw } from "lucide-react";

interface HeaderProps {
  activeTab: "overview" | "datasets" | "experiments" | "runs";
  backendConnected: boolean;
  onSync: () => void;
  isRefreshing?: boolean;
}

export function Header({ activeTab, backendConnected, onSync, isRefreshing = false }: HeaderProps) {
  const getTitle = () => {
    switch (activeTab) {
      case "overview":
        return "Platform Overview";
      case "datasets":
        return "Dataset Hub";
      case "experiments":
        return "Experiment Sweeps";
      case "runs":
        return "Evaluation Trajectories";
      default:
        return "Platform Overview";
    }
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "2rem",
      }}
    >
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0, color: "#FFF" }}>
          {getTitle()}
        </h2>
        <p style={{ margin: "0.25rem 0 0 0", color: "#6B7280", fontSize: "0.9rem" }}>
          Continuous evaluation dashboard for agentic workflows
        </p>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {!backendConnected && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              background: "rgba(239, 68, 68, 0.1)",
              border: "1px solid #EF4444",
              padding: "0.4rem 0.8rem",
              borderRadius: "0.375rem",
              color: "#EF4444",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            <span
              style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "#EF4444",
              }}
            />
            Backend Offline
          </div>
        )}
        {backendConnected && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              background: "rgba(16, 185, 129, 0.1)",
              border: "1px solid #10B981",
              padding: "0.4rem 0.8rem",
              borderRadius: "0.375rem",
              color: "#10B981",
              fontSize: "0.85rem",
              fontWeight: 600,
            }}
          >
            <span
              style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "#10B981",
              }}
            />
            Connected
          </div>
        )}
        <button
          onClick={onSync}
          disabled={isRefreshing}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            background: "#1F2937",
            color: "#FFF",
            border: "1px solid #374151",
            padding: "0.5rem 1rem",
            borderRadius: "0.375rem",
            cursor: "pointer",
            fontSize: "0.9rem",
            fontWeight: 500,
            opacity: isRefreshing ? 0.7 : 1,
          }}
        >
          <RefreshCw size={14} className={isRefreshing ? "animate-spin" : ""} /> Sync Metrics
        </button>
      </div>
    </div>
  );
}
