import React from "react";
import { Activity } from "lucide-react";
import { Card } from "../common/Card";
import { Run } from "../../types";
import { useRuns } from "../../hooks/useRuns";

interface RunsTabProps {
  runs: Run[];
}

export function RunsTab({ runs }: RunsTabProps) {
  const { selectedRun, inspectRun } = useRuns();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      <Card style={{ padding: "1.5rem" }}>
        <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
          Evaluation Execution Runs
        </h3>
        <table style={{ width: "100%", borderCollapse: "collapse", color: "#FFF" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #1F2937", textAlign: "left" }}>
              <th style={{ padding: "0.75rem", color: "#9CA3AF" }}>Run ID</th>
              <th style={{ padding: "0.75rem", color: "#9CA3AF" }}>Dataset ID</th>
              <th style={{ padding: "0.75rem", color: "#9CA3AF" }}>Success Rate</th>
              <th style={{ padding: "0.75rem", color: "#9CA3AF" }}>Tokens</th>
              <th style={{ padding: "0.75rem", color: "#9CA3AF" }}>Cost</th>
              <th style={{ padding: "0.75rem", color: "#9CA3AF" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: "3rem 1.5rem", textAlign: "center", color: "#6B7280" }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
                    <Activity size={28} color="#4B5563" />
                    <p style={{ margin: 0, fontSize: "0.95rem", fontWeight: 500, color: "#9CA3AF" }}>
                      No Evaluation Runs Yet
                    </p>
                    <p style={{ margin: 0, fontSize: "0.85rem", color: "#6B7280" }}>
                      Trigger a benchmark sweep from the Overview tab.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              runs.map((r) => (
                <tr key={r.run_id} style={{ borderBottom: "1px solid #111827" }}>
                  <td style={{ padding: "0.75rem" }}>`{r.run_id}`</td>
                  <td style={{ padding: "0.75rem" }}>
                    {r.dataset_id} (v{r.dataset_version})
                  </td>
                  <td style={{ padding: "0.75rem" }}>{((r.summary?.success_rate || 0) * 100).toFixed(1)}%</td>
                  <td style={{ padding: "0.75rem" }}>{r.summary?.total_tokens || 0}</td>
                  <td style={{ padding: "0.75rem" }}>${(r.summary?.total_cost || 0).toFixed(4)}</td>
                  <td style={{ padding: "0.75rem" }}>
                    <button
                      onClick={() => inspectRun(r.run_id)}
                      style={{
                        background: "#3B82F6",
                        color: "#FFF",
                        border: "none",
                        padding: "0.25rem 0.75rem",
                        borderRadius: "0.25rem",
                        cursor: "pointer",
                        fontWeight: 500,
                      }}
                    >
                      Inspect Trace
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      {/* Run Trajectory Details */}
      {selectedRun && (
        <Card style={{ padding: "2rem" }}>
          <h3 style={{ fontSize: "1.3rem", color: "#FFF", margin: "0 0 1.5rem 0" }}>
            Run Trajectory Inspector: `{selectedRun.run_id}`
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
            <div>
              <h4 style={{ fontSize: "1.1rem", color: "#FFF", margin: "0 0 1rem 0" }}>Test Case Traces</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {selectedRun.cases.map((c: any) => (
                  <div
                    key={c.case_id}
                    style={{
                      background: "#111827",
                      border: "1px solid #1F2937",
                      padding: "1rem",
                      borderRadius: "0.5rem",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#FFF", fontWeight: 600 }}>Case: `{c.case_id}`</span>
                      <span style={{ color: c.success ? "#10B981" : "#EF4444" }}>
                        {c.success ? "Passed" : "Failed"}
                      </span>
                    </div>
                    <p style={{ color: "#9CA3AF", fontSize: "0.85rem", margin: "0.5rem 0 0 0" }}>
                      Query: "{c.input_query}"
                    </p>
                    {c.metrics && (
                      <div style={{ marginTop: "0.75rem" }}>
                        <span style={{ fontSize: "0.85rem", color: "#FFF" }}>Metrics:</span>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.25rem" }}>
                          {c.metrics.map((m: any) => (
                            <span
                              key={m.metric_name}
                              style={{
                                fontSize: "0.75rem",
                                background: "#1F2937",
                                padding: "0.15rem 0.4rem",
                                borderRadius: "0.25rem",
                                color: "#FFF",
                              }}
                            >
                              {m.metric_name}:{" "}
                              {typeof m.score === "number" ? `${(m.score * 100).toFixed(0)}%` : String(m.score)}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: "1.1rem", color: "#FFF", margin: "0 0 1rem 0" }}>
                Run Report (Markdown)
              </h4>
              <pre
                style={{
                  background: "#111827",
                  padding: "1rem",
                  borderRadius: "0.5rem",
                  overflowX: "auto",
                  color: "#E2E8F0",
                  fontSize: "0.85rem",
                  maxHeight: "350px",
                }}
              >
                {selectedRun.report}
              </pre>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
