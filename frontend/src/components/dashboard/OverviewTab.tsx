import React from "react";
import { Activity, TrendingUp, DollarSign, Clock, Play } from "lucide-react";
import { Card } from "../common/Card";
import { Dataset, Run, Experiment } from "../../types";
import { useBenchmark } from "../../hooks/useBenchmark";

interface OverviewTabProps {
  runs: Run[];
  datasets: Dataset[];
  experiments: Experiment[];
  onBenchmarkSuccess: () => void;
}

export function OverviewTab({ runs, datasets, experiments, onBenchmarkSuccess }: OverviewTabProps) {
  const totalRuns = runs.length;
  const avgSuccessRate = runs.reduce((acc, r) => acc + (r.summary?.success_rate || 0), 0) / (totalRuns || 1);
  const totalCostVal = runs.reduce((acc, r) => acc + (r.summary?.total_cost || 0), 0);
  const avgLatencyVal = runs.reduce((acc, r) => acc + (r.summary?.avg_latency || 0), 0) / (totalRuns || 1);

  const {
    runDatasetId,
    setRunDatasetId,
    runVersion,
    setRunVersion,
    runConcurrency,
    setRunConcurrency,
    runMaxRetries,
    setRunMaxRetries,
    runExperimentId,
    setRunExperimentId,
    runId,
    setRunId,
    statusMsg,
    handleRunBenchmark,
  } = useBenchmark(onBenchmarkSuccess);

  const uniqueDatasetIds = Array.from(new Set(datasets.map((d) => d.dataset_id)));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      {/* Quick Metrics Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1.5rem" }}>
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
            <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Total Runs</span>
            <Activity size={18} color="#3B82F6" />
          </div>
          <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>{totalRuns}</h3>
        </Card>

        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
            <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Avg Success Rate</span>
            <TrendingUp size={18} color="#10B981" />
          </div>
          <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>
            {avgSuccessRate ? `${(avgSuccessRate * 100).toFixed(1)}%` : "0.0%"}
          </h3>
        </Card>

        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
            <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Cumulative Cost</span>
            <DollarSign size={18} color="#EAB308" />
          </div>
          <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>
            ${totalCostVal.toFixed(4)}
          </h3>
        </Card>

        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", color: "#9CA3AF" }}>
            <span style={{ fontSize: "0.875rem", fontWeight: 500 }}>Avg Latency</span>
            <Clock size={18} color="#A755F7" />
          </div>
          <h3 style={{ fontSize: "1.75rem", margin: "0.5rem 0 0 0", color: "#FFF" }}>
            {avgLatencyVal.toFixed(2)}s
          </h3>
        </Card>
      </div>

      {/* Run Benchmark panel */}
      <Card style={{ padding: "2rem" }}>
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
              {uniqueDatasetIds.map((id) => (
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
              {experiments.map((exp) => (
                <option key={exp.experiment_id} value={exp.experiment_id}>
                  {exp.name}
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
            {statusMsg && (
              <span style={{ marginLeft: "1.5rem", color: "#10B981", fontSize: "0.95rem" }}>
                {statusMsg}
              </span>
            )}
          </div>
        </form>
      </Card>
    </div>
  );
}
