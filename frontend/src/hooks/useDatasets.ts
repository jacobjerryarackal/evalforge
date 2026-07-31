import { useState } from "react";
import { apiService } from "../services/api";

export function useDatasets(onSuccess?: () => void) {
  const [status, setStatus] = useState("");
  const [newDatasetId, setNewDatasetId] = useState("");
  const [newDatasetName, setNewDatasetName] = useState("");
  const [newDatasetVersion, setNewDatasetVersion] = useState("1.0.0");
  const [newDatasetQuery, setNewDatasetQuery] = useState("");
  const [newDatasetExpected, setNewDatasetExpected] = useState("");

  const resetForm = () => {
    setNewDatasetId("");
    setNewDatasetName("");
    setNewDatasetQuery("");
    setNewDatasetExpected("");
  };

  const createDataset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDatasetId || !newDatasetName || !newDatasetQuery) {
      setStatus("Please fill all required fields.");
      return;
    }

    setStatus("Registering dataset...");
    try {
      await apiService.createDataset({
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
      });
      setStatus("Dataset registered!");
      resetForm();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setStatus(`Failed to connect: ${err.message}`);
    }
  };

  return {
    newDatasetId,
    setNewDatasetId,
    newDatasetName,
    setNewDatasetName,
    newDatasetVersion,
    setNewDatasetVersion,
    newDatasetQuery,
    setNewDatasetQuery,
    newDatasetExpected,
    setNewDatasetExpected,
    status,
    setStatus,
    createDataset,
  };
}
