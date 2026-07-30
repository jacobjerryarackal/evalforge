from abc import ABC, abstractmethod

from src.domain.entities import EvaluationRun, Experiment, GoldenDataset


class EvaluationRepository(ABC):
    """Abstract Repository interface for storing golden datasets and evaluation run results."""

    @abstractmethod
    async def save_dataset(self, dataset: GoldenDataset) -> None:
        """Saves or updates a golden dataset in the store."""
        pass

    @abstractmethod
    async def get_dataset(
        self, dataset_id: str, version: str | None = None
    ) -> GoldenDataset | None:
        """Retrieves a specific version of a golden dataset."""
        pass

    @abstractmethod
    async def list_datasets(self) -> list[GoldenDataset]:
        """Lists all golden datasets stored in the repository."""
        pass

    @abstractmethod
    async def save_run(self, run: EvaluationRun) -> None:
        """Saves an evaluation run's trajectory data and computed metrics."""
        pass

    @abstractmethod
    async def get_run(self, run_id: str) -> EvaluationRun | None:
        """Retrieves a past evaluation run by its ID."""
        pass

    @abstractmethod
    async def list_runs(self, dataset_id: str | None = None) -> list[EvaluationRun]:
        """Lists past evaluation runs, optionally filtered by dataset ID."""
        pass

    @abstractmethod
    async def save_experiment(self, experiment: Experiment) -> None:
        """Saves or updates an experiment in the repository."""
        pass

    @abstractmethod
    async def get_experiment(self, experiment_id: str) -> Experiment | None:
        """Retrieves a specific experiment by its ID."""
        pass

    @abstractmethod
    async def list_experiments(self) -> list[Experiment]:
        """Lists all experiments stored in the repository."""
        pass
