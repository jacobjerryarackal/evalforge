import logging
from typing import Dict, List, Tuple

from src.domain.entities.dataset import GoldenDataset

logger = logging.getLogger("evaluation.datasets.registry")


class DatasetRegistry:
    """Registry for discovery, registration, and uniqueness validation of GoldenDatasets."""

    def __init__(self) -> None:
        # Keyed by (dataset_id, version)
        self._datasets: Dict[Tuple[str, str], GoldenDataset] = {}

    def register(self, dataset: GoldenDataset) -> None:
        """Registers a GoldenDataset.

        Raises ValueError if the dataset_id and version combo is a duplicate.
        """
        key = (dataset.dataset_id, dataset.version)
        if key in self._datasets:
            raise ValueError(
                f"Dataset '{dataset.dataset_id}' with version "
                f"'{dataset.version}' is already registered."
            )
        self._datasets[key] = dataset
        logger.info(f"Registered dataset: {dataset.dataset_id} (v{dataset.version})")

    def get(self, dataset_id: str, version: str | None = None) -> GoldenDataset:
        """Retrieves a dataset by its ID and optional version.

        If version is not provided, retrieves the latest version based on semantic sorting.
        Raises ValueError if no matching dataset is found.
        """
        if version is not None:
            key = (dataset_id, version)
            if key not in self._datasets:
                raise ValueError(
                    f"Dataset '{dataset_id}' with version '{version}' is not registered."
                )
            return self._datasets[key]

        # Get all versions for the given dataset_id
        matching = [ds for (ds_id, v), ds in self._datasets.items() if ds_id == dataset_id]
        if not matching:
            raise ValueError(f"Dataset '{dataset_id}' is not registered.")

        # Sort based on semantic version numbers (simple string split comparison)
        def parse_version(ds: GoldenDataset) -> Tuple[int, ...]:
            try:
                # E.g. "1.2.3" -> (1, 2, 3)
                # Filter out non-numeric suffixes for sorting
                clean_v = ds.version.split("-")[0]
                return tuple(int(x) for x in clean_v.split("."))
            except ValueError:
                return (0,)

        matching.sort(key=parse_version)
        return matching[-1]

    def list_datasets(self) -> List[GoldenDataset]:
        """Returns all registered dataset instances."""
        return list(self._datasets.values())

    def list_keys(self) -> List[Tuple[str, str]]:
        """Returns a list of all registered (dataset_id, version) tuples."""
        return list(self._datasets.keys())
