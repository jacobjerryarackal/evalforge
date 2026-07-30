from src.domain.entities import EvaluationRun, Experiment, GoldenDataset
from src.domain.interfaces.repository import EvaluationRepository


class InMemoryEvaluationRepository(EvaluationRepository):
    """An in-memory store for evaluation datasets and runs, suitable for testing and mocks."""

    def __init__(self) -> None:
        self._datasets: dict[tuple[str, str], GoldenDataset] = {}  # Keyed by (dataset_id, version)
        self._runs: dict[str, EvaluationRun] = {}  # Keyed by run_id
        self._experiments: dict[str, Experiment] = {}  # Keyed by experiment_id

    async def save_dataset(self, dataset: GoldenDataset) -> None:
        """Saves a dataset to the in-memory store by deep-copying it."""
        # Store using a compound key of (dataset_id, version) to support version tracking
        key = (dataset.dataset_id, dataset.version)
        self._datasets[key] = dataset.model_copy(deep=True)

    async def get_dataset(
        self, dataset_id: str, version: str | None = None
    ) -> GoldenDataset | None:
        """Retrieves a specific dataset version.

        If version is None, retrieves the latest sorted version.
        """
        if version is not None:
            dataset = self._datasets.get((dataset_id, version))
            return dataset.model_copy(deep=True) if dataset else None

        # Filter by dataset_id and find the latest version (string comparison / semantic sorting)
        matching_datasets = [ds for (d_id, v), ds in self._datasets.items() if d_id == dataset_id]
        if not matching_datasets:
            return None

        # Simple string-based semantic sort on version numbers
        matching_datasets.sort(key=lambda ds: ds.version)
        return matching_datasets[-1].model_copy(deep=True)

    async def list_datasets(self) -> list[GoldenDataset]:
        """Lists all golden datasets currently stored in the repository."""
        return [ds.model_copy(deep=True) for ds in self._datasets.values()]

    async def save_run(self, run: EvaluationRun) -> None:
        """Saves an evaluation run to memory."""
        self._runs[run.run_id] = run.model_copy(deep=True)

    async def get_run(self, run_id: str) -> EvaluationRun | None:
        """Retrieves a specific evaluation run."""
        run = self._runs.get(run_id)
        return run.model_copy(deep=True) if run else None

    async def list_runs(self, dataset_id: str | None = None) -> list[EvaluationRun]:
        """Lists all evaluation runs, optionally filtered by dataset ID."""
        runs = list(self._runs.values())
        if dataset_id is not None:
            runs = [r for r in runs if r.dataset_id == dataset_id]
        return [r.model_copy(deep=True) for r in runs]

    async def save_experiment(self, experiment: Experiment) -> None:
        """Saves an experiment to memory."""
        self._experiments[experiment.experiment_id] = experiment.model_copy(deep=True)

    async def get_experiment(self, experiment_id: str) -> Experiment | None:
        """Retrieves a specific experiment."""
        exp = self._experiments.get(experiment_id)
        return exp.model_copy(deep=True) if exp else None

    async def list_experiments(self) -> list[Experiment]:
        """Lists all experiments currently stored in the repository."""
        return [exp.model_copy(deep=True) for exp in self._experiments.values()]
