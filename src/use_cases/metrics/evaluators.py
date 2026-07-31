from src.domain.entities import GoldenTestCase, MetricResult, Trajectory
from src.domain.interfaces.evaluator import BaseEvaluator


def extract_retrieved_contexts(trajectory: Trajectory) -> list[str]:
    """Helper to dynamically extract context text snippets from steps."""
    contexts = []
    # Check trajectory metadata
    if "retrieved_contexts" in trajectory.metadata:
        val = trajectory.metadata["retrieved_contexts"]
        if isinstance(val, list):
            contexts.extend([str(item) for item in val])
    if "contexts" in trajectory.metadata:
        val = trajectory.metadata["contexts"]
        if isinstance(val, list):
            contexts.extend([str(item) for item in val])

    # Check steps
    for step in trajectory.steps:
        # Step metadata
        if "retrieved_contexts" in step.metadata:
            val = step.metadata["retrieved_contexts"]
            if isinstance(val, list):
                contexts.extend([str(item) for item in val])
        if "contexts" in step.metadata:
            val = step.metadata["contexts"]
            if isinstance(val, list):
                contexts.extend([str(item) for item in val])

        # Step observation values
        obs = step.observation
        if isinstance(obs, dict):
            for k, v in obs.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            contexts.append(str(item))
                        elif isinstance(item, str):
                            contexts.append(item)
                elif isinstance(v, str):
                    contexts.append(v)
        elif isinstance(obs, list):
            for item in obs:
                if isinstance(item, dict):
                    contexts.append(str(item))
                elif isinstance(item, str):
                    contexts.append(item)
        elif isinstance(obs, str):
            contexts.append(obs)

    # Remove duplicates and empty items while preserving order where possible
    seen = set()
    unique_contexts = []
    for c in contexts:
        cleaned = c.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique_contexts.append(cleaned)
    return unique_contexts


class LatencyEvaluator(BaseEvaluator):
    """Evaluates SUT execution latency against a threshold constraint."""

    def __init__(self, default_max_latency: float = 10.0) -> None:
        self.default_max_latency = default_max_latency

    @property
    def name(self) -> str:
        return "Latency"

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        latency_sec = trajectory.total_latency.seconds
        max_latency = test_case.constraints.get("max_latency", self.default_max_latency)
        passed = latency_sec <= max_latency

        return MetricResult(
            metric_name=self.name,
            score=1.0 if passed else 0.0,
            reasoning=(
                f"Latency of {latency_sec:.2f}s is under the threshold of {max_latency:.2f}s."
                if passed
                else f"Latency of {latency_sec:.2f}s exceeds the threshold of {max_latency:.2f}s."
            ),
            metadata={
                "latency_seconds": latency_sec,
                "max_latency_threshold": max_latency,
            },
        )


class TokenUsageEvaluator(BaseEvaluator):
    """Evaluates SUT total token usage against a threshold constraint."""

    def __init__(self, default_max_tokens: int = 2000) -> None:
        self.default_max_tokens = default_max_tokens

    @property
    def name(self) -> str:
        return "TokenUsage"

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        total_tokens = trajectory.total_token_usage.total_tokens
        max_tokens = test_case.constraints.get("max_tokens", self.default_max_tokens)
        passed = total_tokens <= max_tokens

        return MetricResult(
            metric_name=self.name,
            score=1.0 if passed else 0.0,
            reasoning=(
                f"Token usage {total_tokens} is under the threshold of {max_tokens}."
                if passed
                else f"Token usage {total_tokens} exceeds the threshold of {max_tokens}."
            ),
            metadata={
                "total_tokens": total_tokens,
                "max_tokens_threshold": max_tokens,
                "prompt_tokens": trajectory.total_token_usage.prompt_tokens,
                "completion_tokens": trajectory.total_token_usage.completion_tokens,
            },
        )


class CostEvaluator(BaseEvaluator):
    """Evaluates SUT estimated execution cost against a threshold constraint."""

    def __init__(self, default_max_cost: float = 0.05) -> None:
        self.default_max_cost = default_max_cost

    @property
    def name(self) -> str:
        return "Cost"

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        cost_amount = trajectory.total_cost.amount
        currency = trajectory.total_cost.currency
        max_cost = test_case.constraints.get("max_cost", self.default_max_cost)
        passed = cost_amount <= max_cost

        return MetricResult(
            metric_name=self.name,
            score=1.0 if passed else 0.0,
            reasoning=(
                f"Cost {cost_amount:.4f} {currency} is under the threshold of "
                f"{max_cost:.4f} {currency}."
                if passed
                else f"Cost {cost_amount:.4f} {currency} exceeds the threshold of "
                f"{max_cost:.4f} {currency}."
            ),
            metadata={
                "cost_amount": cost_amount,
                "cost_currency": currency,
                "max_cost_threshold": max_cost,
            },
        )


