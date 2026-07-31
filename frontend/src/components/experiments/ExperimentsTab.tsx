import React from "react";
import { Award } from "lucide-react";
import { Card } from "../common/Card";
import { Experiment } from "../../types";
import { useExperiments } from "../../hooks/useExperiments";

interface ExperimentsTabProps {
  experiments: Experiment[];
  onExperimentCreated: () => void;
}

export function ExperimentsTab({ experiments, onExperimentCreated }: ExperimentsTabProps) {
  const {
    newExpId,
    setNewExpId,
    newExpName,
    setNewExpName,
    newExpDesc,
    setNewExpDesc,
    status,
    selectedExperiment,
    createExperiment,
    inspectExperiment,
  } = useExperiments(onExperimentCreated);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "2rem" }}>
        {/* Create Experiment Form */}
        <Card style={{ padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
            Create Experiment Sweep
          </h3>
          <form onSubmit={createExperiment} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Experiment ID *
              </label>
              <input
                type="text"
                value={newExpId}
                onChange={(e) => setNewExpId(e.target.value)}
                placeholder="e.g. prompt-v2-vs-v1"
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Experiment Name *
              </label>
              <input
                type="text"
                value={newExpName}
                onChange={(e) => setNewExpName(e.target.value)}
                placeholder="e.g. Prompt Optimization Sweep"
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                Description
              </label>
              <textarea
                value={newExpDesc}
                onChange={(e) => setNewExpDesc(e.target.value)}
                placeholder="Comparing prompt styles on flight queries"
                style={{
                  width: "100%",
                  padding: "0.4rem",
                  background: "#111827",
                  border: "1px solid #374151",
                  borderRadius: "0.25rem",
                  color: "#FFF",
                  minHeight: "80px",
                }}
              />
            </div>
            <button
              type="submit"
              style={{
                background: "#8B5CF6",
                color: "#FFF",
                border: "none",
                padding: "0.5rem 1rem",
                borderRadius: "0.25rem",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Create Experiment
            </button>
            {status && <span style={{ color: "#EAB308", fontSize: "0.85rem" }}>{status}</span>}
          </form>
        </Card>

        {/* Experiments Catalog */}
        <Card style={{ padding: "1.5rem" }}>
          <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
            Experiments Overview
          </h3>
          {experiments.length === 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "3rem 1.5rem",
                background: "#111827",
                border: "1px dashed #374151",
                borderRadius: "0.5rem",
                textAlign: "center",
                gap: "0.75rem",
              }}
            >
              <Award size={32} color="#4B5563" />
              <div>
                <p style={{ margin: 0, color: "#9CA3AF", fontSize: "0.95rem", fontWeight: 500 }}>
                  No Active Experiments
                </p>
                <p style={{ margin: "0.25rem 0 0 0", color: "#6B7280", fontSize: "0.85rem" }}>
                  Create a sweep to group and compare evaluation runs.
                </p>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {experiments.map((e) => (
                <div
                  key={e.experiment_id}
                  onClick={() => inspectExperiment(e.experiment_id)}
                  style={{
                    background: "#111827",
                    border: "1px solid #1F2937",
                    padding: "1.25rem",
                    borderRadius: "0.5rem",
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <h4 style={{ fontSize: "1.1rem", margin: 0, color: "#FFF" }}>{e.name}</h4>
                    <span style={{ fontSize: "0.75rem", color: "#3B82F6" }}>{e.runs_count} Sweeps Registered</span>
                  </div>
                  <p style={{ margin: "0.5rem 0 0.25rem 0", color: "#9CA3AF", fontSize: "0.9rem" }}>
                    {e.description || "No description provided."}
                  </p>
                  <code style={{ fontSize: "0.75rem", color: "#6B7280" }}>{e.experiment_id}</code>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Experiment Comparison Details */}
      {selectedExperiment && (
        <Card style={{ padding: "2rem" }}>
          <h3 style={{ fontSize: "1.3rem", color: "#FFF", margin: "0 0 1.5rem 0" }}>
            Experiment Comparison Report: `{selectedExperiment.experiment_id}`
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
            <div>
              <h4 style={{ fontSize: "1.1rem", color: "#FFF", margin: "0 0 1rem 0" }}>
                Registered Runs List
              </h4>
              <table style={{ width: "100%", borderCollapse: "collapse", color: "#FFF" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #1F2937", textAlign: "left" }}>
                    <th style={{ padding: "0.5rem", color: "#9CA3AF" }}>Run ID</th>
                    <th style={{ padding: "0.5rem", color: "#9CA3AF" }}>Success Rate</th>
                    <th style={{ padding: "0.5rem", color: "#9CA3AF" }}>Avg Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedExperiment.runs.map((r: any) => (
                    <tr key={r.run_id} style={{ borderBottom: "1px solid #111827" }}>
                      <td style={{ padding: "0.5rem" }}>`{r.run_id}`</td>
                      <td style={{ padding: "0.5rem" }}>{((r.summary?.success_rate || 0) * 100).toFixed(1)}%</td>
                      <td style={{ padding: "0.5rem" }}>{(r.summary?.avg_latency || 0).toFixed(2)}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <h4 style={{ fontSize: "1.1rem", color: "#FFF", margin: "0 0 1rem 0" }}>
                Experiment Sweeps Analysis
              </h4>
              <pre
                style={{
                  background: "#111827",
                  padding: "1rem",
                  borderRadius: "0.5rem",
                  overflowX: "auto",
                  color: "#E2E8F0",
                  fontSize: "0.85rem",
                  maxHeight: "300px",
                }}
              >
                {selectedExperiment.report_markdown}
              </pre>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
