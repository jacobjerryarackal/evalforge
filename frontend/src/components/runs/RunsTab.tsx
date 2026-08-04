import React, { useState, useEffect } from "react";
import {
  Activity, CheckCircle, AlertCircle, Clock, DollarSign, Cpu, FileText, ChevronRight, Play, Terminal, HelpCircle, ShieldAlert
} from "lucide-react";
import { Card } from "../common/Card";
import { Run, Dataset } from "../../types";
import { useRuns } from "../../hooks/useRuns";

interface RunsTabProps {
  runs: Run[];
  datasets: Dataset[];
}

export function RunsTab({ runs, datasets }: RunsTabProps) {
  const { selectedRun, inspectRun } = useRuns();
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [activeSubTab, setActiveSubTab] = useState<"timeline" | "report">("timeline");

  // Reset active case selection when inspecting a different run
  useEffect(() => {
    if (selectedRun && selectedRun.cases.length > 0) {
      setActiveCaseId(selectedRun.cases[0].case_id);
    } else {
      setActiveCaseId(null);
    }
  }, [selectedRun]);

  const activeCaseEvaluation = selectedRun?.cases.find(c => c.case_id === activeCaseId);
  const selectedDataset = datasets.find(d => d.dataset_id === selectedRun?.dataset_id);
  const canonicalTestCase = selectedDataset?.test_cases?.find(
    tc => tc.id === activeCaseId || tc.case_id === activeCaseId
  );

  const getMetricColor = (name: string, score: number | string) => {
    const val = typeof score === "number" ? score : parseFloat(score);
    if (isNaN(val)) return "#94A3B8";
    if (name.toLowerCase() === "hallucination") {
      if (val <= 0.2) return "#10B981"; // green
      if (val <= 0.5) return "#F59E0B"; // orange
      return "#EF4444"; // red
    }
    if (val >= 0.8) return "#10B981"; // green
    if (val >= 0.5) return "#F59E0B"; // orange
    return "#EF4444"; // red
  };

  const getDifficultyColor = (level: string) => {
    if (!level) return "#9CA3AF";
    switch (level.toLowerCase()) {
      case "easy": return "#10B981";
      case "medium": return "#3B82F6";
      case "hard": return "#F59E0B";
      case "expert": return "#EF4444";
      default: return "#9CA3AF";
    }
  };


  const formatCost = (cost: any) => {
    if (typeof cost === "number") return `$${cost.toFixed(4)}`;
    if (cost && typeof cost === "object" && typeof cost.amount === "number") {
      return `$${cost.amount.toFixed(4)}`;
    }
    return "$0.0000";
  };

  const getFinalResponse = (c: any) => {
    const steps = c.trajectory?.steps || [];
    for (let i = steps.length - 1; i >= 0; i--) {
      if (steps[i].response) return steps[i].response;
    }
    return steps[steps.length - 1]?.response || "No final response text generated.";
  };

  const extractRetrievedContexts = (c: any) => {
    const contexts: string[] = [];
    if (!c || !c.trajectory) return contexts;
    const trajectory = c.trajectory;
    if (trajectory.metadata?.retrieved_contexts && Array.isArray(trajectory.metadata.retrieved_contexts)) {
      contexts.push(...trajectory.metadata.retrieved_contexts);
    }
    if (trajectory.metadata?.contexts && Array.isArray(trajectory.metadata.contexts)) {
      contexts.push(...trajectory.metadata.contexts);
    }
    trajectory.steps?.forEach((step: any) => {
      if (step.metadata?.retrieved_contexts && Array.isArray(step.metadata.retrieved_contexts)) {
        contexts.push(...step.metadata.retrieved_contexts);
      }
      if (step.metadata?.contexts && Array.isArray(step.metadata.contexts)) {
        contexts.push(...step.metadata.contexts);
      }
      const obs = step.observation;
      if (obs) {
        if (typeof obs === "object") {
          Object.values(obs).forEach((v: any) => {
            if (Array.isArray(v)) {
              v.forEach((item: any) => {
                if (typeof item === "string") contexts.push(item);
                else if (item && typeof item === "object") contexts.push(JSON.stringify(item));
              });
            } else if (typeof v === "string") {
              contexts.push(v);
            }
          });
        } else if (typeof obs === "string") {
          contexts.push(obs);
        }
      }
    });
    return Array.from(new Set(contexts.map(s => s.trim()).filter(Boolean)));
  };

  const getActualToolCalls = (c: any) => {
    return c?.trajectory?.steps?.flatMap((step: any) => step.tool_calls || []) || [];
  };


  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem", color: "#E5E7EB" }}>
      {/* Runs Table Card */}
      <Card style={{ padding: "1.5rem", background: "#1E293B", border: "1px solid #334155" }}>
        <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Activity size={18} color="#3B82F6" />
          Evaluation Run Executions Log
        </h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#FFF", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #334155", textAlign: "left" }}>
                <th style={{ padding: "0.75rem", color: "#94A3B8", fontWeight: 600 }}>Run ID</th>
                <th style={{ padding: "0.75rem", color: "#94A3B8", fontWeight: 600 }}>Dataset ID</th>
                <th style={{ padding: "0.75rem", color: "#94A3B8", fontWeight: 600 }}>Success Rate</th>
                <th style={{ padding: "0.75rem", color: "#94A3B8", fontWeight: 600 }}>Tokens</th>
                <th style={{ padding: "0.75rem", color: "#94A3B8", fontWeight: 600 }}>Cost</th>
                <th style={{ padding: "0.75rem", color: "#94A3B8", fontWeight: 600 }}>Timestamp</th>
                <th style={{ padding: "0.75rem", color: "#94A3B8", fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: "3rem 1.5rem", textAlign: "center", color: "#64748B" }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
                      <Activity size={32} color="#475569" />
                      <p style={{ margin: 0, fontSize: "0.95rem", fontWeight: 500, color: "#94A3B8" }}>
                        No Evaluation Runs Recorded
                      </p>
                      <p style={{ margin: 0, fontSize: "0.85rem", color: "#64748B" }}>
                        Launch benchmark runs from the Overview dashboard.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                runs.map((r) => (
                  <tr key={r.run_id} style={{ borderBottom: "1px solid #1E293B", transition: "all 0.2s" }}>
                    <td style={{ padding: "0.75rem", fontFamily: "monospace", color: "#38BDF8", fontWeight: 600 }}>
                      {r.run_id}
                    </td>
                    <td style={{ padding: "0.75rem", color: "#E2E8F0" }}>
                      {r.dataset_id} (v{r.dataset_version})
                    </td>
                    <td style={{ padding: "0.75rem" }}>
                      <span style={{
                        color: (r.summary?.success_rate || 0) >= 0.8 ? "#10B981" : (r.summary?.success_rate || 0) >= 0.5 ? "#F59E0B" : "#EF4444",
                        fontWeight: 600
                      }}>
                        {((r.summary?.success_rate || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td style={{ padding: "0.75rem", color: "#94A3B8" }}>{r.summary?.total_tokens || 0}</td>
                    <td style={{ padding: "0.75rem", color: "#10B981", fontWeight: 500 }}>
                      {formatCost(r.summary?.total_cost)}
                    </td>
                    <td style={{ padding: "0.75rem", color: "#64748B", fontSize: "0.8rem" }}>
                      {r.timestamp ? new Date(r.timestamp).toLocaleString() : "N/A"}
                    </td>
                    <td style={{ padding: "0.75rem" }}>
                      <button
                        onClick={() => inspectRun(r.run_id)}
                        style={{
                          background: selectedRun?.run_id === r.run_id ? "#2563EB" : "#334155",
                          color: "#FFF",
                          border: "none",
                          padding: "0.35rem 0.8rem",
                          borderRadius: "0.375rem",
                          cursor: "pointer",
                          fontWeight: 600,
                          fontSize: "0.8rem",
                          display: "flex",
                          alignItems: "center",
                          gap: "0.25rem"
                        }}
                      >
                        Inspect Trace
                        <ChevronRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Redesigned Run Trajectory Inspector Panel */}
      {selectedRun && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

          {/* Header metadata summary */}
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr", gap: "1rem" }}>
            <Card style={{ padding: "1.25rem", background: "#1E293B", border: "1px solid #334155" }}>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "#94A3B8" }}>INSPECTING RUN</p>
              <h3 style={{ margin: "0.25rem 0 0 0", fontSize: "1.25rem", color: "#38BDF8", fontFamily: "monospace", fontWeight: 700 }}>
                {selectedRun.run_id}
              </h3>
              <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>
                Dataset: <strong>{selectedRun.dataset_id} (v{selectedRun.dataset_version})</strong>
              </p>
            </Card>

            <Card style={{ padding: "1.25rem", background: "#1E293B", border: "1px solid #334155" }}>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "#94A3B8" }}>SUCCESS RATE</p>
              <h3 style={{ margin: "0.25rem 0 0 0", fontSize: "1.5rem", color: (selectedRun.summary?.success_rate || 0) >= 0.8 ? "#10B981" : "#EF4444", fontWeight: 700 }}>
                {((selectedRun.summary?.success_rate || 0) * 100).toFixed(1)}%
              </h3>
              <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>
                {selectedRun.summary?.successful_cases}/{selectedRun.summary?.total_cases} passed
              </p>
            </Card>

            <Card style={{ padding: "1.25rem", background: "#1E293B", border: "1px solid #334155" }}>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "#94A3B8" }}>AVG LATENCY</p>
              <h3 style={{ margin: "0.25rem 0 0 0", fontSize: "1.5rem", color: "#FFF", fontWeight: 700 }}>
                {selectedRun.summary?.avg_latency ? `${selectedRun.summary.avg_latency.toFixed(2)}s` : "0.00s"}
              </h3>
              <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>Per execution case</p>
            </Card>

            <Card style={{ padding: "1.25rem", background: "#1E293B", border: "1px solid #334155" }}>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "#94A3B8" }}>TOTAL COST</p>
              <h3 style={{ margin: "0.25rem 0 0 0", fontSize: "1.5rem", color: "#10B981", fontWeight: 700 }}>
                {formatCost(selectedRun.summary?.total_cost)}
              </h3>
              <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>Model & tokens fee</p>
            </Card>

            <Card style={{ padding: "1.25rem", background: "#1E293B", border: "1px solid #334155" }}>
              <p style={{ margin: 0, fontSize: "0.75rem", color: "#94A3B8" }}>TOTAL TOKENS</p>
              <h3 style={{ margin: "0.25rem 0 0 0", fontSize: "1.5rem", color: "#A78BFA", fontWeight: 700 }}>
                {selectedRun.summary?.total_tokens?.toLocaleString() || 0}
              </h3>
              <p style={{ margin: "0.25rem 0 0 0", fontSize: "0.75rem", color: "#64748B" }}>Input + Output</p>
            </Card>
          </div>

          {/* Sub-tab selection (Visual Timeline vs. Markdown Report) */}
          <div style={{ display: "flex", borderBottom: "1px solid #334155", gap: "1rem" }}>
            <button
              onClick={() => setActiveSubTab("timeline")}
              style={{
                background: "none",
                border: "none",
                borderBottom: activeSubTab === "timeline" ? "2px solid #3B82F6" : "none",
                padding: "0.5rem 1rem",
                color: activeSubTab === "timeline" ? "#3B82F6" : "#94A3B8",
                fontWeight: 600,
                cursor: "pointer",
                fontSize: "0.95rem"
              }}
            >
              Visual Trajectory timeline
            </button>
            <button
              onClick={() => setActiveSubTab("report")}
              style={{
                background: "none",
                border: "none",
                borderBottom: activeSubTab === "report" ? "2px solid #3B82F6" : "none",
                padding: "0.5rem 1rem",
                color: activeSubTab === "report" ? "#3B82F6" : "#94A3B8",
                fontWeight: 600,
                cursor: "pointer",
                fontSize: "0.95rem"
              }}
            >
              Markdown Summary Report
            </button>
          </div>

          {activeSubTab === "timeline" ? (
            <div style={{ display: "grid", gridTemplateColumns: "250px 1fr", gap: "1.5rem", alignItems: "start" }}>

              {/* Left sidebar: Case Navigator */}
              <Card style={{ padding: "1rem", background: "#1E293B", border: "1px solid #334155", maxHeight: "650px", overflowY: "auto" }}>
                <h4 style={{ margin: "0 0 0.75rem 0", color: "#FFF", fontSize: "0.9rem", fontWeight: 600, borderBottom: "1px solid #334155", paddingBottom: "0.5rem" }}>
                  Benchmark Cases ({selectedRun.cases.length})
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {selectedRun.cases.map((c) => (
                    <button
                      key={c.case_id}
                      onClick={() => setActiveCaseId(c.case_id)}
                      style={{
                        textAlign: "left",
                        width: "100%",
                        padding: "0.5rem 0.75rem",
                        background: activeCaseId === c.case_id ? "rgba(59, 130, 246, 0.15)" : "#0F172A",
                        border: activeCaseId === c.case_id ? "1px solid #3B82F6" : "1px solid #1E293B",
                        borderRadius: "0.375rem",
                        color: "#FFF",
                        cursor: "pointer",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "0.8rem",
                        transition: "all 0.15s"
                      }}
                    >
                      <span style={{
                        fontFamily: "monospace",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        maxWidth: "130px",
                        color: activeCaseId === c.case_id ? "#60A5FA" : "#94A3B8"
                      }}>
                        {c.case_id}
                      </span>
                      <span style={{
                        fontSize: "0.7rem",
                        padding: "0.1rem 0.3rem",
                        borderRadius: "0.2rem",
                        background: c.success ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                        color: c.success ? "#10B981" : "#EF4444",
                        fontWeight: 600
                      }}>
                        {c.success ? "Pass" : "Fail"}
                      </span>
                    </button>
                  ))}
                </div>
              </Card>

              {/* Right side: Detailed Visual Timeline */}
              {activeCaseEvaluation && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>

                  {/* Case Header Details Card */}
                  <Card style={{ padding: "1.25rem", background: "#1E293B", border: "1px solid #334155" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #334155", paddingBottom: "0.75rem", marginBottom: "0.75rem" }}>
                      <div>
                        <span style={{ fontSize: "0.75rem", color: "#64748B", fontWeight: 600 }}>ACTIVE TEST CASE</span>
                        <h4 style={{ margin: 0, color: "#60A5FA", fontFamily: "monospace", fontSize: "1.1rem" }}>{activeCaseId}</h4>
                      </div>
                      <span style={{
                        padding: "0.25rem 0.75rem",
                        borderRadius: "0.375rem",
                        background: activeCaseEvaluation.success ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                        color: activeCaseEvaluation.success ? "#34D399" : "#F87171",
                        fontWeight: 700,
                        border: `1px solid ${activeCaseEvaluation.success ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)"}`
                      }}>
                        {activeCaseEvaluation.success ? "PASSED THRESHOLDS" : "FAILED CONSTRAINTS"}
                      </span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", fontSize: "0.8rem" }}>
                      {canonicalTestCase && (
                        <>
                          <div>
                            <span style={{ color: "#64748B" }}>Difficulty:</span>
                            <span style={{ color: getDifficultyColor(canonicalTestCase.difficulty), marginLeft: "0.35rem", fontWeight: 600 }}>{canonicalTestCase.difficulty}</span>
                          </div>
                          <div>
                            <span style={{ color: "#64748B" }}>Category:</span>
                            <span style={{ color: "#FFF", marginLeft: "0.35rem", fontWeight: 500 }}>{canonicalTestCase.category}</span>
                          </div>
                          <div>
                            <span style={{ color: "#64748B" }}>Failure Mode Target:</span>
                            <span style={{ color: "#FCA5A5", marginLeft: "0.35rem" }}>{canonicalTestCase.failure_mode || "None"}</span>
                          </div>
                        </>
                      )}
                    </div>
                  </Card>

                  {/* Vertical Chronological Timeline */}
                  <div style={{ position: "relative", paddingLeft: "1.5rem", borderLeft: "2px solid #334155", display: "flex", flexDirection: "column", gap: "1.5rem" }}>

                    {/* Node 1: User Query / Input */}
                    <div style={{ position: "relative" }}>
                      <span style={{ position: "absolute", left: "-2rem", top: "0.25rem", width: "12px", height: "12px", borderRadius: "50%", background: "#3B82F6", border: "3px solid #0F172A" }} />
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                        <span style={{ fontSize: "0.7rem", color: "#60A5FA", fontWeight: 700 }}>INPUT PROMPT</span>
                        <div style={{ background: "#1E293B", padding: "0.75rem 1rem", borderRadius: "0.5rem", border: "1px solid #334155" }}>
                          <p style={{ margin: 0, fontSize: "0.85rem", color: "#E2E8F0", lineHeight: "1.4" }}>
                            "{canonicalTestCase?.user_query || activeCaseEvaluation.input_query || "N/A"}"
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Node 2: Retrieved Ground Truth Context */}
                    {(canonicalTestCase?.retrieved_context || (activeCaseEvaluation.ground_truth_context?.length ?? 0) > 0) && (
                      <div style={{ position: "relative" }}>
                        <span style={{ position: "absolute", left: "-2rem", top: "0.25rem", width: "12px", height: "12px", borderRadius: "50%", background: "#A78BFA", border: "3px solid #0F172A" }} />
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                          <span style={{ fontSize: "0.7rem", color: "#A78BFA", fontWeight: 700 }}>RETRIEVED CONTEXT (GROUND TRUTH)</span>
                          <div style={{ background: "#111827", padding: "0.75rem 1rem", borderRadius: "0.5rem", border: "1px dashed #4B5563" }}>
                            <p style={{ margin: 0, fontSize: "0.8rem", color: "#94A3B8", lineHeight: "1.4" }}>
                              {canonicalTestCase?.retrieved_context || activeCaseEvaluation.ground_truth_context?.join("\n") || "No reference context defined."}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Node 3: Chronological Tool Calls & Thoughts */}
                    {activeCaseEvaluation.trajectory?.steps?.map((step: any, sIdx: number) => (
                      <div key={sIdx} style={{ position: "relative" }}>
                        <span style={{ position: "absolute", left: "-2rem", top: "0.25rem", width: "12px", height: "12px", borderRadius: "50%", background: "#FBBF24", border: "3px solid #0F172A" }} />
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                          <span style={{ fontSize: "0.7rem", color: "#F59E0B", fontWeight: 700 }}>
                            STEP {step.step_number} {step.thought ? `— "${step.thought}"` : ""}
                          </span>

                          {/* Tool Calls block */}
                          {step.tool_calls && step.tool_calls.length > 0 && (
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                              {step.tool_calls.map((tc: any, tcIdx: number) => (
                                <div key={tcIdx} style={{ background: "#0F172A", border: "1px solid #1E293B", borderRadius: "0.375rem", padding: "0.75rem", fontSize: "0.8rem" }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                                    <span style={{ color: "#EC4899", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.25rem" }}>
                                      <Terminal size={12} />
                                      {tc.tool_name}()
                                    </span>
                                    <span style={{ fontSize: "0.7rem", color: tc.success ? "#10B981" : "#EF4444", fontWeight: 600 }}>
                                      {tc.success ? "Success" : "Failed"}
                                    </span>
                                  </div>

                                  {tc.arguments && Object.keys(tc.arguments).length > 0 && (
                                    <div style={{ marginTop: "0.25rem", background: "rgba(0,0,0,0.3)", padding: "0.4rem", borderRadius: "0.25rem" }}>
                                      <pre style={{ margin: 0, fontSize: "0.75rem", color: "#E2E8F0", whiteSpace: "pre-wrap" }}>
                                        {JSON.stringify(tc.arguments, null, 2)}
                                      </pre>
                                    </div>
                                  )}

                                  {tc.error && (
                                    <div style={{ color: "#EF4444", fontSize: "0.75rem", marginTop: "0.25rem", background: "rgba(239, 68, 68, 0.1)", padding: "0.35rem", borderRadius: "0.25rem" }}>
                                      Error: {tc.error}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Observation block */}
                          {step.observation && (
                            <div style={{ background: "#1E293B", padding: "0.5rem 0.75rem", borderRadius: "0.25rem", fontSize: "0.8rem", borderLeft: "3px solid #64748B" }}>
                              <span style={{ fontSize: "0.65rem", color: "#64748B", fontWeight: 600, display: "block" }}>OBSERVATION</span>
                              <span style={{ color: "#94A3B8", whiteSpace: "pre-wrap", overflowWrap: "anywhere", wordBreak: "break-word" }}>
                                {typeof step.observation === "object" ? JSON.stringify(step.observation) : String(step.observation)}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* Node 4: Agent Response / LLM Output */}
                    <div style={{ position: "relative" }}>
                      <span style={{ position: "absolute", left: "-2rem", top: "0.25rem", width: "12px", height: "12px", borderRadius: "50%", background: "#10B981", border: "3px solid #0F172A" }} />
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                        <span style={{ fontSize: "0.7rem", color: "#10B981", fontWeight: 700 }}>LLM FINAL RESPONSE</span>
                        <div style={{ background: "#064E3B", padding: "0.75rem 1rem", borderRadius: "0.5rem", border: "1px solid #065F46" }}>
                          <p style={{ margin: 0, fontSize: "0.85rem", color: "#34D399", fontWeight: 500, lineHeight: "1.4" }}>
                            "{getFinalResponse(activeCaseEvaluation)}"
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Node 5: Expected Answer comparison */}
                    {canonicalTestCase?.expected_answer && (
                      <div style={{ position: "relative" }}>
                        <span style={{ position: "absolute", left: "-2rem", top: "0.25rem", width: "12px", height: "12px", borderRadius: "50%", background: "#14B8A6", border: "3px solid #0F172A" }} />
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                          <span style={{ fontSize: "0.7rem", color: "#14B8A6", fontWeight: 700 }}>EXPECTED GROUND TRUTH ANSWER</span>
                          <div style={{ background: "#0F172A", padding: "0.75rem 1rem", borderRadius: "0.5rem", border: "1px solid #14B8A6" }}>
                            <p style={{ margin: 0, fontSize: "0.85rem", color: "#2DD4BF", lineHeight: "1.4" }}>
                              "{canonicalTestCase.expected_answer}"
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Node 6: Metrics & Judge Scores */}
                    <div style={{ position: "relative" }}>
                      <span style={{ position: "absolute", left: "-2rem", top: "0.25rem", width: "12px", height: "12px", borderRadius: "50%", background: "#EC4899", border: "3px solid #0F172A" }} />
                      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                        <span style={{ fontSize: "0.75rem", color: "#EC4899", fontWeight: 700, letterSpacing: "0.05em" }}>EVALUATION SCORES DETAILED VIEW</span>

                        {/* Deterministic / Constraints Metrics */}
                        <Card style={{ padding: "1.25rem", background: "#111827", border: "1px solid #1F2937" }}>
                          <h5 style={{ margin: "0 0 1rem 0", color: "#FFF", fontSize: "0.9rem", fontWeight: 600 }}>
                            Deterministic Constraints
                          </h5>
                          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                            {activeCaseEvaluation.metrics
                              ?.filter((m: any) => ["Latency", "TokenUsage", "Cost", "ToolCalling"].includes(m.metric_name))
                              .map((m: any) => (
                                <div key={m.metric_name} style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem" }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: "0.35rem", alignItems: "center" }}>
                                    <span style={{ color: "#E2E8F0", fontWeight: 600 }}>{m.metric_name}</span>
                                    <span style={{
                                      color: getMetricColor(m.metric_name, m.score),
                                      fontWeight: 700,
                                      background: `${getMetricColor(m.metric_name, m.score)}15`,
                                      padding: "0.15rem 0.4rem",
                                      borderRadius: "0.25rem"
                                    }}>
                                      {typeof m.score === "number" ? `${(m.score * 100).toFixed(0)}%` : String(m.score)}
                                    </span>
                                  </div>
                                  <p style={{ margin: 0, fontSize: "0.75rem", color: "#94A3B8", lineHeight: "1.4" }}>
                                    <strong>Explanation:</strong> {m.reasoning || "No reasoning explanation provided."}
                                  </p>
                                </div>
                              ))}
                          </div>
                        </Card>

                        {/* Tool Calling Verification */}
                        <Card style={{ padding: "1.25rem", background: "#111827", border: "1px solid #1F2937" }}>
                          <h5 style={{ margin: "0 0 1rem 0", color: "#FFF", fontSize: "0.9rem", fontWeight: 600 }}>
                            Tool Calling Verification
                          </h5>
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: "1rem" }}>
                            <div style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem" }}>
                              <span style={{ fontSize: "0.7rem", color: "#EC4899", fontWeight: 700, display: "block", marginBottom: "0.5rem" }}>EXPECTED TOOL CALLS</span>
                              {canonicalTestCase?.expected_tool_calls && canonicalTestCase.expected_tool_calls.length > 0 ? (
                                <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                                  {canonicalTestCase.expected_tool_calls.map((tc: any, idx: number) => (
                                    <div key={idx} style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "#94A3B8", background: "#0F172A", padding: "0.35rem", borderRadius: "0.25rem", whiteSpace: "pre-wrap", overflowWrap: "anywhere", wordBreak: "break-word", maxWidth: "100%", overflow: "hidden" }}>
                                      {typeof tc === "string" ? tc : `${tc.method || tc.tool_name || "unknown"}(${JSON.stringify(tc.parameters || tc.arguments || {})})`}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <span style={{ fontSize: "0.75rem", color: "#64748B" }}>No expected tool calls.</span>
                              )}
                            </div>
                            <div style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem" }}>
                              <span style={{ fontSize: "0.7rem", color: "#10B981", fontWeight: 700, display: "block", marginBottom: "0.5rem" }}>ACTUAL TOOL CALLS</span>
                              {getActualToolCalls(activeCaseEvaluation).length > 0 ? (
                                <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                                  {getActualToolCalls(activeCaseEvaluation).map((tc: any, idx: number) => (
                                    <div key={idx} style={{
                                      fontFamily: "monospace",
                                      fontSize: "0.75rem",
                                      color: tc.success ? "#34D399" : "#F87171",
                                      background: "#0F172A",
                                      padding: "0.35rem",
                                      borderRadius: "0.25rem",
                                      whiteSpace: "pre-wrap",
                                      overflowWrap: "anywhere",
                                      wordBreak: "break-word",
                                      maxWidth: "100%", overflow: "hidden"
                                    }}>
                                      {tc.tool_name}({JSON.stringify(tc.arguments || {})})
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <span style={{ fontSize: "0.75rem", color: "#64748B" }}>No actual tool calls executed.</span>
                              )}
                            </div>
                          </div>
                          {(() => {
                            const tcMetric = activeCaseEvaluation.metrics?.find((m: any) => m.metric_name === "ToolCalling");
                            if (tcMetric && tcMetric.reasoning) {
                              return (
                                <div style={{ marginTop: "1rem", background: tcMetric.score === 1 ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)", border: `1px solid ${tcMetric.score === 1 ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)"}`, padding: "0.75rem", borderRadius: "0.375rem" }}>
                                  <span style={{ fontSize: "0.7rem", color: tcMetric.score === 1 ? "#34D399" : "#F87171", fontWeight: 700, display: "block", marginBottom: "0.25rem" }}>
                                    TOOL CALLS AUDIT REPORT & MISMATCH EXPLANATION
                                  </span>
                                  <p style={{ margin: 0, fontSize: "0.75rem", color: "#E2E8F0" }}>{tcMetric.reasoning}</p>
                                </div>
                              );
                            }
                            return null;
                          })()}
                        </Card>

                        {/* Retrieval Verification */}
                        <Card style={{ padding: "1.25rem", background: "#111827", border: "1px solid #1F2937" }}>
                          <h5 style={{ margin: "0 0 1rem 0", color: "#FFF", fontSize: "0.9rem", fontWeight: 600 }}>
                            Retrieval Verification
                          </h5>
                          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                            <div style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem" }}>
                              <span style={{ fontSize: "0.7rem", color: "#A78BFA", fontWeight: 700, display: "block", marginBottom: "0.5rem" }}>EXPECTED / GROUND TRUTH CONTEXT</span>
                              {canonicalTestCase?.ground_truth_context && canonicalTestCase.ground_truth_context.length > 0 ? (
                                <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.75rem", color: "#94A3B8" }}>
                                  {canonicalTestCase.ground_truth_context.map((c: string, idx: number) => (
                                    <li key={idx} style={{ marginBottom: "0.25rem" }}>{c}</li>
                                  ))}
                                </ul>
                              ) : (
                                <span style={{ fontSize: "0.75rem", color: "#64748B" }}>No expected ground truth context.</span>
                              )}
                            </div>

                            <div style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem" }}>
                              <span style={{ fontSize: "0.7rem", color: "#60A5FA", fontWeight: 700, display: "block", marginBottom: "0.5rem" }}>RETRIEVED CONTEXT snippets</span>
                              {extractRetrievedContexts(activeCaseEvaluation).length > 0 ? (
                                <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.75rem", color: "#94A3B8" }}>
                                  {extractRetrievedContexts(activeCaseEvaluation).map((c: string, idx: number) => (
                                    <li key={idx} style={{ marginBottom: "0.25rem" }}>{c}</li>
                                  ))}
                                </ul>
                              ) : (
                                <span style={{ fontSize: "0.75rem", color: "#64748B" }}>No retrieved context.</span>
                              )}
                            </div>

                            {/* Missing / Extra Analysis */}
                            {(() => {
                              const gt = canonicalTestCase?.ground_truth_context || [];
                              const ret = extractRetrievedContexts(activeCaseEvaluation);
                              const missing = gt.filter((g: string) => !ret.some((r: string) => r.toLowerCase().includes(g.toLowerCase()) || g.toLowerCase().includes(r.toLowerCase())));
                              const extra = ret.filter((r: string) => !gt.some((g: string) => g.toLowerCase().includes(r.toLowerCase()) || r.toLowerCase().includes(g.toLowerCase())));

                              return (
                                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: "1rem" }}>
                                  <div style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem", borderLeft: `3px solid ${missing.length > 0 ? "#EF4444" : "#10B981"}` }}>
                                    <span style={{ fontSize: "0.7rem", color: missing.length > 0 ? "#F87171" : "#34D399", fontWeight: 700, display: "block", marginBottom: "0.25rem" }}>MISSING CONTEXT</span>
                                    {missing.length > 0 ? (
                                      <ul style={{ margin: 0, paddingLeft: "1rem", fontSize: "0.7rem", color: "#FCA5A5" }}>
                                        {missing.map((c: string, idx: number) => <li key={idx}>{c}</li>)}
                                      </ul>
                                    ) : (
                                      <span style={{ fontSize: "0.7rem", color: "#34D399" }}>Perfect recall - 0 items missing.</span>
                                    )}
                                  </div>
                                  <div style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem", borderLeft: "3px solid #3B82F6" }}>
                                    <span style={{ fontSize: "0.7rem", color: "#60A5FA", fontWeight: 700, display: "block", marginBottom: "0.25rem" }}>EXTRA CONTEXT</span>
                                    {extra.length > 0 ? (
                                      <ul style={{ margin: 0, paddingLeft: "1rem", fontSize: "0.7rem", color: "#93C5FD" }}>
                                        {extra.map((c: string, idx: number) => <li key={idx}>{c}</li>)}
                                      </ul>
                                    ) : (
                                      <span style={{ fontSize: "0.7rem", color: "#94A3B8" }}>0 extra items retrieved.</span>
                                    )}
                                  </div>
                                </div>
                              );
                            })()}

                            {/* Precision & Recall metrics */}
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0,1fr))", gap: "1rem" }}>
                              {activeCaseEvaluation.metrics
                                ?.filter((m: any) => ["ContextPrecision", "ContextRecall"].includes(m.metric_name))
                                .map((m: any) => (
                                  <div key={m.metric_name} style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem" }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "0.2rem", alignItems: "center" }}>
                                      <span style={{ color: "#E2E8F0", fontWeight: 600 }}>{m.metric_name}</span>
                                      <strong style={{ color: getMetricColor(m.metric_name, m.score) }}>
                                        {typeof m.score === "number" ? `${(m.score * 100).toFixed(0)}%` : String(m.score)}
                                      </strong>
                                    </div>
                                    <p style={{ margin: 0, fontSize: "0.7rem", color: "#94A3B8", lineHeight: "1.4" }}>
                                      {m.reasoning}
                                    </p>
                                  </div>
                                ))}
                            </div>
                          </div>
                        </Card>

                        {/* LLM-as-a-Judge Scores */}
                        <Card style={{ padding: "1.25rem", background: "#111827", border: "1px solid #1F2937" }}>
                          <h5 style={{ margin: "0 0 1rem 0", color: "#FFF", fontSize: "0.9rem", fontWeight: 600 }}>
                            LLM-as-a-Judge Scores
                          </h5>
                          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                            {activeCaseEvaluation.metrics
                              ?.filter((m: any) => ["Faithfulness", "Groundedness", "AnswerCorrectness", "Hallucination"].includes(m.metric_name))
                              .map((m: any) => (
                                <div key={m.metric_name} style={{ background: "#1E293B", padding: "0.75rem", borderRadius: "0.375rem" }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: "0.35rem", alignItems: "center" }}>
                                    <span style={{ color: "#E2E8F0", fontWeight: 600 }}>{m.metric_name}</span>
                                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                                      {m.metadata?.confidence !== undefined && (
                                        <span style={{ fontSize: "0.7rem", color: "#64748B" }}>
                                          Confidence: {typeof m.metadata.confidence === "number" ? `${(m.metadata.confidence * 100).toFixed(0)}%` : String(m.metadata.confidence)}
                                        </span>
                                      )}
                                      <span style={{
                                        color: getMetricColor(m.metric_name, m.score),
                                        fontWeight: 700,
                                        background: `${getMetricColor(m.metric_name, m.score)}15`,
                                        padding: "0.15rem 0.4rem",
                                        borderRadius: "0.25rem"
                                      }}>
                                        {typeof m.score === "number" ? `${(m.score * 100).toFixed(0)}%` : String(m.score)}
                                      </span>
                                    </div>
                                  </div>
                                  <p style={{ margin: 0, fontSize: "0.75rem", color: "#94A3B8", lineHeight: "1.4" }}>
                                    <strong>Judge Reasoning:</strong> {m.reasoning}
                                  </p>
                                </div>
                              ))}
                            {(!activeCaseEvaluation.metrics || activeCaseEvaluation.metrics.filter((m: any) => ["Faithfulness", "Groundedness", "AnswerCorrectness", "Hallucination"].includes(m.metric_name)).length === 0) && (
                              <div style={{ fontSize: "0.75rem", color: "#64748B", textAlign: "center", padding: "1rem 0" }}>
                                No LLM judge scores computed.
                              </div>
                            )}
                          </div>
                        </Card>
                      </div>
                    </div>

                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Render Markdown report professionally */
            <Card style={{ padding: "2rem", background: "#1E293B", border: "1px solid #334155" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #334155", paddingBottom: "1rem", marginBottom: "1rem" }}>
                <h4 style={{ margin: 0, fontSize: "1.1rem", color: "#FFF", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <FileText size={18} color="#A78BFA" />
                  Generated Run Report (Markdown)
                </h4>
              </div>

              <div
                style={{
                  background: "#0F172A",
                  padding: "1.5rem",
                  borderRadius: "0.5rem",
                  color: "#E2E8F0",
                  fontFamily: "monospace",
                  fontSize: "0.85rem",
                  maxHeight: "650px",
                  overflowY: "auto",
                  lineHeight: "1.5",
                  whiteSpace: "pre-wrap"
                }}
              >
                {selectedRun.report || "No markdown summary report was compiled for this execution."}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
