import { useState, useEffect, useCallback } from "react";
import { apiService } from "../services/api";
import { Dataset, Run, Experiment } from "../types";

export function useDashboardData() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [backendConnected, setBackendConnected] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [dsData, runsData, expsData] = await Promise.all([
        apiService.getDatasets(),
        apiService.getRuns(),
        apiService.getExperiments(),
      ]);
      setDatasets(dsData);
      setRuns(runsData);
      setExperiments(expsData);
      setBackendConnected(true);
    } catch (e) {
      console.error("Dashboard synchronization failed", e);
      setBackendConnected(false);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const latestRuns = Object.values(
    runs.reduce<Record<string, Run>>((acc, run) => {
      const key = run.dataset_id;

      if (
        !acc[key] ||
        new Date(run.timestamp).getTime() > new Date(acc[key].timestamp).getTime()
      ) {
        acc[key] = run;
      }

      return acc;
    }, {})
  );

  return {
    datasets,
    runs,
    latestRuns,
    experiments,
    backendConnected,
    isRefreshing,
    refresh: fetchData,
  };
}
