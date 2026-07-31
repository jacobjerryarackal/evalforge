import { useState } from "react";
import { apiService } from "../services/api";
import { ExperimentDetail } from "../types";

export function useExperiments(onSuccess?: () => void) {
  const [status, setStatus] = useState("");
  const [newExpId, setNewExpId] = useState("");
  const [newExpName, setNewExpName] = useState("");
  const [newExpDesc, setNewExpDesc] = useState("");
  const [selectedExperiment, setSelectedExperiment] = useState<ExperimentDetail | null>(null);

  const resetForm = () => {
    setNewExpId("");
    setNewExpName("");
    setNewExpDesc("");
  };

  const createExperiment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newExpId || !newExpName) {
      setStatus("Please fill required fields.");
      return;
    }

    setStatus("Creating experiment...");
    try {
      await apiService.createExperiment({
        experiment_id: newExpId,
        name: newExpName,
        description: newExpDesc || undefined,
      });
      setStatus("Experiment created!");
      resetForm();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setStatus(`Failed to connect: ${err.message}`);
    }
  };

  const inspectExperiment = async (expId: string) => {
    try {
      const data = await apiService.getExperimentDetails(expId);
      setSelectedExperiment(data);
    } catch (e) {
      console.error(e);
    }
  };

  return {
    newExpId,
    setNewExpId,
    newExpName,
    setNewExpName,
    newExpDesc,
    setNewExpDesc,
    status,
    setStatus,
    selectedExperiment,
    setSelectedExperiment,
    createExperiment,
    inspectExperiment,
  };
}
