import { useState } from "react";
import { apiService } from "../services/api";

export function useBenchmark(onSuccess?: () => void) {
  const [runDatasetId, setRunDatasetId] = useState("");
  const [runVersion, setRunVersion] = useState("");
  const [runConcurrency, setRunConcurrency] = useState(3);
  const [runMaxRetries, setRunMaxRetries] = useState(0);
  const [runExperimentId, setRunExperimentId] = useState("");
  const [runId, setRunId] = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  const handleRunBenchmark = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!runDatasetId || !runVersion) {
      setStatusMsg("Please select dataset and version.");
      return;
    }
    setStatusMsg("Triggering execution...");
    try {
      const data = await apiService.runBenchmark({
        dataset_id: runDatasetId,
        version: runVersion,
        run_id: runId || undefined,
        concurrency: runConcurrency,
        max_retries: runMaxRetries,
        experiment_id: runExperimentId || undefined,
      });
      setStatusMsg(`Started successfully! Run ID: ${data.run_id}`);
      setRunId("");
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setStatusMsg(err.message || "Failed to trigger benchmark");
    }
  };

  return {
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
    setStatusMsg,
    handleRunBenchmark,
  };
}
