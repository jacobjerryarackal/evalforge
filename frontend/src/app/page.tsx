"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  Award,
  BarChart3,
  BookOpen,
  Calendar,
  ChevronRight,
  Database,
  DollarSign,
  FlaskConical,
  Play,
  RefreshCw,
  TrendingUp,
  Clock,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Dataset {
  dataset_id: string;
  name: string;
  version: string;
  cases_count: number;
}

interface Run {
  run_id: string;
  dataset_id: string;
  dataset_version: string;
  sut_version: string;
  timestamp: string;
  summary: {
    success_rate: number;
    total_cases: number;
    successful_cases: number;
    total_tokens: number;
    total_cost: number;
    avg_latency: number;
  };
}

interface Experiment {
  experiment_id: string;
  name: string;
  description: string;
  runs_count: number;
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"overview" | "datasets" | "experiments" | "runs">(
    "overview"
  );
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [selectedExperiment, setSelectedExperiment] = useState<any>(null);

  // Form states
  const [runDatasetId, setRunDatasetId] = useState("");
  const [runVersion, setRunVersion] = useState("");
  const [runConcurrency, setRunConcurrency] = useState(3);
  const [runMaxRetries, setRunMaxRetries] = useState(0);
  const [runExperimentId, setRunExperimentId] = useState("");
  const [runId, setRunId] = useState("");
  const [runStatusMsg, setRunStatusMsg] = useState("");

  const [newDatasetId, setNewDatasetId] = useState("");
  const [newDatasetName, setNewDatasetName] = useState("");
  const [newDatasetVersion, setNewDatasetVersion] = useState("1.0.0");
  const [newDatasetQuery, setNewDatasetQuery] = useState("");
  const [newDatasetExpected, setNewDatasetExpected] = useState("");
  const [newDatasetStatus, setNewDatasetStatus] = useState("");

  const [newExpId, setNewExpId] = useState("");
  const [newExpName, setNewExpName] = useState("");
  const [newExpDesc, setNewExpDesc] = useState("");
  const [newExpStatus, setNewExpStatus] = useState("");

