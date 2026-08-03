export interface Dataset {
  dataset_id: string;
  name: string;
  version: string;
  cases_count: number;
  test_cases?: any[];
}

export interface RunSummary {
  success_rate: number;
  total_cases: number;
  successful_cases: number;
  total_tokens: number;
  total_cost: number;
  avg_latency: number;
}

export interface Run {
  run_id: string;
  dataset_id: string;
  dataset_version: string;
  sut_version: string;
  timestamp: string;
  summary: RunSummary;
}

export interface Experiment {
  experiment_id: string;
  name: string;
  description: string;
  runs_count: number;
}

export interface TestCaseMetric {
  metric_name: string;
  score: number | string;
  reasoning?: string;
  metadata?: any;
}

export interface TestCaseTrace {
  case_id: string;
  input_query: string;
  expected_output: string | null;
  success: boolean;
  metrics?: TestCaseMetric[];
  trajectory?: {
    steps: any[];
    total_token_usage: any;
    total_cost: any;
    total_latency: any;
  };
  ground_truth_context?: string[];
}

export interface RunDetail extends Run {
  cases: TestCaseTrace[];
  report?: string;
}

export interface ExperimentDetail extends Experiment {
  runs: {
    run_id: string;
    summary: RunSummary;
  }[];
  report_markdown: string;
}
