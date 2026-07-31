import json
import os

from pydantic import ValidationError

from src.domain.entities.dataset import GoldenDataset, GoldenTestCase
from src.use_cases.datasets.validator import DatasetValidationError, DatasetValidator


class DatasetLoader:
    """Loader to parse and validate evaluation datasets in JSON and JSONL formats."""

    def __init__(self, validator: DatasetValidator | None = None) -> None:
        self.validator = validator or DatasetValidator()

    def load_json(self, filepath: str) -> GoldenDataset:
        """Loads and validates a GoldenDataset from a JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DatasetValidationError(f"Invalid JSON syntax in '{filepath}': {e}") from e
        except OSError as e:
            raise DatasetValidationError(f"Failed to read file '{filepath}': {e}") from e

        # Handle raw list format (benchmark cases array)
        if isinstance(data, list):
            dataset_id = os.path.splitext(os.path.basename(filepath))[0]
            name = dataset_id.replace("_", " ").title() + " Dataset"
            version = "1.0.0"
            try:
                test_cases = [GoldenTestCase.model_validate(item) for item in data]
            except ValidationError as e:
                errors = [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()]
                raise DatasetValidationError(
                    f"Dataset case schema validation failed in '{filepath}'", errors
                ) from e

            dataset = GoldenDataset(
                dataset_id=dataset_id,
                name=name,
                version=version,
                test_cases=test_cases,
                metadata={},
            )
        else:
            # Validate structure using Pydantic for standard wrapper format
            try:
                dataset = GoldenDataset.model_validate(data)
            except ValidationError as e:
                errors = [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()]
                raise DatasetValidationError(
                    f"Dataset schema validation failed in '{filepath}'", errors
                ) from e

        # Run semantic validator
        self.validator.validate(dataset)
        return dataset

    def load_jsonl(
        self,
        filepath: str,
        dataset_id: str | None = None,
        name: str | None = None,
        version: str | None = None,
    ) -> GoldenDataset:
        """Loads and validates a GoldenDataset from a JSONL file.

        Supports two formats:
        1. First line contains dataset metadata (dataset_id, name, version),
           followed by lines of test cases.
        2. Every line is a test case, with dataset metadata passed as parameter overrides.
        """
        lines: list[str] = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            raise DatasetValidationError(f"Failed to read file '{filepath}': {e}") from e

        if not lines:
            raise DatasetValidationError(f"JSONL dataset file '{filepath}' is empty.")

        metadata_dict: dict = {}
        test_cases: list[GoldenTestCase] = []
        errors: list[str] = []

        # Try to parse the first line
        first_line_parsed = False
        try:
            first_line_data = json.loads(lines[0].strip())
            # If the first line has dataset_id, it is metadata
            if isinstance(first_line_data, dict) and "dataset_id" in first_line_data:
                metadata_dict = first_line_data
                first_line_parsed = True
        except json.JSONDecodeError:
            # First line is not valid JSON or not metadata; we will treat it as a test case below
            pass

        start_index = 1 if first_line_parsed else 0

        for idx, line in enumerate(lines[start_index:], start=start_index + 1):
            line_str = line.strip()
            if not line_str:
                continue  # Skip empty lines

            try:
                case_data = json.loads(line_str)
                case = GoldenTestCase.model_validate(case_data)
                test_cases.append(case)
            except json.JSONDecodeError as e:
                errors.append(f"Line {idx}: Invalid JSON syntax - {e}")
            except ValidationError as e:
                pydantic_errs = ", ".join(
                    f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()
                )
                errors.append(f"Line {idx}: Schema validation failed - {pydantic_errs}")

        if errors:
            raise DatasetValidationError(f"JSONL dataset parsing failed for '{filepath}'", errors)

        # Merge metadata with parameters
        final_id = dataset_id or metadata_dict.get("dataset_id")
        final_name = (
            name or metadata_dict.get("name") or (f"{final_id} Dataset" if final_id else None)
        )
        final_version = version or metadata_dict.get("version") or "1.0.0"
        final_description = metadata_dict.get("description")
        final_metadata = metadata_dict.get("metadata") or {}

        if not final_id:
            raise DatasetValidationError(
                "Dataset 'dataset_id' is missing. "
                "Provide it in the first line of JSONL or pass as an override."
            )
        if not final_name:
            raise DatasetValidationError(
                "Dataset 'name' is missing. "
                "Provide it in the first line of JSONL or pass as an override."
            )

        dataset = GoldenDataset(
            dataset_id=final_id,
            name=final_name,
            description=final_description,
            version=final_version,
            test_cases=test_cases,
            metadata=final_metadata,
        )

        # Run semantic validator
        self.validator.validate(dataset)
        return dataset
