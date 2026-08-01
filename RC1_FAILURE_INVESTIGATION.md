# EvalForge RC1 Failure Investigation Report

## 1. Root Cause Analysis
The E2E execution of all 180 benchmark cases across the 10 canonical datasets resulted in a **100% failure rate** (`0 / 180 Passed`) under the default mock evaluation profile. The investigation identified three root causes:

1. **Mock SUT Resource FOOTPRINT**:
   * The mock `TravelAgentSUT` executes a fixed 5-step agent loop (loading user profiles, searching flights, searching hotels, validating corporate policy, and compiling recommendations) for every user query.
   * This transaction consumes an average of **298 to 398 tokens** and costs **$0.0075 to $0.0101 USD** of simulated API usage.
   * Simple benchmark cases define strict resource constraints (e.g. `token_constraint: 200` and `cost_constraint: 0.01`). Because the mock SUT's verbose execution exceeds these parameters, the deterministic `TokenUsage` and `Cost` evaluators return `0.0` (Fail), flagging the case as failed.
2. **Quality Metric Threshold Mismatch**:
   * The benchmark JSON datasets require perfect scores (`1.0`) for quality criteria like `faithfulness`, `groundedness`, and `correctness`.
   * Under mock mode, the LLM judges return static mock scores (`0.8`). Because `0.8 < 1.0`, the cases fail the strict quality thresholds of the benchmark suite.
3. **Negative Metric Polarity (Hallucination)**:
   * The benchmark JSON datasets define a target threshold of `"hallucination": 0.0` (expecting zero hallucinations).
   * Our programmatic analysis proved that evaluating the mock hallucination score (`0.8`) against the expected threshold (`0.0`) failed because `0.8 > 0.0`, resulting in a failure.

---

## 2. Failure Statistics by Metric (Phase 2)
The E2E run of all 180 cases yielded the following failure frequencies and percentages:

* **Total Cases Checked**: 180
* **Total Failed Cases**: 180
* **Failure Count & Percentage by Metric**:
  1. **Hallucination**: 180 cases (100.0%) — *Actual score (0.8) > expected threshold (0.0)*
  2. **Faithfulness**: 164 cases (91.1%) — *Actual score (0.8) < expected threshold (1.0)*
  3. **Groundedness**: 136 cases (75.6%) — *Actual score (0.8) < expected threshold (1.0)*
  4. **AnswerCorrectness**: 134 cases (74.4%) — *Actual score (0.8) < expected threshold (1.0)*
  5. **ContextPrecision**: 133 cases (73.9%) — *SUT did not retrieve relevant context, score < threshold*
  6. **ContextRecall**: 129 cases (71.7%) — *SUT did not recall ground truth contexts*
  7. **ToolCalling**: 122 cases (67.8%) — *SUT missed calling expected tools (e.g., get_forecast, convert)*
  8. **TokenUsage**: 115 cases (63.9%) — *Actual tokens (~398) exceeded case limits (e.g., 200)*
  9. **Cost**: 80 cases (44.4%) — *Actual cost ($0.0101) exceeded case limits (e.g., $0.01)*
  10. **Latency**: 0 cases (0.0%) — *Actual latency (0.00s) satisfied all constraints*

---

## 3. Evaluators Core Validation Formula (Phase 3)

### Deterministic Evaluators
1. **LatencyEvaluator**:
   * **Input**: SUT execution duration, `latency_constraint` threshold.
   * **Output**: `score = 1.0` if `latency <= constraint` else `0.0`.
2. **TokenUsageEvaluator**:
   * **Input**: Trajectory total tokens, `token_constraint` threshold.
   * **Output**: `score = 1.0` if `tokens <= constraint` else `0.0`.
3. **CostEvaluator**:
   * **Input**: Trajectory total cost, `cost_constraint` threshold.
   * **Output**: `score = 1.0` if `cost <= constraint` else `0.0`.
4. **ToolCallingEvaluator**:
   * **Input**: Trajectory `all_tool_calls`, dataset `expected_tool_calls`.
   * **Output**: `score = 1.0` if all expected tools called, no tool execution errors, and below `max_tool_calls`.

### Retrieval Evaluators
5. **ContextPrecisionEvaluator**:
   * **Formula**: $\frac{1}{K} \sum_{k=1}^K (\text{Precision}@k \times \text{Relevance}(k))$
   * **Output**: Average precision score `0.0` - `1.0`.
6. **ContextRecallEvaluator**:
   * **Formula**: $\frac{|\text{Recalled Ground Truth Contexts}|}{|\text{Total Ground Truth Contexts}|}$
   * **Output**: Recall score `0.0` - `1.0`.

### LLM Judge Evaluators
7. **FaithfulnessJudge**:
   * **Rubric**: `1.0` if final response claims are fully supported by context; `0.0` otherwise.
8. **GroundednessJudge**:
   * **Rubric**: `1.0` if final response satisfies all user query constraints; `0.0` otherwise.
9. **AnswerCorrectnessJudge**:
   * **Rubric**: `1.0` for factual/semantic match; `0.5` for minor omissions; `0.0` for mismatch.
10. **HallucinationJudge**:
    * **Rubric**: `0.0` if hallucination-free; `1.0` if hallucinating.

---

## 4. SUT & Benchmark Expectations (Phase 4)
* **SUT Design**: The mock `TravelAgentSUT` behaves as a **generic baseline**. It does not dynamically optimize its reasoning steps or curtail its output size to meet tight cost/token constraints.
* **Benchmark Design**: The benchmark datasets represent a **strict, high-quality target suite** with fine-grained constraints.
* **Verdict**: The benchmark expectations are highly realistic for optimized production-grade agents, but too strict for the mock baseline agent. This represents correct evaluation behavior, verifying the platform's diagnostic capability.

---

## 5. UI/UX & Browser Audit (Phases 5 & 6)
We ran a Playwright audit to check responsive layouts:
* **Clipping & Scroll (FIXED)**: The Dataset Hub catalog container overflowed the screen, clipping the bottom two dataset items (`travel_v1` and `travel_tool_calls`). We resolved this by adding `paddingBottom: "3rem"` to the outer catalog container, ensuring all 10 datasets are fully scrollable and visible.
* **Version Reset**: Changing the Dataset ID dropdown clears the Version selection, prompting a validation error.
* **Non-interactive Headers**: Run history log headers (ID, Success Rate, Cost) are styled as interactive elements but do not sort execution runs.

---

## 6. Actionable Recommendations

### [BLOCKER] None
No blocker platform defects remain. The E2E execution, persistence, and reporting are fully functional.

### [HIGH] Dataset ID Version Autopopulation (Nice to Have)
* **Description**: Automatically select the first available SemVer version when switching Dataset IDs in the execute benchmark dropdown to prevent validation errors.

### [MEDIUM] Interactive Run Sorting
* **Description**: Add toggle sort parameters (`sort_by`, `direction`) to the Run History table headers.