  const fetchData = async () => {
    try {
      const dsRes = await fetch(`${API_BASE}/api/datasets`);
      if (dsRes.ok) setDatasets(await dsRes.json());

      const runsRes = await fetch(`${API_BASE}/api/runs`);
      if (runsRes.ok) setRuns(await runsRes.json());

      const expsRes = await fetch(`${API_BASE}/api/experiments`);
      if (expsRes.ok) setExperiments(await expsRes.json());
    } catch (e) {
      console.error("API offline", e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleRunBenchmark = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!runDatasetId || !runVersion) {
      setRunStatusMsg("Please select dataset and version.");
      return;
    }
    setRunStatusMsg("Triggering execution...");
    try {
      const res = await fetch(`${API_BASE}/api/benchmarks/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: runDatasetId,
          version: runVersion,
          run_id: runId || undefined,
          concurrency: runConcurrency,
          max_retries: runMaxRetries,
          experiment_id: runExperimentId || undefined,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setRunStatusMsg(`Started successfully! Run ID: ${data.run_id}`);
        setRunId("");
        fetchData();
      } else {
        const error = await res.json();
        setRunStatusMsg(`Error: ${error.detail}`);
      }
    } catch (err: any) {
      setRunStatusMsg(`Failed to connect: ${err.message}`);
    }
  };

  const handleCreateDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDatasetId || !newDatasetName || !newDatasetQuery) {
      setNewDatasetStatus("Please fill all required fields.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/datasets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: newDatasetId,
          name: newDatasetName,
          version: newDatasetVersion,
          test_cases: [
            {
              case_id: "case-1",
              input_query: newDatasetQuery,
              expected_output: newDatasetExpected || null,
              expected_tool_calls: [],
              constraints: {},
              ground_truth_context: [],
            },
          ],
        }),
      });
      if (res.ok) {
        setNewDatasetStatus("Dataset registered!");
        setNewDatasetId("");
        setNewDatasetName("");
        setNewDatasetQuery("");
        setNewDatasetExpected("");
        fetchData();
      } else {
        const err = await res.json();
        setNewDatasetStatus(`Error: ${err.detail}`);
      }
    } catch (err: any) {
      setNewDatasetStatus(`Failed to connect: ${err.message}`);
    }
  };

  const handleCreateExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newExpId || !newExpName) {
      setNewExpStatus("Please fill required fields.");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/experiments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          experiment_id: newExpId,
          name: newExpName,
          description: newExpDesc || undefined,
        }),
      });
      if (res.ok) {
        setNewExpStatus("Experiment created!");
        setNewExpId("");
        setNewExpName("");
        setNewExpDesc("");
        fetchData();
      } else {
        const err = await res.json();
        setNewExpStatus(`Error: ${err.detail}`);
      }
    } catch (err: any) {
      setNewExpStatus(`Failed to connect: ${err.message}`);
    }
  };

  const inspectRun = async (runId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/runs/${runId}`);
      if (res.ok) {
        const data = await res.json();
        // Fetch report
        const repRes = await fetch(`${API_BASE}/api/runs/${runId}/report`);
        const reportData = repRes.ok ? await repRes.json() : { report_markdown: "" };
        setSelectedRun({ ...data, report: reportData.report_markdown });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const inspectExperiment = async (expId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/experiments/${expId}`);
      if (res.ok) {
        setSelectedExperiment(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Metrics aggregations for overview
  const totalRuns = runs.length;
  const avgSuccessRate = runs.reduce((acc, r) => acc + (r.summary?.success_rate || 0), 0) / (totalRuns || 1);
  const totalCostVal = runs.reduce((acc, r) => acc + (r.summary?.total_cost || 0), 0);
  const avgLatencyVal = runs.reduce((acc, r) => acc + (r.summary?.avg_latency || 0), 0) / (totalRuns || 1);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar Navigation */}
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
          <button
            onClick={() => setActiveTab("overview")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              width: "100%",
              padding: "0.75rem 1rem",
              borderRadius: "0.5rem",
              border: "none",
              background: activeTab === "overview" ? "rgba(59, 130, 246, 0.1)" : "transparent",
              color: activeTab === "overview" ? "#3B82F6" : "#9CA3AF",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "0.95rem",
              fontWeight: 500,
              transition: "all 0.2s",
            }}
          >
            <BarChart3 size={18} /> Overview
          </button>

          <button
            onClick={() => setActiveTab("datasets")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              width: "100%",
              padding: "0.75rem 1rem",
              borderRadius: "0.5rem",
              border: "none",
              background: activeTab === "datasets" ? "rgba(59, 130, 246, 0.1)" : "transparent",
              color: activeTab === "datasets" ? "#3B82F6" : "#9CA3AF",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "0.95rem",
              fontWeight: 500,
              transition: "all 0.2s",
            }}
          >
            <Database size={18} /> Datasets
          </button>

          <button
            onClick={() => setActiveTab("experiments")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              width: "100%",
              padding: "0.75rem 1rem",
              borderRadius: "0.5rem",
              border: "none",
              background: activeTab === "experiments" ? "rgba(59, 130, 246, 0.1)" : "transparent",
              color: activeTab === "experiments" ? "#3B82F6" : "#9CA3AF",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "0.95rem",
              fontWeight: 500,
              transition: "all 0.2s",
            }}
          >
            <Award size={18} /> Experiments
          </button>

          <button
            onClick={() => setActiveTab("runs")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              width: "100%",
              padding: "0.75rem 1rem",
              borderRadius: "0.5rem",
              border: "none",
              background: activeTab === "runs" ? "rgba(59, 130, 246, 0.1)" : "transparent",
              color: activeTab === "runs" ? "#3B82F6" : "#9CA3AF",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "0.95rem",
              fontWeight: 500,
              transition: "all 0.2s",
            }}
          >
            <Activity size={18} /> Run History
          </button>
        </nav>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, padding: "2rem 3rem", overflowY: "auto", maxHeight: "100vh" }}>
        {/* Top Header */}
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
              {activeTab === "overview" && "Platform Overview"}
              {activeTab === "datasets" && "Dataset Hub"}
              {activeTab === "experiments" && "Experiment swept Sweeps"}
              {activeTab === "runs" && "Evaluation Trajectories"}
            </h2>
            <p style={{ margin: "0.25rem 0 0 0", color: "#6B7280", fontSize: "0.9rem" }}>
              Continuous evaluation dashboard for agentic workflows
            </p>
          </div>
          <button
            onClick={fetchData}
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
            }}
          >
            <RefreshCw size={14} /> Sync Metrics
          </button>
        </div>

        {/* OVERVIEW TAB CONTENT */}
        {activeTab === "overview" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            {/* Quick Metrics Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1.5rem" }}>
              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  backdropFilter: "blur(10px)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Total Runs</span>
                  <Activity size={18} color="#3B82F6" />
                </div>
                <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>
                  {totalRuns}
                </h3>
              </div>

              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  backdropFilter: "blur(10px)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Avg Success Rate</span>
                  <TrendingUp size={18} color="#10B981" />
                </div>
                <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>
                  {avgSuccessRate ? `${(avgSuccessRate * 100).toFixed(1)}%` : "0.0%"}
                </h3>
              </div>

              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  backdropFilter: "blur(10px)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Cumulative Cost</span>
                  <DollarSign size={18} color="#EAB308" />
                </div>
                <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>
                  ${totalCostVal.toFixed(4)}
                </h3>
              </div>

              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  backdropFilter: "blur(10px)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Avg Latency</span>
                  <Clock size={18} color="#A755F7" />
                </div>
                <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>
                  {avgLatencyVal.toFixed(2)}s
                </h3>
              </div>
            </div>

            {/* Run Benchmark panel */}
            <div
              style={{
                background: "rgba(17, 24, 39, 0.6)",
                border: "1px solid #1F2937",
                borderRadius: "0.75rem",
                padding: "2rem",
              }}
            >
              <h3
                style={{
                  fontSize: "1.2rem",
                  margin: "0 0 1.5rem 0",
                  color: "#FFF",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <Play size={16} color="#3B82F6" /> Trigger Async Benchmark
              </h3>
              <form
                onSubmit={handleRunBenchmark}
                style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1.5rem" }}
              >
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      color: "#9CA3AF",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Select Dataset ID *
                  </label>
                  <select
                    value={runDatasetId}
                    onChange={(e) => setRunDatasetId(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#111827",
                      border: "1px solid #374151",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                    }}
                  >
                    <option value="">-- Choose Dataset --</option>
                    {Array.from(new Set(datasets.map((d) => d.dataset_id))).map((id) => (
                      <option key={id} value={id}>
                        {id}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      color: "#9CA3AF",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Dataset Version *
                  </label>
                  <select
                    value={runVersion}
                    onChange={(e) => setRunVersion(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#111827",
                      border: "1px solid #374151",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                    }}
                  >
                    <option value="">-- Choose Version --</option>
                    {datasets
                      .filter((d) => d.dataset_id === runDatasetId)
                      .map((d) => (
                        <option key={d.version} value={d.version}>
                          {d.version}
                        </option>
                      ))}
                  </select>
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      color: "#9CA3AF",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Run ID (Optional)
                  </label>
                  <input
                    type="text"
                    value={runId}
                    onChange={(e) => setRunId(e.target.value)}
                    placeholder="e.g. run-sweep-1"
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#111827",
                      border: "1px solid #374151",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      color: "#9CA3AF",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Concurrency Limit
                  </label>
                  <input
                    type="number"
                    value={runConcurrency}
                    onChange={(e) => setRunConcurrency(parseInt(e.target.value) || 1)}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#111827",
                      border: "1px solid #374151",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      color: "#9CA3AF",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Max Retries
                  </label>
                  <input
                    type="number"
                    value={runMaxRetries}
                    onChange={(e) => setRunMaxRetries(parseInt(e.target.value) || 0)}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#111827",
                      border: "1px solid #374151",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                    }}
                  />
                </div>

                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.85rem",
                      color: "#9CA3AF",
                      marginBottom: "0.5rem",
                    }}
                  >
                    Associate Experiment (Optional)
                  </label>
                  <select
                    value={runExperimentId}
                    onChange={(e) => setRunExperimentId(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      background: "#111827",
                      border: "1px solid #374151",
                      borderRadius: "0.375rem",
                      color: "#FFF",
                    }}
                  >
                    <option value="">-- Choose Experiment --</option>
                    {experiments.map((e) => (
                      <option key={e.experiment_id} value={e.experiment_id}>
                        {e.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ gridColumn: "span 3" }}>
                  <button
                    type="submit"
                    style={{
                      background: "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)",
                      color: "#FFF",
                      border: "none",
                      padding: "0.75rem 1.5rem",
                      borderRadius: "0.375rem",
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    Launch Execution Job
                  </button>
                  {runStatusMsg && (
                    <span style={{ marginLeft: "1.5rem", color: "#10B981", fontSize: "0.95rem" }}>
                      {runStatusMsg}
                    </span>
                  )}
                </div>
              </form>
            </div>
          </div>
        )}

        {/* DATASETS TAB CONTENT */}
        {activeTab === "datasets" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "2rem" }}>
              {/* Add Dataset Form */}
              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
                  Register Golden Dataset
                </h3>
                <form onSubmit={handleCreateDataset} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                      Dataset ID *
                    </label>
                    <input
                      type="text"
                      value={newDatasetId}
                      onChange={(e) => setNewDatasetId(e.target.value)}
                      placeholder="e.g. ds-booking-flights"
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF" }}
                    />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                      Dataset Name *
                    </label>
                    <input
                      type="text"
                      value={newDatasetName}
                      onChange={(e) => setNewDatasetName(e.target.value)}
                      placeholder="e.g. Flight Booking Validation Suite"
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF" }}
                    />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                      Version (SemVer) *
                    </label>
                    <input
                      type="text"
                      value={newDatasetVersion}
                      onChange={(e) => setNewDatasetVersion(e.target.value)}
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF" }}
                    />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                      Initial Case: Input Query *
                    </label>
                    <textarea
                      value={newDatasetQuery}
                      onChange={(e) => setNewDatasetQuery(e.target.value)}
                      placeholder="e.g. Find flights from NYC to Paris on August 5"
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF", minHeight: "80px" }}
                    />
                  </div>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                      Expected Output (Optional)
                    </label>
                    <input
                      type="text"
                      value={newDatasetExpected}
                      onChange={(e) => setNewDatasetExpected(e.target.value)}
                      placeholder="e.g. Flight AirFrance 015"
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF" }}
                    />
                  </div>
                  <button type="submit" style={{ background: "#3B82F6", color: "#FFF", border: "none", padding: "0.5rem 1rem", borderRadius: "0.25rem", cursor: "pointer", fontWeight: 600 }}>
                    Register Dataset
                  </button>
                  {newDatasetStatus && (
                    <span style={{ color: "#EAB308", fontSize: "0.85rem" }}>{newDatasetStatus}</span>
                  )}
                </form>
              </div>

              {/* Registered Datasets List */}
              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
                  Registered Datasets Catalog
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                  {datasets.map((d) => (
                    <div
                      key={`${d.dataset_id}-${d.version}`}
                      style={{
                        background: "#111827",
                        border: "1px solid #1F2937",
                        padding: "1.25rem",
                        borderRadius: "0.5rem",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "0.75rem", background: "rgba(59, 130, 246, 0.2)", color: "#3B82F6", padding: "0.25rem 0.5rem", borderRadius: "0.25rem", fontWeight: 600 }}>
                          v{d.version}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "#9CA3AF" }}>
                          {d.cases_count} Test Cases
                        </span>
                      </div>
                      <h4 style={{ fontSize: "1.1rem", margin: "0.75rem 0 0.25rem 0", color: "#FFF" }}>
                        {d.name}
                      </h4>
                      <code style={{ fontSize: "0.8rem", color: "#6B7280" }}>{d.dataset_id}</code>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* EXPERIMENTS TAB CONTENT */}
        {activeTab === "experiments" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "2rem" }}>
              {/* Create Experiment Form */}
              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
                  Create Experiment Sweep
                </h3>
                <form onSubmit={handleCreateExperiment} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#9CA3AF", marginBottom: "0.25rem" }}>
                      Experiment ID *
                    </label>
                    <input
                      type="text"
                      value={newExpId}
                      onChange={(e) => setNewExpId(e.target.value)}
                      placeholder="e.g. prompt-v2-vs-v1"
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF" }}
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
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF" }}
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
                      style={{ width: "100%", padding: "0.4rem", background: "#111827", border: "1px solid #374151", borderRadius: "0.25rem", color: "#FFF", minHeight: "80px" }}
                    />
                  </div>
                  <button type="submit" style={{ background: "#8B5CF6", color: "#FFF", border: "none", padding: "0.5rem 1rem", borderRadius: "0.25rem", cursor: "pointer", fontWeight: 600 }}>
                    Create Experiment
                  </button>
                  {newExpStatus && (
                    <span style={{ color: "#EAB308", fontSize: "0.85rem" }}>{newExpStatus}</span>
                  )}
                </form>
              </div>

              {/* Experiments Catalog */}
              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "1.5rem",
                }}
              >
                <h3 style={{ fontSize: "1.2rem", margin: "0 0 1.5rem 0", color: "#FFF" }}>
                  Experiments Overview
                </h3>
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
                        <h4 style={{ fontSize: "1.1rem", margin: 0, color: "#FFF" }}>
                          {e.name}
                        </h4>
                        <span style={{ fontSize: "0.75rem", color: "#3B82F6" }}>
                          {e.runs_count} Sweeps Registered
                        </span>
                      </div>
                      <p style={{ margin: "0.5rem 0 0.25rem 0", color: "#9CA3AF", fontSize: "0.9rem" }}>
                        {e.description || "No description provided."}
                      </p>
                      <code style={{ fontSize: "0.75rem", color: "#6B7280" }}>{e.experiment_id}</code>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Experiment Comparison Details */}
            {selectedExperiment && (
              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "2rem",
                }}
              >
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
                            <td style={{ padding: "0.5rem" }}>
                              {((r.summary?.success_rate || 0) * 100).toFixed(1)}%
                            </td>
                            <td style={{ padding: "0.5rem" }}>
                              {(r.summary?.avg_latency || 0).toFixed(2)}s
                            </td>
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
              </div>
            )}
          </div>
        )}

        {/* RUN HISTORY TAB CONTENT */}
        {activeTab === "runs" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            <div
              style={{
                background: "rgba(17, 24, 39, 0.6)",
                border: "1px solid #1F2937",
                borderRadius: "0.75rem",
                padding: "1.5rem",
              }}
            >
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
                  {runs.map((r) => (
                    <tr key={r.run_id} style={{ borderBottom: "1px solid #111827" }}>
                      <td style={{ padding: "0.75rem" }}>`{r.run_id}`</td>
                      <td style={{ padding: "0.75rem" }}>
                        {r.dataset_id} (v{r.dataset_version})
                      </td>
                      <td style={{ padding: "0.75rem" }}>
                        {((r.summary?.success_rate || 0) * 100).toFixed(1)}%
                      </td>
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
                  ))}
                </tbody>
              </table>
            </div>

            {/* Run Trajectory Details */}
            {selectedRun && (
              <div
                style={{
                  background: "rgba(17, 24, 39, 0.6)",
                  border: "1px solid #1F2937",
                  borderRadius: "0.75rem",
                  padding: "2rem",
                }}
              >
                <h3 style={{ fontSize: "1.3rem", color: "#FFF", margin: "0 0 1.5rem 0" }}>
                  Run Trajectory Inspector: `{selectedRun.run_id}`
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
                  <div>
                    <h4 style={{ fontSize: "1.1rem", color: "#FFF", margin: "0 0 1rem 0" }}>
                      Test Case Traces
                    </h4>
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
                                  <span key={m.metric_name} style={{ fontSize: "0.75rem", background: "#1F2937", padding: "0.15rem 0.4rem", borderRadius: "0.25rem", color: "#FFF" }}>
                                    {m.metric_name}: {typeof m.score === "number" ? `${(m.score * 100).toFixed(0)}%` : String(m.score)}
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
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
