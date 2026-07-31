import { Dataset, Run, Experiment, RunDetail, ExperimentDetail } from "../types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiService = {
  getDatasets: async (): Promise<Dataset[]> => {
    const res = await fetch(`${API_BASE}/api/datasets`);
    if (!res.ok) throw new Error("Failed to fetch datasets");
    return res.json();
  },

  getRuns: async (): Promise<Run[]> => {
    const res = await fetch(`${API_BASE}/api/runs`);
    if (!res.ok) throw new Error("Failed to fetch runs");
    return res.json();
  },

  getExperiments: async (): Promise<Experiment[]> => {
    const res = await fetch(`${API_BASE}/api/experiments`);
    if (!res.ok) throw new Error("Failed to fetch experiments");
    return res.json();
  },

  runBenchmark: async (payload: {
    dataset_id: string;
    version: string;
    run_id?: string;
    concurrency: number;
    max_retries: number;
    experiment_id?: string;
  }): Promise<{ run_id: string }> => {
    const res = await fetch(`${API_BASE}/api/benchmarks/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to trigger execution");
    }
    return res.json();
  },

  createDataset: async (payload: {
    dataset_id: string;
    name: string;
    version: string;
    test_cases: Array<{
      case_id: string;
      input_query: string;
      expected_output: string | null;
      expected_tool_calls: never[];
      constraints: Record<string, never>;
      ground_truth_context: never[];
    }>;
  }): Promise<void> => {
    const res = await fetch(`${API_BASE}/api/datasets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to register dataset");
    }
  },

  createExperiment: async (payload: {
    experiment_id: string;
    name: string;
    description?: string;
  }): Promise<void> => {
    const res = await fetch(`${API_BASE}/api/experiments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create experiment");
    }
  },

  getRunDetails: async (runId: string): Promise<RunDetail> => {
    const res = await fetch(`${API_BASE}/api/runs/${runId}`);
    if (!res.ok) throw new Error("Failed to fetch run details");
    const data = await res.json();

    let reportMarkdown = "";
    try {
      const repRes = await fetch(`${API_BASE}/api/runs/${runId}/report`);
      if (repRes.ok) {
        const reportData = await repRes.json();
        reportMarkdown = reportData.report_markdown;
      }
    } catch (e) {
      console.error("Failed to fetch run report", e);
    }

    return { ...data, report: reportMarkdown };
  },

  getExperimentDetails: async (expId: string): Promise<ExperimentDetail> => {
    const res = await fetch(`${API_BASE}/api/experiments/${expId}`);
    if (!res.ok) throw new Error("Failed to fetch experiment details");
    return res.json();
  },

  checkHealth: async (): Promise<boolean> => {
    try {
      // Just check datasets as a proxy for connection/health
      const res = await fetch(`${API_BASE}/api/datasets`, { method: "GET" });
      return res.ok;
    } catch (e) {
      return false;
    }
  },
};