class ToolCallingEvaluator(BaseEvaluator):
    """Evaluates whether tool executions succeeded and matched the expected sequence."""

    def __init__(self, default_max_tool_calls: int | None = None) -> None:
        self.default_max_tool_calls = default_max_tool_calls

    @property
    def name(self) -> str:
        return "ToolCalling"

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        tool_calls = trajectory.all_tool_calls
        failures = [tc for tc in tool_calls if not tc.success]

        # Check 1: Tool failures
        has_failures = len(failures) > 0

        # Check 2: Expected tool calls
        called_tool_names = [tc.tool_name for tc in tool_calls]
        missing_expected = []
        for expected in test_case.expected_tool_calls:
            expected_name = ""
            if isinstance(expected, dict):
                expected_name = expected.get("method") or ""
            elif isinstance(expected, str):
                expected_name = expected

            if expected_name and expected_name not in called_tool_names:
                missing_expected.append(expected_name)


        # Check 3: Max tool calls threshold
        max_tool_calls = test_case.constraints.get("max_tool_calls", self.default_max_tool_calls)
        exceeded_limit = False
        if max_tool_calls is not None and len(tool_calls) > max_tool_calls:
            exceeded_limit = True

        # Overall status
        passed = not has_failures and not missing_expected and not exceeded_limit

        reasons = []
        if passed:
            reasons.append("All executed tools succeeded and all expected tools were called.")
        else:
            if has_failures:
                reasons.append(f"Failed tools: {', '.join(f.tool_name for f in failures)}")
            if missing_expected:
                reasons.append(f"Missing expected tools: {', '.join(missing_expected)}")
            if exceeded_limit:
                reasons.append(
                    f"Exceeded tool call count limit ({len(tool_calls)} > {max_tool_calls})"
                )

        return MetricResult(
            metric_name=self.name,
            score=1.0 if passed else 0.0,
            reasoning="; ".join(reasons),
            metadata={
                "total_tool_calls": len(tool_calls),
                "failed_tool_calls_count": len(failures),
                "missing_expected_tools": missing_expected,
                "max_tool_calls_threshold": max_tool_calls,
            },
        )


class ContextRecallEvaluator(BaseEvaluator):
    """Heuristic evaluation of context recall by matching ground truth text strings."""

    @property
    def name(self) -> str:
        return "ContextRecall"

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        ground_truth = test_case.ground_truth_context
        if not ground_truth:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                reasoning=(
                    "No ground truth context provided for this test case. "
                    "Recall defaults to 1.0."
                ),
            )

        retrieved = extract_retrieved_contexts(trajectory)
        if not retrieved:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                reasoning="No context was retrieved by the SUT. Recall is 0.0.",
                metadata={"ground_truth_count": len(ground_truth), "retrieved_count": 0},
            )

        recalled_count = 0
        matched_gt = []
        for gt_item in ground_truth:
            gt_lower = gt_item.strip().lower()
            found = False
            for ret_item in retrieved:
                ret_lower = ret_item.strip().lower()
                if gt_lower in ret_lower or ret_lower in gt_lower:
                    found = True
                    break
            if found:
                recalled_count += 1
                matched_gt.append(gt_item)

        recall_score = recalled_count / len(ground_truth)

        return MetricResult(
            metric_name=self.name,
            score=recall_score,
            reasoning=(
                f"Recalled {recalled_count} out of {len(ground_truth)} ground truth context items."
            ),
            metadata={
                "ground_truth_count": len(ground_truth),
                "retrieved_count": len(retrieved),
                "matched_ground_truth": matched_gt,
            },
        )


class ContextPrecisionEvaluator(BaseEvaluator):
    """Heuristic evaluation of context precision ranking using Average Precision (AP)."""

    @property
    def name(self) -> str:
        return "ContextPrecision"

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        ground_truth = test_case.ground_truth_context
        if not ground_truth:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                reasoning="No ground truth context provided. Precision defaults to 1.0.",
            )

        retrieved = extract_retrieved_contexts(trajectory)
        if not retrieved:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                reasoning="No context was retrieved by the SUT. Precision is 0.0.",
                metadata={"ground_truth_count": len(ground_truth), "retrieved_count": 0},
            )

        precision_sum = 0.0
        relevant_retrieved = 0

        for i, ret_item in enumerate(retrieved):
            rank = i + 1
            ret_lower = ret_item.strip().lower()
            is_relevant = False
            for gt_item in ground_truth:
                gt_lower = gt_item.strip().lower()
                if gt_lower in ret_lower or ret_lower in gt_lower:
                    is_relevant = True
                    break

            if is_relevant:
                relevant_retrieved += 1
                precision_at_k = relevant_retrieved / rank
                precision_sum += precision_at_k

        if relevant_retrieved == 0:
            precision_score = 0.0
        else:
            precision_score = precision_sum / relevant_retrieved

        return MetricResult(
            metric_name=self.name,
            score=precision_score,
            reasoning=(
                f"Context precision is {precision_score:.2%} "
                f"({relevant_retrieved} relevant items found across "
                f"{len(retrieved)} retrieved contexts)."
            ),
            metadata={
                "ground_truth_count": len(ground_truth),
                "retrieved_count": len(retrieved),
                "relevant_retrieved_count": relevant_retrieved,
            },
        )
