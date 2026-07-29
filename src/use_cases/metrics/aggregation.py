from typing import Any, List

from src.domain.entities import TestCaseEvaluation


class AggregationEngine:
    """Aggregates metrics and statistics across test case evaluations."""

    def aggregate(self, cases: List[TestCaseEvaluation]) -> dict[str, Any]:
        """Calculates aggregated metrics and summaries for a collection of case results."""
        if not cases:
            return {
                "total_cases": 0,
                "successful_cases": 0,
                "success_rate": 0.0,
                "avg_latency": 0.0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "avg_metrics": {},
            }

        total_cases = len(cases)
        successful_cases = sum(1 for c in cases if c.success)
        success_rate = successful_cases / total_cases

        total_sec = 0.0
        total_usd = 0.0
        total_tokens = 0

        metric_sums: dict[str, float] = {}
        metric_counts: dict[str, int] = {}

        for case in cases:
            total_sec += case.trajectory.total_latency.seconds
            total_usd += case.trajectory.total_cost.amount
            total_tokens += case.trajectory.total_token_usage.total_tokens

            for m_name, m_res in case.metrics.items():
                if isinstance(m_res.score, (int, float)):
                    metric_sums[m_name] = metric_sums.get(m_name, 0.0) + float(m_res.score)
                    metric_counts[m_name] = metric_counts.get(m_name, 0) + 1
                elif isinstance(m_res.score, bool):
                    score_val = 1.0 if m_res.score else 0.0
                    metric_sums[m_name] = metric_sums.get(m_name, 0.0) + score_val
                    metric_counts[m_name] = metric_counts.get(m_name, 0) + 1

        avg_metrics = {
            m_name: metric_sums[m_name] / metric_counts[m_name] for m_name in metric_sums
        }

        return {
            "total_cases": total_cases,
            "successful_cases": successful_cases,
            "success_rate": success_rate,
            "avg_latency": total_sec / total_cases,
            "total_cost": total_usd,
            "total_tokens": total_tokens,
            "avg_metrics": avg_metrics,
        }
