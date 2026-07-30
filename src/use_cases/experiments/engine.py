import logging
from typing import Any, Dict, List

from src.domain.entities.evaluation import EvaluationRun
from src.domain.entities.experiment import Experiment
from src.domain.interfaces.repository import EvaluationRepository

logger = logging.getLogger("evaluation.experiments.engine")


class ExperimentComparer:
    """Computes comparative metrics and deltas across runs in an experiment."""

    @staticmethod
    def compare_runs(runs: List[EvaluationRun]) -> Dict[str, Any]:
        """Compares evaluation runs and calculates performance deltas.

        The chronologically first run is treated as the baseline.
        """
        if not runs:
            return {}

        comparison = {}
        # Sort runs chronologically by timestamp
        sorted_runs = sorted(runs, key=lambda r: r.timestamp)
        baseline = sorted_runs[0]
        # Force baseline summary calculation if not already computed
        baseline.compute_summary()
        base_summary = baseline.summary

        for i, run in enumerate(sorted_runs):
            run.compute_summary()
            summary = run.summary

            run_data = {
                "run_id": run.run_id,
                "sut_version": run.sut_version,
                "dataset_id": run.dataset_id,
                "dataset_version": run.dataset_version,
                "timestamp": run.timestamp.isoformat(),
                "total_cases": summary.get("total_cases", 0),
                "successful_cases": summary.get("successful_cases", 0),
                "success_rate": summary.get("success_rate", 0.0),
                "avg_latency": summary.get("avg_latency", 0.0),
                "total_cost": summary.get("total_cost", 0.0),
                "total_tokens": summary.get("total_tokens", 0),
                "avg_metrics": summary.get("avg_metrics", {}),
                "deltas": {},
            }

            if i > 0:
                # Compute delta against the baseline run
                run_data["deltas"] = {
                    "success_rate": run_data["success_rate"]
                    - base_summary.get("success_rate", 0.0),
                    "avg_latency": run_data["avg_latency"] - base_summary.get("avg_latency", 0.0),
                    "total_cost": run_data["total_cost"] - base_summary.get("total_cost", 0.0),
                    "total_tokens": run_data["total_tokens"] - base_summary.get("total_tokens", 0),
                }

                # Compute delta for individual metrics
                metric_deltas = {}
                base_avg_metrics = base_summary.get("avg_metrics", {})
                for m_name, score in run_data["avg_metrics"].items():
                    if m_name in base_avg_metrics:
                        metric_deltas[m_name] = score - base_avg_metrics[m_name]
                run_data["deltas"]["avg_metrics"] = metric_deltas

            comparison[run.run_id] = run_data

        return comparison


