import { useState } from "react";
import { apiService } from "../services/api";

export function useDatasets(onSuccess?: () => void) {
  const [status, setStatus] = useState("");
  const [registrationType, setRegistrationType] = useState<"single" | "suite">("single");
  const [newDatasetId, setNewDatasetId] = useState("");
  const [newDatasetName, setNewDatasetName] = useState("");
  const [newDatasetVersion, setNewDatasetVersion] = useState("1.0.0");
  
  // Single Case Form States
  const [newDatasetQuery, setNewDatasetQuery] = useState("");
  const [newDatasetExpected, setNewDatasetExpected] = useState("");

  // Suite Form States
  const [suiteJsonText, setSuiteJsonText] = useState("");
  const [suiteFileContent, setSuiteFileContent] = useState<string | null>(null);

  const resetForm = () => {
    setNewDatasetId("");
    setNewDatasetName("");
    setNewDatasetQuery("");
    setNewDatasetExpected("");
    setSuiteJsonText("");
    setSuiteFileContent(null);
  };

  const createDataset = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newDatasetId || !newDatasetName) {
      setStatus("Please enter Dataset ID and Name.");
      return;
    }

    let casesPayload: any[] = [];

    if (registrationType === "single") {
      if (!newDatasetQuery) {
        setStatus("Please enter the input query.");
        return;
      }
      casesPayload = [
        {
          case_id: "case-1",
          input_query: newDatasetQuery,
          expected_output: newDatasetExpected || null,
          expected_tool_calls: [],
          constraints: {},
          ground_truth_context: [],
        },
      ];
    } else {
      // Suite Registration
      let rawCases: any[] = [];
      try {
        const textToParse = suiteFileContent || suiteJsonText;
        if (!textToParse) {
          setStatus("Please paste JSON or upload a file.");
          return;
        }
        rawCases = JSON.parse(textToParse.trim());
        if (!Array.isArray(rawCases)) {
          throw new Error("JSON must be an array of test cases.");
        }
      } catch (err: any) {
        setStatus(`Invalid JSON format: ${err.message}`);
        return;
      }

      // Map raw benchmark cases to TestCaseSchema
      casesPayload = rawCases.map((item, idx) => {
        const case_id = item.id || `case-${idx + 1}`;
        const input_query = item.user_query || item.input_query || "";
        const expected_output = item.expected_answer || item.expected_output || null;

        const retrieved_context = item.retrieved_context;
        let ground_truth_context: string[] = [];
        if (retrieved_context) {
          if (Array.isArray(retrieved_context)) {
            ground_truth_context = retrieved_context.map((c: any) => String(c));
          } else {
            ground_truth_context = [String(retrieved_context)];
          }
        } else if (Array.isArray(item.ground_truth_context)) {
          ground_truth_context = item.ground_truth_context;
        }

        let expected_tool_calls: string[] = [];
        const raw_tools = item.expected_tool_calls || [];
        for (const tc of raw_tools) {
          if (typeof tc === "object" && tc !== null) {
            const method = tc.method;
            if (method) expected_tool_calls.push(String(method));
          } else if (typeof tc === "string") {
            expected_tool_calls.push(tc);
          }
        }

        const constraints = item.constraints || {};
        if ("latency_constraint" in item) {
          constraints.max_latency = item.latency_constraint;
        }
        if ("token_constraint" in item) {
          constraints.max_tokens = item.token_constraint;
        }
        if ("cost_constraint" in item) {
          constraints.max_cost = item.cost_constraint;
        }

        return {
          case_id,
          input_query,
          expected_output,
          expected_tool_calls,
          constraints,
          ground_truth_context,
        };
      });
    }

    setStatus("Registering dataset...");
    try {
      await apiService.createDataset({
        dataset_id: newDatasetId,
        name: newDatasetName,
        version: newDatasetVersion,
        test_cases: casesPayload as any,
      });
      setStatus("Dataset registered successfully!");
      resetForm();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setStatus(`Failed to register: ${err.message}`);
    }
  };

  return {
    registrationType,
    setRegistrationType,
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
    suiteJsonText,
    setSuiteJsonText,
    setSuiteFileContent,
    status,
    setStatus,
    createDataset,
  };
}
