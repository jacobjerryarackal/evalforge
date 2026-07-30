from src.domain.entities.dataset import GoldenDataset
from src.domain.entities.evaluation import EvaluationRun


class MarkdownReportGenerator:
    """Generates markdown reports summarizing benchmark execution runs."""

    @staticmethod
    def generate_run_report(run: EvaluationRun, dataset: GoldenDataset | None = None) -> str:
        """Generates a markdown report for a given EvaluationRun."""
        summary = run.summary
        avg_metrics = summary.get("avg_metrics", {})

        lines = [
            f"# Evaluation Run Report: `{run.run_id}`",
            "",
            "## Executive Summary",
            f"- **Dataset ID**: `{run.dataset_id}` (v{run.dataset_version})",
            f"- **SUT Version**: `{run.sut_version}`",
            f"- **Total Cases**: {summary.get('total_cases', 0)}",
            f"- **Successful Cases**: {summary.get('successful_cases', 0)}",
            f"- **Success Rate**: {summary.get('success_rate', 0.0):.2%}",
            f"- **Average Latency**: {summary.get('avg_latency', 0.0):.3f}s",
            f"- **Total Token Usage**: {summary.get('total_tokens', 0)} tokens",
            f"- **Total Cost**: ${summary.get('total_cost', 0.0):.5f}",
            "",
            "## Evaluator Metrics Summary",
            "| Metric | Average Score | Type |",
            "| :--- | :--- | :--- |",
        ]

        # Categorize metrics into Deterministic and LLM Judges
        llm_judges = {"Faithfulness", "Groundedness", "AnswerCorrectness", "Hallucination"}

        for metric_name, score in avg_metrics.items():
            m_type = "LLM Judge" if metric_name in llm_judges else "Deterministic"
            if isinstance(score, float) and 0.0 <= score <= 1.0:
                score_str = f"{score:.2%}"
            else:
                score_str = str(score)
            lines.append(f"| {metric_name} | {score_str} | {m_type} |")

        lines.extend(
            [
                "",
                "## Test Case Details",
                "| Case ID | Success | Latency | Cost | Tokens |",
                "| :--- | :--- | :--- | :--- | :--- |",
            ]
        )

        for case in run.cases:
            success_str = "✅ Passed" if case.success else "❌ Failed"
            latency = case.trajectory.total_latency.seconds
            cost = case.trajectory.total_cost.amount
            tokens = case.trajectory.total_token_usage.total_tokens
            lines.append(
                f"| `{case.case_id}` | {success_str} | {latency:.2f}s | "
                f"${cost:.5f} | {tokens} |"
            )

        lines.extend(
            [
                "",
                "## Trajectory Observability Log",
                "Detailed trace and reasoning logs for each test case:",
                "",
            ]
        )

        for case in run.cases:
            # Look up input query from dataset if provided
            input_query = "Unknown query (Dataset not provided)"
            if dataset:
                for tc in dataset.test_cases:
                    if tc.case_id == case.case_id:
                        input_query = tc.input_query
                        break

            lines.extend(
                [
                    f"### Case `{case.case_id}`",
                    f"- **Input Query**: {input_query}",
                    f"- **Outcome**: {'Passed' if case.success else 'Failed'}",
                    "",
                    "#### Execution Steps",
                ]
            )
            for step in case.trajectory.steps:
                lines.append(f"##### Step {step.step_number}")
                if step.thought:
                    lines.append(f"- **Thought**: {step.thought}")
                for tool in step.tool_calls:
                    lines.append(
                        f"- **Tool Call**: `{tool.tool_name}` (Args: `{tool.arguments}`) "
                        f"-> Success: {tool.success}"
                    )
                if step.response:
                    lines.append(f"- **Response**: {step.response}")

            lines.extend(
                [
                    "",
                    "#### Evaluation Metrics",
                ]
            )
            for metric in case.metrics.values():
                m_name = metric.metric_name
                if isinstance(metric.score, float) and 0.0 <= metric.score <= 1.0:
                    m_score = f"{metric.score:.2%}"
                else:
                    m_score = str(metric.score)
                lines.append(f"- **{m_name}**: Score: `{m_score}`")
                if metric.reasoning:
                    lines.append(f"  - *Reasoning*: {metric.reasoning}")
                if "confidence" in metric.metadata:
                    lines.append(f"  - *Confidence*: {metric.metadata['confidence']:.2f}")
            lines.append("")

        return "\n".join(lines)
