import React from "react";
import { BarChart3, Database, Award, Activity, FlaskConical } from "lucide-react";

interface SidebarProps {
  activeTab: "overview" | "datasets" | "experiments" | "runs";
  setActiveTab: (tab: "overview" | "datasets" | "experiments" | "runs") => void;
}

export function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const navItems = [
    { id: "overview" as const, label: "Overview", icon: BarChart3 },
    { id: "datasets" as const, label: "Datasets", icon: Database },
    { id: "experiments" as const, label: "Experiments", icon: Award },
    { id: "runs" as const, label: "Run History", icon: Activity },
  ];

  return (
    <div
      style={{
        width: "280px",
        background: "linear-gradient(180deg, #111827 0%, #030712 100%)",
        borderRight: "1px solid #1F2937",
        padding: "2rem 1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "2.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <div
          style={{
            background: "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)",
            padding: "0.5rem",
            borderRadius: "0.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 15px rgba(59, 130, 246, 0.4)",
          }}
        >
          <FlaskConical size={24} color="#FFF" />
        </div>
        <div>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0, color: "#FFF" }}>
            EvalForge
          </h1>
          <span style={{ fontSize: "0.75rem", color: "#6B7280" }}>Evaluation Platform</span>
        </div>
      </div>

      <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                width: "100%",
                padding: "0.75rem 1rem",
                borderRadius: "0.5rem",
                border: "none",
                background: isActive ? "rgba(59, 130, 246, 0.1)" : "transparent",
                color: isActive ? "#3B82F6" : "#9CA3AF",
                textAlign: "left",
                cursor: "pointer",
                fontSize: "0.95rem",
                fontWeight: 500,
                transition: "all 0.2s",
              }}
            >
              <Icon size={18} /> {item.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
