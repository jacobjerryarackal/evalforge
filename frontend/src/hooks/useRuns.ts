import { useState } from "react";
import { apiService } from "../services/api";
import { RunDetail } from "../types";

export function useRuns() {
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const inspectRun = async (runId: string) => {
    setIsLoading(true);
    try {
      const data = await apiService.getRunDetails(runId);
      setSelectedRun(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    selectedRun,
    setSelectedRun,
    inspectRun,
    isLoading,
  };
}