class ExperimentSummaryGenerator:
    """Generates detailed reports summarizing experiment runs and outcomes."""

    @staticmethod
    def generate_markdown_summary(experiment: Experiment) -> str:
        """Generates a structured markdown report evaluating runs and highlighting the best one."""
        if not experiment.runs:
            return f"# Experiment: {experiment.name}\n\nNo runs registered in this experiment."

        runs = sorted(experiment.runs, key=lambda r: r.timestamp)
        for run in runs:
            run.compute_summary()

        # Determine the best performing run (highest success rate, lowest latency as tie breaker)
        best_run = None
        best_success_rate = -1.0
        best_latency = float("inf")

        for run in runs:
            rate = run.summary.get("success_rate", 0.0)
            latency = run.summary.get("avg_latency", float("inf"))

            if rate > best_success_rate:
                best_success_rate = rate
                best_run = run
                best_latency = latency
            elif rate == best_success_rate:
                if latency < best_latency:
                    best_run = run
                    best_latency = latency

        lines = [
            f"# Experiment: {experiment.name}",
            f"*{experiment.description or 'No description provided.'}*\n",
            f"- **Experiment ID**: `{experiment.experiment_id}`",
            f"- **Created At**: {experiment.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- **Total Benchmark Runs**: {len(runs)}",
        ]

        if best_run:
            lines.append(
                f"- **Best Run Config**: `{best_run.run_id}` "
                f"(SUT Version: `{best_run.sut_version}`, "
                f"Success Rate: {best_run.summary.get('success_rate', 0.0):.2%})"
            )
        lines.append("")

        lines.append("## Run Comparison Table\n")
        lines.append(
            "| Run ID | SUT Version | Dataset | Success Rate "
            "| Avg Latency | Total Cost | Total Tokens |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for r in runs:
            summary = r.summary
            ds_info = f"{r.dataset_id} (v{r.dataset_version})"
            lines.append(
                f"| `{r.run_id}` | `{r.sut_version}` | {ds_info} | "
                f"{summary.get('success_rate', 0.0):.2%} | "
                f"{summary.get('avg_latency', 0.0):.3f}s | "
                f"${summary.get('total_cost', 0.0):.5f} | "
                f"{summary.get('total_tokens', 0)} |"
            )
        lines.append("")

        # Metric deltas relative to baseline
        if len(runs) > 1:
            lines.append("## Performance Deltas (vs. Baseline Run)\n")
            comparison = ExperimentComparer.compare_runs(runs)
            baseline_id = runs[0].run_id
            lines.append(f"Baseline Run: `{baseline_id}`\n")

            lines.append(
                "| Run ID | Success Rate Delta | Latency Delta | Cost Delta | Tokens Delta |"
            )
            lines.append("| :--- | :--- | :--- | :--- | :--- |")

            for r in runs:
                if r.run_id == baseline_id:
                    continue
                deltas = comparison[r.run_id].get("deltas", {})
                succ_delta = deltas.get("success_rate", 0.0)
                lat_delta = deltas.get("avg_latency", 0.0)
                cost_delta = deltas.get("total_cost", 0.0)
                tok_delta = deltas.get("total_tokens", 0)

                # Format signs
                succ_str = f"{succ_delta:+.2%}"
                lat_str = f"{lat_delta:+.3f}s"
                cost_str = f"${cost_delta:+.5f}"
                tok_str = f"{tok_delta:+d}"

                lines.append(f"| `{r.run_id}` | {succ_str} | {lat_str} | {cost_str} | {tok_str} |")
            lines.append("")

        lines.append("## Detailed Run Metrics Breakdown\n")
        for run in runs:
            lines.append(f"### Run `{run.run_id}` (SUT: `{run.sut_version}`)")
            lines.append(f"- **Timestamp**: {run.timestamp.isoformat()}")
            lines.append("- **Average Metric Scores**:")
            avg_metrics = run.summary.get("avg_metrics", {})
            if not avg_metrics:
                lines.append("  - No evaluation metrics recorded.")
            for name, score in avg_metrics.items():
                lines.append(f"  - **{name}**: {score:.4f}")
            lines.append("")

        return "\n".join(lines)


class ExperimentEngine:
    """Orchestrator for managing the lifecycle, comparing, and summarizing experiments."""

    def __init__(self, repository: EvaluationRepository) -> None:
        self.repository = repository

    async def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> Experiment:
        """Creates a new Experiment, stores it in the repository, and returns it."""
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            metadata=metadata or {},
        )
        await self.repository.save_experiment(experiment)
        logger.info(f"Created experiment: {experiment_id} ({name})")
        return experiment

    async def add_run_to_experiment(self, experiment_id: str, run: EvaluationRun) -> Experiment:
        """Retrieves an experiment, adds an evaluation run to it, and saves it."""
        experiment = await self.repository.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment with ID '{experiment_id}' does not exist.")

        experiment.add_run(run)
        await self.repository.save_experiment(experiment)
        logger.info(f"Added run {run.run_id} to experiment {experiment_id}")
        return experiment

    async def get_experiment(self, experiment_id: str) -> Experiment | None:
        """Retrieves an experiment from the repository."""
        return await self.repository.get_experiment(experiment_id)

    async def list_experiments(self) -> list[Experiment]:
        """Lists all experiments stored in the repository."""
        return await self.repository.list_experiments()

    def compare_experiment_runs(self, experiment: Experiment) -> dict[str, Any]:
        """Runs the comparer on the experiment's run history."""
        return ExperimentComparer.compare_runs(experiment.runs)

    def generate_summary(self, experiment: Experiment) -> str:
        """Generates a detailed markdown report for the experiment."""
        return ExperimentSummaryGenerator.generate_markdown_summary(experiment)
